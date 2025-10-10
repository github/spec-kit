# План реализации: [FEATURE NAME]

**Ветка**: `[###-feature-name]` | **Дата**: [DATE] | **Спецификация**: [link]  
**Артефакт**: `/specs/[###-feature-name]/spec.md`  
**Исполнитель**: Roo Code (перед стартом перечитай `.specify/memory/constitution.md`).

---

## Резюме

[Кратко опиши цель фичи, основные ограничения и ожидаемый результат. Укажи, что стек: Vite + React + TypeScript + Mantine + Zustand + i18next.]

---

## Технический контекст

- **Бандлер и компиляция**: Vite + SWC, TypeScript `"strict": true`, `"noUncheckedIndexedAccess": true`.
- **UI**: Mantine 7+ (`@mantine/core`, `@mantine/hooks`, `@mantine/form`, `@mantine/modals`), Emotion.
- **State**: Zustand (по умолчанию) или Redux Toolkit (если требуется).
- **Маршрутизация**: React Router v6.30+.
- **Формы**: `@mantine/form`.
- **i18n**: `i18next`, `react-i18next`.
- **Нефункциональные цели**: перформанс, a11y (ARIA), минимальное число зависимостей, CI (lint/typecheck/build).
- **Запрещено**: Tailwind, сторонние CSS-фреймворки, CSS-in-JS вне Mantine Emotion.

---

## Проверка конституции

*Проверить до Phase 0 и после итогового дизайна.*

- Соблюдается ли FSD-структура и стек?
- Подготовлен ли Mantine theme, глобальные провайдеры, алиасы?
- Учтены ли требования TypeScript strict, ESLint + Prettier, Conventional Commits?
- Запланированы ли ADR и документация?

Зафиксируй нарушения, причину и план устранения.

---

## Структура артефактов

### Каталог фичи

```
specs/[###-feature-name]/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Исходный код

```
src/
├── app/             # providers, routing, MantineProvider, ErrorBoundary
├── shared/          # ui, lib, api, config, types, assets
├── entities/        # доменные модели (User, Session…)
├── features/        # пользовательские действия (auth/login, theme/toggle…)
├── widgets/         # композиции из entities + features
├── pages/           # маршрутизируемые страницы
└── processes/       # (опционально) сквозные потоки

docs/                # архитектура, ADR, roadmap, changelog
```

**Отклонения**: [Если структура отличается — обоснуй].

---

## Фазы

1. **Phase 0 — Research**
   - Закрыть `NEEDS CLARIFICATION`, оформить `research.md`.
   - Сбор ссылок из context7 по Vite, React, TypeScript, Mantine, React Router, Zustand/RTK.
   - Формирование ADR для ключевых решений.

2. **Phase 1 — Design**
   - Настройка `vite.config.ts`, `tsconfig.*`, ESLint, Prettier, Vitest, GitHub Actions.
   - Описание Mantine theme (`shared/config/theme.ts`), UI-обёртки (`shared/ui`).
   - Настройка провайдеров (MantineProvider, Router, i18n, Zustand).
   - Обновление `quickstart.md`, ADR, roadmap.

3. **Phase 2 — Tasks**
   - Генерация `tasks.md` с фазами и зависимостями.
   - Контроль DoD: TypeScript, ESLint, Prettier, CI, docs.
   - Подготовка к sequential-thinking (Analyze → Plan → Do → Verify → Log).

4. **Phase 3 — Implementation**
   - Итеративная реализация user story (P1 → …).
   - Маленькие коммиты, Conventional Commits, обновление docs.
   - Финальная Verify (lint/typecheck/build/preview/tests).

---

## Контроль сложности и рисков

| Нарушение / риск | Причина | План снижения | Пункт конституции |
|------------------|---------|---------------|-------------------|
| … | … | … | … |

---

## План тестирования (Verify)

- `npm run lint`, `npm run typecheck`, `npm run build`, `npm run preview`.
- Vitest + Testing Library — smoke-кейсы критичных фич.
- Проверка a11y (Mantine, aria-*).
- Обновление docs (architecture, ADR, changelog).

---

## Источники и ссылки

- context7:
  - Vite — [ID / ссылка]
  - React — [ID / ссылка]
  - TypeScript — [ID / ссылка]
  - Mantine — [ID / ссылка]
  - React Router — [ID / ссылка]
  - Zustand/Redux Toolkit — [ID / ссылка]
- Дополнительные материалы: […]
- Открытые вопросы: [что требуется подтверждения].
