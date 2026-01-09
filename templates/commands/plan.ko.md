---
description: 계획 템플릿을 사용하여 구현 계획 워크플로우를 실행하고 설계 산출물을 생성합니다.
handoffs: 
  - label: 작업 목록 생성
    agent: speckit.tasks
    prompt: 계획을 작업으로 세분화
    send: true
  - label: 체크리스트 생성
    agent: speckit.checklist
    prompt: 다음 도메인에 대한 체크리스트 생성...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 고려해야 합니다 (비어있지 않은 경우).

## 개요

1. **설정**: 저장소 루트에서 `{SCRIPT}` 실행 및 FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH에 대한 JSON 파싱. 'I'm Groot'와 같은 인수의 단일 따옴표는 이스케이프 구문 사용: 예: 'I'\''m Groot' (또는 가능하면 큰따옴표: "I'm Groot").

2. **컨텍스트 로드**: FEATURE_SPEC 및 `/memory/constitution.md` 읽기. IMPL_PLAN 템플릿 로드 (이미 복사됨).

3. **계획 워크플로우 실행**: IMPL_PLAN 템플릿의 구조를 따라:
   - 기술 컨텍스트 작성 (알 수 없는 항목을 "명확화 필요"로 표시)
   - 헌장에서 헌장 검증 섹션 작성
   - 게이트 평가 (위반이 정당화되지 않으면 ERROR)
   - Phase 0: research.md 생성 (모든 명확화 필요 해결)
   - Phase 1: data-model.md, contracts/, quickstart.md 생성
   - Phase 1: 에이전트 스크립트 실행하여 에이전트 컨텍스트 업데이트
   - 설계 후 헌장 검증 재평가

4. **중지 및 보고**: Phase 2 계획 후 명령 종료. 브랜치, IMPL_PLAN 경로 및 생성된 산출물 보고.

## 단계

### Phase 0: 개요 & 연구

1. **위의 기술 컨텍스트에서 알 수 없는 항목 추출**:
   - 각 명확화 필요 → 연구 작업
   - 각 의존성 → 모범 사례 작업
   - 각 통합 → 패턴 작업

2. **연구 에이전트 생성 및 파견**:

   ```text
   기술 컨텍스트의 각 알 수 없는 항목에 대해:
     작업: "{기능 컨텍스트}에 대한 {알 수 없는 항목} 연구"
   각 기술 선택에 대해:
     작업: "{도메인}에서 {기술}에 대한 모범 사례 찾기"
   ```

3. **발견 사항 통합** 다음 형식으로 `research.md`에:
   - 결정: [선택한 것]
   - 근거: [선택한 이유]
   - 고려된 대안: [평가한 다른 항목]

**출력**: 모든 명확화 필요가 해결된 research.md

### Phase 1: 설계 & 계약

**선행 조건:** `research.md` 완료

1. **기능 명세서에서 엔티티 추출** → `data-model.md`:
   - 엔티티 이름, 필드, 관계
   - 요구사항의 검증 규칙
   - 해당하는 경우 상태 전이

2. **기능 요구사항에서 API 계약 생성**:
   - 각 사용자 동작 → 엔드포인트
   - 표준 REST/GraphQL 패턴 사용
   - OpenAPI/GraphQL 스키마를 `/contracts/`에 출력

3. **에이전트 컨텍스트 업데이트**:
   - `{AGENT_SCRIPT}` 실행
   - 이 스크립트는 사용 중인 AI 에이전트 감지
   - 적절한 에이전트별 컨텍스트 파일 업데이트
   - 현재 계획의 새로운 기술만 추가
   - 마커 사이의 수동 추가 보존

**출력**: data-model.md, /contracts/*, quickstart.md, 에이전트별 파일

## 주요 규칙

- 절대 경로 사용
- 게이트 실패 또는 미해결 명확화에 대해 ERROR
