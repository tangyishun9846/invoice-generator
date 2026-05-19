# Contributing | 参与贡献

Thanks for your interest! This is a small project, so the bar for contributing is low — just open an issue or PR.

感谢你的兴趣! 项目很小, 贡献门槛也不高 — 直接开 issue 或 PR 即可.

---

## Quick start for local dev | 本地开发快速开始

```bash
git clone https://github.com/tangyishun9846/invoice-generator.git
cd invoice-generator

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # 改成你的测试公司信息
python3 webapp.py     # http://localhost:5001
```

You need **Google Chrome** installed locally (the code auto-detects the macOS / Linux paths). For Docker dev, see the `Dockerfile`.

本地需要装 **Google Chrome** (代码会自动找 macOS / Linux 的常见路径). 用 Docker 开发请参考 `Dockerfile`.

---

## What kind of PRs are welcome | 欢迎什么样的 PR

### High value | 高价值
- **Support for new goods types** — share your `GOODS_NAME_PATTERN` and any tweaks needed for goods name / brand / HS code extraction.
- **Packing list (装箱单) generation** following the same pattern (parse → template → PDF).
- **Tests** — currently zero. Anything is an improvement.
- **Internationalization** — the UI is Chinese-first; pulling strings into a dict + accepting `?lang=en` would be great.
- **支持新的货物类型** — 把你的 `GOODS_NAME_PATTERN` 和相关解析调整提交上来.
- **装箱单生成** — 按相同流程 (解析→模板→PDF).
- **测试** — 目前完全没有, 加任何测试都是进步.
- **国际化** — UI 现在中文优先; 把文案抽到字典 + 支持 `?lang=en` 切换很赞.

### Medium value | 中等价值
- More robust regexes for the PI / License formats — there are many variants in the wild.
- Better error messages when PDF parsing fails (currently just a stack trace).
- Auto-incrementing invoice number based on date (e.g. `INV-251119-001`).
- 更鲁棒的 PI / 许可证解析正则 (世面上格式很多).
- PDF 解析失败时更友好的报错 (现在就是个 stack trace).
- 基于日期自动递增的发票号 (例如 `INV-251119-001`).

### Not really needed | 不太需要
- Big framework rewrites (Flask + vanilla JS is fine for this scope).
- Adding more JS dependencies — the page should stay zero-build.
- 大的框架重写 (Flask + 原生 JS 对这个规模够用了).
- 加更多 JS 依赖 — 页面应保持零构建.

---

## Code style | 代码风格

- **Python**: 4-space indent, no formal style enforcement, but try to match the surrounding code.
- **Comments**: prefer self-documenting code; comment the *why*, not the *what*.
- **Function size**: it's fine to keep parse functions modest-length — splitting `parse_pi` into 5 micro-helpers is not worth it.
- **Python**: 4 空格缩进, 没有强制风格检查, 但请尽量和周围代码保持一致.
- **注释**: 倾向自解释的代码; 注释解释 *为什么*, 不是 *做什么*.
- **函数长度**: parse 函数适中长度是 OK 的, 把 `parse_pi` 拆成 5 个小工具函数没必要.

---

## Testing your change | 测试你的修改

Until there's a real test suite, the manual smoke test is:

在还没有真正测试套件之前, 手工冒烟测试流程:

1. Start the web app: `python3 webapp.py`
2. Open `http://localhost:5001` and upload your three sample PDFs + two stamp PNGs.
3. Click "预览数据" — verify the extracted fields are correct.
4. Click "下载 PDF" — open the generated PDF and check the layout matches expectations.

For CLI:

```bash
python3 auto_invoice.py /path/to/folder/with/source/pdfs
```

---

## Sensitive data | 敏感数据

**Do not commit real PDFs, real stamps, or real customer names** when opening a PR. The `.gitignore` already excludes most of these, but please double-check `git diff --stat` before pushing.

If you want to share a parsing failure, **redact** the PDF first (use `pdftotext` to extract text and edit out names/addresses).

**请不要在 PR 里提交真实的 PDF、真实的印章、真实的客户名**. `.gitignore` 已经排除了大部分这类文件, 但 push 前请用 `git diff --stat` 再核对一遍.

如果想分享解析失败的样例, 请先 **脱敏** PDF (用 `pdftotext` 提文本后把姓名/地址改成假的).

---

## License

By contributing you agree your changes will be released under the [MIT License](LICENSE).
贡献即表示你同意你的修改以 [MIT License](LICENSE) 发布.
