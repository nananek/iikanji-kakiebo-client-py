# API リファレンス

## KakeiboClient

メインのクライアントクラス。コンテキストマネージャ（`with` 文）に対応。

### コンストラクタ

```python
KakeiboClient(
    base_url: str,
    api_key: str,
    *,
    timeout: float = 30.0,
    http_client: httpx.Client | None = None,
)
```

| 引数 | 型 | 説明 |
|------|-----|------|
| `base_url` | `str` | サーバーの URL（例: `"https://example.com"`） |
| `api_key` | `str` | API キー（`ik_` プレフィックス付き） |
| `timeout` | `float` | HTTP タイムアウト秒数（デフォルト: 30.0） |
| `http_client` | `httpx.Client \| None` | カスタム httpx クライアント（テスト用） |

### メソッド

#### `create_journal`

仕訳を起票する。

```python
create_journal(
    *,
    date: date | str,
    description: str,
    lines: list[JournalLine],
    source: str = "api",
) -> JournalCreateResponse
```

| 引数 | 型 | 説明 |
|------|-----|------|
| `date` | `date \| str` | 日付。`datetime.date` オブジェクトまたは `"YYYY-MM-DD"` 形式の文字列 |
| `description` | `str` | 摘要（必須、空文字不可） |
| `lines` | `list[JournalLine]` | 仕訳明細行のリスト（1行以上必須） |
| `source` | `str` | ソース種別（デフォルト: `"api"`） |

**戻り値:** `JournalCreateResponse`

**例外:**
- `AuthenticationError` — API キーが無効または未指定
- `KakeiboAPIError` — バリデーションエラー（貸借不一致、期間ロック等）

#### `close`

内部の HTTP クライアントを閉じる。コンテキストマネージャ使用時は自動的に呼ばれる。

```python
close() -> None
```

---

## JournalLine

仕訳の1明細行を表すデータクラス。

```python
@dataclass
class JournalLine:
    account_id: int
    debit: int = 0
    credit: int = 0
    description: str = ""
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `account_id` | `int` | 勘定科目 ID（必須） |
| `debit` | `int` | 借方金額（デフォルト: 0） |
| `credit` | `int` | 貸方金額（デフォルト: 0） |
| `description` | `str` | 行レベルの摘要（省略可） |

**注意:** 仕訳全体で借方合計と貸方合計が一致する必要があります（複式簿記）。

---

## JournalCreateResponse

仕訳起票の成功レスポンス。

```python
@dataclass
class JournalCreateResponse:
    id: int
    entry_number: int
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | `int` | 作成された仕訳の内部 ID |
| `entry_number` | `int` | ユーザー内で一意の伝票番号 |

---

## 例外クラス

### KakeiboAPIError

API がエラーレスポンスを返した場合の基底例外。

```python
class KakeiboAPIError(Exception):
    status_code: int   # HTTP ステータスコード
    message: str       # サーバーからのエラーメッセージ
```

### AuthenticationError

`KakeiboAPIError` のサブクラス。401 レスポンス時に送出。

```python
class AuthenticationError(KakeiboAPIError):
    # status_code は常に 401
```

**主なエラーメッセージ（サーバーから返される）:**

| メッセージ | 原因 |
|-----------|------|
| `Authorization ヘッダーが必要です。` | Bearer トークン未指定 |
| `無効な API キーです。` | キーが無効または無効化済み |
| `date は必須です。` | 日付が未指定 |
| `description は必須です。` | 摘要が未指定 |
| `lines は必須です（配列）。` | 明細行が未指定 |
| `date の形式が不正です（YYYY-MM-DD）。` | 日付フォーマット不正 |
| `lines[i].account_id は必須です。` | 科目 ID が未指定 |
| `貸借が一致しません（借方: X, 貸方: Y）` | 借方・貸方の合計不一致 |
