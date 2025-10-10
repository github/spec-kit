# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Core Stack
- Vite + React + TypeScript (strict)
- Mantine 7+ (@mantine/core, @mantine/hooks, @mantine/form, @mantine/modals)
- State: Zustand (по умолчанию) или Redux Toolkit при необходимости
- Routing: React Router v6.30+
- i18n: i18next + react-i18next
- Tests: Vitest + @testing-library/react (финальная фаза)
- **Запрещено**: Tailwind, сторонние CSS-фреймворки, CSS-in-JS вне Mantine Emotion

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure (FSD)
`
[ACTUAL STRUCTURE FROM PLANS]
`

## Commands & Scripts
- npm run lint / typecheck / build / preview
- npm run test (Vitest)
- GitHub Actions: lint + typecheck + build
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style & Quality Gates
- ESLint (typescript-eslint, import, react) + Prettier
- tsconfig strict, noUncheckedIndexedAccess
- Conventional Commits, ADR для новых зависимостей
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
