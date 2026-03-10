# Global Agent Memory Integration

> **Модуль**: SpecKit Memory Extension
> **Версия**: 0.1.0
> **Статус**: Alpha (Foundation Complete)

---

## Обзор

Расширение SpecKit для глобальной системы памяти AI агентов с автоматическим накоплением знаний, векторным поиском и умным определением scope.

### Возможности

- **4-уровневая система памяти**:
  1. Контекстная (сессия)
  2. Файловая (markdown)
  3. Векторная (опционально, через agent-memory-mcp + Ollama)
  4. Identity (AGENTS.md, SOUL.md, USER.md, MEMORY.md)

- **Memory-Aware Workflow**:
  - Before Task: Headers-First чтение (~80-120 tokens)
  - When Stuck: Векторный поиск + глубокое погружение
  - After Task: Авто-документация с AI-классификацией

- **Graceful Degradation**: Система продолжает работу при недоступности Ollama/agent-memory-mcp

---

## Структура

```
src/specify_cli/memory/
├── __init__.py           # Публичный API
├── orchestrator.py      # Memory Orchestrator (координация)
├── file_manager.py       # File Memory Manager (markdown)
├── agent.py             # Memory-Aware Agent (workflow)
├── classifier.py         # AI Importance Classifier (routing)
├── config.py            # Configuration Manager (backup+merge)
└── logging.py           # Logging с graceful degradation

templates/memory/
├── lessons.md           # Шаблон для уроков
├── patterns.md          # Шаблон для паттернов
├── architecture.md      # Шаблон для архитектуры
└── projects-log.md     # Шаблон для лога задач
```

---

## Быстрый старт

### 1. Инициализация памяти проекта

```python
from specify_cli.memory import MemoryOrchestrator, FileMemoryManager

# Создать orchestrator
orchestrator = MemoryOrchestrator(project_id="my-project")

# Инициализировать файлы памяти
manager = FileMemoryManager(project_id="my-project")
manager.initialize_memory_files()
```

### 2. Memory-Average Workflow

```python
from specify_cli.memory.agent import MemoryAwareAgent

agent = MemoryAwareAgent(project_id="my-project")

# Before Task
headers = agent.before_task()  # ~80-120 tokens

# When Stuck
results = agent.when_stuck("как исправить ошибку с JWT")

# After Task
agent.after_task(
    problem="JWT токен истекает через 15 минут",
    solution="Добавили refresh token flow",
    lessons="Хранить refresh token в httpOnly cookie",
    importance=0.6  # medium → patterns.md
)
```

### 3. AI Классификация

```python
from specify_cli.memory.classifier import AIImportanceClassifier

classifier = AIImportanceClassifier()

result = classifier.calculate_importance(
    "Критическое решение по архитектуре базы данных"
)

# result["score"] = 0.87
# result["routing_target"] = "architecture.md"
```

---

## One-Line Summary Format

Все файлы памяти используют формат заголовков с one-line summary:

```markdown
## Error: JWT - expire через 15 мин, нужен refresh token flow
## Pattern: Repository - отделить бизнес-логику от данных
## Pattern: Middleware Chain - compose вместо nested if
```

Это обеспечивает:
- ✅ Понимание суть из заголовка без чтения
- ✅ Контекст оптимизация (~80-120 tokens)
- ✅ Быстрая навигация по памяти

---

## Graceful Degradation

Система продолжает работать при недоступности внешних зависимостей:

| Зависимость | Недоступна | Поведение |
|-------------|------------|-----------|
| Ollama | ✗ | File-based memory только, warning один раз |
| agent-memory-mcp | ✗ | Grep поиск вместо vector |
| SkillsMP | ✗ | Система работает без поиска скиллов |

**Никаких исключений** - система продолжает работу.

---

## Тестирование

Запуск тестов graceful degradation:

```bash
cd F:/IdeaProjects/spec-kit
pytest tests/memory/test_degradation.py -v
```

---

## Зависимости

```
watchdog>=4.0          # File watching
python-frontmatter>=4.0  # Markdown YAML
requests>=2.31        # HTTP для Ollama
```

Устанавливаются автоматически через pyproject.toml.

---

## Следующие шаги

- [ ] Векторная память интеграция
- [ ] SkillsMP поиск скиллов
- [ ] SpecKit команды интеграция
- [ ] CLI инструменты для управления

---

**Создано**: 2025-03-10
**Спецификация**: [spec.md](../../specs/001-global-agent-memory/spec.md)
