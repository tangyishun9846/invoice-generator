<div align="center">

# 📦 Commercial Invoice Auto-Generator

**Turn three trade PDFs into a print-ready commercial invoice in 5 seconds.**

把外贸三件套 PDF 自动变成可打印的商业发票, 5 秒搞定.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-32%20passing-brightgreen.svg)](tests/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](Dockerfile)
[![Live Demo](https://img.shields.io/badge/demo-live-success.svg)](https://invoice-generator-ke4l.onrender.com)

[**🚀 Live Demo**](https://invoice-generator-ke4l.onrender.com) · [**📖 中文文档**](#-中文文档) · [**🐛 Issues**](https://github.com/tangyishun9846/invoice-generator/issues)

<!--
  TODO: replace the placeholder below with a real screenshot.
  See the "Add a screenshot" section near the bottom of this README for safe steps
  (use placeholder business data, never real customer info).
-->
<sub>📸 Screenshot placeholder — see <a href="#-add-a-screenshot">how to add one</a></sub>

</div>

---

## Why this exists

China-export trading companies generate commercial invoices by hand: open a Word template, copy fields from the **Proforma Invoice**, the **Export License**, and the **Booking Note** — three separate PDFs — paste them into the right boxes, add a company seal and a signature, export to PDF. **5–10 minutes per shipment**, plus rework whenever a digit goes wrong.

This tool turns that into a 5-second drag-and-drop. Same template, same fields, no typing.

中国外贸出口的商业发票传统做法: 打开 Word 模板, 从 PI / 出口许可证 / 配载三个 PDF 里抠字段, 手动填进去, 加印章, 导出 PDF. **一次 5-10 分钟, 错一个数字要返工.** 这工具把它变成 5 秒.

## Features

| | |
|---|---|
| 🔄 **Three-PDF → One-PDF** | Parse PI, export license, booking note; render the invoice |
| 🔒 **Zero data retention** | Files live in `tempfile.mkdtemp()`, wiped after the response |
| 🏷 **Browser-side stamps** | Signature and seal stay in `localStorage`, never persisted server-side |
| ⚙️ **Fully configurable** | Company info, defaults, goods-detection regex — all via env vars |
| 🌐 **One-command deploy** | Dockerfile bakes in Chrome + Noto CJK fonts |
| 🧪 **Tested** | 32 unit tests on the pure parsing logic, runs without Chrome or sample PDFs |
| 🌍 **Bilingual UI** | Chinese-first, easy to localize |

## Quick start

### Try the hosted demo

→ <https://invoice-generator-ke4l.onrender.com>

Hosted on Render's free tier — first request after idle takes ~30 s to wake.

### Run locally

```bash
git clone https://github.com/tangyishun9846/invoice-generator.git
cd invoice-generator

pip install -r requirements.txt

cp .env.example .env       # edit with your company info
python3 webapp.py          # → http://localhost:5001
```

Requires Python 3.11+ and Google Chrome installed locally (auto-detected).

### Run via Docker

```bash
docker build -t invoice-gen .
docker run -p 8080:8080 --env-file .env invoice-gen
```

### Run the CLI

```bash
# Drop the three source PDFs + signature.png + seal.png in a folder, then:
python3 auto_invoice.py /path/to/folder
```

## How it works

```
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │   PI.pdf     │   │ License.pdf  │   │ Booking.pdf  │
   │ price · PI#  │   │ buyer · qty  │   │ ports        │
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          │                  │                  │
          └────────┬─────────┴──────────────────┘
                   │   PyMuPDF + regex
                   ▼
            ┌─────────────┐
            │  data dict  │
            └──────┬──────┘
                   │   HTML template (f-string)
                   ▼
            ┌─────────────┐         ┌────────────┐
            │   HTML      │────────▶│ stamp PNGs │
            └──────┬──────┘         └────────────┘
                   │   Chrome headless --print-to-pdf
                   ▼
            ┌─────────────┐
            │ Invoice.pdf │
            └─────────────┘
```

Three small modules:

- **[invoice_core.py](invoice_core.py)** — parsing, HTML template, PDF rendering
- **[webapp.py](webapp.py)** — Flask app, 4 routes (`/`, `/extract`, `/generate`, `/healthz`)
- **[auto_invoice.py](auto_invoice.py)** — thin CLI wrapper around `invoice_core`

## Configuration

Everything seller-specific is in [`.env.example`](.env.example). Copy to `.env`, edit, done.

| Variable | Required | Purpose |
|---|---|---|
| `SELLER_NAME` | ✅ | Shown in the `From:` block on the invoice |
| `SELLER_ADDRESS_LINES` | ✅ | Multi-line address, `\|`-separated |
| `SELLER_ANCHOR` | ✅ | Short string from your address (used to locate the consignee block inside the PI text) |
| `GOODS_NAME_PATTERN` | optional | Python regex for matching your typical goods description |
| `DEFAULT_INVOICE_NO` | optional | Pre-fills the form |
| `DEFAULT_GOODS_NAME` / `DEFAULT_HS_CODE` / `DEFAULT_PORT_*` | optional | Fallbacks when extraction misses |
| `CHROME_BIN` | optional | Override Chrome path |

On hosting platforms (Render / Railway / Fly), set these in the dashboard's environment-variables section instead of committing a `.env` file.

## Deployment

### Render (one-click-ish)

1. Fork this repo on GitHub.
2. Render → **New Web Service** → connect your fork.
3. Runtime: **Docker**.
4. Add env vars from your `.env`.
5. Done. Every `git push` redeploys automatically.

Detailed walkthrough in [DEPLOY.md](DEPLOY.md).

### Other platforms

The same `Dockerfile` works on Railway, Fly.io, Cloud Run, or your own VPS. Just inject the env vars.

## Tests

```bash
python3 -m unittest discover -s tests
```

32 tests covering `num_to_words`, `format_port`, `_split_lines`, and all three `parse_*` functions. No Chrome or sample PDFs needed — purely text-in, dict-out.

## Tech stack

- Python 3.11 · Flask · Gunicorn
- PyMuPDF (`fitz`) for PDF text extraction
- Chrome headless for HTML → PDF
- Vanilla JS + `localStorage` (zero-build frontend)
- Docker (python:3.11-slim + google-chrome-stable + Noto CJK)

## Roadmap

- [ ] Packing list (装箱单) generation following the same flow
- [ ] Auto-incrementing invoice number (e.g. `INV-251119-001`)
- [ ] Multi-language UI (English / Chinese toggle)
- [ ] More goods-type presets contributed via `GOODS_NAME_PATTERN`
- [ ] Better error messages when PDF parsing misses a field

## Add a screenshot

The README would benefit from a screenshot of the extraction-preview page. **Use placeholder business data — never real customer names, contract numbers, or addresses.**

```bash
mkdir -p docs
# Upload 3 redacted/sample PDFs to the running app, screenshot the preview panel,
# save as:
#   docs/screenshot-extract.png
```

Then uncomment the image line near the top of this README.

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Especially helpful:

- Goods-type presets (your `GOODS_NAME_PATTERN` + sample tweaks)
- Packing-list generator following the same pipeline
- Internationalization (UI strings are inline in `webapp.py`)
- More tests

## License

[MIT](LICENSE) © 2026 [tangyishun9846](https://github.com/tangyishun9846)

---

<a id="-中文文档"></a>

## 📖 中文文档

### 这是什么

外贸出口的"商业发票"传统做法是: 拿 Word 模板, 手动从 **PI / 出口许可证 / 配载** 这三个 PDF 里抠数据出来, 一个个字段填进去, 加印章, 导出 PDF. **一次 5-10 分钟, 错一个数字要返工.** 这工具把这 5-10 分钟变成 5 秒.

### 功能亮点

- 🔄 **三个 PDF 进, 一个 PDF 出** — 解析 PI、出口许可证、配载, 自动渲染发票
- 🔒 **零数据保留** — 文件用 `tempfile.mkdtemp()` 隔离, 请求结束自动清理
- 🏷 **印章存浏览器** — 签名章和公司印章存在 `localStorage`, 服务器不留存
- ⚙️ **完全 env var 配置** — 公司信息、默认值、货物正则都可配
- 🌐 **Docker 即用** — 镜像里装好 Chrome + 中文字体, 一键部署
- 🧪 **有测试** — 32 个单元测试覆盖核心解析逻辑
- 🌍 **中文优先界面**, 易于翻译

### 快速开始

#### 在线 Demo
👉 <https://invoice-generator-ke4l.onrender.com>
(Render 免费层, 15 分钟无访问会休眠, 首次访问需要约 30 秒冷启动)

#### 本地运行

```bash
git clone https://github.com/tangyishun9846/invoice-generator.git
cd invoice-generator

pip install -r requirements.txt
cp .env.example .env       # 编辑成自己公司的信息
python3 webapp.py          # 浏览器打开 http://localhost:5001
```

需要 Python 3.11+ 和本地装好的 Google Chrome (代码自动探测路径).

#### Docker 跑

```bash
docker build -t invoice-gen .
docker run -p 8080:8080 --env-file .env invoice-gen
```

#### 命令行版

```bash
# 把三个源 PDF + signature.png + seal.png 放在一个文件夹下:
python3 auto_invoice.py /path/to/folder
```

### 配置项

所有公司相关的硬编码都已抽到环境变量, 详见 [`.env.example`](.env.example).

| 变量 | 是否必填 | 含义 |
|---|---|---|
| `SELLER_NAME` | ✅ | 发票 "From:" 那块的公司名 |
| `SELLER_ADDRESS_LINES` | ✅ | 多行地址, 用 `\|` 分隔 |
| `SELLER_ANCHOR` | ✅ | 你 PI 文本里发货人地址尾部的字符串, 用来定位收货人块 |
| `GOODS_NAME_PATTERN` | 可选 | PI 里识别货物名的 Python 正则 |
| `DEFAULT_INVOICE_NO` | 可选 | 表单里预填的发票号 |
| `DEFAULT_GOODS_NAME` 等 | 可选 | 解析失败时的兜底 |

部署到 Render / Railway / Fly 时, 在平台后台的环境变量页设置(**不要把 `.env` 提交到 git**).

### 部署到 Render

1. 把仓库 fork 到自己 GitHub.
2. Render → New Web Service → 连接 fork → Runtime 选 **Docker**.
3. Environment 页把 `.env.example` 里所有变量加进去.
4. 完事. 之后每次 `git push` 自动 redeploy.

完整步骤见 [DEPLOY.md](DEPLOY.md).

### 解析逻辑

- **出口许可证 PDF** → 收货人公司名、合同号、合同日期、**本次实际发货数量** (kg → MT)
- **PI (形式发票) PDF** → PI 号/日期、收货人地址 (用上面拿到的公司名做锚点)、单价、货物描述、HS Code
- **配载 (订舱通知) PDF** → 装货港、卸货港

然后: 数量 × 单价 = 总金额 → 数字转英文大写填入 "SAY TOTAL …" → HTML 模板 → Chrome headless → PDF.

### 项目结构

```
invoice_core.py     # 核心: 解析 + HTML 模板 + Chrome→PDF
webapp.py           # Flask Web 应用 (4 个路由)
auto_invoice.py     # CLI 入口 (薄壳, 复用 invoice_core)
tests/              # 32 个单元测试 (不依赖 Chrome / 真实 PDF)
Dockerfile          # python:3.11-slim + Chrome + Noto CJK
.env.example        # 所有可配置环境变量
DEPLOY.md           # Render 部署详细指南
CHANGELOG.md        # 版本变更记录
```

### 跑测试

```bash
python3 -m unittest discover -s tests
```

### 参与贡献

欢迎 PR — 见 [CONTRIBUTING.md](CONTRIBUTING.md). 特别需要的方向:

- 支持其他货物类型 (提交你的 `GOODS_NAME_PATTERN`)
- 装箱单按同样流程生成
- UI 国际化 (中英切换)
- 更多测试

### 许可证

[MIT](LICENSE) © 2026 [tangyishun9846](https://github.com/tangyishun9846)
