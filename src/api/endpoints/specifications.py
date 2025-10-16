# -*- coding: utf-8 -*-

"""
사양(Specification) 생성과 관련된 API 엔드포인트를 정의하는 파일.
"""

# APIRouter는 엔드포인트들을 그룹화하는 데 사용됩니다.
from fastapi import APIRouter, Depends
# Pydantic 모델들을 가져옵니다. 데이터 유효성 검사 및 응답 구조 정의에 사용됩니다.
from src.models.documents import SpecGenerateRequest, ApiResponse
# 문서 생성 비즈니스 로직을 담고 있는 서비스 클래스를 가져옵니다.
from src.services.document_generator import DocumentGeneratorService

# 'specifications' 라우터를 생성합니다.
# prefix="/spec"는 이 라우터에 속한 모든 경로가 /spec으로 시작하도록 합니다.
# tags=["Specifications"]는 OpenAPI 문서에서 엔드포인트들을 'Specifications' 그룹으로 묶어줍니다.
router = APIRouter(prefix="/spec", tags=["Specifications"])

# 서비스 인스턴스를 생성하는 의존성 주입(Dependency Injection) 함수.
# 이 함수는 FastAPI가 엔드포인트 함수를 호출할 때마다
# DocumentGeneratorService의 새 인스턴스를 생성하여 제공합니다.
# 이를 통해 코드의 재사용성과 테스트 용이성이 향상됩니다.
def get_spec_service() -> DocumentGeneratorService:
    """
    DocumentGeneratorService 인스턴스를 반환하는 의존성 함수.
    """
    # 서비스 클래스의 인스턴스를 생성하여 반환합니다.
    return DocumentGeneratorService()

@router.post("/generate", response_model=ApiResponse[str])
async def generate_specification(
    # request_body는 SpecGenerateRequest 모델에 따라 유효성 검사를 거칩니다.
    # 클라이언트가 보낸 JSON 본문이 이 모델의 구조와 일치해야 합니다.
    request_body: SpecGenerateRequest,
    # Depends(get_spec_service)는 get_spec_service 함수를 실행하고
    # 그 반환값(DocumentGeneratorService 인스턴스)을 spec_service 매개변수에 주입합니다.
    spec_service: DocumentGeneratorService = Depends(get_spec_service)
):
    """
    사용자로부터 기능 설명을 받아 사양(specification) 문서를 생성하는 API 엔드포인트.

    Args:
        request_body (SpecGenerateRequest): 사용자가 제공한 기능 설명이 담긴 요청 본문.
        spec_service (DocumentGeneratorService): 비즈니스 로직을 처리하는 서비스 인스턴스.
                                                 FastAPI의 의존성 주입에 의해 제공됩니다.

    Returns:
        ApiResponse[str]: 생성된 사양 문서의 내용을 담은 공통 응답 객체.
                          실패 시 에러 메시지를 포함할 수 있습니다.
    """
    try:
        # 주입된 서비스 인스턴스의 create_specification 메서드를 호출합니다.
        # 요청 본문에서 받은 feature_description을 인자로 전달합니다.
        # 비동기 함수이므로 await 키워드를 사용합니다.
        generated_spec = await spec_service.create_specification(
            feature_description=request_body.feature_description
        )

        # 성공적으로 문서가 생성되면, ApiResponse 모델에 맞춰 응답을 구성합니다.
        # data 필드에 생성된 사양 문서 내용을 담아 반환합니다.
        return ApiResponse(
            success=True,
            message="사양 문서가 성공적으로 생성되었습니다.",
            data=generated_spec
        )
    except Exception as e:
        # 서비스 로직에서 예외가 발생하면, 실패 응답을 구성합니다.
        # success를 False로 설정하고, 예외 메시지를 message 필드에 담아 반환합니다.
        # 실제 프로덕션 환경에서는 HTTP 500 에러를 반환하고 로그를 남기는 것이 더 좋습니다.
        return ApiResponse(
            success=False,
            message=f"오류가 발생했습니다: {e}",
            data=None
        )