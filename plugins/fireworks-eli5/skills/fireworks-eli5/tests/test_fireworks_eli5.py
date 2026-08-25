#!/usr/bin/env python3
"""Offline contract and renderer smoke tests for the fireworks-eli5 skill."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SKILL_DIR = ROOT / "plugins" / "fireworks-eli5" / "skills" / "fireworks-eli5"
SKILL = SKILL_DIR / "SKILL.md"
PLUGIN_MANIFEST = ROOT / "plugins" / "fireworks-eli5" / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
VERSION = ROOT / "VERSION"


def read_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    if not match:
        return {}
    values: dict[str, str] = {}
    current: str | None = None
    for line in match.group(1).splitlines():
        head = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if head:
            current = head.group(1)
            values[current] = head.group(2).strip()
        elif current and line.startswith(" "):
            values[current] += " " + line.strip()
    return values


class FireworksEli5ContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_workflow_contract(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = read_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "fireworks-eli5")
        self.assertIn("小白", frontmatter.get("description", ""))
        for phrase in (
            "3–5",
            "generate-from-template.py",
            "validate-svg.sh",
            "generate-diagram.sh",
            "cairosvg",
            "自包含",
            "不要上传",
            "[需确认]",
            'OUT_DIR="./fireworks-eli5/<topic-slug>"',
            'mkdir -p "$OUT_DIR"',
            '<<\'JSON\'',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertNotIn("./<topic-slug>.svg '<json-data>'", text)

    def test_validator_uses_unique_render_temp_file(self) -> None:
        text = (SKILL_DIR / "scripts" / "validate-svg.sh").read_text(encoding="utf-8")
        self.assertIn("mktemp", text)
        self.assertIn("trap", text)
        self.assertNotIn("/tmp/test-output.png", text)

    def test_manifest_and_marketplace_parity(self) -> None:
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        entry = next(item for item in marketplace["plugins"] if item["name"] == "fireworks-eli5")
        self.assertEqual(manifest["name"], entry["name"])
        self.assertEqual(entry["source"], "./plugins/fireworks-eli5")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(VERSION.read_text(encoding="utf-8").strip(), marketplace["metadata"]["version"])

    def test_renderer_and_validator_smoke(self) -> None:
        fixture = SKILL_DIR / "fixtures" / "agent-memory-types-style4.json"
        data = fixture.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "memory.svg"
            subprocess.run(
                [sys.executable, str(SKILL_DIR / "scripts" / "generate-from-template.py"), "memory", str(output)],
                input=data,
                check=True,
                capture_output=True,
                text=True,
            )
            ET.parse(output)
            subprocess.run(["bash", str(SKILL_DIR / "scripts" / "validate-svg.sh"), str(output)], check=True)
            subprocess.run(
                ["bash", str(SKILL_DIR / "scripts" / "generate-diagram.sh"), "-t", "memory", "-s", "4", "-o", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            png = output.with_suffix(".png")
            self.assertTrue(png.is_file())
            self.assertGreater(png.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
