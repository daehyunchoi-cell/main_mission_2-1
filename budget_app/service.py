# budget_app/service.py
from datetime import date
from typing import Optional
from .models import Transaction, Budget
from .repository import TransactionRepository, CategoryRepository, BudgetRepository
from .decorators import handle_errors, log_action, measure_time
from .validator import Validator, ValidationError

import csv                          
from pathlib import Path           

class BudgetService:

    def __init__(self, data_dir: str = "./data"):
        self.tx_repo  = TransactionRepository(data_dir)
        self.cat_repo = CategoryRepository(data_dir)
        self.bud_repo = BudgetRepository(data_dir)

    # ══════════════════════════════════════════
    # 거래 CRUD
    # ══════════════════════════════════════════

    @handle_errors
    @log_action
    @measure_time
    def add_transaction(
        self,
        type_    : str,
        amount   : int,
        category : str,
        memo     : Optional[str]       = None,
        tags     : Optional[list[str]] = None,
        tx_date  : Optional[date]      = None,
    ) -> Transaction:
        # ── 검증 ──────────────────────────────
        Validator.validate_transaction_type(type_)
        Validator.amount(amount)
        Validator.memo(memo)
        Validator.tags(tags or [])
        if tx_date:
            Validator.tx_date(tx_date)
        Validator.category_exists(category, self.cat_repo.list_all())

        # ── 저장 ──────────────────────────────
        tx = Transaction(
            type     = type_,
            amount   = amount,
            category = category,
            memo     = memo,
            tags     = tags or [],
            date     = tx_date or date.today(),
        )
        self.tx_repo.save(tx)
        print(f"  ✅ 거래 추가 완료 [{tx.id}]")
        return tx

    @handle_errors
    @log_action
    def update_transaction(
        self,
        tx_id    : str,
        amount   : Optional[int]       = None,
        memo     : Optional[str]       = None,
        tags     : Optional[list[str]] = None,
        category : Optional[str]       = None,
    ) -> Optional[Transaction]:
        # ── ID 검증 ───────────────────────────
        Validator.tx_id(tx_id)

        # ── 존재 확인 ─────────────────────────
        tx = self.tx_repo.find_by_id(tx_id)
        if not tx:
            raise ValidationError(f"거래를 찾을 수 없습니다: {tx_id}")

        # ── 필드별 검증 후 업데이트 ───────────
        if amount is not None:
            Validator.amount(amount)
            tx.amount = amount

        if memo is not None:
            tx.memo = Validator.memo(memo)

        if tags is not None:
            tx.tags = Validator.tags(tags)

        if category is not None:
            Validator.category_exists(category, self.cat_repo.list_all())
            tx.category = category

        self.tx_repo.update(tx)
        print(f"  ✅ 거래 수정 완료 [{tx_id}]")
        return tx

    @handle_errors
    @log_action
    def delete_transaction(self, tx_id: str) -> bool:
        Validator.tx_id(tx_id)

        if not self.tx_repo.find_by_id(tx_id):
            raise ValidationError(f"거래를 찾을 수 없습니다: {tx_id}")

        self.tx_repo.delete(tx_id)
        print(f"  ✅ 거래 삭제 완료 [{tx_id}]")
        return True

    @handle_errors
    @log_action
    def search(
        self,
        type_    : Optional[str]  = None,
        category : Optional[str]  = None,
        start    : Optional[date] = None,
        end      : Optional[date] = None,
        tag      : Optional[str]  = None,
        keyword  : Optional[str]  = None,
    ) -> list[Transaction]:
        # ── 개별 필드 검증 (입력된 경우만) ───
        if type_:
            Validator.validate_transaction_type(type_)
        if category:
            Validator.category_exists(category, self.cat_repo.list_all())
        if start:
            Validator.tx_date(start)
        if end:
            Validator.tx_date(end)
        if start and end and start > end:
            raise ValidationError(f"시작일이 종료일보다 늦습니다: {start} > {end}")

        return self.tx_repo.search(type_, category, start, end, tag, keyword)

    # ══════════════════════════════════════════
    # 월별 요약
    # ══════════════════════════════════════════

    @handle_errors
    @log_action
    @measure_time
    def monthly_summary(self, month: str) -> dict:
        Validator.month(month)

        txs = self.tx_repo.search_by_month(month)
        income  = sum(t.amount for t in txs if t.type == "income")
        expense = sum(t.amount for t in txs if t.type == "expense")

        by_category: dict[str, int] = {}
        for t in txs:
            if t.type == "expense":
                by_category[t.category] = by_category.get(t.category, 0) + t.amount

        return {
            "month"       : month,
            "income"      : income,
            "expense"     : expense,
            "balance"     : income - expense,
            "by_category" : by_category,
        }

    # ══════════════════════════════════════════
    # 예산 관리
    # ══════════════════════════════════════════

    @handle_errors
    @log_action
    def set_budget(self, month: str, amount: int) -> Budget:
        Validator.month(month)
        Validator.budget_amount(amount)

        budget = Budget(month=month, amount=amount)
        self.bud_repo.save(budget)
        print(f"  ✅ {month} 예산 설정 완료: {amount:,}원")
        return budget

    @handle_errors
    def check_budget(self, month: str) -> dict:
        Validator.month(month)

        budget = self.bud_repo.find_by_month(month)
        bud_amount = budget.amount if budget else 0

        txs     = self.tx_repo.search_by_month(month)
        expense = sum(t.amount for t in txs if t.type == "expense")

        remaining = bud_amount - expense
        ratio     = round(expense / bud_amount * 100, 1) if bud_amount else 0.0

        if bud_amount == 0:
            status = "⚪ 예산 미설정"
        elif ratio >= 100:
            status = "🔴 예산 초과"
        elif ratio >= 80:
            status = "🟡 예산 주의"
        else:
            status = "🟢 예산 여유"

        return {
            "month"    : month,
            "budget"   : bud_amount,
            "expense"  : expense,
            "remaining": remaining,
            "ratio"    : ratio,
            "status"   : status,
        }

    # ══════════════════════════════════════════
    # 카테고리 관리
    # ══════════════════════════════════════════

    @handle_errors
    @log_action
    def add_category(self, name: str) -> None:
        Validator.category_name(name)

        cats = self.cat_repo.list_all()
        if name in cats:
            raise ValidationError(f"이미 존재하는 카테고리입니다: '{name}'")

        self.cat_repo.add(name)
        print(f"  ✅ 카테고리 추가 완료: '{name}'")

    @handle_errors
    @log_action
    def remove_category(self, name: str) -> None:
        Validator.category_exists(name, self.cat_repo.list_all())

        # 해당 카테고리 사용 중인 거래 확인
        in_use = self.tx_repo.search(category=name)
        if in_use:
            raise ValidationError(
                f"'{name}' 카테고리에 거래 {len(in_use)}건이 있어 삭제할 수 없습니다."
            )

        self.cat_repo.remove(name)
        print(f"  ✅ 카테고리 삭제 완료: '{name}'")

    @handle_errors
    def list_categories(self) -> list[str]:
        return self.cat_repo.list_all()


    # ══════════════════════════════════════════
    # 데이터 가져오기 / 내보내기
    # ══════════════════════════════════════════

    @handle_errors
    @log_action
    @measure_time
    def export_csv(self, filepath: str) -> int:
        """전체 거래를 CSV로 내보내기. 내보낸 건수 반환."""
        txs = self.tx_repo.search()   # 조건 없이 전체 조회

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # 헤더
            writer.writerow(["id", "type", "amount", "category", "memo", "tags", "date"])
            # 데이터 행
            for t in txs:
                writer.writerow([
                    t.id,
                    t.type,
                    t.amount,
                    t.category,
                    t.memo or "",
                    ";".join(t.tags),      # 태그는 세미콜론으로 연결
                    t.date.isoformat(),    # date → "2024-01-15"
                ])

        print(f"  ✅ {len(txs)}건 내보내기 완료 → {filepath}")
        return len(txs)

    @handle_errors
    @log_action
    @measure_time
    def import_csv(self, filepath: str) -> dict:
        """
        CSV에서 거래를 가져오기.

        정책: 부분 성공 허용
          - 정상 행은 즉시 저장
          - 오류 행은 건너뛰고 오류 내용 기록
          - 완료 후 성공/실패 건수 + 실패 행 상세 리포트 출력
          - 전체 롤백이 필요하면 import 전 export로 백업 권장

        Returns:
            dict: {"success": int, "failed": int, "errors": list[str]}
        """
        if not Path(filepath).exists():
            raise ValidationError(
                f"파일을 찾을 수 없습니다: {filepath}\n"
                "  💡 파일 경로를 다시 확인하세요."
            )

        # ── 필수 컬럼 검증 ──────────────────────────────
        REQUIRED_COLUMNS = {"id", "type", "amount", "category", "memo", "tags", "date"}

        success = 0
        errors: list[str] = []                     # 실패 행 기록용

        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # ── 헤더 컬럼 검증 ──────────────────────
            if reader.fieldnames is None:
                raise ValidationError(
                    "CSV 파일이 비어 있습니다.\n"
                    "  💡 올바른 CSV 파일인지 확인하세요."
                )

            missing = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise ValidationError(
                    f"CSV 컬럼 누락: {', '.join(sorted(missing))}\n"
                    f"  💡 필수 컬럼: {', '.join(sorted(REQUIRED_COLUMNS))}"
                )

            # ── 행별 처리 ────────────────────────────
            for row_num, row in enumerate(reader, start=2):   # 헤더=1행, 데이터=2행~
                try:
                    # 태그 문자열 → 리스트 복원
                    tags = [t for t in row["tags"].split(";") if t] \
                            if row["tags"] else []

                    # 날짜 문자열 → date 객체
                    tx_date = date.fromisoformat(row["date"]) \
                            if row["date"] else None

                    # 기존 add_transaction 재사용 (검증까지 자동!)
                    self.add_transaction(
                        type_    = row["type"],
                        amount   = int(row["amount"]),
                        category = row["category"],
                        memo     = row["memo"] or None,
                        tags     = tags,
                        tx_date  = tx_date,
                    )
                    success += 1

                except (ValueError, ValidationError, KeyError) as e:
                    # 오류 행은 건너뛰고 기록
                    errors.append(f"  {row_num}행: {e}")

        # ── 결과 리포트 출력 ─────────────────────────────
        print(f"\n  📥 import 완료 ← {filepath}")
        print(f"  ✅ {success}건 성공", end="")
        if errors:
            print(f"  |  ❌ {len(errors)}건 실패")
            print("  ── 실패 상세 ──────────────────────")
            for err in errors:
                print(err)
            print("  ───────────────────────────────────")
            print("  💡 전체 롤백이 필요하면 import 전 export로 백업하세요.")
        else:
            print()   # 줄바꿈

        return {"success": success, "failed": len(errors), "errors": errors}