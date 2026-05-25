#!/usr/bin/env python3
"""
商业发票生成 Web 应用 (云端可部署版)

本地启动:
    python3 webapp.py

云端部署 (Render/Railway/Fly):
    通过环境变量 PORT 自动适配, 默认监听 0.0.0.0
    需要在容器中安装 Chrome (见 Dockerfile)
"""
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from flask import Flask, request, send_file, render_template_string, jsonify

from invoice_core import extract_data, render_pdf, DEFAULT_INVOICE_NO


SCRIPT_DIR = Path(__file__).parent.resolve()
IS_PRODUCTION = bool(os.environ.get("PORT"))  # 云端通常会注入 PORT

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30MB


PAGE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>商业发票自动生成</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
.container{max-width:820px;margin:30px auto;background:#fff;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,0.25);overflow:hidden;}
.header{background:linear-gradient(135deg,#2c3e50,#34495e);color:#fff;padding:30px 36px;}
.header h1{margin:0;font-size:22pt;}
.header p{margin:8px 0 0 0;color:#bdc3c7;font-size:11pt;}
.main{padding:30px 36px;}
.section-title{font-size:11pt;font-weight:bold;color:#2d3748;margin:0 0 12px 0;padding-bottom:6px;border-bottom:2px solid #edf2f7;}
.section + .section{margin-top:24px;}
.uploads{display:grid;grid-template-columns:1fr;gap:12px;}
.uploads.cols-2{grid-template-columns:1fr 1fr;}
.upload-card{border:2px dashed #cbd5e0;border-radius:10px;padding:18px;background:#f7fafc;cursor:pointer;transition:all 0.2s;position:relative;}
.upload-card:hover{border-color:#667eea;background:#edf2f7;}
.upload-card.has-file{border-color:#48bb78;border-style:solid;background:#f0fff4;}
.upload-card.has-file::before{content:"✓";position:absolute;right:18px;top:50%;transform:translateY(-50%);color:#48bb78;font-size:22pt;font-weight:bold;}
.upload-card label{display:block;cursor:pointer;}
.upload-card .label-title{font-size:11pt;font-weight:bold;color:#2d3748;margin-bottom:3px;}
.upload-card .label-hint{font-size:9pt;color:#718096;}
.upload-card .filename{font-size:9pt;color:#48bb78;margin-top:4px;font-family:Menlo,Monaco,monospace;word-break:break-all;}
.upload-card input[type=file]{display:none;}
.stamp-card{border:2px dashed #cbd5e0;border-radius:10px;padding:14px;background:#f7fafc;text-align:center;cursor:pointer;transition:all 0.2s;}
.stamp-card:hover{border-color:#667eea;}
.stamp-card.has-file{border-color:#48bb78;border-style:solid;background:#f0fff4;}
.stamp-card label{cursor:pointer;display:block;}
.stamp-card .label-title{font-size:10pt;font-weight:bold;color:#2d3748;margin-bottom:6px;}
.stamp-card .preview{height:60px;display:flex;align-items:center;justify-content:center;margin-top:6px;}
.stamp-card .preview img{max-height:60px;max-width:100%;}
.stamp-card .preview .placeholder{color:#a0aec0;font-size:9pt;}
.stamp-card input[type=file]{display:none;}
.stamp-actions{margin-top:8px;font-size:9pt;}
.stamp-actions a{color:#667eea;cursor:pointer;text-decoration:underline;}
.options{padding:14px;background:#f7fafc;border-radius:10px;}
.options label{display:block;font-size:10pt;color:#4a5568;margin-bottom:6px;font-weight:600;}
.options input[type=text]{width:100%;padding:9px 12px;border:1px solid #cbd5e0;border-radius:8px;font-size:11pt;font-family:inherit;}
.actions{margin-top:24px;display:flex;gap:10px;}
.btn{flex:1;padding:13px 20px;border:none;border-radius:8px;font-size:11pt;font-weight:bold;cursor:pointer;transition:all 0.15s;}
.btn-primary{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 18px rgba(102,126,234,0.4);}
.btn-primary:disabled{background:#cbd5e0;cursor:not-allowed;transform:none;box-shadow:none;}
.btn-secondary{background:#e2e8f0;color:#4a5568;}
.btn-secondary:hover{background:#cbd5e0;}
.status{margin-top:18px;padding:12px 16px;border-radius:8px;font-size:10pt;display:none;}
.status.show{display:block;}
.status.info{background:#ebf8ff;color:#2c5282;border-left:4px solid #4299e1;}
.status.success{background:#f0fff4;color:#22543d;border-left:4px solid #48bb78;}
.status.error{background:#fff5f5;color:#742a2a;border-left:4px solid #f56565;white-space:pre-wrap;}
.preview{margin-top:20px;padding:14px;background:#f7fafc;border-radius:10px;display:none;}
.preview.show{display:block;}
.preview h3{margin:0 0 10px 0;font-size:11pt;color:#2d3748;}
.preview-grid{display:grid;grid-template-columns:max-content 1fr;gap:5px 14px;font-size:9pt;}
.preview-grid .k{color:#718096;}
.preview-grid .v{color:#2d3748;font-weight:600;font-family:Menlo,Monaco,monospace;word-break:break-all;}
.spinner{display:inline-block;width:13px;height:13px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;vertical-align:middle;margin-right:6px;}
@keyframes spin{to{transform:rotate(360deg);}}
.privacy{padding:12px 16px;background:#fffbea;border:1px solid #f6e05e;border-radius:8px;font-size:9pt;color:#744210;margin-bottom:20px;}
.privacy strong{color:#5c2c00;}
.footer{padding:14px 36px;color:#a0aec0;font-size:9pt;text-align:center;border-top:1px solid #edf2f7;}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>📦 商业发票自动生成器</h1>
    <p>上传 PI、出口许可证、配载 + 印章 → 自动生成商业发票 PDF</p>
  </div>

  <div class="main">
    <div class="privacy">
      🔒 <strong>隐私保护</strong>：所有文件仅在生成 PDF 期间临时处理，处理完即刻删除，不会保留。印章保存在你自己的浏览器（localStorage），不上传到服务器（除生成那一刻）。
    </div>

    <form id="form" onsubmit="return false;">
      <div class="section">
        <h2 class="section-title">📄 第一步：上传源文件（每次都要上传）</h2>
        <div class="uploads">
          <div class="upload-card" id="card-pi">
            <label for="pi">
              <div class="label-title">① PI（形式发票）</div>
              <div class="label-hint">提取：PI 号、PI 日期、收货人地址、单价、货物</div>
              <div class="filename" id="name-pi"></div>
            </label>
            <input type="file" id="pi" name="pi" accept=".pdf" required>
          </div>
          <div class="upload-card" id="card-license">
            <label for="license">
              <div class="label-title">② 出口许可证</div>
              <div class="label-hint">提取：收货人公司名、合同号、合同日期、数量</div>
              <div class="filename" id="name-license"></div>
            </label>
            <input type="file" id="license" name="license" accept=".pdf" required>
          </div>
          <div class="upload-card" id="card-booking">
            <label for="booking">
              <div class="label-title">③ 配载（订舱通知）</div>
              <div class="label-hint">提取：装货港、卸货港</div>
              <div class="filename" id="name-booking"></div>
            </label>
            <input type="file" id="booking" name="booking" accept=".pdf" required>
          </div>
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">🏷️ 第二步：印章（首次上传后浏览器记住，下次免传）</h2>
        <div class="uploads cols-2">
          <div class="stamp-card" id="card-sig">
            <label for="sig">
              <div class="label-title">签名章 (PNG)</div>
              <div class="preview" id="preview-sig"><span class="placeholder">点击上传</span></div>
            </label>
            <input type="file" id="sig" name="sig" accept="image/png,image/jpeg">
            <div class="stamp-actions"><a onclick="clearStamp('sig')">清除</a></div>
          </div>
          <div class="stamp-card" id="card-seal">
            <label for="seal">
              <div class="label-title">公司印章 (PNG)</div>
              <div class="preview" id="preview-seal"><span class="placeholder">点击上传</span></div>
            </label>
            <input type="file" id="seal" name="seal" accept="image/png,image/jpeg">
            <div class="stamp-actions"><a onclick="clearStamp('seal')">清除</a></div>
          </div>
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">🏢 第三步：抬头（可选，浏览器记住，下次免传）</h2>
        <div class="uploads cols-2">
          <div class="stamp-card" id="card-logo">
            <label for="logo">
              <div class="label-title">公司 Logo (PNG)</div>
              <div class="preview" id="preview-logo"><span class="placeholder">点击上传</span></div>
            </label>
            <input type="file" id="logo" name="logo" accept="image/png,image/jpeg">
            <div class="stamp-actions"><a onclick="clearBrand('logo')">清除</a></div>
          </div>
          <div class="stamp-card" id="card-nameplate">
            <label for="nameplate">
              <div class="label-title">公司英文名 (PNG)</div>
              <div class="preview" id="preview-nameplate"><span class="placeholder">点击上传</span></div>
            </label>
            <input type="file" id="nameplate" name="nameplate" accept="image/png,image/jpeg">
            <div class="stamp-actions"><a onclick="clearBrand('nameplate')">清除</a></div>
          </div>
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">⚙️ 第四步：发票号</h2>
        <div class="options">
          <label for="invoice_no">Invoice No.</label>
          <input type="text" id="invoice_no" name="invoice_no" value="{{ default_invoice_no }}">
        </div>
      </div>

      <div class="actions">
        <button type="button" class="btn btn-secondary" onclick="resetForm()">清空</button>
        <button type="button" class="btn btn-primary" id="submit" onclick="submitForm()" disabled>预览数据</button>
        <button type="button" class="btn btn-primary" id="download" onclick="downloadPDF()" style="display:none;">下载 PDF</button>
      </div>

      <div class="status" id="status"></div>

      <div class="preview" id="preview">
        <h3>📋 提取数据预览</h3>
        <div class="preview-grid" id="preview-grid"></div>
      </div>
    </form>
  </div>

  <div class="footer">
    数据全部临时处理，不留存 · 印章存于你浏览器本地
  </div>
</div>

<script>
const PDF_KEYS = ['pi','license','booking'];
const STAMP_KEYS = ['sig','seal'];          // 必传, 影响 submit 状态
const BRAND_KEYS = ['logo','nameplate'];    // 可选 (抬头), 不影响 submit 状态
const LABELS = {
  invoice_no:'发票号', invoice_date:'发票日期',
  consignee_name:'收货人', consignee_addr:'收货人地址',
  contract_no:'合同号', contract_date:'合同日期',
  port_loading:'起运港', port_discharge:'卸货港',
  goods_name:'货物名称', goods_brand:'品牌', hs_code:'HS Code',
  quantity_mt:'数量(MT)', unit_price:'单价(USD)', total:'总金额(USD)',
  pi_no:'PI 号', pi_date:'PI 日期',
};

// ============ 文件输入处理 ============
PDF_KEYS.forEach(k => {
  const inp = document.getElementById(k);
  inp.addEventListener('change', () => {
    const card = document.getElementById('card-' + k);
    const name = document.getElementById('name-' + k);
    if (inp.files.length) {
      card.classList.add('has-file');
      name.textContent = inp.files[0].name;
    } else {
      card.classList.remove('has-file');
      name.textContent = '';
    }
    updateSubmitState();
  });
});

// 通用: 印章 + 抬头 都用 localStorage 记住, 逻辑相同
function _wireImageCard(k, storagePrefix) {
  const inp = document.getElementById(k);
  inp.addEventListener('change', () => {
    if (!inp.files.length) return;
    const reader = new FileReader();
    reader.onload = e => {
      localStorage.setItem(storagePrefix + k, e.target.result);
      _renderImagePreview(k, storagePrefix);
      updateSubmitState();
    };
    reader.readAsDataURL(inp.files[0]);
  });
}

function _renderImagePreview(k, storagePrefix) {
  const data = localStorage.getItem(storagePrefix + k);
  const preview = document.getElementById('preview-' + k);
  const card = document.getElementById('card-' + k);
  if (data) {
    preview.innerHTML = '<img src="' + data + '">';
    card.classList.add('has-file');
  } else {
    preview.innerHTML = '<span class="placeholder">点击上传</span>';
    card.classList.remove('has-file');
  }
}

STAMP_KEYS.forEach(k => _wireImageCard(k, 'stamp_'));
BRAND_KEYS.forEach(k => _wireImageCard(k, 'brand_'));

function renderStampPreview(k) { _renderImagePreview(k, 'stamp_'); }
function renderBrandPreview(k) { _renderImagePreview(k, 'brand_'); }

function clearStamp(k) {
  localStorage.removeItem('stamp_' + k);
  document.getElementById(k).value = '';
  renderStampPreview(k);
  updateSubmitState();
}

function clearBrand(k) {
  localStorage.removeItem('brand_' + k);
  document.getElementById(k).value = '';
  renderBrandPreview(k);
  // brand 是可选, 不影响 submit 状态
}

function updateSubmitState() {
  const allPdfs = PDF_KEYS.every(k => document.getElementById(k).files.length);
  const allStamps = STAMP_KEYS.every(k =>
    document.getElementById(k).files.length || localStorage.getItem('stamp_' + k));
  document.getElementById('submit').disabled = !(allPdfs && allStamps);
}

// 转 base64 dataURL 到 Blob
function dataUrlToBlob(dataUrl) {
  const [header, b64] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)[1];
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

function buildFormData() {
  const fd = new FormData();
  PDF_KEYS.forEach(k => fd.append(k, document.getElementById(k).files[0]));
  fd.append('invoice_no', document.getElementById('invoice_no').value);
  // 印章 (必传) — 必走 localStorage 或本次上传
  STAMP_KEYS.forEach(k => {
    const inp = document.getElementById(k);
    if (inp.files.length) {
      fd.append(k, inp.files[0]);
    } else {
      const data = localStorage.getItem('stamp_' + k);
      if (data) fd.append(k, dataUrlToBlob(data), k + '.png');
    }
  });
  // 抬头 (可选) — 有就附上, 没有就跳过
  BRAND_KEYS.forEach(k => {
    const inp = document.getElementById(k);
    if (inp.files.length) {
      fd.append(k, inp.files[0]);
    } else {
      const data = localStorage.getItem('brand_' + k);
      if (data) fd.append(k, dataUrlToBlob(data), k + '.png');
    }
  });
  return fd;
}

function showStatus(text, kind) {
  const el = document.getElementById('status');
  el.className = 'status show ' + kind;
  el.textContent = text;
}

function resetForm() {
  if (!confirm('确定清空所有上传文件？(印章会保留在浏览器)')) return;
  PDF_KEYS.forEach(k => {
    document.getElementById(k).value = '';
    document.getElementById('card-' + k).classList.remove('has-file');
    document.getElementById('name-' + k).textContent = '';
  });
  document.getElementById('submit').disabled = true;
  document.getElementById('download').style.display = 'none';
  document.getElementById('submit').style.display = '';
  document.getElementById('status').className = 'status';
  document.getElementById('preview').classList.remove('show');
}

async function submitForm() {
  const btn = document.getElementById('submit');
  btn.innerHTML = '<span class="spinner"></span>解析中...';
  btn.disabled = true;
  showStatus('正在解析 PDF 并提取数据...', 'info');
  try {
    const res = await fetch('/extract', { method: 'POST', body: buildFormData() });
    const j = await res.json();
    if (!res.ok) throw new Error(j.error || '提取失败');
    const grid = document.getElementById('preview-grid');
    grid.innerHTML = '';
    const order = ['invoice_no','invoice_date','consignee_name','consignee_addr',
                   'contract_no','contract_date','port_loading','port_discharge',
                   'goods_name','goods_brand','hs_code','quantity_mt','unit_price','total',
                   'pi_no','pi_date'];
    order.forEach(k => {
      if (j[k] === undefined || j[k] === null || j[k] === '') return;
      const k1 = document.createElement('div'); k1.className = 'k'; k1.textContent = LABELS[k] || k;
      const v1 = document.createElement('div'); v1.className = 'v';
      v1.textContent = String(j[k]).replace(/\n/g, ' / ');
      grid.appendChild(k1); grid.appendChild(v1);
    });
    document.getElementById('preview').classList.add('show');
    showStatus('✓ 数据提取完成，检查无误后点"下载 PDF"', 'success');
    document.getElementById('submit').style.display = 'none';
    document.getElementById('download').style.display = '';
  } catch (e) {
    showStatus('错误: ' + e.message, 'error');
    btn.disabled = false;
  } finally {
    btn.innerHTML = '预览数据';
  }
}

async function downloadPDF() {
  const btn = document.getElementById('download');
  btn.innerHTML = '<span class="spinner"></span>生成中...';
  btn.disabled = true;
  showStatus('正在生成 PDF...', 'info');
  try {
    const res = await fetch('/generate', { method: 'POST', body: buildFormData() });
    if (!res.ok) { const j = await res.json(); throw new Error(j.error || '生成失败'); }
    const blob = await res.blob();
    const dispo = res.headers.get('Content-Disposition') || '';
    const m = dispo.match(/filename\*?=(?:UTF-8'')?([^;]+)/i);
    const fname = m ? decodeURIComponent(m[1].replace(/^"|"$/g, '')) : 'invoice.pdf';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = fname; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    showStatus('✓ PDF 已下载: ' + fname, 'success');
  } catch (e) {
    showStatus('错误: ' + e.message, 'error');
  } finally {
    btn.innerHTML = '下载 PDF';
    btn.disabled = false;
  }
}

// ============ 初始化 ============
window.addEventListener('DOMContentLoaded', () => {
  STAMP_KEYS.forEach(renderStampPreview);
  BRAND_KEYS.forEach(renderBrandPreview);
  updateSubmitState();
});
</script>
</body>
</html>
"""


def _save_uploads(req) -> tuple:
    """保存所有上传文件到临时目录.

    必传: 3 个 PDF (pi/license/booking) + 2 个印章 (sig/seal)
    可选: 2 个抬头 (logo/nameplate)
    """
    tmp = Path(tempfile.mkdtemp(prefix="invoice_"))
    paths = {}
    # 必传
    for key in ("pi", "license", "booking", "sig", "seal"):
        f = req.files.get(key)
        if not f or not f.filename:
            raise ValueError(f"缺少文件: {key}")
        ext = ".pdf" if key in ("pi", "license", "booking") else ".png"
        out = tmp / f"{key}{ext}"
        f.save(out)
        paths[key] = out
    # 可选 (抬头: 公司 logo + 公司英文名图)
    for key in ("logo", "nameplate"):
        f = req.files.get(key)
        if f and f.filename:
            out = tmp / f"{key}.png"
            f.save(out)
            paths[key] = out
    return tmp, paths


def _cleanup(tmp_dir: Path):
    """删除临时目录, 不留任何数据"""
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@app.route("/")
def index():
    return render_template_string(PAGE, default_invoice_no=DEFAULT_INVOICE_NO)


@app.route("/extract", methods=["POST"])
def extract():
    tmp = None
    try:
        tmp, paths = _save_uploads(request)
        invoice_no = (request.form.get("invoice_no") or DEFAULT_INVOICE_NO).strip()
        data = extract_data(paths["pi"], paths["license"], paths["booking"], invoice_no=invoice_no)
        try:
            qty = float(data.get("quantity_mt") or 0)
            price = float(data.get("unit_price") or 0)
            data["total"] = f"{qty * price:,.2f}"
        except Exception:
            pass
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if tmp:
            _cleanup(tmp)


@app.route("/generate", methods=["POST"])
def generate():
    tmp = None
    try:
        tmp, paths = _save_uploads(request)
        invoice_no = (request.form.get("invoice_no") or DEFAULT_INVOICE_NO).strip()
        data = extract_data(paths["pi"], paths["license"], paths["booking"], invoice_no=invoice_no)
        today = datetime.now().strftime("%Y%m%d")
        out_pdf = tmp / f"商业发票_{invoice_no}_修改于{today}.pdf"
        render_pdf(
            data, paths["sig"], paths["seal"], out_pdf,
            logo_path=paths.get("logo"),
            nameplate_path=paths.get("nameplate"),
        )
        # 注意: send_file 在请求结束前不能删 tmp, 用 after_this_request 延迟删除
        from flask import after_this_request
        @after_this_request
        def cleanup_after(response):
            _cleanup(tmp)
            return response
        return send_file(out_pdf, as_attachment=True, download_name=out_pdf.name,
                         mimetype="application/pdf")
    except Exception as e:
        if tmp:
            _cleanup(tmp)
        import traceback
        return jsonify({"error": f"{e}\n{traceback.format_exc()}"}), 500


@app.route("/healthz")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 5001))
    # 云端部署需要绑 0.0.0.0; 本地默认仅 127.0.0.1
    if IS_PRODUCTION or "--lan" in sys.argv:
        host = "0.0.0.0"
    else:
        host = "127.0.0.1"
    print("=" * 60)
    print(f"📦 商业发票生成器 启动中...")
    print(f"   访问: http://localhost:{port}")
    if host == "0.0.0.0" and not IS_PRODUCTION:
        print(f"   局域网: http://<本机IP>:{port}")
    print("=" * 60)
    app.run(host=host, port=port, debug=False)
