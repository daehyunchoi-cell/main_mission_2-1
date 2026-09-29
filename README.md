# 💰 파일 기반 가계부 콘솔 앱

Python 표준 라이브러리만으로 구현한 CLI 가계부 앱입니다.  
데이터는 JSONL 파일로 저장되며 별도 DB 설치가 필요 없습니다.

---

## 📁 프로젝트 구조

```
main_mission_2-1/
│
├── main.py                  # 진입점 (대화형)
├── README.md
├── .gitignore
├── data/                    # 자동 생성 (gitignore 권장)
│   ├── transactions.jsonl   # 거래 내역
│   ├── categories.jsonl     # 카테고리 목록
│   └── budgets.jsonl        # 월별 예산
│
└── budget_app/
    ├── __init__.py
    ├── __main__.py          # argparse CLI 진입점
    ├── models.py            # 데이터클래스
    ├── decorators.py        # 예외처리 · 로깅 · 성능측정
    ├── repository.py        # 파일 I/O + 제너레이터
    ├── validator.py         # 입력 검증
    ├── service.py           # 비즈니스 로직
    └── cli.py               # 사용자 인터페이스
```

---

## ⚙️ 실행 방법

```bash
# Python 3.10 이상 필요 (별도 패키지 설치 없음)

# 1. 폴더 이동
cd main_mission_2-1

# 2. 대화형 메뉴 실행 (data/ 폴더 자동 생성)
python3 main.py

# 3. 데이터 폴더 직접 지정 (선택사항)
python3 main.py ./data
```

---

## 🖥️ 메뉴 구성 (대화형)

```
══════════════════════════════════════════════════
  💰 가계부 메뉴
══════════════════════════════════════════════════
  1. 거래 추가        5. 거래 삭제
  2. 전체 목록        6. 월별 요약
  3. 검색 / 필터      7. 예산 관리
  4. 거래 수정        8. 카테고리 관리
  0. 종료
══════════════════════════════════════════════════
```

---

## 📋 명령어 예시 (대화형)

### 거래 추가
```
유형 선택 → 2           # 1.수입 / 2.지출
금액 → 15000
카테고리 번호 → 3       # 식비
메모 → 점심 김치찌개
태그 → 외식, 점심
날짜 → 2025-01-15      # 생략 시 오늘 날짜 자동 입력
```

### 검색 / 필터
```
유형 → 2               # 지출만 조회
카테고리 번호 → 3      # 식비만 조회
시작일 → 2025-01-01
종료일 → 2025-01-31
태그 → 외식
메모 키워드 → 김치
```

### 월별 요약 출력 예시
```
══════════════════════════════════════════════════
  📅 2025-01 요약
══════════════════════════════════════════════════
  수입:      3,000,000원
  지출:      1,250,000원
  잔액:      1,750,000원
──────────────────────────────────────────────────
  카테고리별 지출
    식비           350,000원
    교통           120,000원
    쇼핑           780,000원
──────────────────────────────────────────────────
  예산:      2,000,000원
  잔여:        750,000원  (62.5%)
  상태:   🟢 예산 여유
══════════════════════════════════════════════════
```

---

## 🖥️ CLI 사용법 (argparse)

두 가지 실행 방식을 지원합니다.

### 방식 A: 대화형 메뉴
```bash
python3 main.py
```

### 방식 B: CLI 명령어 실행 
```bash
python3 -m budget_app <명령> [옵션]
```

### 📋 명령어 목록

| 명령 | 설명 | 예시 |
|------|------|------|
| `add` | 거래 추가 | `python -m budget_app add --type expense --amount 15000 --category 식비` |
| `search` | 거래 검색 | `python -m budget_app search --type expense --category 식비` |
| `summary` | 월별 요약 | `python -m budget_app summary --month 2026-09` |
| `budget set` | 예산 설정 | `python -m budget_app budget set --month 2026-09 --amount 500000` |
| `budget check` | 예산 확인 | `python -m budget_app budget check --month 2026-09` |
| `category list` | 카테고리 목록 | `python -m budget_app category list` |
| `category add` | 카테고리 추가 | `python -m budget_app category add 반려동물` |
| `category remove` | 카테고리 삭제 | `python -m budget_app category remove 반려동물` |
| `export` | CSV 내보내기 | `python -m budget_app export --file backup.csv` |
| `import` | CSV 가져오기 | `python -m budget_app import --file backup.csv` |

### 🔧 공통 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--data-dir` | 데이터 폴더 경로 | `./data` |
| `-h, --help` | 도움말 | - |

### 📌 add 명령 옵션 상세

| 옵션 | 필수 | 설명 |
|------|:---:|------|
| `--type` | ✅ | `income` 또는 `expense` |
| `--amount` | ✅ | 금액 (정수) |
| `--category` | ✅ | 카테고리명 |
| `--memo` | | 메모 |
| `--tags` | | 태그 (공백 구분, 여러 개 가능) |
| `--date` | | 날짜 `YYYY-MM-DD` (기본: 오늘) |