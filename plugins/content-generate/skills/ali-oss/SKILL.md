---
name: ali-oss
description: Use when uploading files (images, articles, builds, any asset) to Aliyun OSS (阿里云对象存储) — supports configuring multiple named buckets, a default bucket, region auto-detection, listing/deleting objects, and generating presigned share URLs. Pure Python stdlib, no SDK install required.
---

# ali-oss

Upload files to Aliyun OSS (Object Storage Service) from the command line. The
script is **self-contained** — it implements OSS request signing (V1 / HMAC-SHA1)
using only the Python 3 standard library, so there is nothing to `pip install`.

Multiple buckets can be configured under named entries with one marked as the
default. Credentials and bucket config live **outside the repository** in
`~/.config/ali-oss/config.json` (mode `0600`) — they are never written into the
plugin source tree.

## Quick Start

```bash
SCRIPT=skills/ali-oss/scripts/ali_oss.py

# 1. Configure a bucket. Region is auto-detected from the account if omitted.
python3 $SCRIPT add-bucket my-bucket \
  --access-key-id "$ALI_OSS_ACCESS_KEY_ID" \
  --access-key-secret "$ALI_OSS_ACCESS_KEY_SECRET" \
  --default

# 2. Upload — the first configured/default bucket is used unless --bucket is given.
python3 $SCRIPT upload ./cover.png --prefix blog/2026
#   → https://my-bucket.oss-cn-beijing.aliyuncs.com/blog/2026/cover.png

# 3. Inspect / share / clean up
python3 $SCRIPT list --prefix blog/2026
python3 $SCRIPT sign-url blog/2026/cover.png --expires 3600   # presigned GET URL
python3 $SCRIPT delete blog/2026/cover.png
```

## Commands

| Command | Purpose |
|---------|---------|
| `add-bucket NAME` | Add/update a bucket. Auto-detects region via the GetService (ListBuckets) API unless `--endpoint`/`--region` is given. `--default` marks it default. |
| `remove-bucket NAME` | Remove a bucket from config (re-points default if needed). |
| `set-default NAME` | Set the default bucket. |
| `list-buckets` | List configured buckets (AccessKey secret never shown; ID masked). |
| `info` | Print config path + default bucket. |
| `upload PATH...` | Upload file(s) or a directory (`--recursive`). Options: `--bucket`, `--key` (single file), `--prefix`, `--content-type`, `--acl`, `--sign SECONDS`. |
| `list` | List objects. Options: `--bucket`, `--prefix`, `--max-keys`. |
| `delete KEY` | Delete an object (`--bucket`). |
| `sign-url KEY` | Presigned GET URL (`--bucket`, `--expires`, default 3600s). |

## Key resolution rules

- **Default bucket**: any command taking `--bucket` falls back to the configured
  default. The first bucket added becomes the default automatically.
- **Object key**: `upload` defaults the key to the file's basename. `--prefix foo/bar`
  prepends a remote folder. `--key` overrides the full key (single file only).
  Uploading a directory with `--recursive` mirrors its tree under the prefix.
- **Content-Type** is guessed from the filename; override with `--content-type`.

## Credentials & config

The config file (default `~/.config/ali-oss/config.json`) holds:

```json
{
  "default_bucket": "my-bucket",
  "buckets": {
    "my-bucket": {
      "access_key_id": "LTAI...",
      "access_key_secret": "....",
      "endpoint": "oss-cn-beijing.aliyuncs.com"
    }
  }
}
```

- Override the config location with `--config PATH` or `ALI_OSS_CONFIG`.
- `add-bucket` reads credentials from `--access-key-id`/`--access-key-secret` or,
  if absent, from `ALI_OSS_ACCESS_KEY_ID` / `ALI_OSS_ACCESS_KEY_SECRET`.
- The config dir is created `0700` and the file `0600`. Keep it out of version
  control. Treat AccessKey pairs as secrets — prefer a RAM user scoped to the
  target bucket(s) over a primary-account key, and rotate if exposed.

## Notes / limits

- Uploads use a single `PutObject` request (supports objects up to 5 GB). Files
  beyond that would need multipart upload, which this skill does not implement.
- Region auto-detection needs the `oss:ListBuckets` permission on the key. If the
  key is scoped to a single bucket without that permission, pass `--endpoint`
  (e.g. `oss-cn-beijing.aliyuncs.com`) or `--region cn-beijing` explicitly.
- Object public reachability depends on bucket/object ACL. Use `sign-url` to share
  objects in a private bucket without changing ACLs.

Run the offline tests with `python3 tests/test_ali_oss.py`.
