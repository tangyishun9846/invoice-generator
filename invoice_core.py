#!/usr/bin/env python3
"""商业发票生成核心模块: PDF -> 数据 -> HTML -> PDF

发货人公司信息和默认值通过环境变量配置, 详见 .env.example
"""
import os
import re
import base64
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF


# ============== 配置 (从环境变量读取, 缺省时用占位值) ==============

def _split_lines(raw: str) -> list:
    """把 | 分隔的字符串拆成多行, 兼容字面 \\n"""
    if not raw:
        return []
    raw = raw.replace("\\n", "|")
    return [l.strip() for l in raw.split("|") if l.strip()]


SELLER_NAME = os.environ.get("SELLER_NAME", "YOUR COMPANY NAME CO.,LTD")
SELLER_ADDRESS_LINES = _split_lines(os.environ.get(
    "SELLER_ADDRESS_LINES",
    "ROOM 101, BUILDING A,|123 MAIN STREET, DISTRICT,|CITY, COUNTRY"
))
# PI 文本里发货人地址结尾的锚点 (用来跳过发货人段, 定位收货人块)
SELLER_ANCHOR = os.environ.get("SELLER_ANCHOR", "CITY, COUNTRY")

DEFAULT_INVOICE_NO = os.environ.get("DEFAULT_INVOICE_NO", "INV-001")
DEFAULT_GOODS_NAME = os.environ.get("DEFAULT_GOODS_NAME", "")
DEFAULT_GOODS_BRAND = os.environ.get("DEFAULT_GOODS_BRAND", "")
DEFAULT_HS_CODE = os.environ.get("DEFAULT_HS_CODE", "")
DEFAULT_PORT_LOADING = os.environ.get("DEFAULT_PORT_LOADING", "")
DEFAULT_PORT_DISCHARGE = os.environ.get("DEFAULT_PORT_DISCHARGE", "")
DEFAULT_DISCHARGE_COUNTRY = os.environ.get("DEFAULT_DISCHARGE_COUNTRY", "")

# 可选: PI 里货物名识别正则, 用户可针对自己常用货物定制
GOODS_NAME_PATTERN = os.environ.get(
    "GOODS_NAME_PATTERN",
    r"(SODIUM\s+SULPHIDE\s+FLAKES[^\n]*)"  # 兼容旧版默认; 可改成你的货物
)


def _find_chrome() -> str:
    """按优先级查找 Chrome 可执行文件: 环境变量 -> 常见路径 -> PATH

    找不到时返回 None, 让模块仍可被 import (例如在没装 Chrome 的 CI 跑测试).
    实际调用 render_pdf 时若仍为 None 会报错.
    """
    env = os.environ.get("CHROME_BIN") or os.environ.get("GOOGLE_CHROME_BIN")
    if env and Path(env).exists():
        return env
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return shutil.which("google-chrome") or shutil.which("chromium")


CHROME = _find_chrome()


# ============== 文件识别 ==============

def find_source_files(folder: Path):
    """识别 PI / 出口许可证 / 配载 PDF"""
    pdfs = list(folder.glob("*.pdf")) + list(folder.glob("*/*.pdf"))
    found = {"pi": None, "license": None, "booking": None}
    for p in pdfs:
        name = p.name
        if "商业发票" in name or "COMMERCIAL" in name.upper():
            continue
        if name.startswith("PI") or "PROFORMA" in name.upper() or re.search(r"\bPI\b", name):
            found["pi"] = p
        elif "出口许可证" in name or "LICENCE" in name.upper() or "LICENSE" in name.upper():
            found["license"] = p
        elif "配载" in name or "BOOKING" in name.upper():
            found["booking"] = p
    return found


def pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


# ============== 数据提取 ==============

def parse_pi(text: str, consignee_hint: str = "") -> dict:
    d = {}
    if m := re.search(r"PI\s*No\.?\s*:?\s*(\S+)", text):
        d["pi_no"] = m.group(1).strip()
    if m := re.search(r"PI\s*Date\s*:?\s*([A-Z][a-z]+,\s*\d{1,2},\s*\d{4})", text):
        d["pi_date"] = m.group(1).replace(" ", "").upper()

    # ---- 提取收货人块 (PI 内): 优先用 consignee_hint 定位, 否则用通用规则 ----
    block = ""
    if consignee_hint:
        idx = text.find(consignee_hint)
        if idx >= 0:
            after = text[idx:]  # 包含 hint 行本身
            cut = after.find("INCOTERMS")
            block = after[:cut] if cut > 0 else after[:500]

    if not block:
        # 通用回退: 找 "To:" 和 "INCOTERMS" 之间的内容, 跳过发货人 (anchor 之后)
        if "INCOTERMS" in text:
            before_inco = text[:text.find("INCOTERMS")]
            # 用 SELLER_ANCHOR (默认你公司地址末尾) 作为发货人段结束的标志
            sender_end = before_inco.rfind(SELLER_ANCHOR) if SELLER_ANCHOR else -1
            if sender_end >= 0:
                block = before_inco[sender_end + len(SELLER_ANCHOR):]
            else:
                # 退一步: 用 To: 作为起点
                to_pos = before_inco.find("To:")
                if to_pos >= 0:
                    block = before_inco[to_pos + 3:]

    if block:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        # 第一行是收货人名 (如果当时是用 hint 定位的, 它就是 hint 本身)
        # 后续 2-3 行是地址
        if lines:
            if not consignee_hint:
                # 通用模式: 第一行就是公司名
                d["consignee_name_pi"] = lines[0]
                d["consignee_addr"] = "\n".join(lines[1:4])
            else:
                # hint 模式: 第一行是 hint (已知公司名), 后续是地址
                d["consignee_addr"] = "\n".join(lines[1:4])

    if m := re.search(r"USD\s*([\d,]+(?:\.\d+)?)\s*/\s*([A-Z]+)", text):
        d["unit_price"] = m.group(1).replace(",", "")
        d["price_unit"] = m.group(2)

    if m := re.search(r"(\d+(?:\.\d+)?)\s*(MT|KG|TON)\s*\n?\s*USD", text, re.IGNORECASE):
        d["pi_qty_num"] = m.group(1)
        d["pi_qty_unit"] = m.group(2).upper()

    if m := re.search(GOODS_NAME_PATTERN, text):
        d["goods_name"] = m.group(1).strip()
    # 品牌识别: 找 "(XXX BRAND)" 模式; 没有就用环境默认
    if m := re.search(r"\(([A-Z][A-Z\s]*?BRAND)\)", text):
        d["goods_brand"] = f"({m.group(1)})"
    elif DEFAULT_GOODS_BRAND:
        d["goods_brand"] = DEFAULT_GOODS_BRAND
    if m := re.search(r"H\.S\.\s*CODE\s*:?\s*([\d.]+)", text):
        d["hs_code"] = m.group(1).strip(".")
    return d


def parse_license(text: str) -> dict:
    d = {}
    # 试多种公司名模式 (兼容不同 PyMuPDF 版本的文本提取差异)
    patterns = [
        # 经典模式: 全大写公司名 + 常见后缀
        r"\b([A-Z][A-Z &]{2,}(?:INTERNATIONAL|ENTERPRISES|CO\.?,?\s*LTD|LIMITED|INC|CORPORATION|TRADING|GROUP))\b",
        # 在 "11．收货人" / "Consignee" 标签后面找公司名
        r"(?:11．收货人|11．[^\n]*收货人[^\n]*|Consignee)[\s\S]{0,80}?\n\s*([A-Z][A-Z0-9 &.,'\-]{4,})",
        # 退一步: 任意全大写 4+ 字符且至少含 2 个单词的内容
        r"^([A-Z][A-Z &]{3,}\s+[A-Z][A-Z &]+)$",
    ]
    for pat in patterns:
        if m := re.search(pat, text, re.MULTILINE):
            name = m.group(1).strip()
            # 过滤掉显然不对的 (太短、含数字开头、含中文)
            if len(name) >= 4 and not any(c.isdigit() for c in name[:3]):
                d["consignee_name"] = name
                break

    if m := re.search(r"\b(RF[A-Z]{2,3}\d{4,6})\b", text):
        d["contract_no"] = m.group(1)

    for m in re.finditer(r"(?<!\d)(20\d{6})(?!\d)", text):
        try:
            dt = datetime.strptime(m.group(1), "%Y%m%d")
            if 2000 <= dt.year <= 2099:
                d["contract_date"] = dt.strftime("%b,%d,%Y").upper()
                break
        except ValueError:
            pass

    nums = []
    for m in re.finditer(r"\*([\d,]+(?:\.\d+)?)", text):
        try:
            nums.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    if nums:
        kg = max(nums)
        d["qty_kg"] = int(kg)
        d["qty_mt"] = kg / 1000

    return d


def parse_booking(text: str) -> dict:
    d = {}
    clean = re.sub(r"([一-鿿])\1", r"\1", text)
    if m := re.search(r"装货港\s+([A-Z][A-Z\s,]*?)\s+卸货港", clean):
        d["port_loading"] = m.group(1).strip()
    elif "DALIAN" in clean:
        d["port_loading"] = "DALIAN"
    if m := re.search(r"卸货港\s+([A-Z][A-Z\s,]+?)$", clean, re.MULTILINE):
        d["port_discharge_raw"] = m.group(1).strip()
    elif "KARACHI" in clean:
        d["port_discharge_raw"] = "KARACHI PAKISTAN"
    return d


def format_port(raw: str, default_country: str = "PAKISTAN"):
    raw = raw.strip()
    if not raw:
        return f"{default_country} PORT", "UNKNOWN"
    if "PORT" in raw.upper():
        return raw, raw.split()[0]
    parts = raw.replace(",", "").split()
    if len(parts) >= 2:
        city, country = parts[0], parts[-1]
        return f"{city} PORT, {country}", city
    return f"{parts[0]} PORT, {default_country}", parts[0]


# ============== 数字转大写 ==============

ONES = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE']
TEENS = ['TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
TENS = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY']

def _chunk(n: int) -> str:
    if n == 0: return ''
    if n < 10: return ONES[n]
    if n < 20: return TEENS[n - 10]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + (f'-{ONES[o]}' if o else '')
    h, r = divmod(n, 100)
    return ONES[h] + ' HUNDRED' + (' AND ' + _chunk(r) if r else '')

def num_to_words(n) -> str:
    n = int(n)
    if n == 0: return 'ZERO'
    m, rem = divmod(n, 1_000_000)
    t, h = divmod(rem, 1_000)
    parts = []
    if m: parts.append(_chunk(m) + ' MILLION')
    if t: parts.append(_chunk(t) + ' THOUSAND')
    if h: parts.append(_chunk(h))
    return ' '.join(parts)


# ============== HTML 模板 ==============

def build_html(d: dict, sig_b64: str, seal_b64: str) -> str:
    qty_mt = d["quantity_mt"]
    price = float(d["unit_price"])
    total = qty_mt * price
    total_words = num_to_words(total)
    qty_display = f"{int(qty_mt) if qty_mt == int(qty_mt) else qty_mt}MT"
    total_str = f"{total:,.2f}"

    pi_line = (f"ALL OTHER DETAILS AS PER BENEFICIARY'S PROFORMA INVOICE NO. {d['pi_no']}"
               if d.get("pi_no") else "")
    pi_date_line = f"DATED: {d['pi_date']}" if d.get("pi_date") else ""
    addr_lines = (d.get("consignee_addr") or "").split("\n")
    addr_html = "".join(f'<div class="addr">{l}</div>' for l in addr_lines if l)

    fallback_country = DEFAULT_DISCHARGE_COUNTRY or "COUNTRY"
    discharge_country = d['port_discharge'].split(',')[-1].strip() if ',' in d['port_discharge'] else fallback_country
    seller_addr_html = "".join(f'<div class="addr">{l}</div>' for l in SELLER_ADDRESS_LINES)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Commercial Invoice</title>
<style>
@page {{ size: A4; margin: 50px 55px 50px 55px; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial,"Helvetica Neue",Helvetica,sans-serif; font-size:9pt; color:#000; margin:0; padding:0; }}
.title-en {{ text-align:center; font-size:18pt; font-weight:bold; text-decoration:underline; margin:0; }}
.title-cn {{ text-align:center; font-size:18pt; font-weight:bold; margin:6px 0 0 0; letter-spacing:8px; font-family:"Songti SC","SimSun","Times New Roman",serif; }}
.original {{ text-align:center; font-size:14pt; font-weight:bold; margin:6px 0 10px 0; }}
table.head {{ width:100%; border-collapse:collapse; }}
table.head td {{ border:1px solid #bfbfbf; padding:4px 6px; vertical-align:top; font-size:9pt; }}
.fromto {{ width:52%; }}
.fromto .role {{ font-weight:bold; font-size:10pt; }}
.fromto .name {{ font-weight:bold; font-size:9pt; margin-top:2px; }}
.fromto .addr {{ font-size:9pt; line-height:13pt; }}
.lbl {{ width:18%; font-size:9pt; line-height:13pt; }}
.lbl .en {{ font-weight:bold; }}
.val {{ width:30%; font-weight:bold; font-size:9pt; vertical-align:middle; }}
.port-tbl {{ width:100%; border:none; border-collapse:collapse; }}
.port-tbl td {{ border:none; padding:1px 0; font-weight:bold; font-size:9pt; }}
.port-tbl .lbl-port {{ width:32%; }}
.incoterm td {{ border:1px solid #bfbfbf; padding:4px 8px; text-align:right; font-weight:bold; font-size:9pt; }}
table.goods {{ width:100%; border-collapse:collapse; }}
table.goods th, table.goods td {{ border:1px solid #bfbfbf; font-size:9pt; padding:4px 6px; vertical-align:middle; text-align:center; font-weight:bold; }}
table.goods tr.spacer-row td {{ border:1px solid #bfbfbf; border-bottom:none; height:10px; padding:0; }}
table.goods tr.row-data td {{ height:120px; vertical-align:top; padding-top:6px; border-top:none; }}
table.goods tr.row-data td.desc {{ text-align:left; padding-left:12px; position:relative; }}
table.goods tr.row-data td.desc .hs {{ text-align:left; position:absolute; bottom:8px; left:12px; }}
table.goods tr.totval td {{ border:1px solid #bfbfbf; padding:6px; font-size:9pt; font-weight:bold; }}
table.goods tr.totval td.lbl2 {{ text-align:right; }}
table.goods tr.totval td.val2 {{ text-align:center; }}
table.goods tr.say td {{ border:1px solid #bfbfbf; padding:6px 8px; font-size:9pt; font-weight:bold; text-align:left; }}
table.goods tr.other td {{ border:1px solid #bfbfbf; padding:6px 8px; font-size:9pt; vertical-align:top; min-height:200px; text-align:left; }}
.other .lbl3 {{ font-size:8pt; font-weight:bold; margin-bottom:6px; }}
.other p {{ margin:1px 0; font-size:9pt; font-weight:bold; }}
.stamp-area {{ position:relative; width:100%; height:160px; }}
.stamp-seal {{ position:absolute; right:20px; top:5px; width:240px; }}
.stamp-sig {{ position:absolute; right:90px; top:90px; width:95px; }}
</style></head><body>

<div class="title-en">COMMERCIAL INVOICE</div>
<div class="title-cn">商 业 发 票</div>
<div class="original">(ORIGINAL)</div>

<table class="head">
  <tr>
    <td rowspan="2" class="fromto">
      <div class="role">From:</div>
      <div class="name">{SELLER_NAME}</div>
      {seller_addr_html}
    </td>
    <td class="lbl">发票号码：<br><span class="en">Invoice No.:</span></td>
    <td class="val">{d['invoice_no']}</td>
  </tr>
  <tr>
    <td class="lbl">发票日期:<br><span class="en">Invoice Date:</span></td>
    <td class="val">{d['invoice_date']}</td>
  </tr>
  <tr>
    <td rowspan="2" class="fromto">
      <div class="role">To:</div>
      <div class="name">{d['consignee_name']}</div>
      {addr_html}
    </td>
    <td class="lbl">合同号：<br><span class="en">Contract No.:</span></td>
    <td class="val">{d['contract_no']}</td>
  </tr>
  <tr>
    <td class="lbl">合同日期：<br><span class="en">Contract Date:</span></td>
    <td class="val">{d['contract_date']}</td>
  </tr>
  <tr>
    <td colspan="3" style="border:1px solid #bfbfbf;padding:6px 6px;">
      <table class="port-tbl">
        <tr><td class="lbl-port">Port of Loading:</td><td>{d['port_loading']}</td></tr>
        <tr><td class="lbl-port">Port of Discharge:</td><td>{d['port_discharge']}</td></tr>
      </table>
    </td>
  </tr>
  <tr class="incoterm"><td colspan="3">INCOTERMS: CFR {d['port_discharge']}</td></tr>
</table>

<table class="goods">
  <tr>
    <th style="width:14%;">1.<br>Marks &amp; No.</th>
    <th style="width:36%;">2.<br>Description of goods</th>
    <th style="width:13%;">3.<br>Quantity</th>
    <th style="width:16%;">4.<br>Unit price</th>
    <th style="width:21%;">5.<br>Total Amount</th>
  </tr>
  <tr class="spacer-row"><td></td><td></td><td></td><td></td><td></td></tr>
  <tr class="row-data">
    <td>N/M</td>
    <td class="desc">
      {d['goods_name']}<br>
      {d['goods_brand']}
      <div class="hs">H.S. CODE:{d['hs_code']}</div>
    </td>
    <td>{qty_display}</td>
    <td>USD {int(price) if price == int(price) else price}/{d['price_unit']}</td>
    <td>USD {total_str}</td>
  </tr>
  <tr class="totval">
    <td colspan="4" class="lbl2">Total Value:</td>
    <td class="val2">USD {total_str}</td>
  </tr>
  <tr class="say">
    <td colspan="5">SAY TOTAL USD DOLLARS {total_words} ONLY.</td>
  </tr>
  <tr class="other">
    <td colspan="5">
      <div class="lbl3">Other Descriptions:</div>
      <p>&nbsp;</p>
      <p>CFR {d['discharge_city']} SEAPORT, {discharge_country}</p>
      <p>{pi_line}</p>
      <p>{pi_date_line}</p>
      <p>H.S. CODE NO. {d['hs_code']}</p>
      <p>GOODS ARE OF CHINA ORIGIN.</p>
    </td>
  </tr>
</table>

<div class="stamp-area">
  <img class="stamp-seal" src="data:image/png;base64,{seal_b64}" alt="seal">
  <img class="stamp-sig" src="data:image/png;base64,{sig_b64}" alt="signature">
</div>

</body></html>"""


# ============== 高层流程 ==============

def extract_data(pi_path: Path, license_path: Path, booking_path: Path,
                 invoice_no: str = None) -> dict:
    """从三个 PDF 中提取数据并组装成 invoice 数据字典"""
    lic = parse_license(pdf_text(license_path))
    pi = parse_pi(pdf_text(pi_path), consignee_hint=lic.get("consignee_name", ""))
    bk = parse_booking(pdf_text(booking_path))

    today = datetime.now()
    invoice_date = today.strftime("%b,%d,%Y").upper()

    loading = bk.get("port_loading") or DEFAULT_PORT_LOADING or ""
    if loading and "," not in loading:
        # 起运港若没带国家, 默认追加 CHINA
        loading = f"{loading}, CHINA"
    discharge_raw = bk.get("port_discharge_raw") or DEFAULT_PORT_DISCHARGE or ""
    discharge_full, discharge_city = format_port(
        discharge_raw, default_country=DEFAULT_DISCHARGE_COUNTRY or "COUNTRY"
    )

    # 收货人名优先用许可证的, 失败则用 PI 提取的回退值
    consignee_name = lic.get("consignee_name") or pi.get("consignee_name_pi") or "N/A"

    return {
        "invoice_no": invoice_no or DEFAULT_INVOICE_NO,
        "invoice_date": invoice_date,
        "consignee_name": consignee_name,
        "consignee_addr": pi.get("consignee_addr", ""),
        "contract_no": lic.get("contract_no", "N/A"),
        "contract_date": lic.get("contract_date", "N/A"),
        "port_loading": loading,
        "port_discharge": discharge_full,
        "discharge_city": discharge_city,
        "quantity_mt": lic.get("qty_mt", 0),
        "unit_price": pi.get("unit_price", "0"),
        "price_unit": pi.get("price_unit", "MT"),
        "goods_name": pi.get("goods_name") or DEFAULT_GOODS_NAME,
        "goods_brand": pi.get("goods_brand") or DEFAULT_GOODS_BRAND,
        "hs_code": pi.get("hs_code") or DEFAULT_HS_CODE,
        "pi_no": pi.get("pi_no", ""),
        "pi_date": pi.get("pi_date", ""),
    }


def render_pdf(data: dict, sig_path: Path, seal_path: Path, out_pdf: Path) -> Path:
    """渲染数据成 PDF, 返回输出路径"""
    sig_b64 = base64.b64encode(sig_path.read_bytes()).decode()
    seal_b64 = base64.b64encode(seal_path.read_bytes()).decode()
    html = build_html(data, sig_b64, seal_b64)

    html_path = out_pdf.parent / f".{out_pdf.stem}_temp.html"
    html_path.write_text(html, encoding="utf-8")

    if out_pdf.exists():
        out_pdf.unlink()

    if not CHROME:
        raise RuntimeError("找不到 Chrome 可执行文件, 请设置环境变量 CHROME_BIN")
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer"]
    # Docker / 以 root 跑时 Chrome 需要 --no-sandbox
    if os.geteuid() == 0 or os.environ.get("CHROME_NO_SANDBOX"):
        cmd += ["--no-sandbox", "--disable-dev-shm-usage"]
    cmd += [f"--print-to-pdf={out_pdf}", f"file://{html_path}"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    html_path.unlink(missing_ok=True)

    if not out_pdf.exists():
        raise RuntimeError(f"PDF 生成失败: {result.stderr}")
    return out_pdf
