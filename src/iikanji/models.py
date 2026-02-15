"""いいかんじ家計簿 API データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class JournalLine:
    """仕訳明細行"""

    account_id: int
    debit: int = 0
    credit: int = 0
    description: str = ""

    def to_dict(self) -> dict:
        d: dict = {"account_id": self.account_id}
        if self.debit:
            d["debit"] = self.debit
        if self.credit:
            d["credit"] = self.credit
        if self.description:
            d["description"] = self.description
        return d


@dataclass
class JournalCreateRequest:
    """仕訳起票リクエスト"""

    date: date | str
    description: str
    lines: list[JournalLine]
    source: str = "api"

    def to_dict(self) -> dict:
        d = self.date if isinstance(self.date, str) else self.date.isoformat()
        return {
            "date": d,
            "description": self.description,
            "lines": [line.to_dict() for line in self.lines],
            "source": self.source,
        }


@dataclass
class JournalCreateResponse:
    """仕訳起票レスポンス"""

    id: int
    entry_number: int
