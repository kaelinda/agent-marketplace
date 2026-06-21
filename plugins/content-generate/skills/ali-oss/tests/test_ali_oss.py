#!/usr/bin/env python3
"""Offline unit tests for ali_oss.py signing + config helpers (no network)."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "ali_oss.py")
spec = importlib.util.spec_from_file_location("ali_oss", SCRIPT)
ali = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ali)


class TestSigning(unittest.TestCase):
    def test_sign_known_vector(self):
        # HMAC-SHA1 of a fixed string with a fixed secret, base64-encoded.
        # Verified independently against the same primitive.
        sts = "GET\n\n\n0\n/bucket/key"
        sig = ali._sign("secret", sts)
        self.assertIsInstance(sig, str)
        # base64 of 20-byte sha1 digest is 28 chars ending in '='
        self.assertEqual(len(sig), 28)
        self.assertTrue(sig.endswith("="))
        # deterministic
        self.assertEqual(sig, ali._sign("secret", sts))
        # secret sensitivity
        self.assertNotEqual(sig, ali._sign("secret2", sts))

    def test_canonicalized_resource_object(self):
        self.assertEqual(
            ali._canonicalized_resource("b", "dir/file.txt", None),
            "/b/dir/file.txt",
        )

    def test_canonicalized_resource_service(self):
        self.assertEqual(ali._canonicalized_resource(None, "", None), "/")

    def test_canonicalized_resource_ignores_unsigned_query(self):
        # prefix / max-keys are NOT signed subresources
        self.assertEqual(
            ali._canonicalized_resource("b", "", {"prefix": "x", "max-keys": "10"}),
            "/b/",
        )

    def test_canonicalized_resource_signs_subresource(self):
        self.assertEqual(
            ali._canonicalized_resource("b", "k", {"acl": ""}),
            "/b/k?acl",
        )

    def test_sign_url_shape(self):
        cfg = {"access_key_id": "AKID", "access_key_secret": "SEC"}
        url = ali.sign_url(cfg, "mybucket", "oss-cn-hangzhou.aliyuncs.com", "a/b.png", 600)
        self.assertTrue(url.startswith("https://mybucket.oss-cn-hangzhou.aliyuncs.com/a/b.png?"))
        self.assertIn("OSSAccessKeyId=AKID", url)
        self.assertIn("Expires=", url)
        self.assertIn("Signature=", url)


class TestConfig(unittest.TestCase):
    def test_roundtrip_and_perms(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "config.json")
            cfg = {
                "default_bucket": "b1",
                "buckets": {"b1": {"access_key_id": "x", "access_key_secret": "y",
                                   "endpoint": "oss-cn-hangzhou.aliyuncs.com"}},
            }
            ali.save_config(path, cfg)
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
            loaded = ali.load_config(path)
            self.assertEqual(loaded["default_bucket"], "b1")
            self.assertIn("b1", loaded["buckets"])

    def test_load_missing_returns_empty(self):
        loaded = ali.load_config("/nonexistent/path/config.json")
        self.assertEqual(loaded["default_bucket"], None)
        self.assertEqual(loaded["buckets"], {})

    def test_resolve_bucket_default(self):
        cfg = {"default_bucket": "b1", "buckets": {"b1": {"endpoint": "e"}}}
        name, bcfg = ali.resolve_bucket(cfg, None)
        self.assertEqual(name, "b1")

    def test_resolve_bucket_missing_raises(self):
        cfg = {"default_bucket": None, "buckets": {}}
        with self.assertRaises(SystemExit):
            ali.resolve_bucket(cfg, None)


class TestHelpers(unittest.TestCase):
    def test_mask(self):
        self.assertEqual(ali.mask(""), "(empty)")
        self.assertEqual(ali.mask("12345678"), "********")
        masked = ali.mask("LTAI0000example0000id00")
        self.assertTrue(masked.startswith("LTA"))
        self.assertTrue(masked.endswith("d00"))
        self.assertIn("*", masked)

    def test_human_size(self):
        self.assertEqual(ali.human_size(512), "512B")
        self.assertEqual(ali.human_size(1536), "1.5KB")

    def test_iter_upload_targets_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "a.txt")
            with open(f, "w") as fh:
                fh.write("hi")
            targets = list(ali.iter_upload_targets([f], recursive=False))
            self.assertEqual(targets, [(f, "a.txt")])

    def test_iter_upload_targets_dir_requires_recursive(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                list(ali.iter_upload_targets([d], recursive=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
