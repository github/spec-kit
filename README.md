[**Русский**](#ru) | [English](#en)

---

<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>Spec Kit Memory System</h1>
    <h3><em>4-уровневая архитектура памяти для AI-агентов</em></h3>
</div>

<p align="center">
    <strong>Глобальная интеграция памяти агентов для автоматического накопления знаний между проектами.</strong>
</p>

---

## Обзор (Overview) {#ru}

SpecKit Memory System - это комплексная 4-уровневая архитектура памяти, разработанная для AI-агентов, работающих с фреймворком SpecKit spec-driven development. Она позволяет агентам автоматически накапливать, организовывать и извлекать знания из всех проектов.

### Ключевые возможности

- **4-уровневая архитектура памяти**: Файловая, Векторная, Контекстная и Идентификационная
- **Чтение заголовков**: Эффективная загрузка контекста с накладными расходами всего ~1-2%
- **Обучение между проектами**: Обмен паттернами и уроками между всеми проектами
- **Умный поиск**: Автоматическое определение области (локально/глобально) с семантическим поиском
- **Интеграция SkillsMP**: Доступ к 425K+ навыков агентов из сообщества
- **Создание агентов**: Автоматическое создание агентов на основе изученных паттернов
- **Автосохранение и резервирование**: Никогда не потеряете важные открытия

---

## Установка

### Через AI-помощника

Попросите вашего AI-помощника выполнить установку:

```
Выполни инструкции по установке из specs/001-global-agent-memory/INSTALL.md
```

AI-помощник:
- Создаст структуру директорий `~/.claude/memory/`
- Настроит символическую ссылку SpecKit
- Сконфигурирует шаблоны проектов
- Опционально установит Ollama для векторного поиска

### Ручная настройка

```bash
# Создание директорий памяти
mkdir -p ~/.claude/memory/projects

# Создание символической ссылки SpecKit (укажите правильный путь)
ln -s /path/to/spec-kit ~/.claude/spec-kit
```

См. [INSTALL.md](specs/001-global-agent-memory/INSTALL.md) для полных AI-executable инструкций по установке.

---

## Быстрый старт

### 1. Инициализация памяти для проекта

Попросите AI-помощника:

```
Инициализируй SpecKit Memory System для этого проекта согласно specs/001-global-agent-memory/INSTALL.md
```

Или вручную:

```bash
cd ваш-проект
mkdir -p .spec-kit/memory
```

### 2. Использование памяти в коде

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

# Инициализация системы памяти
memory = MemoryOrchestrator()

# Сохранение того, что вы узнали
memory.add_lesson(
    title="Проблема с истечением JWT токена",
    problem="Токены доступа истекали через 1 час, прерывая работу пользователей",
    solution="Увеличено до 24 часов и добавлена ротация refresh токенов"
)

# Поиск прошлых решений
results = memory.search("истечение срока действия аутентификации")
for result in results:
    print(f"{result['title']}: {result['summary']}")
```

### 3. Создание паттернов из открытий

```python
memory.add_pattern(
    title="Паттерн Refresh токена",
    description="Длительные пользовательские сессии с короткими access токенами",
    when="Аутентификация требует сессии длиннее 1 часа",
    code="""
def create_access_token(user_id):
    return jwt.encode({'user_id': user_id, 'exp': time() + 86400}, secret)

def create_refresh_token(user_id):
    return jwt.encode({'user_id': user_id, 'exp': time() + 2592000}, secret)
"""
)
```

---

## 4-уровневая архитектура памяти

### Уровень 1: Файловая память

Постоянное хранилище в markdown файлах:
- `lessons.md` - Уроки из ошибок и исправлений
- `patterns.md` - Переиспользуемые решения и паттерны кода
- `architecture.md` - Технические решения и компромиссы
- `projects-log.md` - Вехи и история проектов

### Уровень 2: Векторная память

Семантический поиск с Ollama:
- Автоматическая генерация вложений
- RAG индексация для быстрого извлечения
- Graceful degradation без Ollama

### Уровень 3: Контекстная память

Рабочая память для текущих задач:
- Чтение заголовков (~1-2% накладных расходов контекста)
- Целевое глубокое чтение при необходимости
- Контекст специфичный для сессии

### Уровень 4: Идентификационная память

Долгосрочное обучение и предпочтения:
- Паттерны программирования пользователя
- Предпочтения технологического стека
- История командной работы

---

## Файлы памяти

### lessons.md

Запись того, что вы узнали из ошибок:

```markdown
## Истечение JWT токена

**Дата**: 2026-03-10
**Проблема**: Токены истекали через 1 час, прерывая пользователей
**Решение**: Использовать refresh токены, увеличить access токен до 24ч
**Влияние**: Снижено количество обращений в поддержку на 80%
```

### patterns.md

Документирование переиспользуемых решений:

```markdown
## Паттерн Refresh токена

**Когда**: Аутентификация требует длительные сессии
**Как**: Короткий access токен + долгоживущий refresh токен
**Технологический стек**: JWT, Redis для хранения токенов
**Код**: [Смотреть реализацию]
```

### architecture.md

Запись технических решений:

```markdown
## JWT против Session-Based аутентификации

**Решение**: JWT с refresh токенами
**Контекст**: Мобильное приложение + веб-панель
**Обоснование**: Без состояния, масштабируемо, мобильное-дружественно
**Компромисс**: Более сложная отзыва токенов
**Дата**: 2026-03-10
```

---

## Интеграция с командами SpecKit

Память автоматически интегрируется с командами разработки SpecKit:

```bash
# /speckit.specify - Получает релевантный контекст памяти перед созданием спецификации
/speckit.specify Создать систему пользовательской аутентификации

# /speckit.plan - Извлекает архитектурные решения для планирования
/speckit.plan Использовать Next.js с PostgreSQL

# /speckit.tasks - Предлагает паттерны из памяти
/speckit.tasks

# /speckit.clarify - Контекст между проектами для уточнения
/speckit.clarify

# /speckit.features - Быстрая генерация функций с памятью
/speckit.features
```

---

## Умный поиск

### Автоматическое определение области

```python
from specify_cli.memory.smart_search import SmartSearchEngine

engine = SmartSearchEngine()

# Автоматически ищет сначала локально, затем глобально
results = engine.search("истечение срока действия аутентификации")
# Возвращает: уроки, паттерны, архитектурные записи
```

### Поиск между проектами

```python
# Поиск по всем вашим проектам
results = memory.search("аутентификация", scope="global")
```

---

## Интеграция SkillsMP

Доступ к 425K+ навыков агентов из сообщества:

```python
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

skillsmp = SkillsMPIntegration()

# Поиск существующих агентов/навыков
results = skillsmp.search_skills("миграция базы данных")

# Использование решений сообщества вместо создания с нуля
for skill in results:
    print(f"{skill['title']}: {skill['description']}")
```

---

## Создание агентов

Автоматическое создание агентов на основе изученных паттернов:

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Поиск перед созданием
results = workflow.search_agents("фронтенд разработка")

# Создание нового агента из требований
agent = workflow.create_agent_from_requirements(
    agent_name="frontend-dev",
    requirements={
        "role": "Frontend Разработчик",
        "personality": "Творческий и внимательный к деталям",
        "skills": ["React", "TypeScript", "Tailwind CSS"]
    }
)
```

---

## Производительность

| Метрика | Значение |
|---------|----------|
| Накладные расходы контекста (заголовки) | ~1-2% (130-280 токенов) |
| Время поиска (локально) | <200мс |
| Время поиска (векторно) | <1с |
| Макс. записей на проект | 1000+ |
| Размер резервной копии | ~10КБ на запись |

---

## Документация

- **[Краткое руководство](docs/memory/quickstart.md)** - Начните работу за 5 минут
- **[Полная документация](docs/memory/README.md)** - Полный справочник API
- **[Руководство по установке](specs/001-global-agent-memory/INSTALL.md)** - AI-executable инструкции по установке
- **[Руководство по миграции](docs/memory/migration_guide.md)** - Миграция существующих проектов
- **[Настройка производительности](docs/memory/performance_tuning.md)** - Оптимизация для вашей конфигурации
- **[Примечания к выпуску](docs/memory/RELEASE_NOTES.md)** - Что нового

---

## Статус проекта

**Версия**: 0.1.0

**Реализация**: 92 задачи в 10 фазах завершено

| Фаза | Статус | Задачи |
|------|--------|--------|
| Фаза 3: Накопление памяти | ✅ Завершено | 12/12 |
| Фаза 4: Глобальная установка | ✅ Завершено | 14/14 |
| Фаза 5: Векторная память | ✅ Завершено | 10/10 |
| Фаза 6: Поиск SkillsMP | ✅ Завершено | 9/9 |
| Фаза 7: Создание агентов | ✅ Завершено | 8/8 |
| Фаза 8: Интеграция SpecKit | ✅ Завершено | 9/9 |
| Фаза 9: Полировка и выпуск | ✅ Завершено | 11/11 |

---

## Конфигурация

Конфигурация памяти хранится в `~/.claude/spec-kit/config/memory.json`:

```json
{
  "enabled": true,
  "auto_save": true,
  "vector_search": {
    "enabled": true,
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "skillsmp": {
    "enabled": true,
    "api_key": "ваш-ключ-здесь"
  }
}
```

---

## Лицензия

Этот проект расширяет [SpecKit](https://github.com/github/spec-kit), который распространяется по лицензии MIT.

---

## Поддержка

По проблемам и вопросам:
- Откройте issue в репозитории
- Проверьте [Решение проблем](docs/memory/README.md#troubleshooting)
- Ознакомьтесь [FAQ](docs/memory/README.md#faq)

---

---

<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>Spec Kit Memory System</h1>
    <h3><em>4-Level Memory Architecture for AI Agents</em></h3>
</div>

<p align="center">
    <strong>Global agent memory integration that enables automatic knowledge accumulation across projects.</strong>
</p>

---

## Overview {#en}

SpecKit Memory System is a comprehensive 4-level memory architecture designed for AI agents working with the SpecKit spec-driven development framework. It enables agents to automatically accumulate, organize, and retrieve knowledge across all projects.

### Key Features

- **4-Level Memory Architecture**: File, Vector, Context, and Identity layers
- **Headers-First Reading**: Efficient context loading with only ~1-2% overhead
- **Cross-Project Learning**: Share patterns and lessons across all your projects
- **Smart Search**: Automatic scope detection (local/global) with semantic search
- **SkillsMP Integration**: Access 425K+ agent skills from the community
- **Agent Creation**: Build agents automatically using learned patterns
- **Auto-Save & Backup**: Never lose important discoveries

---

## Installation

### Via AI Assistant

Ask your AI assistant to execute the installation:

```
Execute the installation instructions from specs/001-global-agent-memory/INSTALL.md
```

The AI assistant will:
- Create `~/.claude/memory/` directory structure
- Set up SpecKit symlink
- Configure project templates
- Optionally install Ollama for vector search

### Manual Setup

```bash
# Create memory directories
mkdir -p ~/.claude/memory/projects

# Create SpecKit symlink (adjust path as needed)
ln -s /path/to/spec-kit ~/.claude/spec-kit
```

See [INSTALL.md](specs/001-global-agent-memory/INSTALL.md) for complete AI-executable installation instructions.

---

## Quickstart

### 1. Initialize Memory for Your Project

Ask your AI assistant:

```
Initialize SpecKit Memory System for this project following specs/001-global-agent-memory/INSTALL.md
```

Or manually:

```bash
cd your-project
mkdir -p .spec-kit/memory
```

### 2. Use Memory in Your Code

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

# Initialize memory system
memory = MemoryOrchestrator()

# Save what you learned
memory.add_lesson(
    title="JWT Token Expiration Issue",
    problem="Access tokens expired after 1 hour, disrupting users",
    solution="Increased to 24 hours and added refresh token rotation"
)

# Search for past solutions
results = memory.search("authentication timeout")
for result in results:
    print(f"{result['title']}: {result['summary']}")
```

### 3. Create Patterns from Discoveries

```python
memory.add_pattern(
    title="Refresh Token Pattern",
    description="Handle long user sessions with short access tokens",
    when="Authentication requires sessions longer than 1 hour",
    code="""
def create_access_token(user_id):
    return jwt.encode({'user_id': user_id, 'exp': time() + 86400}, secret)

def create_refresh_token(user_id):
    return jwt.encode({'user_id': user_id, 'exp': time() + 2592000}, secret)
"""
)
```

---

## 4-Level Memory Architecture

### Level 1: File Memory

Persistent storage in markdown files:
- `lessons.md` - Learnings from mistakes and fixes
- `patterns.md` - Reusable solutions and code patterns
- `architecture.md` - Technical decisions and trade-offs
- `projects-log.md` - Project milestones and history

### Level 2: Vector Memory

Semantic search with Ollama:
- Automatic embeddings generation
- RAG indexing for fast retrieval
- Graceful degradation without Ollama

### Level 3: Context Memory

Working memory for current tasks:
- Headers-first reading (~1-2% context overhead)
- Targeted deep reads when needed
- Session-specific context

### Level 4: Identity Memory

Long-term learning and preferences:
- User coding patterns
- Tech stack preferences
- Team collaboration history

---

## Memory Files

### lessons.md

Record what you learned from mistakes:

```markdown
## JWT Token Expiration

**Date**: 2026-03-10
**Problem**: Tokens expired after 1 hour, disrupting users
**Solution**: Use refresh tokens, increase access token to 24h
**Impact**: Reduced support tickets by 80%
```

### patterns.md

Document reusable solutions:

```markdown
## Refresh Token Pattern

**When**: Authentication requires long sessions
**How**: Short access token + long-lived refresh token
**Tech Stack**: JWT, Redis for token storage
**Code**: [See implementation]
```

### architecture.md

Record technical decisions:

```markdown
## JWT vs Session-Based Auth

**Decision**: JWT with refresh tokens
**Context**: Mobile app + web dashboard
**Rationale**: Stateless, scalable, mobile-friendly
**Trade-off**: More complex token revocation
**Date**: 2026-03-10
```

---

## Integration with SpecKit Commands

Memory automatically integrates with SpecKit development commands:

```bash
# /speckit.specify - Gets relevant memory context before creating spec
/speckit.specify Build a user authentication system

# /speckit.plan - Retrieves architecture decisions for planning
/speckit.plan Use Next.js with PostgreSQL

# /speckit.tasks - Suggests patterns from memory
/speckit.tasks

# /speckit.clarify - Cross-project context for clarification
/speckit.clarify

# /speckit.features - Quick feature generation with memory
/speckit.features
```

---

## Smart Search

### Automatic Scope Detection

```python
from specify_cli.memory.smart_search import SmartSearchEngine

engine = SmartSearchEngine()

# Automatically searches local first, then global
results = engine.search("authentication timeout")
# Returns: lessons, patterns, architecture entries
```

### Cross-Project Search

```python
# Search across all your projects
results = memory.search("authentication", scope="global")
```

---

## SkillsMP Integration

Access 425K+ agent skills from the community:

```python
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

skillsmp = SkillsMPIntegration()

# Search for existing agents/skills
results = skillsmp.search_skills("database migration")

# Use community solutions instead of building from scratch
for skill in results:
    print(f"{skill['title']}: {skill['description']}")
```

---

## Agent Creation

Create agents automatically using learned patterns:

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Search before creating
results = workflow.search_agents("frontend development")

# Create new agent from requirements
agent = workflow.create_agent_from_requirements(
    agent_name="frontend-dev",
    requirements={
        "role": "Frontend Developer",
        "personality": "Creative and detail-oriented",
        "skills": ["React", "TypeScript", "Tailwind CSS"]
    }
)
```

---

## Performance

| Metric | Value |
|--------|-------|
| Context overhead (headers) | ~1-2% (130-280 tokens) |
| Search time (local) | <200ms |
| Search time (vector) | <1s |
| Max entries per project | 1000+ |
| Backup size | ~10KB per entry |

---

## Documentation

- **[Quickstart Guide](docs/memory/quickstart.md)** - Get started in 5 minutes
- **[Full Documentation](docs/memory/README.md)** - Complete API reference
- **[Installation Guide](specs/001-global-agent-memory/INSTALL.md)** - AI-executable installation instructions
- **[Migration Guide](docs/memory/migration_guide.md)** - Migrate existing projects
- **[Performance Tuning](docs/memory/performance_tuning.md)** - Optimize for your setup
- **[Release Notes](docs/memory/RELEASE_NOTES.md)** - What's new

---

## Project Status

**Version**: 0.1.0

**Implementation**: 92 tasks across 10 phases complete

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 3: Memory Accumulation | ✅ Complete | 12/12 |
| Phase 4: Global Installation | ✅ Complete | 14/14 |
| Phase 5: Vector Memory | ✅ Complete | 10/10 |
| Phase 6: SkillsMP Search | ✅ Complete | 9/9 |
| Phase 7: Agent Creation | ✅ Complete | 8/8 |
| Phase 8: SpecKit Integration | ✅ Complete | 9/9 |
| Phase 9: Polish & Release | ✅ Complete | 11/11 |

---

## Configuration

Memory configuration is stored in `~/.claude/spec-kit/config/memory.json`:

```json
{
  "enabled": true,
  "auto_save": true,
  "vector_search": {
    "enabled": true,
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "skillsmp": {
    "enabled": true,
    "api_key": "your-key-here"
  }
}
```

---

## License

This project extends [SpecKit](https://github.com/github/spec-kit) which is licensed under the MIT license.

---

## Support

For issues and questions:
- Open an issue in the repository
- Check [Troubleshooting](docs/memory/README.md#troubleshooting)
- Review [FAQ](docs/memory/README.md#faq)
