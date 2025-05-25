# 貢献ガイドライン

Jupyter MCP Serverプロジェクトへの貢献をお考えいただき、ありがとうございます！

## 開発環境のセットアップ

1. リポジトリをフォーク
2. ローカルにクローン:
   ```bash
   git clone https://github.com/yourusername/jupyter-mcp.git
   cd jupyter-mcp
   ```

3. 依存関係をインストール:
   ```bash
   make install
   ```

4. 環境変数を設定:
   ```bash
   cp env.example .env
   # .envファイルを編集して適切な値を設定
   ```

## 開発ワークフロー

1. 機能ブランチを作成:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 変更を実装

3. テストを実行:
   ```bash
   make test
   ```

4. コードスタイルを確認:
   ```bash
   # 必要に応じてフォーマッターを実行
   black src/ tests/
   ```

5. コミットとプッシュ:
   ```bash
   git add .
   git commit -m "feat: 新機能の説明"
   git push origin feature/your-feature-name
   ```

6. プルリクエストを作成

## コーディング規約

- Python PEP 8に従う
- 型ヒントを使用する
- docstringを適切に記述する
- テストカバレッジを維持する

## テスト

新機能を追加する場合は、対応するテストも追加してください：

- 単体テスト: `tests/`ディレクトリに追加
- 統合テスト: 既存のテストファイルに追加

テストの実行:
```bash
# すべてのテスト
make test

# 特定のテスト
make test-basic
make test-deletion
```

## バグレポート

バグを発見した場合は、以下の情報を含めてIssueを作成してください：

- 問題の詳細な説明
- 再現手順
- 期待される動作
- 実際の動作
- 環境情報（OS、Pythonバージョンなど）

## 機能リクエスト

新機能の提案は歓迎します。Issueで以下を説明してください：

- 機能の詳細
- 使用ケース
- 実装の提案（あれば）

## コミットメッセージ

Conventional Commitsの形式を推奨します：

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント更新
- `test:` テスト追加・修正
- `refactor:` リファクタリング

## 質問

質問がある場合は、Issueを作成するか、プロジェクトメンテナーに直接連絡してください。

ご協力ありがとうございます！ 