"""KakeiboClient のユニットテスト"""

import json

import httpx
import pytest

from iikanji import (
    AnalyzeResponse,
    AuthenticationError,
    DraftDetail,
    DraftListItem,
    JournalCreateResponse,
    JournalDetail,
    JournalLine,
    JournalListResponse,
    KakeiboAPIError,
    KakeiboClient,
)


def _make_transport(status_code: int, body: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=body)

    return httpx.MockTransport(handler)


def _make_client(status_code: int, body: dict) -> KakeiboClient:
    transport = _make_transport(status_code, body)
    http_client = httpx.Client(
        transport=transport,
        base_url="https://test.example.com",
        headers={"Authorization": "Bearer ik_testkey"},
    )
    return KakeiboClient(
        "https://test.example.com",
        "ik_testkey",
        http_client=http_client,
    )


SAMPLE_JOURNAL = {
    "id": 42,
    "date": "2026-02-15",
    "entry_number": 7,
    "description": "テスト仕訳",
    "source": "api",
    "lines": [
        {"account_id": 12, "debit": 1000, "credit": 0, "description": ""},
        {"account_id": 1, "debit": 0, "credit": 1000, "description": "メモ"},
    ],
}


class TestCreateJournal:
    def test_success(self) -> None:
        client = _make_client(201, {"ok": True, "id": 42, "entry_number": 7})

        with client:
            result = client.create_journal(
                date="2026-02-15",
                description="テスト仕訳",
                lines=[
                    JournalLine(account_id=12, debit=1000),
                    JournalLine(account_id=1, credit=1000),
                ],
            )

        assert isinstance(result, JournalCreateResponse)
        assert result.id == 42
        assert result.entry_number == 7

    def test_sends_correct_payload(self) -> None:
        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(201, json={"ok": True, "id": 1, "entry_number": 1})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.create_journal(
                date="2026-01-10",
                description="食材",
                lines=[
                    JournalLine(account_id=5, debit=500, description="メモ"),
                    JournalLine(account_id=1, credit=500),
                ],
                source="custom",
            )

        payload = captured[0]
        assert payload["date"] == "2026-01-10"
        assert payload["description"] == "食材"
        assert payload["source"] == "custom"
        assert len(payload["lines"]) == 2
        assert payload["lines"][0] == {"account_id": 5, "debit": 500, "description": "メモ"}
        assert payload["lines"][1] == {"account_id": 1, "credit": 500}

    def test_with_draft_id(self) -> None:
        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(201, json={"ok": True, "id": 1, "entry_number": 1, "draft_id": 10})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.create_journal(
                date="2026-01-10",
                description="下書きから確定",
                lines=[
                    JournalLine(account_id=5, debit=500),
                    JournalLine(account_id=1, credit=500),
                ],
                draft_id=10,
            )

        assert captured[0]["draft_id"] == 10

    def test_without_draft_id(self) -> None:
        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(201, json={"ok": True, "id": 1, "entry_number": 1})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.create_journal(
                date="2026-01-10",
                description="通常の仕訳",
                lines=[
                    JournalLine(account_id=5, debit=500),
                    JournalLine(account_id=1, credit=500),
                ],
            )

        assert "draft_id" not in captured[0]

    def test_authentication_error(self) -> None:
        client = _make_client(401, {"error": "無効な API キーです。"})

        with client, pytest.raises(AuthenticationError) as exc_info:
            client.create_journal(
                date="2026-02-15",
                description="テスト",
                lines=[JournalLine(account_id=1, debit=100)],
            )

        assert exc_info.value.status_code == 401
        assert "無効な API キー" in exc_info.value.message

    def test_validation_error(self) -> None:
        client = _make_client(400, {"error": "貸借が一致しません（借方: 1000, 貸方: 500）"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.create_journal(
                date="2026-02-15",
                description="テスト",
                lines=[
                    JournalLine(account_id=1, debit=1000),
                    JournalLine(account_id=2, credit=500),
                ],
            )

        assert exc_info.value.status_code == 400
        assert "貸借が一致しません" in exc_info.value.message

    def test_context_manager(self) -> None:
        client = _make_client(201, {"ok": True, "id": 1, "entry_number": 1})

        with client as c:
            assert c is client

    def test_date_object(self) -> None:
        from datetime import date

        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(201, json={"ok": True, "id": 1, "entry_number": 1})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.create_journal(
                date=date(2026, 3, 1),
                description="date objectテスト",
                lines=[JournalLine(account_id=1, debit=100), JournalLine(account_id=2, credit=100)],
            )

        assert captured[0]["date"] == "2026-03-01"

    def test_datetime_object(self) -> None:
        from datetime import datetime

        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(201, json={"ok": True, "id": 1, "entry_number": 1})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.create_journal(
                date=datetime(2026, 3, 1, 14, 30, 0),
                description="datetimeテスト",
                lines=[JournalLine(account_id=1, debit=100), JournalLine(account_id=2, credit=100)],
            )

        assert captured[0]["date"] == "2026-03-01"


class TestGetJournal:
    def test_success(self) -> None:
        client = _make_client(200, {"ok": True, "journal": SAMPLE_JOURNAL})

        with client:
            result = client.get_journal(42)

        assert isinstance(result, JournalDetail)
        assert result.id == 42
        assert result.date == "2026-02-15"
        assert result.entry_number == 7
        assert result.description == "テスト仕訳"
        assert result.source == "api"
        assert len(result.lines) == 2
        assert result.lines[0].account_id == 12
        assert result.lines[0].debit == 1000
        assert result.lines[1].description == "メモ"

    def test_not_found(self) -> None:
        client = _make_client(404, {"error": "仕訳が見つかりません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.get_journal(999)

        assert exc_info.value.status_code == 404

    def test_forbidden(self) -> None:
        client = _make_client(403, {"error": "この API キーには journals:read 権限がありません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.get_journal(1)

        assert exc_info.value.status_code == 403


class TestListJournals:
    def test_success(self) -> None:
        body = {
            "ok": True,
            "journals": [SAMPLE_JOURNAL],
            "total": 1,
            "page": 1,
            "per_page": 20,
        }
        client = _make_client(200, body)

        with client:
            result = client.list_journals()

        assert isinstance(result, JournalListResponse)
        assert result.total == 1
        assert result.page == 1
        assert result.per_page == 20
        assert len(result.journals) == 1
        assert result.journals[0].id == 42

    def test_sends_query_params(self) -> None:
        captured_urls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_urls.append(str(request.url))
            return httpx.Response(200, json={
                "ok": True, "journals": [], "total": 0, "page": 2, "per_page": 10,
            })

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.list_journals(date_from="2026-01-01", date_to="2026-01-31", page=2, per_page=10)

        url = captured_urls[0]
        assert "date_from=2026-01-01" in url
        assert "date_to=2026-01-31" in url
        assert "page=2" in url
        assert "per_page=10" in url


class TestDeleteJournal:
    def test_success(self) -> None:
        client = _make_client(200, {"ok": True})

        with client:
            client.delete_journal(42)  # should not raise

    def test_not_found(self) -> None:
        client = _make_client(404, {"error": "仕訳が見つかりません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.delete_journal(999)

        assert exc_info.value.status_code == 404

    def test_locked_period(self) -> None:
        client = _make_client(400, {"error": "2026年1月は確定済みのため変更できません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.delete_journal(42)

        assert exc_info.value.status_code == 400
        assert "確定済み" in exc_info.value.message

    def test_sends_delete_method(self) -> None:
        captured_methods: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_methods.append(request.method)
            return httpx.Response(200, json={"ok": True})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.delete_journal(1)

        assert captured_methods[0] == "DELETE"


# --- AI 証憑仕訳 ---


SAMPLE_SUGGESTIONS = [
    {
        "title": "食費",
        "date": "2026-02-19",
        "description": "レシート",
        "entry_description": "スーパーで食材購入",
        "lines": [
            {"account_id": 12, "account_name": "食費", "debit_amount": 3000, "credit_amount": 0},
            {"account_id": 1, "account_name": "現金", "debit_amount": 0, "credit_amount": 3000},
        ],
    }
]

SAMPLE_DRAFT = {
    "id": 10,
    "status": "analyzed",
    "comment": "テスト",
    "created_at": "2026-02-19T12:00:00",
    "summary": {
        "title": "食費",
        "date": "2026-02-19",
        "description": "スーパーで食材購入",
        "amount": 3000,
        "suggestion_count": 1,
    },
}


class TestAnalyze:
    def test_success(self) -> None:
        body = {"ok": True, "draft_id": 10, "suggestions": SAMPLE_SUGGESTIONS}

        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(201, json=body)

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            result = client.analyze(b"\xff\xd8\xff\xe0", comment="テストメモ")

        assert isinstance(result, AnalyzeResponse)
        assert result.draft_id == 10
        assert len(result.suggestions) == 1
        assert result.suggestions[0]["title"] == "食費"

        # multipart で送信されていることを確認
        req = captured[0]
        assert "/api/v1/ai/analyze" in str(req.url)

    def test_with_notify(self) -> None:
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(201, json={"ok": True, "draft_id": 1, "suggestions": []})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.analyze(b"\xff\xd8", notify=True)

        content = captured[0].content.decode("utf-8", errors="replace")
        assert "notify" in content

    def test_api_error(self) -> None:
        client = _make_client(400, {"error": "AI API設定が未登録です。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.analyze(b"\xff\xd8")

        assert exc_info.value.status_code == 400


class TestListDrafts:
    def test_success(self) -> None:
        body = {"ok": True, "drafts": [SAMPLE_DRAFT]}
        client = _make_client(200, body)

        with client:
            result = client.list_drafts()

        assert len(result) == 1
        assert isinstance(result[0], DraftListItem)
        assert result[0].id == 10
        assert result[0].status == "analyzed"
        assert result[0].summary is not None
        assert result[0].summary.amount == 3000

    def test_sends_status_param(self) -> None:
        captured_urls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_urls.append(str(request.url))
            return httpx.Response(200, json={"ok": True, "drafts": []})

        http_client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://test.example.com",
            headers={"Authorization": "Bearer ik_testkey"},
        )

        with KakeiboClient("https://test.example.com", "ik_testkey", http_client=http_client) as client:
            client.list_drafts(status="all")

        assert "status=all" in captured_urls[0]


class TestGetDraft:
    def test_success(self) -> None:
        draft_with_suggestions = {**SAMPLE_DRAFT, "suggestions": SAMPLE_SUGGESTIONS}
        body = {"ok": True, "draft": draft_with_suggestions}
        client = _make_client(200, body)

        with client:
            result = client.get_draft(10)

        assert isinstance(result, DraftDetail)
        assert result.id == 10
        assert len(result.suggestions) == 1
        assert result.suggestions[0]["title"] == "食費"

    def test_not_found(self) -> None:
        client = _make_client(404, {"error": "下書きが見つかりません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.get_draft(999)

        assert exc_info.value.status_code == 404


class TestDeleteDraft:
    def test_success(self) -> None:
        client = _make_client(200, {"ok": True})

        with client:
            client.delete_draft(10)  # should not raise

    def test_not_found(self) -> None:
        client = _make_client(404, {"error": "下書きが見つかりません。"})

        with client, pytest.raises(KakeiboAPIError) as exc_info:
            client.delete_draft(999)

        assert exc_info.value.status_code == 404
