# SpecKit: Global Agent Memory Integration

> **Extension for SpecKit**
> **Version**: 0.1.0
> **Status**: Alpha

---

## Что это?

Расширение SpecKit, добавляющее глобальную систему памяти AI агентов с автоматическим накоплением знаний, векторным поиском и умным определением scope.

---

## Ключевые отличия от оригинального SpecKit

| Feature | Оригинальный SpecKit | С этим расширением |
|---------|---------------------|---------------------|
| **Спецификация** | Создаёт спецификацию проекта | Создаёт спецификацию + учитывает накопленную память |
| **Планирование** | Генерирует план реализации | Генерирует план + использует прошлые архитектурные решения |
| **Задачи** | Декомпозирует на задачи | Декомпозирует + использует накопленные паттерны |
| **Уточнение** | Задаёт вопросы по спецификации | Задаёт вопросы + проверяет прошлые решения |

---

## Возможности

### 4-уровневая система памяти

1. **Контекстная**: Текущая сессия (теряется при обрыве)
2. **Файловая**: Markdown файлы по проектам (lessons.md, patterns.md, architecture.md)
3. **Векторная**: Семантический поиск (опционально, через Ollama)
4. **Identity**: AGENTS.md, SOUL.md, USER.md, MEMORY.md

### Memory-Agent Workflow

```
Before Task → Headers-First чтение (~80-120 токенов)
When Stuck  → Векторный поиск + глубокое погружение
After Task   → Авто-документация с AI-классификацией
```

### Graceful Degradation

Система работает при недоступности внешних зависимостей:
- Ollama недоступен → Файловая память работает
- agent-memory-mcp недоступен → Grep поиск
- SkillsMP недоступен → Система работает без поиска скиллов

---

## Быстрый старт

### Установка

```bash
cd F:/IdeaProjects/spec-kit
bash scripts/memory/install_global.sh
```

### Проверка

```bash
bash scripts/memory/verify_install.sh
```

### Использование

```python
from specify_cli.memory import MemoryOrchestrator, FileMemoryManager

# Создаём orchestrator
orchestrator = MemoryOrchestrator(project_id="my-project")

# Headers-First чтение (~80-120 токенов)
headers = orchestrator.get_headers_first(limit=10)

# Умный поиск (авто-dеление scope)
results = orchestrator.search("как исправить ошибку с JWT")
```

---

## Документация

- [INSTALL_MEMORY.md](../docs/INSTALL_MEMORY.md) - Полная инструкция по установке
- [spec.md](specs/001-global-agent-memory/spec.md) - Спецификация функционала
- [README.md](src/specify_cli/memory/README.md) - Документация модулей

---

## Оригинальный SpecKit

Полная документация: https://github.com/github/spec-kit

---

**Разработано**: 2025-03-10
**Spec**: [001-global-agent-memory](specs/001-global-agent-memory/spec.md)
