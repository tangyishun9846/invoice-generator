"""invoice_core 纯函数单元测试

跑法:
    python3 -m unittest discover -s tests
    或
    python3 -m unittest tests.test_invoice_core

不依赖 Chrome、不依赖真实 PDF, 任何环境都能跑通.
"""
import sys
import unittest
from pathlib import Path

# 让测试可以直接 import 项目根目录的模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from invoice_core import (
    num_to_words,
    format_port,
    _split_lines,
    parse_pi,
    parse_license,
    parse_booking,
)


class TestNumToWords(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(num_to_words(0), "ZERO")

    def test_single_digit(self):
        self.assertEqual(num_to_words(7), "SEVEN")

    def test_teens(self):
        self.assertEqual(num_to_words(13), "THIRTEEN")
        self.assertEqual(num_to_words(19), "NINETEEN")

    def test_tens(self):
        self.assertEqual(num_to_words(40), "FORTY")
        self.assertEqual(num_to_words(42), "FORTY-TWO")

    def test_hundreds(self):
        self.assertEqual(num_to_words(100), "ONE HUNDRED")
        self.assertEqual(num_to_words(305), "THREE HUNDRED AND FIVE")

    def test_thousands(self):
        self.assertEqual(num_to_words(1000), "ONE THOUSAND")
        self.assertEqual(
            num_to_words(48750),
            "FORTY-EIGHT THOUSAND SEVEN HUNDRED AND FIFTY",
        )

    def test_invoice_total_typical(self):
        # 125MT * USD 390 = 48750
        self.assertEqual(
            num_to_words(125 * 390),
            "FORTY-EIGHT THOUSAND SEVEN HUNDRED AND FIFTY",
        )

    def test_millions(self):
        self.assertEqual(num_to_words(1_000_000), "ONE MILLION")
        self.assertEqual(num_to_words(2_500_000), "TWO MILLION FIVE HUNDRED THOUSAND")


class TestFormatPort(unittest.TestCase):
    def test_two_word_input(self):
        full, city = format_port("KARACHI PAKISTAN")
        self.assertEqual(full, "KARACHI PORT, PAKISTAN")
        self.assertEqual(city, "KARACHI")

    def test_already_has_port(self):
        full, city = format_port("JEBEL ALI PORT, UAE")
        self.assertEqual(city, "JEBEL")  # 第一个 word

    def test_empty_input(self):
        full, city = format_port("", default_country="PAKISTAN")
        self.assertEqual(full, "PAKISTAN PORT")
        self.assertEqual(city, "UNKNOWN")

    def test_single_word(self):
        full, city = format_port("KARACHI", default_country="PAKISTAN")
        self.assertEqual(full, "KARACHI PORT, PAKISTAN")

    def test_comma_separated(self):
        full, city = format_port("KARACHI, PAKISTAN")
        self.assertEqual(full, "KARACHI PORT, PAKISTAN")
        self.assertEqual(city, "KARACHI")


class TestSplitLines(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_split_lines(""), [])

    def test_single_line(self):
        self.assertEqual(_split_lines("ONLY LINE"), ["ONLY LINE"])

    def test_pipe_separated(self):
        self.assertEqual(
            _split_lines("LINE A|LINE B|LINE C"),
            ["LINE A", "LINE B", "LINE C"],
        )

    def test_literal_backslash_n(self):
        # 兼容 .env 里写 \n 字面量的情况
        self.assertEqual(
            _split_lines("LINE A\\nLINE B"),
            ["LINE A", "LINE B"],
        )

    def test_strips_whitespace(self):
        self.assertEqual(
            _split_lines("  A  | B |  C  "),
            ["A", "B", "C"],
        )

    def test_skips_empty_segments(self):
        self.assertEqual(_split_lines("A||B|"), ["A", "B"])


class TestParseLicense(unittest.TestCase):
    def test_extracts_consignee_with_international(self):
        text = "Some header\nACME EXAMPLE INTERNATIONAL\n100 SAMPLE STREET\n"
        d = parse_license(text)
        self.assertEqual(d.get("consignee_name"), "ACME EXAMPLE INTERNATIONAL")

    def test_extracts_consignee_with_enterprises(self):
        text = "...\nFOOBAR ENTERPRISES\nSOME CITY, COUNTRY\n"
        d = parse_license(text)
        self.assertEqual(d.get("consignee_name"), "FOOBAR ENTERPRISES")

    def test_extracts_contract_no(self):
        text = "Contract: RFAB12345 issued on 20250227"
        d = parse_license(text)
        self.assertEqual(d.get("contract_no"), "RFAB12345")

    def test_extracts_contract_date(self):
        text = "Contract: RFAB12345 issued on 20250227 other-text"
        d = parse_license(text)
        self.assertEqual(d.get("contract_date"), "FEB,27,2025")

    def test_extracts_quantity_max_value(self):
        # 多个 *数字, 取最大值, 转 MT
        text = "Items: *1000 *125000 *500"
        d = parse_license(text)
        self.assertEqual(d.get("qty_kg"), 125000)
        self.assertEqual(d.get("qty_mt"), 125.0)


class TestParseBooking(unittest.TestCase):
    def test_extracts_loading_port_chinese(self):
        text = "装货港 DALIAN 卸货港 KARACHI PAKISTAN"
        d = parse_booking(text)
        self.assertEqual(d.get("port_loading"), "DALIAN")

    def test_extracts_discharge_port_chinese(self):
        text = "装货港 DALIAN 卸货港 KARACHI PAKISTAN"
        d = parse_booking(text)
        self.assertEqual(d.get("port_discharge_raw"), "KARACHI PAKISTAN")

    def test_fallback_keyword_match(self):
        # 没有"装货港"标签, 但文本含 DALIAN
        text = "Loading at DALIAN port, discharge to KARACHI"
        d = parse_booking(text)
        self.assertEqual(d.get("port_loading"), "DALIAN")
        self.assertEqual(d.get("port_discharge_raw"), "KARACHI PAKISTAN")


class TestParsePI(unittest.TestCase):
    def test_extracts_pi_no(self):
        text = "PI No.: PI-EXAMPLE-001\nPI Date: Aug, 07, 2025\n"
        d = parse_pi(text)
        self.assertEqual(d.get("pi_no"), "PI-EXAMPLE-001")

    def test_extracts_pi_date(self):
        text = "PI No.: PI-EXAMPLE-001\nPI Date: Aug, 07, 2025\n"
        d = parse_pi(text)
        self.assertEqual(d.get("pi_date"), "AUG,07,2025")

    def test_extracts_unit_price(self):
        text = "Total: USD 390/MT for the shipment"
        d = parse_pi(text)
        self.assertEqual(d.get("unit_price"), "390")
        self.assertEqual(d.get("price_unit"), "MT")

    def test_extracts_consignee_addr_with_hint(self):
        text = (
            "...header...\n"
            "ACME EXAMPLE INTERNATIONAL\n"
            "100 SAMPLE STREET, INDUSTRIAL ZONE,\n"
            "SOME CITY, COUNTRY.\n"
            "TAX ID: 0000000-0\n"
            "INCOTERMS: CFR PORT"
        )
        d = parse_pi(text, consignee_hint="ACME EXAMPLE INTERNATIONAL")
        addr = d.get("consignee_addr", "")
        self.assertIn("100 SAMPLE STREET", addr)
        self.assertIn("SOME CITY", addr)

    def test_hs_code(self):
        text = "Goods: Sample\nH.S. CODE: 1234.5678\n"
        d = parse_pi(text)
        self.assertEqual(d.get("hs_code"), "1234.5678")


if __name__ == "__main__":
    unittest.main()
