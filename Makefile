.PHONY: test test-basic test-deletion test-pytest install clean help jupyter

# デフォルトターゲット
help:
	@echo "Jupyter MCP Server - 利用可能なコマンド:"
	@echo "  make install      - 依存関係をインストール"
	@echo "  make test         - すべてのテストを実行"
	@echo "  make test-basic   - 基本機能テストを実行"
	@echo "  make test-deletion - 削除同期テストを実行"
	@echo "  make test-pytest  - pytestでテストを実行"
	@echo "  make clean        - テスト出力とキャッシュをクリーンアップ"
	@echo "  make jupyter      - Jupyterサーバーを開始（テスト用）"

# 依存関係をインストール
install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio

# すべてのテストを実行
test:
	./run_tests.sh

# 基本機能テストを実行
test-basic:
	./run_tests.sh basic

# 削除同期テストを実行
test-deletion:
	./run_tests.sh deletion

# pytestでテストを実行
test-pytest:
	./run_tests.sh pytest

# テスト出力とキャッシュをクリーンアップ
clean:
	rm -rf test_output/
	rm -rf test_images/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete

# テスト用Jupyterサーバーを開始
jupyter:
	@echo "Jupyterサーバーを開始中..."
	@echo "サーバーURL: http://localhost:8888"
	@echo "トークン: my-token"
	jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='my-token' 