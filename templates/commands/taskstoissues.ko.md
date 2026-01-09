---
description: 사용 가능한 설계 산출물을 기반으로 기존 작업을 실행 가능하고 의존성이 정렬된 GitHub 이슈로 변환합니다.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 고려해야 합니다 (비어있지 않은 경우).

## 개요

1. 저장소 루트에서 `{SCRIPT}` 실행 및 FEATURE_DIR 및 AVAILABLE_DOCS 목록 파싱. 모든 경로는 절대 경로여야 합니다. 'I'm Groot'와 같은 인수의 단일 따옴표는 이스케이프 구문 사용: 예: 'I'\''m Groot' (또는 가능하면 큰따옴표: "I'm Groot").
1. 실행된 스크립트에서 **tasks** 경로 추출.
1. 다음을 실행하여 Git 원격 가져오기:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> 원격이 GITHUB URL인 경우에만 다음 단계로 진행

1. 목록의 각 작업에 대해 GitHub MCP 서버를 사용하여 Git 원격을 대표하는 저장소에 새 이슈 생성.

> [!CAUTION]
> 어떤 경우에도 원격 URL과 일치하지 않는 저장소에 이슈를 생성하지 마세요

## 이슈 생성 규칙

- 각 작업을 개별 GitHub 이슈로 변환
- 이슈 제목: 작업 설명 사용
- 이슈 본문: 작업 세부사항, 파일 경로, 의존성 포함
- 레이블: Phase 번호, 우선순위, 사용자 스토리 레이블 추가
- 의존성: 다른 작업에 대한 의존성을 이슈 본문에 명시

## 보고

- 생성된 이슈 수
- 각 이슈의 링크
- 생성된 이슈의 요약
