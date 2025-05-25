# Jupyter Notebook MCP Server

Jupyter NotebookとModel Context Protocol (MCP)を統合するサーバーです。`jupyter-ydoc`、`nbclient`、`nbformat`を使用して実装されています。

## 機能

- **ノートブックの操作**: コードセルとマークダウンセルの追加、実行、編集、削除
- **リアルタイムコラボレーション**: `jupyter-ydoc`を使用したYDocベースの同期
- **カーネル管理**: `nbclient`を使用した堅牢なカーネル実行
- **標準フォーマット**: `nbformat`を使用したJupyterノートブックの標準的な処理
- **画像サポート**: PNG画像の自動保存と表示
- **非同期処理**: 効率的な非同期I/O操作
- **Jupyter Server統合**: 実際のJupyter Serverに接続してカーネルを実行

## 利用可能なツール

### `add_markdown_cell`
マークダウンセルをノートブックに追加します。

### `add_code_cell_and_execute`
コードセルを追加して実行します。

### `execute_cell`
既存のセルを指定したインデックスで実行します。

### `get_all_cells`
ノートブック内のすべてのセルを取得します。

### `update_cell`
既存のセルの内容を更新します。

### `delete_cell`
指定したインデックスのセルを削除します。

### `clear_all_outputs`
すべてのコードセルの出力をクリアします。

### `get_available_kernels`
Jupyter Serverから利用可能なカーネルの一覧を取得します。現在使用中のカーネルと、環境変数で設定されたカーネルも表示します。

## 環境変数

- `NOTEBOOK_PATH`: ノートブックファイルのパス（デフォルト: `notebook.ipynb`）
- `SERVER_URL`: Jupyter ServerのURL（デフォルト: `http://localhost:8888`）**必須**
- `TOKEN`: Jupyter Serverの認証トークン **必須**
- `KERNEL_NAME`: 使用するJupyterカーネル名（オプション。設定されていない場合はサーバーから自動選択）
- `MCP_IMAGE_DIR`: 画像を保存するディレクトリ（デフォルト: `mcp_images`）
- `TIMEOUT`: セル実行のタイムアウト秒数（デフォルト: 180）
- `STARTUP_TIMEOUT`: カーネル起動のタイムアウト秒数（デフォルト: 60）

## カーネルの自動選択

`KERNEL_NAME`環境変数が設定されていない場合、サーバーは以下の優先順位でカーネルを自動選択します：

1. Jupyter Serverのデフォルトカーネル
2. `python3`カーネル（利用可能な場合）
3. 利用可能な最初のカーネル

`get_available_kernels`ツールを使用して、利用可能なカーネルの一覧を確認できます。

## Jupyter Serverの起動

まず、Jupyter Serverを起動する必要があります：

```bash
jupyter notebook --NotebookApp.token='your-secure-token' --NotebookApp.allow_origin='*'
```

または、JupyterLabを使用する場合：

```bash
jupyter lab --ServerApp.token='your-secure-token' --ServerApp.allow_origin='*'
```

## インストール

```bash
pip install -r requirements.txt
```

## 実行

環境変数を設定してから実行します：

```bash
export SERVER_URL="http://localhost:8888"
export TOKEN="your-secure-token"
python src/server.py
```

## アーキテクチャ

このサーバーは以下のコンポーネントで構成されています：

1. **NotebookManager**: ノートブックの操作を管理するメインクラス
   - Jupyter Server APIとの通信
   - YDocとの同期
   - ノートブックの読み書き
   - カーネルの実行管理

2. **Jupyter Server統合**: 
   - REST APIを使用したノートブックの読み書き
   - WebSocketを使用したカーネルとの通信
   - セッション管理

3. **YDoc統合**: リアルタイムコラボレーション機能のための`jupyter-ydoc`
   - ノートブックの状態を同期
   - 将来的な共同編集機能の基盤

4. **nbclient**: カーネル実行の管理
   - 非同期実行
   - タイムアウト処理
   - エラーハンドリング

5. **nbformat**: Jupyterノートブックの標準フォーマット処理
   - ノートブックの読み書き
   - セルの作成と操作 