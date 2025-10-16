# -*- coding: utf-8 -*-

"""
FastAPI 애플리케이션의 메인 파일.
애플리케이션을 생성하고, API 라우터를 포함하며, 서버 실행의 시작점 역할을 합니다.
"""

# FastAPI 클래스를 가져옵니다. 웹 애플리케이션을 생성하는 데 사용됩니다.
from fastapi import FastAPI
# API 라우터를 가져옵니다. 이 라우터는 모든 API 엔드포인트를 포함합니다.
from src.api.router import api_router

# FastAPI 애플리케이션 인스턴스를 생성합니다.
# 이 인스턴스가 모든 API의 중심이 됩니다.
app = FastAPI(
    title="Document Generator API",  # API의 제목
    description="CLI-based document generator converted to a FastAPI service.",  # API에 대한 설명
    version="0.1.0",  # API 버전
)

# 루트 엔드포인트: 서버의 상태를 확인하기 위한 간단한 테스트 경로입니다.
@app.get("/", tags=["Status"])
def health_check():
    """
    서버 헬스 체크(Health Check) 엔드포인트.

    Returns:
        dict: 서버가 정상적으로 동작하고 있음을 알리는 메시지.
    """
    # 서버 상태를 나타내는 딕셔너리 객체.
    # 이 메시지는 클라이언트에게 서버가 준비되었음을 알립니다.
    response_message = {"status": "ok", "message": "Welcome to the Document Generator API!"}
    return response_message

# API 라우터를 애플리케이션에 포함시킵니다.
# prefix="/api/v1"은 모든 API 경로가 /api/v1으로 시작하도록 설정합니다.
# 예를 들어, specifications.py에 정의된 /generate-spec 경로는
# http://localhost:8000/api/v1/generate-spec 으로 접근할 수 있습니다.
app.include_router(api_router, prefix="/api/v1")

# Uvicorn 서버를 직접 실행하기 위한 코드 블록입니다.
# 'python src/main.py' 명령으로 실행할 때 사용됩니다.
if __name__ == "__main__":
    # uvicorn 라이브러리를 가져옵니다. ASGI 서버 구현체입니다.
    import uvicorn
    # uvicorn.run()을 호출하여 서버를 시작합니다.
    # "src.main:app"은 src 폴더의 main.py 파일 안에 있는 app 객체를 의미합니다.
    # host="0.0.0.0"은 모든 네트워크 인터페이스에서 접속을 허용합니다.
    # port=8000은 8000번 포트를 사용하도록 설정합니다.
    # reload=True는 코드 변경 시 서버를 자동으로 재시작하는 개발용 옵션입니다.
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)