---
title: Component API Specification (Template)
---

Guidelines
- Keep props explicit and serializable; avoid passing whole objects when IDs suffice.
- Document default values and whether the prop is required.
- Embrace unidirectional data flow; surface events with clear payloads.

Example: Selector component

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `options` | `Array<{ id: string; label: string; value: string }>` | Yes | `[]` | Available options |
| `value` | `string` | No | `""` | Currently selected `value` |
| `disabled` | `boolean` | No | `false` | Disable interactions |
| `onChange` | `(value: string) => void` | Yes | `() => {}` | Fired when selection changes |

Example: ResultCard component

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | Yes | — | Main heading |
| `summary` | `string` | No | `""` | Short description |
| `data` | `Record<string, string | number>` | No | `{}` | Key-value pairs to render |
| `variant` | `'success' | 'warning' | 'danger' | 'info'` | No | `'info'` | Visual treatment |

Events (example)

| Event | Payload | Description |
|-------|---------|-------------|
| `select` | `{ id: string; value: string }` | User chooses an item |
| `retry` | `void` | User triggers retry action |

