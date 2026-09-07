#!/usr/bin/env python3
"""Validate brand tokens and required SVG marks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand"
TOKENS = BRAND / "tokens.json"
REQUIRED_SVG = (
    "mark-opsdevcode.svg",
    "mark-opsdevcode-mono.svg",
    "mark-repave.svg",
    "mark-overpass.svg",
    "mark-toll.svg",
    "mark-dispatch.svg",
    "mark-repave-mono.svg",
    "mark-overpass-mono.svg",
    "mark-toll-mono.svg",
    "mark-dispatch-mono.svg",
    "lockup-opsdevcode.svg",
    "lockup-repave.svg",
    "lockup-overpass.svg",
    "lockup-toll.svg",
    "lockup-dispatch.svg",
    "favicon-opsdevcode.svg",
    "section-system.svg",
    "diagram-primitives.svg",
    "og-opsdevcode.svg",
    "wordmark-opsdevcode.svg",
)


class BrandSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tokens = json.loads(TOKENS.read_text(encoding="utf-8"))

    def test_thesis_named(self) -> None:
        thesis = self.tokens.get("thesis") or {}
        self.assertEqual(thesis.get("name"), "The governed section")
        self.assertIn("section", str(thesis.get("idea") or "").lower())

    def test_company_and_four_product_accents(self) -> None:
        company = self.tokens.get("company") or {}
        self.assertEqual(company.get("ink"), "#1A1F1C")
        self.assertEqual(company.get("paper"), "#F3EFE6")
        products = self.tokens.get("products") or {}
        self.assertEqual(set(products), {"repave", "overpass", "toll", "dispatch"})
        self.assertNotIn("convergence", products)
        self.assertNotIn("relay", products)
        for row in products.values():
            self.assertTrue(str(row.get("accent") or "").startswith("#"))

    def test_required_svgs_use_construction_stroke(self) -> None:
        svg_dir = BRAND / "svg"
        for name in REQUIRED_SVG:
            path = svg_dir / name
            self.assertTrue(path.is_file(), msg=name)
            text = path.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            if name.startswith("mark-"):
                self.assertIn("stroke-linecap=\"square\"", text)
                self.assertIn("stroke-width=\"1.5\"", text)


if __name__ == "__main__":
    unittest.main()
