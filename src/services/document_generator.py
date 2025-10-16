# -*- coding: utf-8 -*-

"""
문서 생성과 관련된 비즈니스 로직을 처리하는 서비스 파일.
템플릿 파일을 읽고, 동적 데이터를 삽입하여 최종 문서를 생성하는 역할을 합니다.
"""

# 날짜와 시간을 다루기 위한 datetime 라이브러리를 가져옵니다.
from datetime import datetime
# 비동기 파일 I/O 작업을 위한 aiofiles 라이브러리를 가져옵니다.
import aiofiles

class DocumentGeneratorService:
    """
    문서 생성 로직을 담당하는 서비스 클래스.
    """

    async def create_specification(self, feature_description: str) -> str:
        """
        기능 설명을 기반으로 사양(specification) 문서를 생성합니다.

        이 함수는 비동기적으로 동작하며, 'spec-template.md' 파일을 읽어
        필요한 부분을 사용자의 입력과 현재 날짜로 교체한 후,
        완성된 문서 내용을 문자열로 반환합니다.

        Args:
            feature_description (str): API 요청을 통해 전달받은 사용자의 기능 설명.

        Returns:
            str: 동적 데이터가 채워진 완성된 사양 문서의 내용.

        Raises:
            FileNotFoundError: 'templates/spec-template.md' 파일이 존재하지 않을 경우 발생.
            Exception: 파일 읽기 또는 다른 예기치 않은 오류 발생 시.
        """
        try:
            # 템플릿 파일의 경로를 변수에 저장합니다.
            template_path = "templates/spec-template.md"

            # aiofiles를 사용하여 템플릿 파일을 비동기적으로 엽니다.
            # 'async with' 구문은 파일이 자동으로 닫히도록 보장합니다.
            async with aiofiles.open(template_path, mode='r', encoding='utf-8') as f:
                # 파일의 전체 내용을 비동기적으로 읽어 content 변수에 저장합니다.
                content = await f.read()

            # 현재 날짜를 'YYYY-MM-DD' 형식의 문자열로 포맷팅합니다.
            # 이 변수는 템플릿의 '[DATE]' 부분을 대체하는 데 사용됩니다.
            current_date = datetime.now().strftime("%Y-%m-%d")

            # 템플릿 내용에서 플레이스홀더(placeholder)를 실제 데이터로 교체합니다.
            # 1. '[FEATURE NAME]' -> 'Generated Feature' (임시 이름)
            # 2. '[DATE]' -> 현재 날짜
            # 3. '$ARGUMENTS' -> 사용자가 입력한 기능 설명
            # feature_name 변수는 나중에 더 동적으로 만들 수 있습니다.
            feature_name = "Generated Feature"
            content = content.replace("[FEATURE NAME]", feature_name)
            content = content.replace("[DATE]", current_date)
            content = content.replace("$ARGUMENTS", feature_description)

            # 완성된 문서 내용을 반환합니다.
            return content

        except FileNotFoundError:
            # 템플릿 파일이 없을 경우, 에러 메시지를 포함하여 예외를 발생시킵니다.
            # 이 예외는 API 엔드포인트에서 처리되어 사용자에게 적절한 오류 응답을 보냅니다.
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
        except Exception as e:
            # 파일 읽기 중 다른 예외가 발생할 경우, 해당 예외를 다시 발생시킵니다.
            # 로깅 등을 추가하여 오류를 추적할 수 있습니다.
            # 예를 들어: logging.error(f"사양 생성 중 오류 발생: {e}")
            raise e

    async def create_plan(self, feature_name: str) -> str:
        """
        기능 이름을 기반으로 구현 계획(plan) 문서를 생성합니다.

        Args:
            feature_name (str): 계획을 생성할 기능의 이름.

        Returns:
            str: 완성된 계획 문서의 내용.
        """
        try:
            # 계획 템플릿 파일의 경로.
            template_path = "templates/plan-template.md"
            async with aiofiles.open(template_path, mode='r', encoding='utf-8') as f:
                content = await f.read()

            # 현재 날짜를 포맷팅합니다.
            current_date = datetime.now().strftime("%Y-%m-%d")

            # 템플릿의 플레이스홀더를 교체합니다.
            content = content.replace("[FEATURE]", feature_name)
            content = content.replace("[DATE]", current_date)
            # '[###-feature-name]'과 같은 다른 플레이스홀더는
            # 실제 구현 시 더 정교한 로직으로 처리될 수 있습니다.

            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
        except Exception as e:
            raise e

    async def create_tasks(self, feature_name: str) -> str:
        """
        기능 이름을 기반으로 작업 목록(tasks) 문서를 생성합니다.

        Args:
            feature_name (str): 작업 목록을 생성할 기능의 이름.

        Returns:
            str: 완성된 작업 목록 문서의 내용.
        """
        try:
            # 작업 템플릿 파일의 경로.
            template_path = "templates/tasks-template.md"
            async with aiofiles.open(template_path, mode='r', encoding='utf-8') as f:
                content = await f.read()

            # 템플릿의 플레이스홀더를 교체합니다.
            content = content.replace("[FEATURE NAME]", feature_name)

            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
        except Exception as e:
            raise e