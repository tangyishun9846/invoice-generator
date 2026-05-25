#!/usr/bin/env python3
"""
商业发票自动生成器 — 命令行版本

扫描指定文件夹里的源 PDF (PI / 出口许可证 / 配载), 提取数据后生成商业发票 PDF.
解析、HTML 模板和 PDF 渲染逻辑都复用 invoice_core 模块.

用法:
    python3 auto_invoice.py                    # 扫描当前目录
    python3 auto_invoice.py /path/to/folder    # 扫描指定目录

印章路径 (按优先级, 必传):
    1. 环境变量 SIGNATURE_PATH / SEAL_PATH (绝对路径)
    2. 扫描目录下的 signature.png / seal.png
    3. 兼容旧文件名: 安然签名章.png / 公司名称章.png

抬头 (都可选, 都不设则不渲染抬头):
    - 公司 Logo 图: 环境变量 LOGO_PATH, 或目录下的 logo.png / company_logo.png
    - 公司英文名 (文本): 环境变量 NAMEPLATE_TEXT, 缺省时用 SELLER_NAME

依赖: pymupdf, Chrome (本地路径自动探测)
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from invoice_core import (
    find_source_files,
    extract_data,
    render_pdf,
    DEFAULT_INVOICE_NO,
    SELLER_NAME,
)


SCRIPT_DIR = Path(__file__).parent.resolve()


def _resolve_stamp(folder: Path, env_var: str, default_names: list) -> Path:
    """按优先级查找印章: env var -> folder 下的候选文件名 (必传, 找不到退出)"""
    env_path = os.environ.get(env_var)
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.exists():
            return p
        sys.exit(f"❌ {env_var} 指向的文件不存在: {p}")
    for name in default_names:
        candidate = folder / name
        if candidate.exists():
            return candidate
    sys.exit(
        f"❌ 找不到印章, 请设置环境变量 {env_var} 或把文件放到 {folder}\n"
        f"   候选文件名: {', '.join(default_names)}"
    )


def _resolve_optional(folder: Path, env_var: str, default_names: list):
    """按优先级查找可选图 (抬头 logo/nameplate): env var -> folder 候选名 -> None"""
    env_path = os.environ.get(env_var)
    if env_path:
        p = Path(env_path).expanduser().resolve()
        return p if p.exists() else None
    for name in default_names:
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def main():
    folder = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SCRIPT_DIR
    print(f"📂 扫描文件夹: {folder}")

    sources = find_source_files(folder)
    for k, v in sources.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {v.name if v else '未找到'}")

    if not all(sources.values()):
        sys.exit("\n❌ 缺少必要的源文件 (PI / 出口许可证 / 配载), 请确认文件名包含相关关键词")

    invoice_no = os.environ.get("INVOICE_NO") or DEFAULT_INVOICE_NO
    data = extract_data(
        sources["pi"], sources["license"], sources["booking"],
        invoice_no=invoice_no,
    )

    print("\n📊 提取的数据:")
    print(f"  PI No: {data.get('pi_no')}, PI Date: {data.get('pi_date')}")
    print(f"  收货人: {data.get('consignee_name')}")
    print(f"  地址: {data.get('consignee_addr', '').replace(chr(10), ' / ')}")
    print(f"  合同号: {data.get('contract_no')}, 合同日期: {data.get('contract_date')}")
    print(f"  起运港: {data.get('port_loading')}, 卸货港: {data.get('port_discharge')}")
    print(f"  数量: {data.get('quantity_mt')}MT, 单价: USD {data.get('unit_price')}/{data.get('price_unit')}")

    sig_path = _resolve_stamp(folder, "SIGNATURE_PATH",
                               ["signature.png", "sig.png", "安然签名章.png"])
    seal_path = _resolve_stamp(folder, "SEAL_PATH",
                                ["seal.png", "company_seal.png", "公司名称章.png"])
    # 可选: 抬头 (找不到就跳过)
    logo_path = _resolve_optional(folder, "LOGO_PATH",
                                   ["logo.png", "company_logo.png"])
    # 抬头文本: 优先 NAMEPLATE_TEXT, 否则用 SELLER_NAME (注意: 若都为空则不渲染抬头)
    nameplate_text = os.environ.get("NAMEPLATE_TEXT") or SELLER_NAME or ""
    if logo_path or nameplate_text:
        print(f"  抬头: logo={'有' if logo_path else '无'}, "
              f"公司英文名='{nameplate_text or '(无)'}'")

    today = datetime.now().strftime("%Y%m%d")
    out_pdf = folder / f"商业发票_{invoice_no}_修改于{today}.pdf"
    print(f"\n🖨️  生成 PDF: {out_pdf.name}")
    render_pdf(data, sig_path, seal_path, out_pdf,
               logo_path=logo_path, nameplate_text=nameplate_text)
    print(f"✅ 完成: {out_pdf}")


if __name__ == "__main__":
    main()
