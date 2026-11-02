import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from visual_manifest import ManifestError, compare_manifests, create_manifest, load_manifest, validate_manifest


def png(width=2, height=3, pixel=b"\x00\xff\x00\x00"):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    rows = b"".join(b"\x00" + pixel * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def manifest(items): return {"version": 1, "screenshots": items}


def item(path="a.png", digest="a" * 64, width=10, height=20, size=100):
    return {"path": path, "width": width, "height": height, "bytes": size, "sha256": digest}


class ManifestTests(unittest.TestCase):
    def test_create_reads_dimensions_hash_and_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "nested").mkdir(); data = png(4, 5)
            (root / "nested" / "shot.png").write_bytes(data)
            result = create_manifest(root)["screenshots"][0]
            self.assertEqual((result["path"], result["width"], result["height"]), ("nested/shot.png", 4, 5))
            self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())

    def test_create_sorts_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "z.png").write_bytes(png()); (root / "a.png").write_bytes(png())
            self.assertEqual([x["path"] for x in create_manifest(root)["screenshots"]], ["a.png", "z.png"])

    def test_create_rejects_invalid_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "bad.png").write_bytes(b"not png")
            with self.assertRaises(ManifestError): create_manifest(root)

    def test_compare_unchanged(self):
        report = compare_manifests(manifest([item()]), manifest([item()]))
        self.assertEqual(report["status"], "unchanged")
        self.assertEqual(report["unchanged"], ["a.png"])

    def test_compare_added_and_removed(self):
        report = compare_manifests(manifest([item("old.png")]), manifest([item("new.png")]))
        self.assertEqual(report["added"], ["new.png"]); self.assertEqual(report["removed"], ["old.png"])

    def test_compare_lists_changed_fields(self):
        report = compare_manifests(manifest([item()]), manifest([item(digest="b" * 64, width=11)]))
        self.assertEqual(report["changed"], [{"path": "a.png", "changed_fields": ["width", "sha256"]}])

    def test_duplicate_paths_rejected_case_insensitively(self):
        with self.assertRaises(ManifestError): validate_manifest(manifest([item("A.png"), item("a.png", "b" * 64)]))

    def test_parent_path_rejected(self):
        with self.assertRaises(ManifestError): validate_manifest(manifest([item("../a.png")]))

    def test_bad_digest_rejected(self):
        with self.assertRaises(ManifestError): validate_manifest(manifest([item(digest="not-a-hash")]))

    def test_boolean_dimension_rejected(self):
        with self.assertRaises(ManifestError): validate_manifest(manifest([item(width=True)]))

    def test_unknown_manifest_field_rejected(self):
        data = manifest([]); data["extra"] = 1
        with self.assertRaises(ManifestError): validate_manifest(data)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"; path.write_text('{"version":1,"version":1,"screenshots":[]}', encoding="utf-8")
            with self.assertRaises(ManifestError): load_manifest(path)


if __name__ == "__main__": unittest.main()
