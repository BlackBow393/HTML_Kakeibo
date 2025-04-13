# ベースイメージ
FROM python:3.12-slim

# 日本語フォントとロケール設定
ENV LANG=C.UTF-8
RUN apt-get update && \
    apt-get install -y fonts-ipafont && \
    rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成
WORKDIR /app

# アプリケーションファイルをコピー
COPY . /app

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# Flaskのポートを開放
EXPOSE 5000

# アプリケーションの起動
CMD ["python", "app.py"]
