# -*- coding: utf-8 -*-

"""
작업 목록(Tasks) 생성과 관련된 API 엔드포인트를 정의하는 파일.
"""

from fastapi import APIRouter, Depends
from src.models.documents import TasksGenerateRequest, ApiResponse
from src.services.document_generator import DocumentGeneratorService

# 'tasks' 라우터를 생성합니다.
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# 의존성 주입 함수
def get_doc_service() -> DocumentGeneratorService:
    return DocumentGeneratorService()

@router.post("/generate", response_model=ApiResponse[str])
async def generate_tasks(
    request_body: TasksGenerateRequest,
    doc_service: DocumentGeneratorService = Depends(get_doc_service)
):
    """
    기능 이름을 받아 작업 목록(tasks) 문서를 생성하는 API 엔드포인트.

    Args:
        request_body (TasksGenerateRequest): 기능 이름이 담긴 요청 본문.
        doc_service (DocumentGeneratorService): 비즈니스 로직을 처리하는 서비스 인스턴스.

    Returns:
        ApiResponse[str]: 생성된 작업 목록의 내용을 담은 공통 응답 객체.
    """
    try:
        # 서비스의 create_tasks 메서드를 호출하여 작업 목록을 생성합니다.
        generated_tasks = await doc_service.create_tasks(
            feature_name=request_body.feature_name
        )
        return ApiResponse(
            success=True,
            message="작업 목록이 성공적으로 생성되었습니다.",
            data=generated_tasks
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"오류가 발생했습니다: {e}",
            data=None
        )