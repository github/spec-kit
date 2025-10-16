# -*- coding: utf-8 -*-

"""
구현 계획(Plan) 생성과 관련된 API 엔드포인트를 정의하는 파일.
"""

from fastapi import APIRouter, Depends
from src.models.documents import PlanGenerateRequest, ApiResponse
from src.services.document_generator import DocumentGeneratorService

# 'plans' 라우터를 생성합니다.
router = APIRouter(prefix="/plan", tags=["Plans"])

# 의존성 주입 함수는 재사용 가능하므로, 여기서는 간단하게 서비스 인스턴스를 생성합니다.
# 더 큰 애플리케이션에서는 공통 의존성 관리 파일을 만들 수 있습니다.
def get_doc_service() -> DocumentGeneratorService:
    return DocumentGeneratorService()

@router.post("/generate", response_model=ApiResponse[str])
async def generate_plan(
    request_body: PlanGenerateRequest,
    doc_service: DocumentGeneratorService = Depends(get_doc_service)
):
    """
    기능 이름을 받아 구현 계획(plan) 문서를 생성하는 API 엔드포인트.

    Args:
        request_body (PlanGenerateRequest): 기능 이름이 담긴 요청 본문.
        doc_service (DocumentGeneratorService): 비즈니스 로직을 처리하는 서비스 인스턴스.

    Returns:
        ApiResponse[str]: 생성된 계획 문서의 내용을 담은 공통 응답 객체.
    """
    try:
        # 서비스의 create_plan 메서드를 호출하여 계획 문서를 생성합니다.
        generated_plan = await doc_service.create_plan(
            feature_name=request_body.feature_name
        )
        return ApiResponse(
            success=True,
            message="계획 문서가 성공적으로 생성되었습니다.",
            data=generated_plan
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"오류가 발생했습니다: {e}",
            data=None
        )