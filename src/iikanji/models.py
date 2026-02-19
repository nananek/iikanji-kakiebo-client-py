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

    draft_id: int | None = None

    def to_dict(self) -> dict:
        if isinstance(self.date, str):
            d = self.date
        elif isinstance(self.date, datetime):
            d = self.date.date().isoformat()
        else:
            d = self.date.isoformat()
        result = {
            "date": d,
            "description": self.description,
            "lines": [line.to_dict() for line in self.lines],
            "source": self.source,
        }
        if self.draft_id is not None:
            result["draft_id"] = self.draft_id
        return result


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


# --- AI 証憑仕訳 ---


@dataclass
class DraftSummary:
    """下書きのサマリー情報"""

    title: str = ""
    date: str = ""
    description: str = ""
    amount: int = 0
    suggestion_count: int = 0


@dataclass
class DraftListItem:
    """下書き一覧の1件"""

    id: int
    status: str
    comment: str
    created_at: str
    summary: DraftSummary | None = None

    @classmethod
    def from_dict(cls, data: dict) -> DraftListItem:
        summary = None
        if "summary" in data and data["summary"]:
            s = data["summary"]
            summary = DraftSummary(
                title=s.get("title", ""),
                date=s.get("date", ""),
                description=s.get("description", ""),
                amount=s.get("amount", 0),
                suggestion_count=s.get("suggestion_count", 0),
            )
        return cls(
            id=data["id"],
            status=data["status"],
            comment=data.get("comment", ""),
            created_at=data["created_at"],
            summary=summary,
        )


@dataclass
class DraftDetail:
    """下書きの詳細（候補データ含む）"""

    id: int
    status: str
    comment: str
    created_at: str
    summary: DraftSummary | None = None
    suggestions: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> DraftDetail:
        summary = None
        if "summary" in data and data["summary"]:
            s = data["summary"]
            summary = DraftSummary(
                title=s.get("title", ""),
                date=s.get("date", ""),
                description=s.get("description", ""),
                amount=s.get("amount", 0),
                suggestion_count=s.get("suggestion_count", 0),
            )
        return cls(
            id=data["id"],
            status=data["status"],
            comment=data.get("comment", ""),
            created_at=data["created_at"],
            summary=summary,
            suggestions=data.get("suggestions", []),
        )


@dataclass
class AnalyzeResponse:
    """AI解析レスポンス"""

    draft_id: int
    suggestions: list[dict]
