# Jupyter MCP Server

Jupyter notebookと統合されたModel Context Protocol (MCP) サーバーで、MCPツールを通じてコードセルの実行やノートブックコンテンツの管理を可能にします。

## 機能

- Jupyter notebookでのコードセル実行
- マークダウンセルとコードセルの追加・管理
- テキスト、画像、HTMLを含むセル出力の表示
- jupyter-ydocによる協調編集サポート
- 自動セッション・カーネル管理

## Dockerを使用したクイックスタート

JupyterLab環境を素早くセットアップするには、事前設定済みのDocker環境を使用できます：

### JupyterLab Docker環境のセットアップ

1. **JupyterLab Dockerリポジトリをクローン:**
   ```bash
   git clone https://github.com/TomokiIshimine/jupyter-lab-docker.git
   cd jupyter-lab-docker
   ```

2. **Docker Composeを使用してJupyterLabを起動:**
   ```bash
   docker-compose up -d
   ```

3. **JupyterLabにアクセス:**
   - ブラウザで `http://localhost:8888` を開く
   - トークンを求められた場合は `my-token` を入力

### Claude Desktopとの連携

Docker JupyterLab環境でこのMCPサーバーを使用するために、`claude_desktop_config.json` を設定します：

```json
{
  "mcpServers": {
    "jupyter": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "SERVER_URL=http://host.docker.internal:8888",
        "-e", "TOKEN=my-token",
        "-e", "NOTEBOOK_PATH=test.ipynb",
        "-e", "TIMEOUT=30",
        "tonlab/jupyter-mcp-server"
      ]
    }
  }
}
```

**設定パラメータ:**
- `SERVER_URL`: JupyterLab サーバーURL（通常は `http://host.docker.internal:8888`）
- `TOKEN`: JupyterLab アクセストークン（デフォルトは `my-token`）
- `NOTEBOOK_PATH`: 対象のJupyter Notebookファイル名
- `TIMEOUT`: タイムアウト時間（秒）

Docker JupyterLab環境には以下が含まれます：
- **最新のJupyterLabバージョン**: `quay.io/jupyter/base-notebook:x86_64-lab-4.1.5` を使用
- **協調編集機能**: `jupyter-server-ydoc` と `jupyter-collaboration` がプリインストール
- **日本語サポート**: 日本語フォントとmatplotlib設定
- **主要なPythonライブラリ**: matplotlib、scikit-learn、pandas、numpy
- **データ永続化**: ホストの `./work` ディレクトリが `/home/jovyan/work` にマウント

## プロジェクト構造

```
jupyter-mcp/
├── src/
│   ├── __init__.py          # パッケージ初期化
│   ├── server.py            # メインエントリーポイント
│   ├── models.py            # データモデル (AppConfig)
│   ├── config.py            # 設定管理
│   ├── exceptions.py        # カスタム例外
│   ├── notebook_manager.py  # ノートブック操作マネージャー
│   ├── tools.py             # MCPツール定義
│   └── utils.py             # ユーティリティ関数
├── tests/
│   ├── __init__.py          # テストパッケージ初期化
│   ├── conftest.py          # pytest設定
│   ├── test_jupyter_mcp.py  # 基本機能テスト
│   └── test_deletion_sync.py # セル削除同期テスト
├── .devcontainer/           # 開発コンテナ設定
├── .vscode/                 # VSCode設定
├── test_images/             # テスト用画像出力ディレクトリ
├── test_output/             # テスト出力ディレクトリ
├── requirements.txt         # Python依存関係
├── Dockerfile              # Docker設定
├── Makefile                # ビルド・テストコマンド
├── run_tests.sh            # テスト実行スクリプト
├── env.example             # 環境変数設定例
├── .gitignore              # Git除外設定
└── README.md               # このファイル
```

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/yourusername/jupyter-mcp.git
cd jupyter-mcp
```

2. 依存関係をインストール:
```bash
make install
# または
pip install -r requirements.txt
```

## 設定

サーバーは環境変数で設定されます：

- `NOTEBOOK_PATH`: ノートブックファイルのパス (デフォルト: "notebook.ipynb")
- `SERVER_URL`: Jupyter サーバーURL (デフォルト: "http://localhost:8888")
- `TOKEN`: Jupyter サーバー認証トークン (必須)
- `KERNEL_NAME`: 使用する特定のカーネル (オプション、サーバーのデフォルトを使用)
- `MCP_IMAGE_DIR`: 抽出した画像を保存するディレクトリ (デフォルト: "mcp_images")
- `TIMEOUT`: 一般的な操作タイムアウト秒数 (デフォルト: 180)
- `STARTUP_TIMEOUT`: 起動タイムアウト秒数 (デフォルト: 60)

### 環境変数の設定

`env.example`を`.env`にコピーして必要に応じて調整してください：

```bash
cp env.example .env
```

## 使用方法

### オプション1: Docker JupyterLab環境を使用（推奨）

最も簡単な開始方法は、事前設定済みのDocker JupyterLab環境を使用することです。上記の[Dockerを使用したクイックスタート](#dockerを使用したクイックスタート)セクションを参照してください。

### オプション2: サーバーをスタンドアロンで実行

```bash
# 必要な環境変数を設定
export TOKEN="your-jupyter-token"
export SERVER_URL="http://localhost:8888"

# サーバーを実行
python -m src.server
```

### オプション3: MCPサーバーのみDockerを使用

Dockerコンテナをビルドして実行:

```bash
docker build -t jupyter-mcp .
docker run -e TOKEN="your-token" -p 8080:8080 jupyter-mcp
```

### 利用可能なMCPツール

1. **add_markdown_cell**: ノートブックにマークダウンセルを追加
2. **add_code_cell_and_execute**: コードセルを追加して実行
3. **execute_cell**: インデックスで既存のセルを実行
4. **get_all_cells**: ノートブックからすべてのセルを取得
5. **update_cell**: 特定のセルの内容を更新
6. **delete_cell**: インデックスでセルを削除
7. **clear_all_outputs**: すべてのコードセルから出力をクリア

## 開発

### テストの実行

```bash
# すべてのテストを実行
make test

# 特定のテストを実行
make test-basic      # 基本機能テスト
make test-deletion   # 削除同期テスト
make test-pytest     # pytestでテスト実行
```

### コード構造

- **NotebookManager**: すべてのノートブック操作を処理:
  - Jupyterサーバーからのノートブックの読み込み・保存
  - 協調編集のためのYDoc管理
  - カーネルWebSocket接続によるセル実行
  - カーネルセッション管理

- **MCPツール**: 各ツールは`@mcp.tool()`でデコレートされ、以下を処理:
  - 入力検証
  - 適切なNotebookManagerメソッドの呼び出し
  - MCP応答用の出力フォーマット

- **Utils**: 以下のヘルパー関数:
  - nbformat互換性のためのノートブックデータクリーニング
  - セル出力の抽出とフォーマット
  - 異なる出力形式間の変換

## エラーハンドリング

サーバーには、より良いエラーハンドリングのためのカスタム例外クラスが含まれています：

- `ConfigurationError`: 設定関連エラー
- `NotebookError`: ノートブック操作エラー
- `KernelError`: カーネル実行エラー
- `ServerConnectionError`: Jupyterサーバー接続エラー

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を実装
4. 新機能のテストを追加
5. プルリクエストを送信

詳細な貢献ガイドラインについては、[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## テスト

プロジェクトには、すべての機能に対する包括的なテストが含まれています。テストは`tests/`ディレクトリに整理されています。

### テスト構造

```
tests/
├── __init__.py              # テストパッケージ初期化
├── conftest.py              # pytest設定
├── test_jupyter_mcp.py      # 基本機能テスト
└── test_deletion_sync.py    # セル削除同期テスト
```

### テストの実行

#### Make使用（推奨）

```bash
# テスト要件を含む依存関係をインストール
make install

# すべてのテストを実行
make test

# 特定のテストを実行
make test-basic      # 基本機能テスト
make test-deletion   # 削除同期テスト
make test-pytest     # pytestでテスト実行
```

#### テストランナースクリプト使用

```bash
# すべてのテストを実行
./run_tests.sh

# 特定のテストを実行
./run_tests.sh basic      # 基本機能テスト
./run_tests.sh deletion   # 削除同期テスト
./run_tests.sh pytest     # pytestで実行
```

#### 直接実行

```bash
# 個別のテストファイルを実行
python tests/test_jupyter_mcp.py
python tests/test_deletion_sync.py

# pytestで実行
pytest tests/ -v -s
```

### テスト環境

テストには実行中のJupyterサーバーが必要です。いくつかのオプションがあります：

#### オプション1: Docker JupyterLab環境を使用（推奨）

```bash
# Docker JupyterLab環境をクローンして開始
git clone https://github.com/TomokiIshimine/jupyter-lab-docker.git
cd jupyter-lab-docker
docker-compose up -d
```

#### オプション2: Makeを使用

```bash
make jupyter
```

#### オプション3: 手動セットアップ

```bash
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='my-token'
```

### 環境変数

`env.example`を`.env`にコピーして必要に応じて調整してください：

```bash
cp env.example .env
```

デフォルトのテスト環境変数：
- `SERVER_URL`: http://host.docker.internal:8888
- `TOKEN`: my-token
- `NOTEBOOK_PATH`: test.ipynb
- `MCP_IMAGE_DIR`: test_images

### クリーンアップ

テスト出力とキャッシュを削除：

```bash
make clean
``` 