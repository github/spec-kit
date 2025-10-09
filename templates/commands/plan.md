---
description: Сформировать план реализации, совместимый с архитектурой FSD + Vite + React + Tailwind + shadcn/ui.
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
   - `FEATURE_SPEC`, `FEATURE_DIR`, `PLAN_TEMPLATE`, `BRANCH`
   - абсолютные пути ко всем артефактам  
   Ошибка → остановись.

2. **Загрузи исходные данные**:
   - `templates/plan-template.md` — структура плана;
   - `specs/.../spec.md` — требования и истории;
   - `.specify/memory/constitution.md` — обязательные правила.

3. **Получить свежую документацию через context7**:
   - JSON-RPC `initialize`, затем `tools/list`;
   - для библиотек `tailwindcss`, `vite`, `react`, `shadcn/ui` последовательно:
     1. `tools/call` → `resolve-library-id` (передай название библиотеки);
     2. `tools/call` → `get-library-docs` (укажи ID и тему, например `"структура проекта"`, `"компоненты"`, `"настройка"`);
   - сохрани ссылки/версии в разделе “Источники и ссылки”.  
   Если ключ недействителен — зафиксируй проблему и продолжай с отметкой.

4. **Сформировать технический контекст**:
   - подтвердить стек: Vite + React + Tailwind + shadcn/ui (JavaScript без TypeScript, если не указано иное);
  - описать уровни FSD: `app`, `processes`, `pages`, `widgets`, `features`, `entities`, `shared`;
   - отметить требования к данным, состоянию, внешним API.

5. **Заполнить план по фазам**:
   - Phase 0 — Research (закрываем `NEEDS CLARIFICATION`, фиксируем решения);
   - Phase 1 — Design (описать структуру директорий, конфиги Vite/Tailwind/shadcn, обновить quickstart);
   - Phase 2 — Tasks (логика генерации `tasks.md`, правило “тесты в конце”);
   - Phase 3+ — Implementation/Testing (при необходимости уточни дополнительные шаги).

6. **Обновить структуру проекта**:
   - опиши фактические директории FSD, укажи отклонения и обоснования;
   - выдели риски и сложность (таблица нарушений конституции).

7. **Сохранить результат** в `plan.md`:
   - текст на русском, используй шаблон и заполни все placeholders;
   - приложи ссылки на context7 и нерешённые вопросы.

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
- Игнорировать конституцию и правила стека.
- Пропускать context7, если доступен ключ (ошибку нужно явно отметить).
