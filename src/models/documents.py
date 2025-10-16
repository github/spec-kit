# -*- coding: utf-8 -*-

"""
Pydantic 모델을 정의하는 파일입니다.
API 요청 및 응답의 데이터 구조를 정의하고 유효성을 검사하는 데 사용됩니다.
"""

# Pydantic 라이브러리에서 BaseModel을 가져옵니다.
# 모든 모델은 이 BaseModel을 상속받아 만들어집니다.
from pydantic import BaseModel
# typing 라이브러리에서 제네릭 타입을 지원하기 위해 Generic과 TypeVar를 가져옵니다.
from typing import Generic, TypeVar

# --- 요청 모델 ---

class SpecGenerateRequest(BaseModel):
    """
    '사양(spec) 생성' API에 대한 요청 모델.

    Attributes:
        feature_description (str): 사용자가 입력한 기능에 대한 상세 설명.
                                   이 설명을 기반으로 사양 문서가 생성됩니다.
    """
    # 기능 설명을 저장하는 변수. 문자열 타입이어야 합니다.
    feature_description: str


class PlanGenerateRequest(BaseModel):
    """
    '계획(plan) 생성' API에 대한 요청 모델.

    Attributes:
        feature_name (str): 계획을 생성할 기능의 이름.
                            이 이름은 보통 사양에서 정의됩니다.
    """
    # 기능 이름을 저장하는 변수. 문자열 타입이어야 합니다.
    feature_name: str


class TasksGenerateRequest(BaseModel):
    """
    '작업(tasks) 생성' API에 대한 요청 모델.

    Attributes:
        feature_name (str): 작업 목록을 생성할 기능의 이름.
                            이 이름은 계획과 사양을 참조하는 데 사용됩니다.
    """
    # 기능 이름을 저장하는 변수. 문자열 타입이어야 합니다.
    feature_name: str


# --- 응답 모델 ---

# 제네릭 데이터 타입을 위한 TypeVar를 생성합니다.
# 어떤 타입이든 담을 수 있는 제네릭 응답 모델을 만들기 위해 사용됩니다.
T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    모든 API에 대한 공통적인 응답 래퍼(wrapper) 모델.
    일관된 응답 구조를 제공하기 위해 사용됩니다.

    Attributes:
        success (bool): API 요청의 성공 여부를 나타내는 플래그.
        message (str): API 처리 결과에 대한 메시지.
        data (T | None): API의 실제 결과 데이터. 제네릭 타입을 사용하여
                         다양한 종류의 데이터를 담을 수 있습니다.
    """
    # 성공 여부를 나타내는 변수. 불리언 타입입니다.
    success: bool = True
    # 응답 메시지를 저장하는 변수. 문자열 타입입니다.
    message: str = "성공적으로 처리되었습니다."
    # 실제 데이터를 담는 변수. 타입은 제네릭 T이며, 데이터가 없을 경우 None이 될 수 있습니다.
    data: T | None = None