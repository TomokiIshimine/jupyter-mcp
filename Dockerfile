FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY src/ .

# 開発用ステージ
FROM base AS dev

RUN apt-get update && apt-get install -y \
    git \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Pythonのユーティリティツールをインストール
RUN python -m pip install --upgrade pip \
    && pip install pylint autopep8 black yapf

CMD ["/bin/bash"]

# 本番用ステージ
FROM base AS prod
CMD ["python", "server.py"] 