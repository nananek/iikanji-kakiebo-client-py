"""いいかんじ家計簿 API データモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


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

    date: date | datetime | str
    description: str
    lines: list[JournalLine]
    source: str = "api"

    def to_dict(self) -> dict:
        if isinstance(self.date, str):
            d = self.date
        elif isinstance(self.date, datetime):
            d = self.date.date().isoformat()
        else:
            d = self.date.isoformat()
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


@dataclass
class JournalDetail:
    """仕訳詳細"""

    id: int
    date: str
    entry_number: int
    description: str
    source: str
    lines: list[JournalLine]

    @classmethod
    def from_dict(cls, data: dict) -> JournalDetail:
        return cls(
            id=data["id"],
            date=data["date"],
            entry_number=data["entry_number"],
            description=data["description"],
            source=data["source"],
            lines=[
                JournalLine(
                    account_id=line["account_id"],
                    debit=line.get("debit", 0),
                    credit=line.get("credit", 0),
                    description=line.get("description", ""),
                )
                for line in data["lines"]
            ],
        )


@dataclass
class JournalListResponse:
    """仕訳一覧レスポンス"""

    journals: list[JournalDetail]
    total: int
    page: int
    per_page: int
