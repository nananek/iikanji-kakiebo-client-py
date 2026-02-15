# 使用例

## 食費の記録（現金払い）

```python
from iikanji import KakeiboClient, JournalLine

with KakeiboClient("https://example.com", "ik_your_key") as client:
    client.create_journal(
        date="2026-02-15",
        description="スーパーで食材購入",
        lines=[
            JournalLine(account_id=12, debit=3500),   # 食費
            JournalLine(account_id=1, credit=3500),    # 現金
        ],
    )
```

## 給与の記録（複数行）

```python
from datetime import date
from iikanji import KakeiboClient, JournalLine

with KakeiboClient("https://example.com", "ik_your_key") as client:
    client.create_journal(
        date=date(2026, 2, 25),
        description="2月分給与",
        lines=[
            JournalLine(account_id=2, debit=300000),     # 普通預金（手取り）
            JournalLine(account_id=30, debit=45000),      # 源泉所得税
            JournalLine(account_id=31, debit=25000),      # 住民税
            JournalLine(account_id=20, debit=30000),      # 社会保険料
            JournalLine(account_id=10, credit=400000),    # 給与収入
        ],
    )
```

## CSV からの一括登録

```python
import csv
from iikanji import KakeiboClient, JournalLine, KakeiboAPIError

ACCOUNT_MAP = {
    "食費": 12,
    "交通費": 16,
    "日用品": 17,
}

with KakeiboClient("https://example.com", "ik_your_key") as client:
    with open("expenses.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["カテゴリ"]
            account_id = ACCOUNT_MAP.get(category)
            if not account_id:
                print(f"不明なカテゴリ: {category}, スキップ")
                continue

            try:
                result = client.create_journal(
                    date=row["日付"],
                    description=row["摘要"],
                    lines=[
                        JournalLine(account_id=account_id, debit=int(row["金額"])),
                        JournalLine(account_id=1, credit=int(row["金額"])),
                    ],
                )
                print(f"登録完了: 伝票#{result.entry_number}")
            except KakeiboAPIError as e:
                print(f"エラー: {row['摘要']} - {e.message}")
```

## 仕訳の閲覧

```python
from iikanji import KakeiboClient

with KakeiboClient("https://example.com", "ik_your_key") as client:
    # 一覧取得（日付範囲で絞り込み）
    result = client.list_journals(date_from="2026-02-01", date_to="2026-02-28")
    print(f"全{result.total}件中 {len(result.journals)}件取得")

    for j in result.journals:
        print(f"  #{j.entry_number} {j.date} {j.description}")

    # 1件取得
    detail = client.get_journal(journal_id=42)
    print(f"伝票#{detail.entry_number}: {detail.description}")
    for line in detail.lines:
        print(f"  科目{line.account_id}: 借方{line.debit} 貸方{line.credit}")
```

## 仕訳の削除

```python
from iikanji import KakeiboClient, KakeiboAPIError

with KakeiboClient("https://example.com", "ik_your_key") as client:
    try:
        client.delete_journal(journal_id=42)
        print("削除しました")
    except KakeiboAPIError as e:
        print(f"削除できません: {e.message}")
```

## タイムアウトの変更

```python
# 長時間かかるリクエスト用にタイムアウトを延長
client = KakeiboClient(
    "https://example.com",
    "ik_your_key",
    timeout=60.0,
)
```

## 行レベルの摘要

仕訳全体の摘要とは別に、各明細行に摘要を付けられます。

```python
with KakeiboClient("https://example.com", "ik_your_key") as client:
    client.create_journal(
        date="2026-02-15",
        description="日用品購入",
        lines=[
            JournalLine(account_id=17, debit=500, description="洗剤"),
            JournalLine(account_id=17, debit=300, description="ゴミ袋"),
            JournalLine(account_id=1, credit=800),
        ],
    )
```
