"""いいかんじ家計簿 API クライアント"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

import httpx

from .exceptions import AuthenticationError, KakeiboAPIError
from .models import (
    JournalCreateRequest,
    JournalCreateResponse,
    JournalDetail,
    JournalLine,
    JournalListResponse,
)

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

    # --- 仕訳起票 ---

    def create_journal(
        self,
        *,
        date: date | datetime | str,
        description: str,
        lines: list[JournalLine],
        source: str = "api",
    ) -> JournalCreateResponse:
        """仕訳を起票する。

        Args:
            date: 日付 (date, datetime, または YYYY-MM-DD 文字列)
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
        if resp.status_code == 201:
            data = resp.json()
            return JournalCreateResponse(
                id=data["id"],
                entry_number=data["entry_number"],
            )
        self._raise_for_error(resp)

    # --- 仕訳閲覧 ---

    def get_journal(self, journal_id: int) -> JournalDetail:
        """仕訳を1件取得する。

        Args:
            journal_id: 仕訳 ID

        Returns:
            JournalDetail: 仕訳の詳細情報

        Raises:
            KakeiboAPIError: 仕訳が見つからない場合 (404) 等
        """
        resp = self._client.get(f"/api/v1/journals/{journal_id}")
        if resp.status_code == 200:
            return JournalDetail.from_dict(resp.json()["journal"])
        self._raise_for_error(resp)

    def list_journals(
        self,
        *,
        date_from: date | datetime | str | None = None,
        date_to: date | datetime | str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> JournalListResponse:
        """仕訳一覧を取得する。

        Args:
            date_from: 日付の下限 (省略可)
            date_to: 日付の上限 (省略可)
            page: ページ番号 (デフォルト 1)
            per_page: 1ページあたりの件数 (デフォルト 20, 上限 100)

        Returns:
            JournalListResponse: 仕訳一覧とページネーション情報
        """
        params: dict[str, str | int] = {"page": page, "per_page": per_page}
        if date_from is not None:
            params["date_from"] = self._to_date_str(date_from)
        if date_to is not None:
            params["date_to"] = self._to_date_str(date_to)

        resp = self._client.get("/api/v1/journals", params=params)
        if resp.status_code == 200:
            data = resp.json()
            return JournalListResponse(
                journals=[JournalDetail.from_dict(j) for j in data["journals"]],
                total=data["total"],
                page=data["page"],
                per_page=data["per_page"],
            )
        self._raise_for_error(resp)

    # --- 仕訳削除 ---

    def delete_journal(self, journal_id: int) -> None:
        """仕訳を削除する。

        Args:
            journal_id: 仕訳 ID

        Raises:
            KakeiboAPIError: 仕訳が見つからない (404)、期間ロック (400) 等
        """
        resp = self._client.delete(f"/api/v1/journals/{journal_id}")
        if resp.status_code == 200:
            return
        self._raise_for_error(resp)

    # --- 内部ヘルパー ---

    @staticmethod
    def _to_date_str(d: date | datetime | str) -> str:
        if isinstance(d, str):
            return d
        if isinstance(d, datetime):
            return d.date().isoformat()
        return d.isoformat()

    @staticmethod
    def _raise_for_error(resp: httpx.Response) -> None:
        data = resp.json()
        message = data.get("error", "不明なエラー")
        if resp.status_code == 401:
            raise AuthenticationError(message)
        raise KakeiboAPIError(resp.status_code, message)
