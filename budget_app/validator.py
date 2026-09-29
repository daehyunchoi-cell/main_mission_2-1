"""
검증 모듈 - service.py의 호출 규칙에 맞춤
"""
from datetime import date, datetime


class ValidationError(Exception):
    """검증 오류"""
    pass


class Validator:
    """입력값 검증 클래스"""

    @staticmethod
    def validate_transaction_type(type_: str) -> str:
        """거래 유형 검증 (income/expense)"""
        if type_ not in ("income", "expense"):
            raise ValidationError("거래 유형은 income 또는 expense여야 합니다")
        return type_

    @staticmethod
    def amount(value: int) -> int:
        """금액 검증 (양수 정수)"""
        if not isinstance(value, int) or value <= 0:
            raise ValidationError("금액은 0보다 큰 정수여야 합니다")
        return value

    @staticmethod
    def memo(value):
        """메모 검증 (선택)"""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValidationError("메모는 문자열이어야 합니다")
        return value.strip() or None

    @staticmethod
    def tags(value: list) -> list:
        """태그 검증 (선택)"""
        if not isinstance(value, list):
            raise ValidationError("태그는 리스트여야 합니다")
        return [t.strip() for t in value if isinstance(t, str) and t.strip()]

    @staticmethod
    def tx_date(value: date) -> date:
        """거래 날짜 검증 (date 객체)"""
        if not isinstance(value, date):
            raise ValidationError("날짜는 date 객체여야 합니다")
        return value

    @staticmethod
    def tx_id(value: str) -> str:
        """거래 ID 검증"""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("거래 ID는 비어있지 않아야 합니다")
        return value.strip()

    @staticmethod
    def category_exists(cat_name: str, valid_categories: list) -> bool:
        """카테고리 존재 여부 확인 (등록된 목록과 대조)"""
        if cat_name not in valid_categories:
            raise ValidationError(f"유효하지 않은 카테고리입니다: '{cat_name}'")
        return True

    @staticmethod
    def category_name(name: str) -> str:
        """카테고리명 검증 (추가 시)"""
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("카테고리명은 비어있지 않아야 합니다")
        if len(name) > 20:
            raise ValidationError("카테고리명은 20자 이하여야 합니다")
        return name.strip()

    @staticmethod
    def month(value: str) -> str:
        """월 형식 검증 (YYYY-MM)"""
        try:
            datetime.strptime(value, "%Y-%m")
            return value
        except ValueError:
            raise ValidationError("월 형식은 YYYY-MM이어야 합니다")

    @staticmethod
    def budget_amount(value: int) -> int:
        """예산 금액 검증"""
        if not isinstance(value, int) or value <= 0:
            raise ValidationError("예산은 0보다 큰 정수여야 합니다")
        return value