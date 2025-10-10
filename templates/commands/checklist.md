---
description: Сформировать контрольный чеклист перед `/speckit.implement` или перед релизом.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Пользовательский ввод

```text
$ARGUMENTS
```

Если нужно конкретный тип чеклиста (QA, UX, Release) — укажи в запросе.

---

## Алгоритм

1. Запусти `{SCRIPT}` и определи `FEATURE_DIR`, доступные артефакты (`spec.md`, `plan.md`, `tasks.md`, `research.md`, `quickstart.md`).
2. Выбери тип чеклиста:
   - если пользователь указал — используй его;
   - иначе `release-ready`.
3. На основе `templates/checklist-template.md` создай файл `FEATURE_DIR/checklists/<type>.md`, заполнив разделы:
   - **Артефакты** — актуальность спецификации, плана, задач, ADR, roadmap.
   - **Архитектура/код** — соблюдение FSD-структуры, TypeScript strict, Mantine theme, отсутствие Tailwind.
   - **Тесты и CI** — наличие скриптов `lint`, `typecheck`, `build`, `vitest`, GitHub Actions.
   - **Документация и риски** — ADR, changelog, незакрытые `NEEDS CLARIFICATION`.
4. Для каждой категории добавь 3–5 пунктов вида `- [ ] ...`. Если пункт уже выполнен — `- [x] ...`.
5. Сохранённый файл должен содержать ссылку на `spec.md` и краткое описание цели.

---

## Отчёт

Укажи:
1. Путь к созданному чеклисту.
2. Количество пунктов и сколько закрыто `[x]`.
3. Какие пункты остаются открытыми и кто ответственен.

---

## Нельзя

- Изменять `spec.md`, `plan.md`, `tasks.md`.
- Добавлять проверки, противоречащие стеку (например, требования к Tailwind).
- Оставлять чеклист без привязки к `spec.md` или без ясной цели.
