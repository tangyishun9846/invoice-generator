# 商业发票生成器 — 公网部署指南

## 选哪个平台

| 平台 | 费用 | 特点 | 推荐场景 |
|------|------|------|---------|
| **Render.com** | 免费层够用 | 简单，GitHub 连接一键部署，15min 不用就休眠（首次访问慢 ~30s） | ✅ 首选，省心 |
| **Fly.io** | 免费层 3 个小机器 | 免费机器更稳定不休眠 | 用得频繁，怕冷启动 |
| **阿里云轻量服务器** | ~50 元/月 | 国内访问快，永久在线 | 中国客户多 |

下面以 **Render.com** 为例，10 分钟搞定。

---

## 一、准备 Git 仓库

Render 是从 Git 拉代码自动部署的。你需要先把代码推到 GitHub。

### 1. 新建一个 GitHub 仓库（私有即可）

打开 https://github.com/new
- Repository name: `invoice-generator`（随便起）
- 选 **Private**
- 不要勾任何 "Initialize"
- 点 **Create repository**

### 2. 上传代码

在终端里：

```bash
cd /Users/shun/Desktop/Claud-code/ranran

# 初始化 git，只把部署需要的文件加进去（不带印章/PDF/Doc）
git init
git add invoice_core.py webapp.py requirements.txt Dockerfile .dockerignore DEPLOY.md
git commit -m "initial commit"

# 替换下面这行的 URL 为你刚创建的仓库地址（GitHub 页面上能复制到）
git remote add origin git@github.com:你的用户名/invoice-generator.git
git branch -M main
git push -u origin main
```

> ⚠️ `.dockerignore` 里已经排除了 PDF/PNG/Doc 等敏感文件，确保不会把客户数据/印章推到 GitHub。

---

## 二、Render.com 部署

### 1. 注册并连接 GitHub

1. 打开 https://render.com，用 GitHub 账号登录
2. 授权 Render 访问你的私有仓库

### 2. 创建 Web Service

1. 顶部右上角点 **+ New** → **Web Service**
2. 选刚才推上去的 `invoice-generator` 仓库
3. 配置：
   - **Name**: `invoice-generator`（这会成为 URL 的一部分）
   - **Region**: Singapore（亚洲访问最近）
   - **Branch**: `main`
   - **Runtime**: 选 **Docker**（自动检测到 Dockerfile）
   - **Instance Type**: **Free**
4. 点 **Create Web Service**

### 3. 等部署完成

- 第一次构建要 5-10 分钟（要装 Chrome）
- 看到日志最后出现 `Booting worker` / `Listening on 0.0.0.0:8080` 就成功了
- URL 形如：`https://invoice-generator-xxxx.onrender.com`

### 4. 测试

直接打开那个 URL，应该能看到上传页面。上传 PI/许可证/配载/印章，下载 PDF 试试。

---

## 三、给同事/客户用

把 Render 给你的 URL（如 `https://invoice-generator-xxxx.onrender.com`）发给任何人就行。

**第一次用：**
1. 上传 3 个 PDF（PI / 出口许可证 / 配载）
2. 上传 2 个印章（签名章 + 公司印章）
3. 点"预览数据"确认无误
4. 点"下载 PDF"

**第二次起：** 印章浏览器记住了，只需上传 3 个 PDF。

---

## 四、隐私保证

✅ 服务器端：所有上传文件保存在临时目录，请求结束立刻 `rm -rf` 删除  
✅ 浏览器端：印章只存在用户自己浏览器的 localStorage，不发到服务器（除生成那一刻）  
✅ 你的 Mac：完全不参与，无任何数据残留  
⚠️ Render 的服务器：处理过程中文件会临时落盘几秒，你需要信任 Render（或换成自己的 VPS）  

---

## 五、自定义域名（可选）

不想用 `xxxx.onrender.com` 这种丑 URL？

1. Render 控制台 → 你的 service → **Settings** → **Custom Domains**
2. 加上你的域名（例如 `invoice.yourcompany.com`）
3. 按提示去你的域名 DNS 加 CNAME 记录
4. 等几分钟生效，HTTPS 证书 Render 自动签发

---

## 六、休眠问题怎么办

Render 免费层 15 分钟没访问就休眠，下次首次访问要等 30 秒冷启动。

**方案 A：升级 Starter 套餐**（$7/月）— 永不休眠

**方案 B：用免费的定时 ping 服务保活**
- 在 https://uptimerobot.com 注册
- 添加监控 `https://invoice-generator-xxxx.onrender.com/healthz`
- 设 5 分钟 ping 一次，永远不休眠

**方案 C：换 Fly.io**
- Fly 的免费机器不休眠
- 部署稍复杂一点点

---

## 七、更新代码怎么办

改完代码：

```bash
cd /Users/shun/Desktop/Claud-code/ranran
git add -A
git commit -m "改了什么"
git push
```

Render 检测到 push 会自动重新构建部署，几分钟后生效。

---

## 八、本地继续开发/测试

```bash
cd /Users/shun/Desktop/Claud-code/ranran
python3 webapp.py
# 浏览器打开 http://localhost:5001
```

本地改完没问题再 push 到 GitHub，让 Render 自动部署。
