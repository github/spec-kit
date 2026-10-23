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
제공하는 오픈 소스 툴킷입니다. 아래 세 가지 프로세스 중 하나로 시작해 필요에 맞게 고쳐 쓰거나,
직접 만든 프로세스를 가져와도 됩니다.

## 프로세스 선택

| 필요한 것 | 프로세스 | 결과 |
| --- | --- | --- |
| 기능이나 애플리케이션 만들기 | [스펙 주도 개발](#스펙-주도-개발) | 계획, 구현, 수렴까지 이어지는 스펙 |
| 잘못된 동작을 진단하고 고치기 | [버그 수정](#버그-수정) | 평가를 거친 원인, 범위를 한정한 수정, 기록으로 남는 검증 |
| 아이디어에 투자할 가치가 있는지 판단하기 | [아이디어 평가](#아이디어-평가) | 근거에 기반한 진행, 명확화, 중단 결정 |

세 프로세스는 반드시 거쳐야 하는 세 단계가 아니라 **각각 독립된 진입점**입니다. 스펙 주도 개발(SDD)은
코어에 포함되어 있고, 버그 수정과 아이디어 평가는 Spec Kit에 함께 제공되며 필요할 때 설치하는 확장입니다.

<a id="-get-started"></a>
<a id="-prerequisites"></a>

## 시작하기

Linux, macOS, Windows 환경에서 **Python 3.11+**, **[uv](https://github.github.io/spec-kit/install/uv.html)**,
그리고 지원되는 AI 코딩 에이전트가 필요합니다.
**CLI 설정**은 터미널에서 진행합니다. 아래 명령어를 실행해 Spec Kit을 설치하고 프로젝트를 만드세요:

```bash
uv tool install specify-cli
specify init my-project --integration copilot
cd my-project
```

<a id="-supported-ai-coding-agent-integrations"></a>

예시는 **GitHub Copilot의 기본 스킬 모드**를 기준으로 합니다. 지원되는 다른 에이전트를 쓰려면
`copilot`을 해당 에이전트의 [통합 키](https://github.github.io/spec-kit/integrations/index.html)로 바꾸세요.

이미 코드가 있나요? [기존 프로젝트 가이드](https://github.github.io/spec-kit/guides/existing-projects.html)를 따르세요.
특정 버전 고정, 다른 설치 방법, CI, 문제 해결은
[설치](https://github.github.io/spec-kit/installation.html) 문서를 참고하세요.
기존 설치를 업데이트하려면 [업그레이드](https://github.github.io/spec-kit/upgrade.html) 문서를 참고하세요.

이제 **프로젝트 디렉터리에서 코딩 에이전트를 실행**하고 아래 프로세스 중 하나를 고르세요.
각 `/speckit-*` **스킬은 에이전트 채팅에서** 한 번에 하나씩 호출하고, 결과를 검토한 뒤 다음으로
넘어가세요. 이들은 터미널 명령어가 아니라 에이전트 스킬입니다. 에이전트나 모드에 따라
[호출 문법이 다를 수 있습니다](https://github.github.io/spec-kit/integrations/cli.html#command-invocation).

<a id="-what-is-spec-driven-development"></a>
<a id="sdd-quickstart"></a>

## 스펙 주도 개발

**어떻게** 만들지 정하기 전에 **무엇을, 왜** 만드는지부터 정의합니다. SDD는 요구 사항을 스펙,
기술 계획, 실행 가능한 작업으로 바꾸고, 이 산출물을 기준으로 구현을 이끕니다.

**원칙(constitution)은 프로젝트당 한 번 정하고, 기능마다 스펙 작성(specify) → 계획(plan) → 작업 분해(tasks) → 구현(implement) → 수렴(converge)을 진행합니다.**

에이전트 채팅에서 다음 스킬을 호출하세요:

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

수렴 결과가 **Converged**로 나올 때까지 **implement → converge**를 반복하세요.
품질 게이트를 더 두고 싶다면 명확화, 체크리스트, 일관성 분석을 추가하세요.

[SDD 실습 가이드](https://github.github.io/spec-kit/quickstart.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-sdd.html)

<a id="-bug-fixing-with-spec-kit"></a>
<a id="bug-fix-quickstart"></a>

## 버그 수정

진단, 수정, 검증을 분리해서 에이전트가 평가로 밝혀낸 원인을 고치고 원래 증상을 다시 확인하게
합니다. SDD 기능 워크플로를 먼저 거칠 필요는 없습니다.

**CLI 설정(터미널):** 프로젝트 디렉터리에서 선택형 확장을 설치하세요:

```bash
specify extension add bug
```

그다음 에이전트 채팅에서 **평가(assess) → 수정(fix) → 테스트(test)** 스킬을 호출하세요:

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

보고서는 `.specify/bugs/login-crash/`에 저장됩니다. 최종 판정이
`verified`(검증됨), `partial`(부분 검증), `failed`(실패) 중 무엇인지 확인하세요. 검증이 빠졌다면 수정에
성공한 것이 아닙니다.

[버그 수정 실습 가이드](https://github.github.io/spec-kit/guides/bugfix.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-bugfix.html)

<a id="-assessing-ideas-with-spec-kit"></a>
<a id="idea-assessment-quickstart"></a>

## 아이디어 평가

소프트웨어가 되든 안 되든, 아이디어에 뛰어들기 전에 근거부터 모읍니다.
독립적으로 쓰는 프로세스라서 소스 코드가 없는 프로젝트에서도 동작합니다.

**CLI 설정(터미널):** 프로젝트 디렉터리에서 선택형 확장을 설치하세요:

```bash
specify extension add assess
```

그다음 에이전트 채팅에서 **접수(intake) → 조사(research) → 정의(define) → 구체화(shape) → 결정(decide)** 스킬을 호출하세요:

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

산출물은 `.specify/assessments/offline-mode/`에 저장되며, 마지막에
**진행(go) / 명확화 필요(needs-clarification) / 중단(kill)** 중 하나로 결정이 나옵니다.
불확실한 부분은 단계 전체를 다시 생성하지 말고, 기존 Markdown 산출물을 직접 또는 에이전트와 함께
다듬어 해소하세요. 만들기로 했다면 `go` 결정을 `/speckit-specify`로 넘길 수 있습니다. 이유를
기록해 두고 멈추는 것도 유용한 결과입니다.

[아이디어 평가 실습 가이드](https://github.github.io/spec-kit/guides/assessment.html) ·
[명령어 레퍼런스](https://github.github.io/spec-kit/reference/agentic-assessment.html)

<a id="-making-spec-kit-your-own-extensions--presets"></a>
<a id="-bundles-role-based-setups"></a>
<a id="-community"></a>

## 커스터마이즈하거나 직접 만든 프로세스 가져오기

**확장**은 기능을 추가하고, **프리셋**은 기존 동작을 조정하며, **워크플로**는 단계를 자동화하고,
**번들**은 역할별 구성을 하나로 묶습니다. 일회성 템플릿 변경에는 프로젝트 로컬 오버라이드를 사용하세요.

[커스터마이즈 가이드](https://github.github.io/spec-kit/guides/customization.html) ·
[커뮤니티 확장, 프리셋, 번들, 실습 가이드](https://github.github.io/spec-kit/community/overview.html)

<a id="-specify-cli-reference"></a>
<a id="available-slash-commands"></a>
<a id="-learn-more"></a>
<a id="-core-philosophy"></a>
<a id="-development-phases"></a>
<a id="-experimental-goals"></a>
<a id="-does-spec-kit-use-spec-kit"></a>

## 문서

- [CLI 레퍼런스](https://github.github.io/spec-kit/reference/overview.html)와 [프로세스 명령어](https://github.github.io/spec-kit/reference/agentic-sdd.html#command-overview)
- [SDD 철학](https://github.github.io/spec-kit/concepts/sdd.html), [전체 방법론](./spec-driven.md), [기존 스펙 발전시키기](https://github.github.io/spec-kit/guides/evolving-specs.html)
- [프로젝트 연혁](https://github.github.io/spec-kit/history.html)
- [Spec Kit이 Spec Kit을 쓰는 방법](./CONTRIBUTING.md#does-spec-kit-use-spec-kit)

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
