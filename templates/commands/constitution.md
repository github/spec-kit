---
description: Сформировать или обновить конституцию проекта под стек FSD + Vite + React + TypeScript + Mantine.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Пользовательский ввод

```text
$ARGUMENTS
```

Если указаны специфические приоритеты (например, безопасность, скорость, UX) — учитывай при формировании правил.

---

## Назначение

Конституция фиксирует неизменяемые принципы разработки: стек, архитектура, качество, процесс. Все последующие команды обязаны ей следовать.

---

## Шаги

1. Запусти `{SCRIPT}` и получи `FEATURE_DIR`. Если файл `memory/constitution.md` существует — загрузи для обновления, иначе используй `templates/memory/constitution.md` как основу.

2. Сформируй разделы:
   - **Базовые принципы**: FSD, Vite + React + TypeScript strict, Mantine 7+, Zustand (или RTK), i18next, отсутствие Tailwind.
   - **Технологический стек**: конфигурация Vite (SWC), ESLint + Prettier, GitHub Actions (lint/typecheck/build), Vitest + RTL, Conventional Commits.
   - **Архитектура FSD**: описание слоёв (`app`, `shared`, `entities`, `features`, `widgets`, `pages`, `processes`), требования к публичным API (index.ts), алиасы (`vite-tsconfig-paths`).
   - **Процесс Spec-Kit**: порядок `/specify → /plan → /task → /implement → /verify → /document → /release`, использование context7 и sequential-thinking.
   - **Документация и ADR**: обязательность `/docs/architecture.md`, `/docs/adr/*`, `/docs/roadmap.md`, `/docs/changelog.md`.
   - **Правила изменения конституции**: кто и как может вносить правки (например, ADR + review).

3. Обнови раздел “Manual additions” только если пользователь предоставил дополнительные правила (не затирай существующие комментарии).

4. Сохрани документ в `memory/constitution.md` и сообщи:
   - количество принципов/секций;
   - что требуется для утверждения (например, “пройти ревью команды”, “добавить ссылку в README”).

---

## Нельзя

- Удалять базовые принципы без явного указания пользователя.
- Добавлять стековые исключения (Tailwind, CSS-in-JS вне Mantine Emotion).
- Противоречить Spec-Kit workflow или требованиям CI/QA.
