"""KakeiboClient のユニットテスト"""

import json

import httpx
import pytest

from iikanji import (
    AuthenticationError,
    JournalCreateResponse,
    JournalLine,
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
