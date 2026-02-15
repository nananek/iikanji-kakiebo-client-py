"""いいかんじ家計簿 API クライアント"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import httpx

from .exceptions import AuthenticationError, KakeiboAPIError
from .models import JournalCreateRequest, JournalCreateResponse, JournalLine

if TYPE_CHECKING:
    from types import TracebackType


class KakeiboClient:
    """いいかんじ家計簿 API クライアント

    Usage::

        with KakeiboClient("https://example.com", "ik_abc...") as client:
            result = client.create_journal(
                date="2026-02-15",
                description="食材購入",
                lines=[
                    JournalLine(account_id=12, debit=3000),
                    JournalLine(account_id=1, credit=3000),
                ],
            )
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self._base_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
            self._owns_client = True

    def __enter__(self) -> KakeiboClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create_journal(
        self,
        *,
        date: date | str,
        description: str,
        lines: list[JournalLine],
        source: str = "api",
    ) -> JournalCreateResponse:
        """仕訳を起票する。

        Args:
            date: 日付 (YYYY-MM-DD 文字列または date オブジェクト)
            description: 摘要
            lines: 仕訳明細行のリスト
            source: ソース種別 (デフォルト "api")

        Returns:
            JournalCreateResponse: 作成された仕訳の ID と伝票番号

        Raises:
            AuthenticationError: APIキーが無効な場合
            KakeiboAPIError: バリデーションエラー等
        """
        req = JournalCreateRequest(
            date=date,
            description=description,
            lines=lines,
            source=source,
        )
        resp = self._client.post("/api/v1/journals", json=req.to_dict())
        return self._handle_response(resp)

    def _handle_response(self, resp: httpx.Response) -> JournalCreateResponse:
        if resp.status_code == 201:
            data = resp.json()
            return JournalCreateResponse(
                id=data["id"],
                entry_number=data["entry_number"],
            )

        data = resp.json()
        message = data.get("error", "不明なエラー")

        if resp.status_code == 401:
            raise AuthenticationError(message)

        raise KakeiboAPIError(resp.status_code, message)
