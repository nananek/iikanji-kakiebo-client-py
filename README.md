# iikanji — いいかんじ家計簿 Python クライアント

いいかんじ家計簿サーバーの API を Python から呼び出すためのクライアントライブラリです。
仕訳の起票・閲覧・削除に対応しています。

## インストール

```bash
uv add iikanji
```

## クイックスタート

```python
from iikanji import KakeiboClient, JournalLine

with KakeiboClient("https://your-server.example.com", "ik_your_api_key") as client:
    result = client.create_journal(
        date="2026-02-15",
        description="スーパーで食材購入",
        lines=[
            JournalLine(account_id=12, debit=3000),   # 食費（借方）
            JournalLine(account_id=1, credit=3000),    # 現金（貸方）
        ],
    )
    print(f"仕訳ID: {result.id}, 伝票番号: {result.entry_number}")
```

API キーはサーバーの **設定 > API キー管理** から発行できます。必要なスコープ（`journals:create`, `journals:read`, `journals:delete`）を選択してください。

## ドキュメント

- [はじめに](docs/getting-started.md) — インストールと基本的な使い方
- [API リファレンス](docs/api-reference.md) — クラス・メソッド・例外の詳細
- [使用例](docs/examples.md) — CSV 一括登録、給与記録など実践的なサンプル

## 要件

- Python 3.12+
- いいかんじ家計簿サーバーの API キー

## 開発

```bash
uv sync --all-extras
uv run pytest
```

## ライセンス

[いいかんじ™ライセンス (IKL)](LICENSE) — MIT 互換
