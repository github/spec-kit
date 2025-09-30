# spec-kit-locale

[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![한국어](https://img.shields.io/badge/lang-한국어-red)](README.ko.md)

💫 명세 기반 개발(Spec-Driven Development)을 시작할 수 있도록 돕는 툴킷

조직이 차별화되지 않은 코드를 작성하는 대신 제품 시나리오에 집중할 수 있도록 명세 기반 개발을 지원합니다.

## 목차

- [🤔 명세 기반 개발이란?](#-명세-기반-개발이란)
- [⚡ 시작하기](#-시작하기)
- [📽️ 영상 개요](#%EF%B8%8F-영상-개요)
- [🤖 지원되는 AI 에이전트](#-지원되는-ai-에이전트)
- [🔧 Specify CLI 참조](#-specify-cli-참조)
- [📚 핵심 철학](#-핵심-철학)
- [🌟 개발 단계](#-개발-단계)
- [🎯 실험적 목표](#-실험적-목표)
- [🔧 사전 요구사항](#-사전-요구사항)
- [📖 더 알아보기](#-더-알아보기)
- [📋 상세 프로세스](#-상세-프로세스)
- [🔍 문제 해결](#-문제-해결)
- [👥 관리자](#-관리자)
- [💬 지원](#-지원)
- [🙏 감사의 말](#-감사의-말)
- [📄 라이선스](#-라이선스)

## 🤔 명세 기반 개발이란?

명세 기반 개발은 전통적인 소프트웨어 개발 방식을 뒤집습니다. 수십 년 동안 코드가 왕이었습니다. 명세는 "진짜 작업"인 코딩이 시작되면 만들고 버리는 비계에 불과했습니다. 명세 기반 개발은 이를 바꿉니다. 명세가 실행 가능해지고, 단순히 안내하는 것이 아니라 직접 작동하는 구현을 생성합니다.

## ⚡ 시작하기

원하는 설치 방법을 선택하세요:

### 한 번 설치하고 어디서나 사용

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

그런 다음 도구를 직접 사용:

```bash
specify init <PROJECT_NAME>
specify check
```

### 설치 없이 직접 실행

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

**영구 설치의 장점:**
- 도구가 설치되어 PATH에서 사용 가능
- 셸 별칭을 만들 필요 없음
- `uv tool list`, `uv tool upgrade`, `uv tool uninstall`로 더 나은 도구 관리
- 더 깔끔한 셸 구성

### 1단계: 프로젝트 원칙 수립

`/constitution` 명령을 사용하여 프로젝트의 기본 원칙과 개발 가이드라인을 만들어 모든 후속 개발을 안내합니다.

```
/constitution 코드 품질, 테스트 표준, 사용자 경험 일관성, 성능 요구사항에 중점을 둔 원칙 만들기
```

### 2단계: 요구사항 명세

`/specify` 명령을 사용하여 만들고자 하는 것을 설명합니다. 기술 스택이 아닌 무엇을, 왜 만들지에 집중하세요.

```
/specify 날짜별로 그룹화된 별도의 사진 앨범으로 사진을 정리할 수 있는 애플리케이션을 만들어줘. 앨범은 메인 페이지에서 드래그 앤 드롭으로 재정렬할 수 있어. 앨범은 다른 중첩 앨범 안에 있지 않아. 각 앨범 내에서 사진은 타일 형식의 인터페이스로 미리보기돼.
```

### 3단계: 기술 계획 수립

`/plan` 명령을 사용하여 기술 스택과 아키텍처 선택을 제공합니다.

```
/plan 이 애플리케이션은 최소한의 라이브러리로 Vite를 사용해. 가능한 한 바닐라 HTML, CSS, JavaScript를 사용해. 이미지는 어디에도 업로드되지 않고 메타데이터는 로컬 SQLite 데이터베이스에 저장돼.
```

### 4단계: 작업 목록 생성

`/tasks`를 사용하여 구현 계획에서 실행 가능한 작업 목록을 만듭니다.

```
/tasks
```

### 5단계: 구현

`/implement`를 사용하여 모든 작업을 실행하고 계획에 따라 기능을 구축합니다.

```
/implement
```

단계별 자세한 지침은 [종합 가이드](spec-driven.md)를 참조하세요.

## 📽️ 영상 개요

Spec Kit의 실제 작동을 보고 싶으신가요? [영상 개요](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)를 시청하세요!

## 🤖 지원되는 AI 에이전트

| 에이전트 | 지원 | 비고 |
|---|---|---|
| [Claude Code](https://www.anthropic.com/claude-code) | ✅ | |
| [GitHub Copilot](https://code.visualstudio.com/) | ✅ | |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ | |
| [Cursor](https://cursor.sh/) | ✅ | |
| [Qwen Code](https://github.com/QwenLM/qwen-code) | ✅ | |
| [opencode](https://opencode.ai/) | ✅ | |
| [Windsurf](https://windsurf.com/) | ✅ | |
| [Kilo Code](https://github.com/Kilo-Org/kilocode) | ✅ | |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview) | ✅ | |
| [Roo Code](https://roocode.com/) | ✅ | |
| [Codex CLI](https://github.com/openai/codex) | ❌ | 슬래시 명령의 [사용자 정의 인수를 지원하지 않음](https://github.com/openai/codex/issues/2890) |

## 🔧 Specify CLI 참조

`specify` 명령은 다음 옵션을 지원합니다:

### 명령어

| 명령어 | 설명 |
|---|---|
| `init` | 최신 템플릿에서 새 Specify 프로젝트 초기화 |
| `check` | 설치된 도구 확인 (git, claude, gemini, code/code-insiders, cursor-agent, windsurf, qwen, opencode, codex) |

### 인수/옵션

| 인수/옵션 | 유형 | 설명 |
|---|---|---|
| `<project-name>` | 인수 | 새 프로젝트 디렉토리 이름 (--here 사용 시 선택사항, 또는 현재 디렉토리에 `.` 사용) |
| `--ai` | 옵션 | 사용할 AI 어시스턴트: claude, gemini, copilot, cursor, qwen, opencode, codex, windsurf, kilocode, auggie, 또는 roo |
| `--script` | 옵션 | 사용할 스크립트 유형: sh (bash/zsh) 또는 ps (PowerShell) |
| `--lang` | 옵션 | 생성된 템플릿 및 메시지 언어: en (영어), ko (한국어) [기본값: en] |
| `--ignore-agent-tools` | 플래그 | Claude Code와 같은 AI 에이전트 도구 확인 건너뛰기 |
| `--no-git` | 플래그 | Git 저장소 초기화 건너뛰기 |
| `--here` | 플래그 | 새 프로젝트를 만드는 대신 현재 디렉토리에서 프로젝트 초기화 |
| `--force` | 플래그 | 현재 디렉토리에서 초기화 시 병합/덮어쓰기 강제 (확인 건너뛰기) |
| `--skip-tls` | 플래그 | SSL/TLS 검증 건너뛰기 (권장하지 않음) |
| `--debug` | 플래그 | 문제 해결을 위한 상세 디버그 출력 활성화 |
| `--github-token` | 옵션 | API 요청용 GitHub 토큰 (또는 GH_TOKEN/GITHUB_TOKEN 환경 변수 설정) |

### 사용 예시

```bash
# 기본 프로젝트 초기화
specify init my-project

# 특정 AI 어시스턴트로 초기화
specify init my-project --ai claude

# Cursor 지원과 함께 초기화
specify init my-project --ai cursor

# Windsurf 지원과 함께 초기화
specify init my-project --ai windsurf

# PowerShell 스크립트로 초기화 (Windows/크로스 플랫폼)
specify init my-project --ai copilot --script ps

# 한국어 템플릿으로 초기화
specify init my-project --ai claude --lang ko

# 현재 디렉토리에서 초기화
specify init . --ai copilot
# 또는 --here 플래그 사용
specify init --here --ai copilot

# 확인 없이 현재 (비어있지 않은) 디렉토리에 강제 병합
specify init . --force --ai copilot
# 또는
specify init --here --force --ai copilot

# Git 초기화 건너뛰기
specify init my-project --ai gemini --no-git

# 문제 해결을 위한 디버그 출력 활성화
specify init my-project --ai claude --debug

# API 요청을 위한 GitHub 토큰 사용 (기업 환경에 유용)
specify init my-project --ai claude --github-token ghp_your_token_here

# 시스템 요구사항 확인
specify check
```

### AI 코딩 에이전트 명령어

`specify init` 실행 후, AI 코딩 에이전트는 구조화된 개발을 위해 다음 슬래시 명령에 액세스할 수 있습니다:

| 명령어 | 설명 |
|---|---|
| `/constitution` | 프로젝트 기본 원칙 및 개발 가이드라인 생성 또는 업데이트 |
| `/specify` | 만들고자 하는 것 정의 (요구사항 및 사용자 스토리) |
| `/clarify` | 명세가 불충분한 영역 명확화 (/plan 전에 실행 필요, 명시적으로 건너뛰지 않는 한; 이전의 /quizme) |
| `/plan` | 선택한 기술 스택으로 기술 구현 계획 생성 |
| `/tasks` | 구현을 위한 실행 가능한 작업 목록 생성 |
| `/analyze` | 아티팩트 간 일관성 및 범위 분석 (/tasks 후, /implement 전에 실행) |
| `/implement` | 계획에 따라 기능을 구축하기 위해 모든 작업 실행 |

### 환경 변수

| 변수 | 설명 |
|---|---|
| `SPECIFY_FEATURE` | Git이 아닌 저장소의 기능 감지 재정의. 특정 기능에서 작업할 기능 디렉토리 이름(예: 001-photo-albums)으로 설정. Git 브랜치를 사용하지 않을 때 사용. **작업 중인 에이전트의 컨텍스트에서 /plan 또는 후속 명령을 사용하기 전에 설정해야 함.** |

## 📚 핵심 철학

명세 기반 개발은 다음을 강조하는 구조화된 프로세스입니다:

- "어떻게"보다 "무엇을" 명세가 정의하는 의도 중심 개발
- 가드레일과 조직 원칙을 사용한 풍부한 명세 생성
- 프롬프트에서 원샷 코드 생성이 아닌 다단계 개선
- 명세 해석을 위한 고급 AI 모델 기능에 대한 높은 의존도

## 🌟 개발 단계

| 단계 | 초점 | 주요 활동 |
|---|---|---|
| 0-to-1 개발 ("그린필드") | 처음부터 생성 | 새로운 애플리케이션 및 기능 구축 |
| 창의적 탐색 | 병렬 구현 | 동일한 명세에 대한 여러 기술 스택 구현 비교 |
| 반복적 개선 ("브라운필드") | 브라운필드 현대화 | 레거시 시스템의 점진적 개선 및 현대화 |

## 🎯 실험적 목표

연구 및 실험은 다음에 중점을 둡니다:

- **다양한 기술 스택을 사용하여 애플리케이션 생성**
  - 명세 기반 개발이 특정 기술, 프로그래밍 언어 또는 프레임워크에 국한되지 않는 프로세스라는 가설 검증
  - 미션 크리티컬 애플리케이션 개발 시연

- **조직 제약 조건 통합**
  - 조직 제약 조건 통합 (클라우드 제공업체, 기술 스택, 엔지니어링 관행)
  - 엔터프라이즈 디자인 시스템 및 규정 준수 요구사항 지원

- **다양한 사용자 코호트 및 선호도를 위한 애플리케이션 구축**
  - 다양한 개발 접근 방식 지원 (바이브 코딩에서 AI 네이티브 개발까지)
  - 병렬 구현 탐색 개념 검증

- **강력한 반복적 기능 개발 워크플로 제공**
  - 업그레이드 및 현대화 작업을 처리하도록 프로세스 확장

## 🔧 사전 요구사항

- Linux/macOS (또는 Windows에서 WSL2)
- AI 코딩 에이전트:
  - [Claude Code](https://www.anthropic.com/claude-code)
  - [GitHub Copilot](https://code.visualstudio.com/)
  - [Gemini CLI](https://github.com/google-gemini/gemini-cli)
  - [Cursor](https://cursor.sh/)
  - [Qwen CLI](https://github.com/QwenLM/qwen-code)
  - [opencode](https://opencode.ai/)
  - [Codex CLI](https://github.com/openai/codex)
  - [Windsurf](https://windsurf.com/)
- 패키지 관리를 위한 [uv](https://docs.astral.sh/uv/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

에이전트에 문제가 발생하면 통합을 개선할 수 있도록 이슈를 열어주세요.

## 📖 더 알아보기

- [전체 명세 기반 개발 방법론](spec-driven.md) - 전체 프로세스에 대한 심층 분석
- [상세 워크스루](#-상세-프로세스) - 단계별 구현 가이드

## 📋 상세 프로세스

<details>
<summary>단계별 상세 워크스루를 보려면 클릭하세요</summary>

### 1단계: 프로젝트 부트스트랩

Specify CLI를 사용하여 프로젝트를 부트스트랩할 수 있으며, 이는 환경에 필요한 아티팩트를 가져옵니다. 실행:

```bash
specify init <project_name>
```

또는 현재 디렉토리에서 초기화:

```bash
specify init .
# 또는 --here 플래그 사용
specify init --here

# 디렉토리에 이미 파일이 있을 때 확인 건너뛰기
specify init . --force
# 또는
specify init --here --force
```

사용 중인 AI 에이전트를 선택하라는 메시지가 표시됩니다. 터미널에서 직접 미리 지정할 수도 있습니다:

```bash
specify init <project_name> --ai claude
specify init <project_name> --ai gemini
specify init <project_name> --ai copilot
specify init <project_name> --ai cursor
specify init <project_name> --ai qwen
specify init <project_name> --ai opencode
specify init <project_name> --ai codex
specify init <project_name> --ai windsurf

# 또는 현재 디렉토리에서:
specify init . --ai claude
specify init . --ai codex
# 또는 --here 플래그 사용
specify init --here --ai claude
specify init --here --ai codex

# 비어있지 않은 현재 디렉토리에 강제 병합
specify init . --force --ai claude
# 또는
specify init --here --force --ai claude
```

CLI는 Claude Code, Gemini CLI, Cursor CLI, Qwen CLI, opencode 또는 Codex CLI가 설치되어 있는지 확인합니다. 설치되어 있지 않거나 올바른 도구를 확인하지 않고 템플릿을 가져오려는 경우 명령에 `--ignore-agent-tools`를 사용하세요:

```bash
specify init <project_name> --ai claude --ignore-agent-tools
```

### 2단계: AI 에이전트 시작

프로젝트 폴더로 이동하여 AI 에이전트를 실행합니다. 예를 들어 `claude`를 사용합니다.

`/constitution`, `/specify`, `/plan`, `/tasks`, `/implement` 명령을 사용할 수 있으면 올바르게 구성된 것입니다.

### 3단계: 프로젝트 원칙 수립

첫 번째 단계는 `/constitution` 명령을 사용하여 프로젝트의 기본 원칙을 수립하는 것입니다. 이는 모든 후속 개발 단계에서 일관된 의사 결정을 보장하는 데 도움이 됩니다:

```
/constitution 코드 품질, 테스트 표준, 사용자 경험 일관성, 성능 요구사항에 중점을 둔 원칙을 만들어줘. 이러한 원칙이 기술적 결정과 구현 선택을 어떻게 안내해야 하는지에 대한 거버넌스를 포함해줘.
```

이 단계는 AI 에이전트가 명세, 계획 및 구현 단계에서 참조할 프로젝트의 기본 가이드라인이 포함된 `.specify/memory/constitution.md` 파일을 생성하거나 업데이트합니다.

### 4단계: 기능 명세 작성

프로젝트 원칙이 수립되면 이제 기능 명세를 작성할 수 있습니다. `/specify` 명령을 사용한 다음 개발하려는 프로젝트에 대한 구체적인 요구사항을 제공합니다.

> **중요**: 만들려는 것과 이유에 대해 가능한 한 명확하게 설명하세요. 이 시점에서는 기술 스택에 집중하지 마세요.

예시 프롬프트:

```
Taskify라는 팀 생산성 플랫폼을 개발해줘. 사용자가 프로젝트를 만들고, 팀원을 추가하고, 
작업을 할당하고, 칸반 스타일로 보드 간에 작업을 이동하고 댓글을 달 수 있어야 해. 
이 초기 단계에서는 "Create Taskify"라고 부르자. 여러 사용자가 있지만 사용자는 미리 정의되어 있어. 
두 가지 범주로 다섯 명의 사용자가 필요해. 한 명의 제품 관리자와 네 명의 엔지니어. 
세 개의 다른 샘플 프로젝트를 만들자. 각 작업의 상태에 대해 "To Do", "In Progress", 
"In Review", "Done"과 같은 표준 칸반 열이 있어야 해. 이것은 기본 기능을 설정하기 위한 
첫 번째 테스트이므로 이 애플리케이션에는 로그인이 없어. 작업 카드 UI에서 
칸반 작업 보드의 다른 열 간에 작업의 현재 상태를 변경할 수 있어야 해. 
특정 카드에 대해 무제한으로 댓글을 남길 수 있어야 해. 작업 카드에서 유효한 사용자 중 
하나를 할당할 수 있어야 해. Taskify를 처음 실행하면 선택할 다섯 명의 사용자 목록이 표시돼. 
비밀번호는 필요 없어. 사용자를 클릭하면 프로젝트 목록을 표시하는 메인 뷰로 이동해. 
프로젝트를 클릭하면 해당 프로젝트의 칸반 보드가 열려. 열이 표시돼. 
다른 열 사이에서 카드를 드래그 앤 드롭할 수 있어. 현재 로그인한 사용자인 당신에게 
할당된 모든 카드는 다른 모든 카드와 다른 색상으로 표시되므로 당신의 것을 빠르게 볼 수 있어. 
당신이 작성한 댓글은 편집할 수 있지만 다른 사람이 작성한 댓글은 편집할 수 없어. 
당신이 작성한 댓글은 삭제할 수 있지만 다른 사람이 작성한 댓글은 삭제할 수 없어.
```

이 프롬프트를 입력하면 Claude Code가 계획 및 명세 초안 작성 프로세스를 시작하는 것을 볼 수 있습니다. Claude Code는 또한 저장소를 설정하기 위해 일부 내장 스크립트를 트리거합니다.

이 단계가 완료되면 새 브랜치(예: `001-create-taskify`)와 `specs/001-create-taskify` 디렉토리의 새 명세가 생성됩니다.

생성된 명세에는 템플릿에 정의된 대로 사용자 스토리 및 기능 요구사항 세트가 포함되어야 합니다.

이 단계에서 프로젝트 폴더 내용은 다음과 유사해야 합니다:

```
└── .specify
    ├── memory
    │   └── constitution.md
    ├── scripts
    │   ├── check-prerequisites.sh
    │   ├── common.sh
    │   ├── create-new-feature.sh
    │   ├── setup-plan.sh
    │   └── update-claude-md.sh
    ├── specs
    │   └── 001-create-taskify
    │       └── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### 5단계: 요구사항 명확화

기본 명세가 생성되면 첫 번째 시도에서 제대로 포착되지 않은 요구사항을 명확히 할 수 있습니다.

다운스트림 재작업을 줄이기 위해 기술 계획을 작성하기 전에 구조화된 명확화 워크플로를 실행해야 합니다.

권장 순서:
1. `/clarify` (구조화됨) 사용 - 명확화 섹션에 답변을 기록하는 순차적, 범위 기반 질문.
2. 무언가가 여전히 모호하다고 느껴지면 선택적으로 자유 형식 개선을 따릅니다.

의도적으로 명확화를 건너뛰려는 경우(예: 스파이크 또는 탐색적 프로토타입), 에이전트가 누락된 명확화를 차단하지 않도록 명시적으로 명시하세요.

예시 자유 형식 개선 프롬프트 (`/clarify` 이후 여전히 필요한 경우):

```
만드는 각 샘플 프로젝트 또는 프로젝트에 대해 완료 상태가 다른 상태로 무작위로 분산된 
5-15개의 작업이 있어야 해. 각 완료 단계에 최소한 하나의 작업이 있는지 확인해줘.
```

또한 Claude Code에 검토 및 수락 체크리스트를 검증하도록 요청하고, 요구사항을 검증/통과하는 항목을 확인하고 그렇지 않은 항목은 확인하지 않은 상태로 둡니다. 다음 프롬프트를 사용할 수 있습니다:

```
검토 및 수락 체크리스트를 읽고 기능 명세가 기준을 충족하는 경우 체크리스트의 각 항목을 확인해줘. 
충족하지 않으면 비워둬.
```

Claude Code와의 상호 작용을 명세에 대한 질문을 명확히하고 질문할 수 있는 기회로 사용하는 것이 중요합니다. 첫 번째 시도를 최종으로 취급하지 마세요.

### 6단계: 기술 계획 수립

이제 기술 스택 및 기타 기술 요구사항에 대해 구체적으로 설명할 수 있습니다. 다음과 같은 프롬프트와 함께 프로젝트 템플릿에 내장된 `/plan` 명령을 사용할 수 있습니다:

```
.NET Aspire를 사용하여 생성하고 데이터베이스로 Postgres를 사용할 거야. 
프론트엔드는 드래그 앤 드롭 작업 보드, 실시간 업데이트가 있는 Blazor 서버를 사용해야 해. 
프로젝트 API, 작업 API, 알림 API로 REST API를 생성해야 해.
```

이 단계의 출력에는 여러 구현 세부 정보 문서가 포함되며 디렉토리 트리는 다음과 유사합니다:

```
.
├── CLAUDE.md
├── memory
│   └── constitution.md
├── scripts
│   ├── check-prerequisites.sh
│   ├── common.sh
│   ├── create-new-feature.sh
│   ├── setup-plan.sh
│   └── update-claude-md.sh
├── specs
│   └── 001-create-taskify
│       ├── contracts
│       │   ├── api-spec.json
│       │   └── signalr-spec.md
│       ├── data-model.md
│       ├── plan.md
│       ├── quickstart.md
│       ├── research.md
│       └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

`research.md` 문서를 확인하여 지침에 따라 올바른 기술 스택이 사용되는지 확인하세요. 구성 요소가 눈에 띄거나 사용하려는 플랫폼/프레임워크의 로컬 설치 버전을 확인하도록 Claude Code에 요청할 수 있습니다(예: .NET).

또한 빠르게 변화하는 것(예: .NET Aspire, JS 프레임워크)인 경우 선택한 기술 스택에 대한 세부 정보를 조사하도록 Claude Code에 요청할 수 있습니다. 다음과 같은 프롬프트를 사용합니다:

```
구현 계획과 구현 세부 사항을 살펴보고 .NET Aspire가 빠르게 변화하는 라이브러리이므로 
추가 조사가 도움이 될 수 있는 영역을 찾아줘. 추가 조사가 필요한 영역을 식별하면 
이 Taskify 애플리케이션에서 사용할 특정 버전에 대한 추가 세부 정보로 연구 문서를 업데이트하고 
병렬 연구 작업을 생성하여 웹 연구를 사용하여 세부 정보를 명확히해줘.
```

이 프로세스 중에 Claude Code가 잘못된 것을 연구하는 데 갇혀 있는 것을 발견할 수 있습니다. 다음과 같은 프롬프트로 올바른 방향으로 유도할 수 있습니다:

```
이것을 일련의 단계로 나누어야 한다고 생각해. 먼저 구현 중에 수행해야 하는 확실하지 않거나 
추가 조사가 도움이 될 작업 목록을 식별해. 그 작업 목록을 작성해. 그런 다음 이러한 각 작업에 대해 
별도의 연구 작업을 생성하여 최종 결과가 매우 구체적인 모든 작업을 병렬로 연구하도록 해. 
내가 본 것은 .NET Aspire를 일반적으로 연구하는 것처럼 보였고 이 경우 많은 도움이 되지 않을 것 같아. 
그것은 너무 목표가 없는 연구야. 연구는 특정 목표 질문을 해결하는 데 도움이 되어야 해.
```

> **참고**: Claude Code는 지나치게 열성적이어서 요청하지 않은 구성 요소를 추가할 수 있습니다. 근거와 변경 소스를 명확히하도록 요청하세요.

### 7단계: 계획 검증

계획이 준비되면 Claude Code가 이를 검토하여 누락된 부분이 없는지 확인하도록 해야 합니다. 다음과 같은 프롬프트를 사용할 수 있습니다:

```
이제 구현 계획과 구현 세부 정보 파일을 감사해줘. 이를 읽어보면서 수행해야 하는 작업의 순서가 
명확한지 확인해줘. 여기에 충분한 내용이 있는지 모르겠어. 예를 들어 핵심 구현을 보면 
핵심 구현이나 개선의 각 단계를 진행할 때 정보를 찾을 수 있는 구현 세부 정보의 적절한 위치를 
참조하는 것이 유용할 거야.
```

이는 구현 계획을 개선하고 Claude Code가 계획 주기에서 놓친 잠재적인 맹점을 피하는 데 도움이 됩니다. 초기 개선 패스가 완료되면 구현에 들어가기 전에 Claude Code에 체크리스트를 한 번 더 검토하도록 요청할 수 있습니다.

또한 [GitHub CLI](https://docs.github.com/en/github-cli/github-cli)가 설치된 경우 Claude Code에 현재 브랜치에서 `main`으로 자세한 설명과 함께 풀 리퀘스트를 생성하도록 요청하여 노력이 제대로 추적되도록 할 수 있습니다.

> **참고**: 에이전트가 구현하기 전에 Claude Code에 세부 사항을 교차 확인하여 과도하게 엔지니어링된 부분이 있는지 확인하도록 프롬프트하는 것도 좋습니다(기억하세요 - 지나치게 열성적일 수 있습니다). 과도하게 엔지니어링된 구성 요소나 결정이 존재하는 경우 Claude Code에 해결하도록 요청할 수 있습니다. Claude Code가 계획을 수립할 때 준수해야 하는 기본 요소로 [constitution]을 따르도록 하세요.

### 8단계: 구현

준비가 되면 `/implement` 명령을 사용하여 구현 계획을 실행합니다:

```
/implement
```

`/implement` 명령은 다음을 수행합니다:
- 모든 전제 조건이 준비되어 있는지 검증 (constitution, spec, plan, tasks)
- `tasks.md`에서 작업 분류 파싱
- 종속성 및 병렬 실행 마커를 고려하여 올바른 순서로 작업 실행
- 작업 계획에 정의된 TDD 접근 방식 따르기
- 진행 상황 업데이트 제공 및 오류 적절히 처리

> **중요**: AI 에이전트는 로컬 CLI 명령(예: `dotnet`, `npm` 등)을 실행합니다. 필요한 도구가 컴퓨터에 설치되어 있는지 확인하세요.

구현이 완료되면 애플리케이션을 테스트하고 CLI 로그에 표시되지 않을 수 있는 런타임 오류(예: 브라우저 콘솔 오류)를 해결합니다. 이러한 오류를 AI 에이전트에 복사하여 붙여넣어 해결할 수 있습니다.

</details>

## 🔍 문제 해결

### Linux에서 Git 인증 문제

Linux에서 Git 인증에 문제가 있는 경우 Git Credential Manager를 설치할 수 있습니다:

```bash
#!/usr/bin/env bash
set -e

echo "Git Credential Manager v2.6.1 다운로드 중..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb

echo "Git Credential Manager 설치 중..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb

echo "Git이 GCM을 사용하도록 구성 중..."
git config --global credential.helper manager

echo "정리 중..."
rm gcm-linux_amd64.2.6.1.deb
```

## 👥 관리자

이 프로젝트는 [GitHub](https://github.com)에서 관리합니다.

## 💬 지원

지원이 필요하면 [GitHub 이슈](https://github.com/github/spec-kit/issues/new)를 열어주세요. 버그 보고서, 기능 요청, 명세 기반 개발 사용에 대한 질문을 환영합니다.

## 🙏 감사의 말

이 프로젝트는 [John Lam](https://github.com/jflam)의 작업과 연구에 크게 영향을 받았으며 이를 기반으로 합니다.

## 📄 라이선스

이 프로젝트는 MIT 오픈 소스 라이선스 조건에 따라 라이선스가 부여됩니다. 전체 조건은 [LICENSE](LICENSE) 파일을 참조하세요.
