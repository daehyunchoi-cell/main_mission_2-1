# budget_app/repository.py
import json
import os
import tempfile
from pathlib import Path
from typing import Generator, Optional
from .models import Transaction, Category, Budget


class TransactionRepository:
    def __init__(self, data_dir: str = "./data"):
        self.path = Path(data_dir) / "transactions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    # ── 스트리밍 읽기 ──────────────────────────────
    def stream_all(self) -> Generator[Transaction, None, None]:
        """파일을 한 줄씩 읽어 Transaction을 yield"""
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Transaction.from_dict(json.loads(line))

    # ── 단건 조회 ──────────────────────────────────
    def find_by_id(self, tx_id: str) -> Optional[Transaction]:
        for tx in self.stream_all():
            if tx.id == tx_id:
                return tx
        return None

    # ── 추가 ───────────────────────────────────────
    def add(self, tx: Transaction) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")

    # ── 삭제 ───────────────────────────────────────
    def delete(self, tx_id: str) -> bool:
        """임시 파일 → 원자적 교체"""
        found = False
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, delete=False,
            suffix=".tmp", encoding="utf-8"
        ) as tmp:
            for tx in self.stream_all():
                if tx.id == tx_id:
                    found = True      # 이 줄만 건너뜀
                else:
                    tmp.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
            tmp_path = tmp.name

        if found:
            os.replace(tmp_path, self.path)  # 원자적 교체
        else:
            os.remove(tmp_path)
        return found

    # ── 수정 ───────────────────────────────────────
    def update(self, updated: Transaction) -> bool:
        """임시 파일 → 원자적 교체"""
        found = False
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, delete=False,
            suffix=".tmp", encoding="utf-8"
        ) as tmp:
            for tx in self.stream_all():
                if tx.id == updated.id:
                    tmp.write(json.dumps(updated.to_dict(), ensure_ascii=False) + "\n")
                    found = True
                else:
                    tmp.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
            tmp_path = tmp.name

        if found:
            os.replace(tmp_path, self.path)
        else:
            os.remove(tmp_path)
        return found

    def save(self, tx: Transaction) -> None:
        self.add(tx)

    def search(
        self,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        start=None,
        end=None,
        tag: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> list:
        results = []
        for tx in self.stream_all():
            if type_ and tx.type != type_:
                continue
            if category and tx.category != category:
                continue
            if start and tx.date < start:
                continue
            if end and tx.date > end:
                continue
            if tag and tag not in tx.tags:
                continue
            if keyword and (not tx.memo or keyword not in tx.memo):
                continue
            results.append(tx)
        return results

    def search_by_month(self, month: str) -> list:
        return [
            tx for tx in self.stream_all()
            if tx.date.strftime("%Y-%m") == month
        ]

class CategoryRepository:
    def __init__(self, data_dir: str = "./data"):
        self.path = Path(data_dir) / "categories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_defaults()

    def _init_defaults(self) -> None:
        """파일이 비어있으면 기본 카테고리 자동 생성"""
        if not self.path.exists() or self.path.stat().st_size == 0:
            defaults = ["식비", "교통", "주거", "의료", "여가", "기타", "급여", "용돈"]
            with open(self.path, "w", encoding="utf-8") as f:
                for name in defaults:
                    f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")

    def stream_all(self) -> Generator[Category, None, None]:
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Category.from_dict(json.loads(line))

    def list_all(self) -> list[str]:
        return [c.name for c in self.stream_all()]

    def add(self, name: str) -> bool:
        if name in self.list_all():
            return False  # 중복
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")
        return True

    def remove(self, name: str) -> bool:
        found = False
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, delete=False,
            suffix=".tmp", encoding="utf-8"
        ) as tmp:
            for cat in self.stream_all():
                if cat.name == name:
                    found = True
                else:
                    tmp.write(json.dumps(cat.to_dict(), ensure_ascii=False) + "\n")
            tmp_path = tmp.name

        if found:
            os.replace(tmp_path, self.path)
        else:
            os.remove(tmp_path)
        return found

class BudgetRepository:
    def __init__(self, data_dir: str = "./data"):
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def stream_all(self) -> Generator[Budget, None, None]:
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Budget.from_dict(json.loads(line))

    def find_by_month(self, month: str) -> Optional[Budget]:
        for b in self.stream_all():
            if b.month == month:
                return b
        return None

    def save(self, budget: Budget) -> None:
        """월 예산 저장 (없으면 추가, 있으면 덮어쓰기)"""
        found = False
        with tempfile.NamedTemporaryFile(
            "w", dir=self.path.parent, delete=False,
            suffix=".tmp", encoding="utf-8"
        ) as tmp:
            for b in self.stream_all():
                if b.month == budget.month:
                    tmp.write(json.dumps(budget.to_dict(), ensure_ascii=False) + "\n")
                    found = True
                else:
                    tmp.write(json.dumps(b.to_dict(), ensure_ascii=False) + "\n")
            if not found:
                tmp.write(json.dumps(budget.to_dict(), ensure_ascii=False) + "\n")
            tmp_path = tmp.name

        os.replace(tmp_path, self.path)