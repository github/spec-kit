<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kit 로고" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>코딩 에이전트와 함께 스펙으로 개발하고, 버그를 고치고, 아이디어를 평가하세요.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/github/spec-kit/releases/latest"><img src="https://img.shields.io/github/v/release/github/spec-kit" alt="최신 릴리스"/></a>
    <a href="https://github.com/github/spec-kit/stargazers"><img src="https://img.shields.io/github/stars/github/spec-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="라이선스"/></a>
    <a href="https://github.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="문서"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <a href="./README.zh-CN.md">简体中文</a> ·
    <a href="./README.ja.md">日本語</a> ·
    <strong>한국어</strong> ·
    <a href="./README.fr.md">Français</a>
</p>

Spec Kit은 AI 코딩 에이전트에게 체계적인 프로세스, 재사용 가능한 템플릿, 문서로 남는 결과물을
제공하는 오픈 소스 툴킷입니다. 이미 만들어진 프로세스로 시작해 필요에 맞게 고쳐 쓰거나,
직접 만든 프로세스를 가져와도 됩니다.

## 프로세스 선택

| 필요한 것 | 프로세스 | 결과 |
| --- | --- | --- |
| 기능이나 애플리케이션 만들기 | [스펙 주도 개발](#스펙-주도-개발) | 계획, 구현, 수렴까지 이어지는 스펙 |
| 잘못된 동작을 진단하고 고치기 | [버그 수정](#버그-수정) | 평가를 거친 원인, 범위를 한정한 수정, 기록으로 남는 검증 |
| 아이디어에 투자할 가치가 있는지 판단하기 | [아이디어 평가](#아이디어-평가) | 근거에 기반한 진행, 명확화, 중단 결정 |
| 다른 프로세스를 도입하거나 새로 만들기 | [직접 만든 프로세스](#제공-기능) | 재사용 가능한 메커니즘으로 조정하거나 조립한 프로세스 |

이 프로세스들은 반드시 거쳐야 하는 단계가 아니라 각각 독립된 진입점입니다. 스펙 주도 개발(SDD)은
코어에 포함되어 있고, 버그 수정과 아이디어 평가는 Spec Kit에 함께 제공되며 필요할 때 설치하는 확장입니다.
아래 메커니즘으로 다른 프로세스를 도입하거나 새로 만들 수도 있습니다.

## 제공 기능

Spec Kit은 바로 쓸 수 있는 프로세스와 조합 가능한 메커니즘을 함께 제공합니다:

| 하고 싶은 일 | Spec Kit 메커니즘 |
| --- | --- |
| 코딩 에이전트에 연결하거나 에이전트 간에 전환하기 | [통합](https://github.github.io/spec-kit/integrations/index.html) |
| 명령어, 품질 게이트, 또는 프로세스 전체 추가하기 | [확장](https://github.github.io/spec-kit/extensions/overview.html) |
| 프로세스를 외부 도구나 서비스에 연결하기 | [확장](https://github.github.io/spec-kit/extensions/overview.html) |
| 코딩 에이전트의 라이프사이클 이벤트에 반응하기 | [확장 런타임 이벤트](https://github.github.io/spec-kit/extensions/api.html#extension-runtime-events) |
| Spec Kit 명령어 전후에 확장 명령어 실행하기 | [확장 훅](https://github.github.io/spec-kit/extensions/api.html#hook-configuration) |
| 템플릿, 명령어, 용어, 방법론 조정하기 | [프리셋](https://github.github.io/spec-kit/presets/overview.html) |
| 조직 또는 규제 기준 강제하기 | [프리셋](https://github.github.io/spec-kit/presets/overview.html) |
| 한 프로젝트에서만 템플릿 오버라이드하기 | [프로젝트 로컬 오버라이드](https://github.github.io/spec-kit/how-to/customization.html#project-local-overrides-and-resolution) |
| 프롬프트, 명령어, 게이트, 셸 작업 자동화하기 | [워크플로](https://github.github.io/spec-kit/workflows/overview.html) |
| 설치된 워크플로를 포크하지 않고 수정하기 | [워크플로 오버레이](https://github.github.io/spec-kit/workflows/overlays.html) |
| 워크플로에 재사용 가능한 실행 동작 추가하기 | [워크플로 스텝](https://github.github.io/spec-kit/workflow-steps/developing.html#custom-step-packages) |
| 역할이나 팀에 맞게 선별한 구성 설치하기 | [번들](https://github.github.io/spec-kit/bundles/overview.html) |
| 커뮤니티 구성 요소 찾기 | [카탈로그](https://github.github.io/spec-kit/overview/catalogs.html) |
| 승인된 구성 요소의 비공개 카탈로그 호스팅하기 | [카탈로그](https://github.github.io/spec-kit/overview/catalogs.html) |
| 비공개 카탈로그와 구성 요소 다운로드에 접근하기 | [인증](https://github.github.io/spec-kit/reference/authentication.html) |
| 오프라인이나 방화벽 뒤에서 작업하기 | [로컬 소스와 자체 호스팅 카탈로그](https://github.github.io/spec-kit/install/air-gapped.html) |
| 명령어, 템플릿, 스크립트를 어느 계층이 제공하는지 확인하기 | [산출물 인벤토리](https://github.github.io/spec-kit/overview/artifacts.html) |

`specify extension search`, `specify preset search`, `specify workflow search`,
`specify bundle search` 같은 명령어로 활성화된 카탈로그를 검색할 수 있습니다.
Spec Kit에는 커뮤니티 카탈로그가 포함되어 있고, 조직은 직접 선별한 소스를 추가할 수 있습니다.
카탈로그 등재는 감사나 보증이 아니므로, 커뮤니티 소스 코드는 설치하거나 실행하기 전에 검토하세요.

<a id="-get-started"></a>
<a id="-prerequisites"></a>

## 시작하기

Linux, macOS, Windows 환경에서 Python 3.11+, [uv](https://github.github.io/spec-kit/install/uv.html),
그리고 지원되는 AI 코딩 에이전트가 필요합니다.

터미널에서 아래 명령어를 실행해 Spec Kit을 설치하고 프로젝트를 만드세요.
이 예시는 GitHub Copilot을 사용합니다.

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-supported-ai-coding-agent-integrations"></a>

Specify CLI를 설치하고 프로젝트를 만들었다면, 프로젝트 디렉터리에서 코딩 에이전트를 실행한 뒤
아래 프로세스 중 하나를 고르세요.

다른 환경이라면:

- [설치](https://github.github.io/spec-kit/installation.html): 특정 버전 고정, 다른 설치 방법, CI, 문제 해결
- [기존 프로젝트](https://github.github.io/spec-kit/how-to/existing-projects.html): 이미 있는 코드에서 시작하기
- [다른 에이전트](https://github.github.io/spec-kit/integrations/index.html): 통합 키와 [호출 문법](https://github.github.io/spec-kit/integrations/cli.html#command-invocation)
- [업그레이드](https://github.github.io/spec-kit/upgrade.html): 기존 설치 업데이트하기

<a id="-what-is-spec-driven-development"></a>
<a id="sdd-quickstart"></a>

## 스펙 주도 개발

무엇을, 왜 만드는지 정의한 다음, 스펙을 계획, 작업, 동작하는 코드로 바꿉니다.

아래는 최소 흐름입니다. 원칙(constitution)은 프로젝트당 한 번 만들고, 나머지 단계는 기능마다
반복합니다. 이 스킬들은 터미널이 아니라 에이전트 채팅에서 한 번에 하나씩 실행하고, 결과를 검토한 뒤
다음으로 넘어가세요.

이 예시는 GitHub Copilot의 기본 스킬 문법을 사용합니다. 다른 에이전트를 쓴다면 해당 에이전트의
[호출 문법](https://github.github.io/spec-kit/integrations/cli.html#command-invocation)을 사용하세요.

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

수렴 결과가 `Converged`로 나올 때까지 implement와 converge를 반복하세요.
명확화, 체크리스트, 일관성 분석은 SDD 실습 가이드를 참고하세요.

[SDD 실습 가이드](https://github.github.io/spec-kit/quickstart.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-bug-fixing-with-spec-kit"></a>
<a id="bug-fix-quickstart"></a>

## 버그 수정

원인을 평가하고, 버그를 고치고, 원래 증상이 해결됐는지 검증합니다.
SDD 기능 워크플로를 먼저 거칠 필요는 없습니다.

터미널의 프로젝트 디렉터리에서 버그 수정 확장을 설치하세요:

```bash
specify extension add bug
```

이 스킬들은 터미널이 아니라 에이전트 채팅에서 한 번에 하나씩 실행하고, 결과를 검토한 뒤 다음으로 넘어가세요.

이 예시는 GitHub Copilot의 기본 스킬 문법을 사용합니다. 다른 에이전트를 쓴다면 해당 에이전트의
[호출 문법](https://github.github.io/spec-kit/integrations/cli.html#command-invocation)을 사용하세요.

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

`.specify/bugs/login-crash/`의 보고서를 검토하세요. 최종 판정은
`verified`(검증됨), `partial`(부분 검증), `failed`(실패) 중 하나이며, `verified`일 때만 수정에 성공한
것입니다.

[버그 수정 실습 가이드](https://github.github.io/spec-kit/guides/bugfix.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-assessing-ideas-with-spec-kit"></a>
<a id="idea-assessment-quickstart"></a>

## 아이디어 평가

아이디어를 추진할 가치가 있는지 판단할 근거를 모읍니다.
소스 코드나 SDD 기능 워크플로가 없어도 됩니다.

터미널의 프로젝트 디렉터리에서 아이디어 평가 확장을 설치하세요:

```bash
specify extension add assess
```

이 스킬들은 터미널이 아니라 에이전트 채팅에서 한 번에 하나씩 실행하고, 결과를 검토한 뒤 다음으로 넘어가세요.

이 예시는 GitHub Copilot의 기본 스킬 문법을 사용합니다. 다른 에이전트를 쓴다면 해당 에이전트의
[호출 문법](https://github.github.io/spec-kit/integrations/cli.html#command-invocation)을 사용하세요.

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

`.specify/assessments/offline-mode/`의 산출물과 최종 결정을 검토하세요. 결정은
`go`(진행), `needs-clarification`(명확화 필요), `kill`(중단) 중 하나입니다. 불확실한 부분은 단계
전체를 다시 실행하지 말고, 기존 Markdown 산출물을 직접 또는 에이전트와 함께 고쳐 해소하세요.
`go` 결정이 난 소프트웨어 아이디어를 만들기로 했다면, 필요한 경우 프로젝트 원칙(constitution)을 먼저
정한 뒤 `decision.md`의 인계 요약을 `/speckit-specify`에 넘기세요. 이유를 기록해 두고 멈추는 것도
유용한 결과입니다.

[아이디어 평가 실습 가이드](https://github.github.io/spec-kit/guides/assessment.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-making-spec-kit-your-own-extensions--presets"></a>
<a id="-bundles-role-based-setups"></a>
<a id="-community"></a>

## 커스터마이즈하거나 직접 만든 프로세스 가져오기

스펙 주도 개발, 버그 수정, 아이디어 평가를 팀의 기준에 맞게 커스터마이즈하세요. 이 중 어느 것도
쓰지 않고 직접 만든 프로세스를 가져올 수도 있습니다. 목표에 맞게 [위의 제공 기능](#제공-기능)을 조합하세요:

- 프리셋으로 기존 프로세스를 조정합니다. 예를 들어 계획에 규제 추적성을 요구할 수 있습니다. 일회성 템플릿 변경에는 프로젝트 로컬 오버라이드를 사용하세요.
- 확장으로 프로세스의 명령어를 추가하고, 통합을 통해 코딩 에이전트에 노출해서 직접 만든 프로세스를 가져옵니다.
- 워크플로로 명령어와 검사를 자동화합니다. 설치된 워크플로를 포크하지 않고 조정하려면 오버레이를 쓰고, 기본 제공 타입으로 부족하면 커스텀 워크플로 스텝을 추가하세요.
- 확장, 프리셋, 워크플로, 워크플로 스텝을 번들로 묶어 재사용 가능한 구성을 공유합니다.

필요를 충족하는 가장 작은 변경부터 시작하세요. 프로세스 전체를 바꿀 필요는 없습니다.

[커스터마이즈 가이드](https://github.github.io/spec-kit/how-to/customization.html) ·
[커뮤니티 구성 요소와 실습 가이드](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-reference"></a>
<a id="available-slash-commands"></a>
<a id="-learn-more"></a>
<a id="-core-philosophy"></a>
<a id="-development-phases"></a>
<a id="-experimental-goals"></a>
<a id="-does-spec-kit-use-spec-kit"></a>

## 문서

- [CLI 레퍼런스](https://github.github.io/spec-kit/index.html#specify-cli)와 [프로세스 명령어](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [사용 가이드(How-to)](https://github.github.io/spec-kit/how-to/index.html): 프로젝트 작업에 Spec Kit 적용하기
- [SDD 철학](https://github.github.io/spec-kit/how-to/sdd.html), [전체 방법론](./spec-driven.md), [기존 스펙 발전시키기](https://github.github.io/spec-kit/how-to/evolving-specs.html)
- [프로젝트 연혁](https://github.github.io/spec-kit/overview/history.html)
- [Spec Kit이 Spec Kit을 쓰는 방법](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

## 소식

- [Open Source Friday: Spec Kit Part 2](https://www.youtube.com/watch?v=8hHCpNVLhmI) (2026년 10월 16일) — Manfred Riem과 Nicole Haugen이 Spec Kit 1.0과 확장된 툴킷에 대해 이야기합니다.
- [Living Specs in SpecKit](https://www.alfredo-perez.dev/blog/2026-10-15-living-specs) (2026년 10월 15일) — Alfredo Perez가 프로젝트가 발전하는 동안 역량(capability) 단위 스펙을 유지하는 방법을 살펴봅니다.
- [Spec Kit Customization Series](https://jesseliberty.com/2026/10/08/4-solutions-to-spec-kit-issues/) (2026년 10월 8–10일) — Jesse Liberty가 테스트와 게시를 포함해 프리셋과 확장 작성 과정을 안내합니다.
- [From Spec-First to Enterprise-Ready: Extending GitHub Spec Kit](https://developer.microsoft.com/blog/from-spec-first-to-enterprise-ready-extending-github-spec-kit/) (2026년 10월 7일) — Apoorv Gupta가 프리셋, 확장, 번들, 워크플로, 관리형 카탈로그를 이용한 엔터프라이즈 커스터마이즈를 설명합니다.
- [Open Source Friday with Spec Kit](https://www.youtube.com/watch?v=2IArMAhkJcE) (2026년 5월 8일) — Manfred Riem과 함께하는 Spec Kit 소개와 SDD 시연입니다.

## 스타 추이

<p align="center">
    <a href="https://www.star-history.com/#github/spec-kit&Date">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date&theme=dark"/>
            <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date"/>
            <img src="https://api.star-history.com/svg?repos=github%2Fspec-kit&type=Date" alt="Spec Kit 스타 추이 차트"/>
        </picture>
    </a>
</p>

<p align="center">
    <em>Spec Kit을 빛내 주시는 모든 분께 감사드립니다.</em>
</p>

<a id="-support"></a>

## 지원 및 기여

[버그 신고 또는 기능 요청](https://github.com/github/spec-kit/issues/new) ·
[기여 가이드](./CONTRIBUTING.md) · [행동 강령](./CODE_OF_CONDUCT.md)

<a id="-license"></a>

Spec Kit은 [MIT 라이선스](./LICENSE)로 배포됩니다.
