# -*- coding: utf-8 -*-

"""
API 라우터를 통합하는 파일.
애플리케이션의 모든 엔드포인트 라우터들을 모아 FastAPI 앱에 등록할 수 있도록 합니다.
"""

# APIRouter 클래스를 가져옵니다.
from fastapi import APIRouter
# 사양(spec) 생성 관련 엔드포인트가 정의된 라우터를 가져옵니다.
from src.api.endpoints import specifications

# 최상위 API 라우터를 생성합니다.
# 이 라우터는 다른 모든 기능별 라우터들을 포함하게 됩니다.
api_router = APIRouter()

# specifications 라우터를 api_router에 포함시킵니다.
# 이렇게 하면 specifications.py에 정의된 모든 엔드포인트들이
# 이 api_router에 등록됩니다.
api_router.include_router(specifications.router)

# 여기에 나중에 plan, tasks 라우터도 추가될 예정입니다.
from src.api.endpoints import plans, tasks
api_router.include_router(plans.router)
api_router.include_router(tasks.router)