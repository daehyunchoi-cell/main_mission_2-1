# budget_app/cli.py
from datetime import date, datetime
from typing import Optional
from .service import BudgetService


# ══════════════════════════════════════════
# 출력 헬퍼
# ══════════════════════════════════════════

def _hr(char: str = "─", width: int = 50) -> None:
    print(char * width)

def _header(title: str) -> None:
    _hr("═")
    print(f"  {title}")
    _hr("═")

def _print_tx(tx) -> None:
    tags = f"  #{' #'.join(tx.tags)}" if tx.tags else ""
    print(
        f"  [{tx.id}] {tx.date} | "
        f"{'수입' if tx.type == 'income' else '지출'} | "
        f"{tx.amount:>10,}원 | {tx.category} | "
        f"{tx.memo or ''}{tags}"
    )


# ══════════════════════════════════════════
# 입력 헬퍼
# ══════════════════════════════════════════

def _input(prompt: str) -> str:
    return input(f"  {prompt}").strip()

def _input_int(prompt: str) -> Optional[int]:
    val = _input(prompt)
    if not val:
        return None
    try:
        return int(val.replace(",", ""))
    except ValueError:
        print("  [오류] 숫자를 입력하세요.")
        return None

def _input_date(prompt: str) -> Optional[date]:
    val = _input(prompt)
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        print("  [오류] 날짜 형식: YYYY-MM-DD")
        return None

def _input_month(prompt: str) -> Optional[str]:
    val = _input(prompt)
    if not val:
        return None
    try:
        datetime.strptime(val, "%Y-%m")
        return val
    except ValueError:
        print("  [오류] 월 형식: YYYY-MM")
        return None


# ══════════════════════════════════════════
# 메뉴별 핸들러
# ══════════════════════════════════════════

class CLI:
    def __init__(self, data_dir: str = "./data"):
        self.svc = BudgetService(data_dir)

    # ── 메인 메뉴 ─────────────────────────
    def run(self) -> None:
        _header("💰 파일 기반 가계부")
        while True:
            self._print_main_menu()
            choice = _input("선택 → ")
            if   choice == "1": self._menu_add()
            elif choice == "2": self._menu_list()
            elif choice == "3": self._menu_search()
            elif choice == "4": self._menu_update()
            elif choice == "5": self._menu_delete()
            elif choice == "6": self._menu_summary()
            elif choice == "7": self._menu_budget()
            elif choice == "8": self._menu_category()
            elif choice == "0": self._exit()
            else: print("  [오류] 0~8 중 선택하세요.\n")

    def _print_main_menu(self) -> None:
        _hr()
        print("  1. 거래 추가        5. 거래 삭제")
        print("  2. 전체 목록        6. 월별 요약")
        print("  3. 검색 / 필터      7. 예산 관리")
        print("  4. 거래 수정        8. 카테고리 관리")
        print("  0. 종료")
        _hr()

    # ── 1. 거래 추가 ──────────────────────
    def _menu_add(self) -> None:
        _header("거래 추가")
        type_map = {"1": "income", "2": "expense"}
        print("  1. 수입   2. 지출")
        type_ = type_map.get(_input("유형 → "))
        if not type_:
            print("  [취소]"); return

        amount = _input_int("금액 (원) → ")
        if not amount:
            print("  [취소]"); return

        # 카테고리 선택
        cats = self.svc.list_categories()
        for i, c in enumerate(cats, 1):
            print(f"  {i}. {c}")
        cat_idx = _input_int("카테고리 번호 → ")
        if not cat_idx or not (1 <= cat_idx <= len(cats)):
            print("  [취소]"); return
        category = cats[cat_idx - 1]

        memo = _input("메모 (생략 가능) → ") or None
        tags_raw = _input("태그 (쉼표 구분, 생략 가능) → ")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        tx_date = _input_date("날짜 YYYY-MM-DD (생략 시 오늘) → ")

        self.svc.add_transaction(type_, amount, category, memo, tags, tx_date)

    # ── 2. 전체 목록 ──────────────────────
    def _menu_list(self) -> None:
        _header("전체 거래 목록")
        txs = self.svc.search()          # 필터 없음 = 전체
        if not txs:
            print("  거래 내역이 없습니다."); return
        for tx in txs:
            _print_tx(tx)
        _hr()
        print(f"  총 {len(txs)}건")

    # ── 3. 검색 / 필터 ────────────────────
    def _menu_search(self) -> None:
        _header("검색 / 필터 (생략 시 전체)")
        print("  유형: 1.수입  2.지출  (생략 가능)")
        type_map = {"1": "income", "2": "expense"}
        type_ = type_map.get(_input("유형 → "))

        cats = self.svc.list_categories()
        for i, c in enumerate(cats, 1):
            print(f"  {i}. {c}")
        cat_raw = _input_int("카테고리 번호 (생략 가능) → ")
        category = cats[cat_raw - 1] if cat_raw and 1 <= cat_raw <= len(cats) else None

        start = _input_date("시작일 YYYY-MM-DD (생략 가능) → ")
        end   = _input_date("종료일 YYYY-MM-DD (생략 가능) → ")
        tag   = _input("태그 (생략 가능) → ") or None
        keyword = _input("메모 키워드 (생략 가능) → ") or None

        txs = self.svc.search(type_, category, start, end, tag, keyword)
        if not txs:
            print("  검색 결과가 없습니다."); return
        for tx in txs:
            _print_tx(tx)
        _hr()
        print(f"  총 {len(txs)}건")

    # ── 4. 거래 수정 ──────────────────────
    def _menu_update(self) -> None:
        _header("거래 수정")
        tx_id = _input("수정할 거래 ID → ")
        if not tx_id: return

        print("  (생략 시 기존 값 유지)")
        amount   = _input_int("새 금액 → ")
        memo     = _input("새 메모 → ") or None
        tags_raw = _input("새 태그 (쉼표 구분) → ")
        tags     = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

        cats = self.svc.list_categories()
        for i, c in enumerate(cats, 1):
            print(f"  {i}. {c}")
        cat_raw  = _input_int("새 카테고리 번호 → ")
        category = cats[cat_raw - 1] if cat_raw and 1 <= cat_raw <= len(cats) else None

        self.svc.update_transaction(tx_id, amount, memo, tags, category)

    # ── 5. 거래 삭제 ──────────────────────
    def _menu_delete(self) -> None:
        _header("거래 삭제")
        tx_id = _input("삭제할 거래 ID → ")
        if not tx_id: return
        confirm = _input(f"'{tx_id}' 삭제하시겠습니까? (y/N) → ")
        if confirm.lower() == "y":
            self.svc.delete_transaction(tx_id)
        else:
            print("  [취소]")

    # ── 6. 월별 요약 ──────────────────────
    def _menu_summary(self) -> None:
        _header("월별 요약")
        month = _input_month("월 YYYY-MM (생략 시 이번 달) → ")
        if not month:
            month = date.today().strftime("%Y-%m")

        s = self.svc.monthly_summary(month)
        b = self.svc.check_budget(month)
        _hr()
        print(f"  📅 {month}")
        print(f"  수입:   {s['income']:>12,}원")
        print(f"  지출:   {s['expense']:>12,}원")
        print(f"  잔액:   {s['balance']:>12,}원")
        _hr("─", 30)
        print("  카테고리별 지출")
        for cat, amt in sorted(s["by_category"].items(), key=lambda x: -x[1]):
            print(f"    {cat:<10} {amt:>10,}원")
        _hr("─", 30)
        print(f"  예산:   {b['budget']:>12,}원")
        print(f"  잔여:   {b['remaining']:>12,}원  ({b['ratio']}%)")
        print(f"  상태:   {b['status']}")

    # ── 7. 예산 관리 ──────────────────────
    def _menu_budget(self) -> None:
        _header("예산 관리")
        month = _input_month("월 YYYY-MM (생략 시 이번 달) → ")
        if not month:
            month = date.today().strftime("%Y-%m")
        amount = _input_int("예산 금액 (원) → ")
        if not amount: return
        self.svc.set_budget(month, amount)

    # ── 8. 카테고리 관리 ──────────────────
    def _menu_category(self) -> None:
        _header("카테고리 관리")
        print("  1. 목록 보기   2. 추가   3. 삭제")
        choice = _input("선택 → ")

        if choice == "1":
            cats = self.svc.list_categories()
            for i, c in enumerate(cats, 1):
                print(f"  {i}. {c}")

        elif choice == "2":
            name = _input("추가할 카테고리명 → ")
            if name: self.svc.add_category(name)

        elif choice == "3":
            cats = self.svc.list_categories()
            for i, c in enumerate(cats, 1):
                print(f"  {i}. {c}")
            idx = _input_int("삭제할 번호 → ")
            if idx and 1 <= idx <= len(cats):
                self.svc.remove_category(cats[idx - 1])
        else:
            print("  [오류] 1~3 중 선택하세요.")

    # ── 0. 종료 ───────────────────────────
    def _exit(self) -> None:
        print("\n  👋 가계부를 종료합니다. 수고하셨습니다!\n")
        raise SystemExit