#!/bin/bash
# Jupyter MCP Server テストランナー

set -e

echo "=== Jupyter MCP Server テストランナー ==="
echo

# .envファイルが存在する場合は読み込み
if [ -f .env ]; then
    echo ".envファイルから環境変数を読み込み中..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ 環境変数が読み込まれました"
    echo
fi

# Jupyterサーバーの接続確認
echo "Jupyterサーバーの接続を確認中..."
if ! curl -s -H "Authorization: token ${TOKEN:-my-token}" "${SERVER_URL:-http://host.docker.internal:8888}/api" > /dev/null; then
    echo "❌ エラー: ${SERVER_URL:-http://host.docker.internal:8888} のJupyterサーバーに接続できません"
    echo "正しいトークンでJupyterサーバーが実行されていることを確認してください。"
    exit 1
fi
echo "✓ Jupyterサーバーにアクセス可能です"
echo

# テスト出力ディレクトリを作成
mkdir -p test_output
mkdir -p test_images

# 引数に基づいてテストを実行
if [ "$1" = "pytest" ]; then
    echo "pytestでテストを実行中..."
    pytest tests/ -v -s
elif [ "$1" = "basic" ]; then
    echo "基本機能テストを実行中..."
    python tests/test_jupyter_mcp.py
elif [ "$1" = "deletion" ]; then
    echo "削除同期テストを実行中..."
    python tests/test_deletion_sync.py
else
    echo "すべてのテストを実行中..."
    echo
    echo "1. 基本機能テスト:"
    python tests/test_jupyter_mcp.py
    echo
    echo "2. 削除同期テスト:"
    python tests/test_deletion_sync.py
fi

echo
echo "=== テスト実行完了 ===" 