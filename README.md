# Commercial Invoice Auto-Generator | 商业发票自动生成器

> Upload 3 source PDFs (Proforma Invoice, Export License, Booking Note) and 2 stamp images — get a properly formatted commercial invoice PDF.
>
> 上传 3 个源 PDF (形式发票、出口许可证、配载) 和 2 个印章 → 自动生成排版规范的商业发票 PDF.

[中文版 ↓](#中文版) | [Live Demo](#live-demo)

---

## English

### What it does

A small self-hostable web app for exporters. It parses three PDFs commonly produced during a shipment workflow, extracts the relevant fields, and renders a print-ready commercial invoice that matches the typical China-export template.

The same logic is exposed as a CLI for batch / local use.

### Features

- **Three-PDF input → one-PDF output** in ~5 seconds.
- **Browser-side stamp storage** — signature and company seal images live in `localStorage`, never persisted on the server.
- **No data retention** — uploaded files are processed in a `tempfile.mkdtemp()` and wiped via `after_this_request`.
- **Bilingual UI** (Chinese-first, but easy to translate).
- **Configurable via env vars** — your company name, address, defaults, even the goods-detection regex.
- **Docker-ready** — Chrome + Chinese fonts baked in; deploys cleanly to Render / Railway / Fly.io.

### Live Demo

A demo running the sample seller config: <https://invoice-generator-ke4l.onrender.com>
(Render free tier sleeps after 15 min — first hit takes ~30s to wake.)

### Quick start

```bash
git clone https://github.com/tangyishun9846/invoice-generator.git
cd invoice-generator

pip install -r requirements.txt

# Copy and edit the config (or just run with built-in placeholder)
cp .env.example .env  # then edit

# Run the web UI
python3 webapp.py
# open http://localhost:5001
```

Or the CLI:

```bash
# Put PI*.pdf, *出口许可证*.pdf (or *LICENCE*.pdf), *配载*.pdf (or *BOOKING*.pdf)
# and signature.png / seal.png in a folder, then:
python3 auto_invoice.py /path/to/folder
```

### Configuration

All seller-specific values are environment variables — see [`.env.example`](.env.example).

Minimum to customize for your own company:

| Variable | What it is |
|---|---|
| `SELLER_NAME` | Shown in the invoice's `From:` block |
| `SELLER_ADDRESS_LINES` | Multiple lines, `\|`-separated |
| `SELLER_ANCHOR` | A short string from your address that appears in your PI — used to locate where the consignee block starts |
| `DEFAULT_INVOICE_NO` | Pre-filled invoice number in the web form |
| `DEFAULT_GOODS_NAME` / `DEFAULT_HS_CODE` | Fallbacks when extraction fails |
| `GOODS_NAME_PATTERN` | Python regex matching your typical goods description in the PI |

### Deployment

#### Docker

```bash
docker build -t invoice-gen .
docker run -p 8080:8080 --env-file .env invoice-gen
```

#### Render.com (one-click-ish)

1. Push your repo to GitHub.
2. New Web Service → connect repo → Runtime: **Docker**.
3. Add env vars from your `.env`.
4. Done. Service auto-redeploys on push.

See [DEPLOY.md](DEPLOY.md) for details.

### How the parsing works

- **Export License PDF** → consignee company name, contract no., contract date, **actual shipment quantity** (in kg, converted to MT).
- **Proforma Invoice PDF** → PI number/date, consignee address (anchored by the consignee name found above), unit price, goods description, HS code.
- **Booking Note PDF** → port of loading, port of discharge.

Then:
- `quantity × unit_price = total amount` (converted to English words for the `SAY TOTAL …` line).
- HTML template → Chrome headless → PDF.

### Project layout

```
invoice_core.py     # Parsing + HTML template + Chrome→PDF rendering
webapp.py           # Flask app: /, /extract, /generate, /healthz
auto_invoice.py     # CLI wrapper: folder scan + stamp lookup → render_pdf()
requirements.txt    # flask, pymupdf, gunicorn
Dockerfile          # Chrome + Noto CJK fonts on python:3.11-slim
.env.example        # All configurable knobs
DEPLOY.md           # Render deployment walkthrough
```

### Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Especially appreciated:
- Support for other goods types (template tweaks, new `GOODS_NAME_PATTERN` examples)
- Packing list (装箱单) generation following the same flow
- Tests (currently none)

### License

[MIT](LICENSE)

---

## 中文版

### 这是什么

一个外贸出口用的自部署小工具。把外贸流程里常见的三份 PDF 解析后, 自动生成符合中国出口模板的商业发票 PDF.

同一套逻辑也提供 CLI 版本, 适合本地批量生成。

### 主要功能

- **三个 PDF 进, 一个 PDF 出**, 大约 5 秒搞定.
- **印章存浏览器** — 签名章和公司印章存在 `localStorage` 里, 服务器不留存.
- **零数据保留** — 上传文件用 `tempfile.mkdtemp()` 隔离, 请求结束自动清理.
- **中文优先界面**, 也方便翻译成其他语言.
- **完全 env var 配置** — 公司信息、默认值、甚至货物识别正则都可配.
- **Docker 即用** — 镜像里已装好 Chrome + 中文字体, 一键部署到 Render/Railway/Fly.

### 在线 Demo

示例配置的部署: <https://invoice-generator-ke4l.onrender.com>
(Render 免费层 15 分钟无访问会休眠, 首次访问需要等约 30 秒冷启动.)

### 快速开始

```bash
git clone https://github.com/tangyishun9846/invoice-generator.git
cd invoice-generator

pip install -r requirements.txt

# 复制配置文件并改成自己公司的信息 (也可直接用占位值跑)
cp .env.example .env  # 编辑里面的值

# 启动 Web 版
python3 webapp.py
# 浏览器打开 http://localhost:5001
```

或者用命令行版:

```bash
# 把 PI*.pdf, *出口许可证*.pdf, *配载*.pdf
# 和 signature.png / seal.png 放在一个文件夹下, 然后:
python3 auto_invoice.py /path/to/folder
```

### 配置项

所有公司相关的硬编码都已抽到环境变量, 详见 [`.env.example`](.env.example).

最少需要改的几项:

| 变量 | 含义 |
|---|---|
| `SELLER_NAME` | 显示在发票 "From:" 那块的公司名 |
| `SELLER_ADDRESS_LINES` | 多行地址, 用 `\|` 分隔 |
| `SELLER_ANCHOR` | 你 PI 文本里发货人地址的尾部字符串, 用来定位收货人块的起点 |
| `DEFAULT_INVOICE_NO` | Web 表单里默认填的发票号 |
| `DEFAULT_GOODS_NAME` / `DEFAULT_HS_CODE` | 解析失败时的兜底 |
| `GOODS_NAME_PATTERN` | PI 里识别货物名的 Python 正则 |

### 部署

#### Docker

```bash
docker build -t invoice-gen .
docker run -p 8080:8080 --env-file .env invoice-gen
```

#### Render.com (近似一键)

1. 把仓库 push 到 GitHub.
2. New Web Service → 连接仓库 → Runtime 选 **Docker**.
3. 把你 `.env` 里的变量加到平台环境变量里.
4. 完事. 之后每次 git push 自动 redeploy.

详细步骤见 [DEPLOY.md](DEPLOY.md).

### 解析逻辑

- **出口许可证 PDF** → 收货人公司名、合同号、合同日期、**本次实际发货数量** (kg, 自动换算成 MT).
- **PI (形式发票) PDF** → PI 号/日期、收货人地址 (用上面拿到的公司名做锚点定位)、单价、货物描述、HS Code.
- **配载 (订舱通知) PDF** → 装货港、卸货港.

然后:
- `数量 × 单价 = 总金额` (再转成英文大写填到 `SAY TOTAL …`).
- HTML 模板 → Chrome headless → PDF.

### 项目结构

```
invoice_core.py     # 解析 + HTML 模板 + Chrome→PDF
webapp.py           # Flask Web 应用: /, /extract, /generate, /healthz
auto_invoice.py     # CLI 入口: 扫文件夹 + 找印章 → render_pdf()
requirements.txt    # flask, pymupdf, gunicorn
Dockerfile          # python:3.11-slim + Chrome + Noto CJK
.env.example        # 所有可配置项
DEPLOY.md           # Render 部署指南
```

### 参与贡献

欢迎 PR — 见 [CONTRIBUTING.md](CONTRIBUTING.md). 特别需要:
- 支持其他货物类型 (模板微调 + 新的 `GOODS_NAME_PATTERN` 示例)
- 装箱单按同样的流程生成
- 单元测试 (目前完全没有)

### 许可证

[MIT](LICENSE)
