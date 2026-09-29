# budget_app/models.py
from dataclasses import dataclass, field
from typing import Optional
import uuid
from datetime import date


@dataclass
class Transaction:
    type: str                          # "income" | "expense"
    date: date                         # YYYY-MM-DD
    amount: int                        # 양수
    category: str
    memo: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "date": str(self.date),
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo or "",
            "tags": ",".join(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            id=d["id"],
            type=d["type"],
            date=date.fromisoformat(d["date"]),
            amount=int(d["amount"]),
            category=d["category"],
            memo=d.get("memo") or None,
            tags=[t for t in d.get("tags", "").split(",") if t],
        )


@dataclass
class Category:
    name: str

    def to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, d: dict) -> "Category":
        return cls(name=d["name"])


@dataclass
class Budget:
    month: str    # "YYYY-MM"
    amount: int   # 양수

    def to_dict(self) -> dict:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, d: dict) -> "Budget":
        return cls(month=d["month"], amount=int(d["amount"]))