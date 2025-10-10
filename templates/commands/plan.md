---
description: Сформировать план реализации под FSD + Vite + React + TypeScript + Mantine.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## Пользовательский ввод

```text
$ARGUMENTS
```

Если вход пустой — сообщи об ошибке.

---

## Алгоритм

1. **Запусти `{SCRIPT}`** из корня репозитория (один раз). Разбери JSON и получи:
   - `FEATURE_SPEC`, `FEATURE_DIR`, `PLAN_TEMPLATE`, `BRANCH`;
   - абсолютные пути ко всем артефактам.  
   Ошибка → остановись.

2. **Загрузи исходные данные**:
   - `templates/plan-template.md`;
   - `specs/.../spec.md`;
   - `.specify/memory/constitution.md`.

3. **Получить свежую документацию через context7**:
   - JSON-RPC `initialize`, затем `tools/list`.
   - Последовательно запроси: `vite`, `react`, `typescript`, `mantine`, `react-router`, `zustand` (или Redux Toolkit).
   - Для каждой библиотеки: `resolve-library-id` → `get-library-docs` (темы: “setup”, “best practices”, “upgrading”).
   - Сохрани версии и ссылки в разделе “Источники и ссылки”.  
   Если ключ недействителен — зафиксируй проблему и продолжай с пометкой.

4. **Сформировать технический контекст**:
   - Vite + React + TypeScript (strict) + Mantine (Emotion), Zustand (по умолчанию).
   - FSD-уровни: `app`, `shared`, `entities`, `features`, `widgets`, `pages`, `processes`.
   - Паттерны: Mantine theme, i18n (i18next), routing (react-router).
   - Отметь требования по линтингу (ESLint + Prettier) и CI (lint/typecheck/build).

5. **Заполнить план по фазам**:
   - Phase 0 — Research (закрыть `NEEDS CLARIFICATION`, собрать выдержки из context7, оформить ADR-заметки).
   - Phase 1 — Design (структура FSD, `vite.config.ts`, `tsconfig.*`, Mantine theme, i18n, Zustand store).
   - Phase 2 — Tasks (правила генерации `tasks.md`, контроль DoD, подготовка CI).
   - Phase 3+ — Implementation/Testing (итерации по историям, финальный Verify, тесты в конце).

6. **Обновить структуру проекта**:
   - опиши директории FSD и публичные контракты (index.ts).
   - отметь алиасы (`vite-tsconfig-paths`), Mantine theme расположение, провайдеры в `app/`.
   - зафиксируй риски и нарушения конституции (таблица).

7. **Сохранить результат** в `plan.md`:
   - заполни шаблон полностью, текст на русском;
   - прилепи ссылки на документацию и список рисков/вопросов.

8. **Синхронизировать контекст агентов**:
   - выполни `{AGENT_SCRIPT}` с `__AGENT__ = roo` после записи плана;
   - убедись, что `.roo/` содержит обновлённые данные о стеке.

9. **Отчёт**:
   - путь к `plan.md` и созданным артефактам (`research.md`, `data-model.md`, …);
   - список ссылок из context7;
   - открытые вопросы/риски.

---

## Нельзя

- Изменять файлы вне каталога фичи.
- Игнорировать конституцию и требования стека (TypeScript strict, Mantine, отсутствие Tailwind).
- Оминать запросы к context7 при наличии ключа (ошибку нужно явно отметить).
