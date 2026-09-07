#!/usr/bin/env python3
"""Offline validation of the canonical family contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "portfolio" / "products.json"
EXPECTED_PRODUCT_IDS = ("repave", "overpass", "toll", "dispatch")
MATURITY = frozenset({"early-access", "in-development", "emerging"})
ENDORSEMENT_ID = "by-opsdevcode"


def load_contract() -> dict[str, Any]:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("products.json must be a mapping")
    return data


def _http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


class PortfolioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_contract()

    def test_schema_version_and_company(self) -> None:
        self.assertEqual(self.data.get("schema_version"), 1)
        company = self.data.get("company")
        self.assertIsInstance(company, dict)
        self.assertEqual(company.get("name"), "OpsDevCode")
        self.assertEqual(company.get("role"), "company")
        self.assertTrue(str(company.get("positioning") or "").strip())
        self.assertTrue(_http_url(str(company.get("public_url") or "")))

    def test_exactly_four_named_products(self) -> None:
        products = self.data.get("products")
        self.assertIsInstance(products, dict)
        self.assertEqual(set(products), set(EXPECTED_PRODUCT_IDS))
        self.assertEqual(len(products), 4)

    def test_convergence_is_not_a_product(self) -> None:
        products = self.data["products"]
        for key in products:
            self.assertNotEqual(key.lower(), "convergence")
            name = str(products[key].get("name") or "").lower()
            self.assertNotEqual(name, "convergence")
        methodology = self.data.get("methodology") or {}
        conv = methodology.get("convergence") or {}
        self.assertEqual(conv.get("relationship"), "independent")
        self.assertNotIn("convergence", products)

    def test_relay_is_not_in_the_product_collection(self) -> None:
        self.assertNotIn("relay", self.data["products"])
        internals = self.data.get("internals") or {}
        self.assertEqual((internals.get("relay") or {}).get("relationship"), "internal-runtime")

    def test_product_required_fields_and_unique_urls(self) -> None:
        products = self.data["products"]
        urls: list[str] = []
        for pid in EXPECTED_PRODUCT_IDS:
            row = products[pid]
            self.assertEqual(row.get("endorsement"), ENDORSEMENT_ID)
            self.assertTrue(str(row.get("name") or "").strip())
            self.assertTrue(str(row.get("semantic_role") or "").strip())
            self.assertTrue(str(row.get("role") or "").strip())
            maturity = row.get("maturity")
            self.assertIn(maturity, MATURITY, msg=f"{pid} maturity {maturity!r}")
            url = str(row.get("public_url") or "")
            self.assertTrue(_http_url(url), msg=f"{pid} public_url")
            urls.append(url.rstrip("/").lower())
            aliases = row.get("aliases") or []
            self.assertIsInstance(aliases, list)
            for alias in aliases:
                self.assertTrue(_http_url(str(alias)), msg=f"{pid} alias")
                urls.append(str(alias).rstrip("/").lower())
        self.assertEqual(len(urls), len(set(urls)), msg=f"duplicate URLs: {urls}")

    def test_endorsement_form(self) -> None:
        endorsement = (self.data.get("family") or {}).get("endorsement") or {}
        self.assertEqual(endorsement.get("id"), ENDORSEMENT_ID)
        self.assertIn("{product}", str(endorsement.get("form") or ""))
        self.assertIn("OpsDevCode", str(endorsement.get("form") or ""))

    def test_maturity_vocabulary_covers_assignments(self) -> None:
        vocab = self.data.get("maturity_vocabulary") or {}
        self.assertEqual(set(vocab), MATURITY)
        for pid, row in self.data["products"].items():
            self.assertIn(row["maturity"], vocab, msg=pid)

    def test_invariants_include_independence_and_host_routing(self) -> None:
        text = "\n".join(str(item) for item in (self.data.get("invariants") or []))
        self.assertIn("independently understandable", text.lower())
        self.assertIn("Repave is not the shell", text)
        self.assertIn("Host headers", text)
        self.assertIn("CNAME", text)
        self.assertIn("plain English", text)

    def test_public_content_layers_and_audience(self) -> None:
        content = (self.data.get("family") or {}).get("public_content") or {}
        self.assertEqual(content.get("rule"), "plain-english-first")
        self.assertEqual(
            content.get("layers"),
            [
                "outcome",
                "problem",
                "product",
                "workflow",
                "mechanism",
                "proof",
                "system",
                "action",
            ],
        )
        self.assertEqual(
            set(content.get("audience_tests") or []),
            {"senior-application-engineer", "staff-platform-engineer"},
        )
        self.assertEqual(
            (self.data.get("family") or {}).get("shared_implementation"),
            "documented-primitives",
        )
        self.assertEqual((self.data.get("family") or {}).get("company_mark"), "unapproved")
        classes = self.data.get("capability_classes") or {}
        self.assertEqual(set(classes), {"available", "preview", "in-development", "planned"})

    def test_product_plain_english_and_site_owner(self) -> None:
        owners = {
            "repave": "opsdevcode/repave",
            "overpass": "opsdevcode/overpass",
            "toll": "opsdevcode/toll",
            "dispatch": "opsdevcode/dispatch",
        }
        for pid, owner in owners.items():
            row = self.data["products"][pid]
            self.assertTrue(str(row.get("plain_english") or "").strip(), msg=pid)
            self.assertTrue(str(row.get("visual_concept") or "").strip(), msg=pid)
            self.assertEqual(row.get("site_owner"), owner)
        docs = ROOT / "portfolio" / "public-content.md"
        visual = ROOT / "portfolio" / "visual-family.md"
        self.assertTrue(docs.is_file())
        self.assertTrue(visual.is_file())
        self.assertIn("Plain English first", docs.read_text(encoding="utf-8"))
        self.assertIn("wordmark", visual.read_text(encoding="utf-8"))
        self.assertNotIn("Relay", " ".join(p["name"] for p in self.data["products"].values()))


if __name__ == "__main__":
    unittest.main()
