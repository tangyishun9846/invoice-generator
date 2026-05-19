# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-05-19

First public open-source release. 首次开源发布.

### Added
- `.env.example` listing every configurable knob (seller info, defaults, regex, paths).
- `README.md` (bilingual zh/en) with quick start, configuration, deployment, contributing.
- `LICENSE` (MIT).
- `CONTRIBUTING.md` (bilingual) with dev setup, PR guidance, sensitive-data warning.
- `tests/test_invoice_core.py` with 32 unit tests covering all pure parsing helpers (`num_to_words`, `format_port`, `_split_lines`, `parse_pi`, `parse_license`, `parse_booking`). Run with `python3 -m unittest discover -s tests`.

### Changed
- **Breaking-ish for self-hosters**: all seller-specific values moved from hardcoded constants to environment variables. See `.env.example` for the full list. If you're upgrading an existing deployment, set these env vars in your hosting platform before redeploying — otherwise the invoice's `From:` block will show the placeholder `YOUR COMPANY NAME CO.,LTD`.
  - `SELLER_NAME`, `SELLER_ADDRESS_LINES`, `SELLER_ANCHOR`
  - `DEFAULT_INVOICE_NO`, `DEFAULT_GOODS_NAME`, `DEFAULT_GOODS_BRAND`, `DEFAULT_HS_CODE`
  - `DEFAULT_PORT_LOADING`, `DEFAULT_PORT_DISCHARGE`, `DEFAULT_DISCHARGE_COUNTRY`
  - `GOODS_NAME_PATTERN` (Python regex for matching the goods name inside the PI)
  - `SIGNATURE_PATH`, `SEAL_PATH`, `INVOICE_NO` (CLI only)
- `auto_invoice.py` rewritten as a thin wrapper around `invoice_core` (was a copy of the pre-extraction CLI, with ~17 KB of duplicated parsing/template logic). The CLI now finds stamps via env vars or by scanning the working directory for common names (`signature.png`, `seal.png`, plus the original Chinese filenames for backward compatibility).
- Brand-extraction regex generalized to match any `(<UPPERCASE> BRAND)` pattern so other brands match without code changes.
- `_find_chrome()` now returns `None` instead of raising when Chrome isn't found, so the module imports cleanly in CI / test environments. `render_pdf()` raises the original error at call time.

### Internal
- Verified end-to-end that the refactored pipeline produces a PDF byte-identical (±3 bytes) to the pre-refactor output for the sample shipment.
