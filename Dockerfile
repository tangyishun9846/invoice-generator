# 用于 Render / Railway / Fly.io / 自建服务器部署
FROM python:3.11-slim

# 安装 Chrome (用于 HTML→PDF 渲染)
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        ca-certificates \
        fonts-liberation \
        fonts-noto-cjk \
    && wget -qO - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/google-chrome-stable

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY invoice_core.py webapp.py ./

# Chrome 在容器里需要 --no-sandbox; 通过 env 传给代码使用 (代码已支持 CHROME_BIN)
ENV PYTHONUNBUFFERED=1

# 默认监听 0.0.0.0:8080, 平台会注入 $PORT 覆盖
ENV PORT=8080
EXPOSE 8080

# 用 gunicorn 而非 Flask dev server (生产推荐)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 webapp:app
