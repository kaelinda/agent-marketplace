#!/usr/bin/env python3
"""ali_oss.py — Upload files to Aliyun OSS with multi-bucket config support.

Self-contained: depends only on the Python 3 standard library. It implements
Aliyun OSS request signing (V1 / HMAC-SHA1) directly, so no `oss2` SDK install
is required.

Config lives OUTSIDE the repo (default: ~/.config/ali-oss/config.json, mode 600)
and stores one or more named buckets plus a default bucket. Credentials are
never written into the plugin source tree.

Commands:
  add-bucket NAME      Add / update a bucket (auto-detects region if omitted)
  remove-bucket NAME   Remove a bucket from config
  set-default NAME     Set the default bucket
  list-buckets         Show configured buckets (secrets masked)
  info                 Show config path + default bucket
  upload PATH...       Upload one or more files / a directory (--recursive)
  list                 List objects in a bucket (--prefix, --max-keys)
  delete KEY           Delete an object
  sign-url KEY         Generate a presigned GET URL (--expires)

Run `ali_oss.py <command> -h` for per-command options.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import formatdate

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG_PATH = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "ali-oss",
    "config.json",
)
SERVICE_ENDPOINT = "oss.aliyuncs.com"  # GetService (ListBuckets), region-agnostic
USER_AGENT = "ali-oss-skill/1.0 (+python-stdlib)"


def config_path(args) -> str:
    return (
        getattr(args, "config", None)
        or os.environ.get("ALI_OSS_CONFIG")
        or DEFAULT_CONFIG_PATH
    )


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        return {"default_bucket": None, "buckets": {}}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("default_bucket", None)
    data.setdefault("buckets", {})
    return data


def save_config(path: str, config: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        os.chmod(os.path.dirname(path), 0o700)
    except OSError:
        pass
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def resolve_bucket(config: dict, name: str | None) -> tuple[str, dict]:
    """Return (bucket_name, bucket_cfg). Falls back to the default bucket."""
    name = name or config.get("default_bucket")
    if not name:
        raise SystemExit(
            "No bucket specified and no default bucket configured. "
            "Use --bucket NAME or `set-default NAME`."
        )
    buckets = config.get("buckets", {})
    if name not in buckets:
        raise SystemExit(
            f"Bucket '{name}' is not configured. Configured: "
            f"{', '.join(buckets) or '(none)'}"
        )
    return name, buckets[name]


# --------------------------------------------------------------------------- #
# OSS V1 signing + HTTP
# --------------------------------------------------------------------------- #

# Subresources that participate in the V1 CanonicalizedResource.
_SIGNED_SUBRESOURCES = {
    "acl", "uploads", "location", "cors", "logging", "website", "referer",
    "lifecycle", "delete", "append", "tagging", "objectMeta", "uploadId",
    "partNumber", "security-token", "position", "img", "style", "styleName",
    "replication", "replicationProgress", "replicationLocation", "cname",
    "bucketInfo", "comp", "qos", "live", "status", "vod", "startTime",
    "endTime", "symlink", "x-oss-process", "response-content-type",
    "response-content-language", "response-expires", "response-cache-control",
    "response-content-disposition", "response-content-encoding", "udf",
    "udfName", "udfImage", "udfId", "udfImageInfo", "udfApplication", "udfApplicationLog",
    "restore", "callback", "callback-var",
}


class OSSError(RuntimeError):
    def __init__(self, status, code, message, endpoint=None, raw=""):
        self.status = status
        self.code = code
        self.message = message
        self.endpoint = endpoint
        self.raw = raw
        detail = f"OSS error {status} {code}: {message}"
        if endpoint:
            detail += f" (correct endpoint: {endpoint})"
        super().__init__(detail)


def _gmt_now() -> str:
    return formatdate(timeval=None, localtime=False, usegmt=True)


def _canonicalized_resource(bucket: str | None, key: str, query: dict | None) -> str:
    if bucket:
        resource = "/" + bucket + "/" + key
    else:
        resource = "/"
    if query:
        signed = []
        for k in sorted(query):
            if k in _SIGNED_SUBRESOURCES:
                v = query[k]
                signed.append(k if v is None or v == "" else f"{k}={v}")
        if signed:
            resource += "?" + "&".join(signed)
    return resource


def _canonicalized_oss_headers(extra_headers: dict | None) -> str:
    """Build CanonicalizedOSSHeaders: every x-oss-* header, lowercased, sorted,
    joined as "k:v\\n". Must be part of the string-to-sign or a request carrying
    e.g. x-oss-object-acl fails with SignatureDoesNotMatch."""
    if not extra_headers:
        return ""
    oss_hdrs = {
        k.lower(): str(v).strip()
        for k, v in extra_headers.items()
        if k.lower().startswith("x-oss-")
    }
    return "".join(f"{k}:{oss_hdrs[k]}\n" for k in sorted(oss_hdrs))


def _sign(secret: str, string_to_sign: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def _parse_oss_error(status: int, body: bytes) -> OSSError:
    code = message = endpoint = ""
    text = body.decode("utf-8", "replace") if body else ""
    try:
        root = ET.fromstring(text)
        code = (root.findtext("Code") or "").strip()
        message = (root.findtext("Message") or "").strip()
        endpoint = (root.findtext("Endpoint") or "").strip()
    except ET.ParseError:
        message = text[:500]
    return OSSError(status, code or "Unknown", message or "(no message)", endpoint or None, text)


def oss_request(
    method: str,
    bucket: str | None,
    endpoint: str | None,
    key: str,
    cfg: dict,
    *,
    body: bytes | None = None,
    content_type: str = "",
    query: dict | None = None,
    extra_headers: dict | None = None,
    timeout: int = 120,
):
    """Perform a signed OSS request. Returns (status, headers, body_bytes)."""
    ak = cfg["access_key_id"]
    sk = cfg["access_key_secret"]
    host = endpoint if bucket is None else f"{bucket}.{endpoint}"
    if bucket is None:
        host = SERVICE_ENDPOINT

    date = _gmt_now()
    canon_resource = _canonicalized_resource(bucket, key, query)
    canon_headers = _canonicalized_oss_headers(extra_headers)
    string_to_sign = f"{method}\n\n{content_type}\n{date}\n{canon_headers}{canon_resource}"
    signature = _sign(sk, string_to_sign)

    path = "/" + urllib.parse.quote(key, safe="/~")
    if query:
        qs = urllib.parse.urlencode(
            {k: ("" if v is None else v) for k, v in query.items()}
        )
        path += "?" + qs
    url = f"https://{host}{path}"

    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Date", date)
    req.add_header("Authorization", f"OSS {ak}:{signature}")
    req.add_header("User-Agent", USER_AGENT)
    if content_type:
        req.add_header("Content-Type", content_type)
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        raise _parse_oss_error(exc.code, exc.read()) from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error contacting {host}: {exc.reason}") from None


# --------------------------------------------------------------------------- #
# OSS operations
# --------------------------------------------------------------------------- #

def detect_region(cfg: dict, bucket: str) -> str:
    """Return the OSS region endpoint (e.g. 'oss-cn-hangzhou.aliyuncs.com')
    for `bucket` by listing all buckets via the region-agnostic GetService API."""
    status, _, body = oss_request("GET", None, None, "", cfg)
    root = ET.fromstring(body.decode("utf-8", "replace"))
    for b in root.iter("Bucket"):
        name = (b.findtext("Name") or "").strip()
        if name == bucket:
            location = (b.findtext("Location") or "").strip()  # e.g. oss-cn-hangzhou
            extranet = (b.findtext("ExtranetEndpoint") or "").strip()
            if extranet:
                return extranet
            if location:
                return f"{location}.aliyuncs.com"
    raise SystemExit(
        f"Bucket '{bucket}' was not found under this account. "
        "Check the bucket name / credentials, or pass --endpoint explicitly."
    )


def put_object(cfg: dict, bucket: str, endpoint: str, key: str, local_path: str,
               content_type: str | None, acl: str | None) -> str:
    with open(local_path, "rb") as fh:
        data = fh.read()
    if not content_type:
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    extra = {"Content-Length": str(len(data))}
    if acl:
        extra["x-oss-object-acl"] = acl
    oss_request(
        "PUT", bucket, endpoint, key, cfg,
        body=data, content_type=content_type, extra_headers=extra,
    )
    return f"https://{bucket}.{endpoint}/{urllib.parse.quote(key, safe='/~')}"


def list_objects(cfg: dict, bucket: str, endpoint: str, prefix: str, max_keys: int):
    query = {"prefix": prefix, "max-keys": str(max_keys)}
    _, _, body = oss_request("GET", bucket, endpoint, "", cfg, query=query)
    root = ET.fromstring(body.decode("utf-8", "replace"))
    items = []
    for c in root.iter("Contents"):
        items.append({
            "key": (c.findtext("Key") or "").strip(),
            "size": int((c.findtext("Size") or "0").strip() or 0),
            "modified": (c.findtext("LastModified") or "").strip(),
        })
    return items


def delete_object(cfg: dict, bucket: str, endpoint: str, key: str) -> None:
    oss_request("DELETE", bucket, endpoint, key, cfg)


def sign_url(cfg: dict, bucket: str, endpoint: str, key: str, expires_in: int) -> str:
    import time
    expires = int(time.time()) + expires_in
    string_to_sign = f"GET\n\n\n{expires}\n/{bucket}/{key}"
    signature = _sign(cfg["access_key_secret"], string_to_sign)
    qs = urllib.parse.urlencode({
        "OSSAccessKeyId": cfg["access_key_id"],
        "Expires": expires,
        "Signature": signature,
    })
    path = urllib.parse.quote(key, safe="/~")
    return f"https://{bucket}.{endpoint}/{path}?{qs}"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def mask(secret: str) -> str:
    if not secret:
        return "(empty)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return secret[:3] + "*" * (len(secret) - 6) + secret[-3:]


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def resolve_credentials(args) -> tuple[str, str]:
    ak = args.access_key_id or os.environ.get("ALI_OSS_ACCESS_KEY_ID")
    sk = args.access_key_secret or os.environ.get("ALI_OSS_ACCESS_KEY_SECRET")
    if not ak or not sk:
        raise SystemExit(
            "Missing credentials. Pass --access-key-id / --access-key-secret "
            "or set ALI_OSS_ACCESS_KEY_ID / ALI_OSS_ACCESS_KEY_SECRET."
        )
    return ak, sk


def iter_upload_targets(paths, recursive):
    """Yield (local_path, relative_key_part) for each file to upload."""
    for p in paths:
        if os.path.isdir(p):
            if not recursive:
                raise SystemExit(f"'{p}' is a directory; pass --recursive to upload it.")
            base = os.path.basename(os.path.normpath(p))
            for root, _, files in os.walk(p):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.join(base, os.path.relpath(full, p))
                    yield full, rel.replace(os.sep, "/")
        elif os.path.isfile(p):
            yield p, os.path.basename(p)
        else:
            raise SystemExit(f"Path not found: {p}")


# --------------------------------------------------------------------------- #
# Command handlers
# --------------------------------------------------------------------------- #

def cmd_add_bucket(args):
    path = config_path(args)
    config = load_config(path)
    ak, sk = resolve_credentials(args)
    bucket_cfg = {"access_key_id": ak, "access_key_secret": sk}

    endpoint = args.endpoint
    if not endpoint and args.region:
        region = args.region if args.region.endswith("aliyuncs.com") else f"{args.region}.aliyuncs.com"
        endpoint = region
    if not endpoint:
        print(f"Auto-detecting region for bucket '{args.name}' ...", file=sys.stderr)
        endpoint = detect_region(bucket_cfg, args.name)
        print(f"  → {endpoint}", file=sys.stderr)
    bucket_cfg["endpoint"] = endpoint

    config["buckets"][args.name] = bucket_cfg
    if args.default or not config.get("default_bucket"):
        config["default_bucket"] = args.name
    save_config(path, config)
    is_default = " (default)" if config["default_bucket"] == args.name else ""
    print(f"Saved bucket '{args.name}'{is_default} → {endpoint}")
    print(f"Config: {path}")


def cmd_remove_bucket(args):
    path = config_path(args)
    config = load_config(path)
    if args.name not in config["buckets"]:
        raise SystemExit(f"Bucket '{args.name}' is not configured.")
    del config["buckets"][args.name]
    if config.get("default_bucket") == args.name:
        config["default_bucket"] = next(iter(config["buckets"]), None)
    save_config(path, config)
    print(f"Removed bucket '{args.name}'. Default is now: {config['default_bucket']}")


def cmd_set_default(args):
    path = config_path(args)
    config = load_config(path)
    if args.name not in config["buckets"]:
        raise SystemExit(f"Bucket '{args.name}' is not configured.")
    config["default_bucket"] = args.name
    save_config(path, config)
    print(f"Default bucket set to '{args.name}'.")


def cmd_list_buckets(args):
    path = config_path(args)
    config = load_config(path)
    buckets = config.get("buckets", {})
    if not buckets:
        print("No buckets configured. Add one with `add-bucket`.")
        return
    default = config.get("default_bucket")
    for name, cfg in buckets.items():
        flag = " *" if name == default else "  "
        print(f"{flag} {name}")
        print(f"     endpoint: {cfg.get('endpoint', '(unset)')}")
        print(f"     access_key_id: {mask(cfg.get('access_key_id', ''))}")
    print(f"\n* = default   |   config: {path}")


def cmd_info(args):
    path = config_path(args)
    config = load_config(path)
    print(f"Config path:    {path}")
    print(f"Config exists:  {os.path.exists(path)}")
    print(f"Default bucket: {config.get('default_bucket')}")
    print(f"Buckets:        {', '.join(config.get('buckets', {})) or '(none)'}")


def cmd_upload(args):
    path = config_path(args)
    config = load_config(path)
    bucket, cfg = resolve_bucket(config, args.bucket)
    endpoint = cfg["endpoint"]
    prefix = args.prefix.strip("/")

    targets = list(iter_upload_targets(args.paths, args.recursive))
    if not targets:
        raise SystemExit("Nothing to upload.")

    for local, rel_key in targets:
        if args.key and len(targets) == 1:
            key = args.key.lstrip("/")
        else:
            key = rel_key
        if prefix:
            key = f"{prefix}/{key}"
        url = put_object(cfg, bucket, endpoint, key, local, args.content_type, args.acl)
        if args.quiet:
            # Machine-readable: just the URL, one per line (for scripting / piping).
            print(url)
            continue
        size = human_size(os.path.getsize(local))
        print(f"✓ {local}  ({size})")
        print(f"  → {url}")
        if args.sign:
            print(f"  signed: {sign_url(cfg, bucket, endpoint, key, args.sign)}")


def cmd_list(args):
    path = config_path(args)
    config = load_config(path)
    bucket, cfg = resolve_bucket(config, args.bucket)
    items = list_objects(cfg, bucket, cfg["endpoint"], args.prefix, args.max_keys)
    if not items:
        print(f"(no objects in {bucket}/{args.prefix})")
        return
    for it in items:
        print(f"{human_size(it['size']):>10}  {it['modified']}  {it['key']}")
    print(f"\n{len(items)} object(s) in '{bucket}' (prefix='{args.prefix}')")


def cmd_delete(args):
    path = config_path(args)
    config = load_config(path)
    bucket, cfg = resolve_bucket(config, args.bucket)
    delete_object(cfg, bucket, cfg["endpoint"], args.key.lstrip("/"))
    print(f"Deleted {bucket}/{args.key.lstrip('/')}")


def cmd_sign_url(args):
    path = config_path(args)
    config = load_config(path)
    bucket, cfg = resolve_bucket(config, args.bucket)
    print(sign_url(cfg, bucket, cfg["endpoint"], args.key.lstrip("/"), args.expires))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ali_oss.py",
        description="Upload files to Aliyun OSS with multi-bucket config support.",
    )
    p.add_argument("--config", help="Override config path (default: ~/.config/ali-oss/config.json)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add-bucket", help="Add / update a bucket")
    a.add_argument("name", help="Bucket name (must match the real OSS bucket)")
    a.add_argument("--access-key-id", help="AccessKey ID (or env ALI_OSS_ACCESS_KEY_ID)")
    a.add_argument("--access-key-secret", help="AccessKey Secret (or env ALI_OSS_ACCESS_KEY_SECRET)")
    a.add_argument("--endpoint", help="Endpoint, e.g. oss-cn-hangzhou.aliyuncs.com (auto-detected if omitted)")
    a.add_argument("--region", help="Region, e.g. oss-cn-hangzhou (alternative to --endpoint)")
    a.add_argument("--default", action="store_true", help="Set as the default bucket")
    a.set_defaults(func=cmd_add_bucket)

    r = sub.add_parser("remove-bucket", help="Remove a bucket")
    r.add_argument("name")
    r.set_defaults(func=cmd_remove_bucket)

    s = sub.add_parser("set-default", help="Set the default bucket")
    s.add_argument("name")
    s.set_defaults(func=cmd_set_default)

    lb = sub.add_parser("list-buckets", help="List configured buckets")
    lb.set_defaults(func=cmd_list_buckets)

    i = sub.add_parser("info", help="Show config location + default bucket")
    i.set_defaults(func=cmd_info)

    u = sub.add_parser("upload", help="Upload file(s) / a directory")
    u.add_argument("paths", nargs="+", help="Local file(s) or directory")
    u.add_argument("--bucket", help="Target bucket (default: configured default)")
    u.add_argument("--key", help="Remote object key (single file only)")
    u.add_argument("--prefix", default="", help="Key prefix / remote folder")
    u.add_argument("--content-type", help="Override Content-Type")
    u.add_argument("--acl", choices=["private", "public-read", "public-read-write", "default"],
                   help="Per-object ACL")
    u.add_argument("--recursive", action="store_true", help="Recurse into directories")
    u.add_argument("--quiet", action="store_true",
                   help="Print only the uploaded URL(s), one per line (for scripting)")
    u.add_argument("--sign", type=int, metavar="SECONDS",
                   help="Also print a presigned URL valid for SECONDS")
    u.set_defaults(func=cmd_upload)

    ls = sub.add_parser("list", help="List objects")
    ls.add_argument("--bucket")
    ls.add_argument("--prefix", default="")
    ls.add_argument("--max-keys", type=int, default=100)
    ls.set_defaults(func=cmd_list)

    d = sub.add_parser("delete", help="Delete an object")
    d.add_argument("key")
    d.add_argument("--bucket")
    d.set_defaults(func=cmd_delete)

    su = sub.add_parser("sign-url", help="Generate a presigned GET URL")
    su.add_argument("key")
    su.add_argument("--bucket")
    su.add_argument("--expires", type=int, default=3600, help="Seconds until expiry (default 3600)")
    su.set_defaults(func=cmd_sign_url)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except OSSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
