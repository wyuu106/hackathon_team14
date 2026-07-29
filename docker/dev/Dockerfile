FROM python:3.12-slim

# Node.jsをインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uvをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 作業ディレクトリ
WORKDIR /workspace

# コンテナを起動したままにする
CMD ["sleep", "infinity"]