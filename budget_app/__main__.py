# budget_app/__main__.py
import argparse
from datetime import date
from .service import BudgetService


def parse_date(s: str) -> date:
    """'2024-01-15' 문자열 → date 객체 (argparse type=용)"""
    return date.fromisoformat(s)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="💰 파일 기반 가계부 CLI",
    )
    parser.add_argument(
        "--data-dir", default="./data",
        help="데이터 폴더 경로 (기본: ./data)",
    )

    # 서브커맨드 등록 (add, search, summary ...)
    sub = parser.add_subparsers(dest="command", required=True)

    # ── add: 거래 추가 ──────────────────────────
    p_add = sub.add_parser("add", help="거래 추가")
    p_add.add_argument("--type", required=True, choices=["income", "expense"],
                       dest="type_", help="수입(income) / 지출(expense)")
    p_add.add_argument("--amount", required=True, type=int, help="금액")
    p_add.add_argument("--category", required=True, help="카테고리")
    p_add.add_argument("--memo", help="메모 (선택)")
    p_add.add_argument("--tags", nargs="*", default=[], help="태그 (공백 구분)")
    p_add.add_argument("--date", type=parse_date, dest="tx_date",
                       help="날짜 YYYY-MM-DD (기본: 오늘)")

    # ── search: 거래 검색 ───────────────────────
    p_search = sub.add_parser("search", help="거래 검색")
    p_search.add_argument("--type", choices=["income", "expense"], dest="type_")
    p_search.add_argument("--category")
    p_search.add_argument("--start", type=parse_date, help="시작일 YYYY-MM-DD")
    p_search.add_argument("--end", type=parse_date, help="종료일 YYYY-MM-DD")
    p_search.add_argument("--tag")
    p_search.add_argument("--keyword", help="메모 검색어")

    # ── summary: 월별 요약 ──────────────────────
    p_sum = sub.add_parser("summary", help="월별 요약")
    p_sum.add_argument("--month", required=True, help="YYYY-MM")

    # ── budget: 예산 (set / check) ──────────────
    p_bud = sub.add_parser("budget", help="예산 관리")
    bud_sub = p_bud.add_subparsers(dest="bud_command", required=True)

    p_bud_set = bud_sub.add_parser("set", help="예산 설정")
    p_bud_set.add_argument("--month", required=True, help="YYYY-MM")
    p_bud_set.add_argument("--amount", required=True, type=int)

    p_bud_check = bud_sub.add_parser("check", help="예산 확인")
    p_bud_check.add_argument("--month", required=True, help="YYYY-MM")

    # ── category: 카테고리 (add / remove / list) ─
    p_cat = sub.add_parser("category", help="카테고리 관리")
    cat_sub = p_cat.add_subparsers(dest="cat_command", required=True)

    p_cat_add = cat_sub.add_parser("add", help="카테고리 추가")
    p_cat_add.add_argument("name")

    p_cat_rm = cat_sub.add_parser("remove", help="카테고리 삭제")
    p_cat_rm.add_argument("name")

    cat_sub.add_parser("list", help="카테고리 목록")

    # ── export / import: CSV ────────────────────
    p_exp = sub.add_parser("export", help="CSV 내보내기")
    p_exp.add_argument("--file", required=True, help="저장할 CSV 파일 경로")

    p_imp = sub.add_parser("import", help="CSV 가져오기")
    p_imp.add_argument("--file", required=True, help="읽을 CSV 파일 경로")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 서비스 생성 (모든 명령이 공유)
    service = BudgetService(args.data_dir)

    # ── 명령 분기 ───────────────────────────────
    if args.command == "add":
        service.add_transaction(
            type_=args.type_, amount=args.amount, category=args.category,
            memo=args.memo, tags=args.tags, tx_date=args.tx_date,
        )

    elif args.command == "search":
        results = service.search(
            type_=args.type_, category=args.category,
            start=args.start, end=args.end,
            tag=args.tag, keyword=args.keyword,
        )
        if not results:
            print("  🔍 검색 결과가 없습니다.")
        else:
            print(f"  🔍 {len(results)}건 검색됨:")
            for t in results:
                print(f"   [{t.id[:8]}] {t.date} | {t.type:7} | "
                      f"{t.amount:>10,}원 | {t.category} | {t.memo or ''}")

    elif args.command == "summary":
        s = service.monthly_summary(args.month)
        print(f"\n  📊 {s['month']} 요약")
        print(f"   수입  : {s['income']:>12,}원")
        print(f"   지출  : {s['expense']:>12,}원")
        print(f"   잔액  : {s['balance']:>12,}원")
        if s["by_category"]:
            print("   ── 카테고리별 지출 ──")
            for cat, amt in s["by_category"].items():
                print(f"     {cat:8} : {amt:>10,}원")

    elif args.command == "budget":
        if args.bud_command == "set":
            service.set_budget(args.month, args.amount)
        elif args.bud_command == "check":
            b = service.check_budget(args.month)
            print(f"\n  💰 {b['month']} 예산 현황 {b['status']}")
            print(f"   예산   : {b['budget']:>12,}원")
            print(f"   지출   : {b['expense']:>12,}원")
            print(f"   잔여   : {b['remaining']:>12,}원")
            print(f"   사용률 : {b['ratio']}%")

    elif args.command == "category":
        if args.cat_command == "add":
            service.add_category(args.name)
        elif args.cat_command == "remove":
            service.remove_category(args.name)
        elif args.cat_command == "list":
            cats = service.list_categories()
            print("  📁 카테고리 목록:")
            for c in cats:
                print(f"   - {c}")

    elif args.command == "export":
        service.export_csv(args.file)

    elif args.command == "import":
        service.import_csv(args.file)


if __name__ == "__main__":
    main()