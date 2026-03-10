# Context Usage Analysis (T077)

## Headers-First Reading Performance

### Lightweight Mode (Always Read)
- **Scope**: Titles + one-liners only
- **Token Usage**: ~130-280 tokens total
  - lessons.md: ~50-100 tokens
  - patterns.md: ~50-100 tokens
  - architecture.md: ~30-80 tokens
- **Context Impact**: ~1-2% of 128K window

### Benefits
1. **Minimal Overhead**: Only 1-2% of context window
2. **Navigation**: Agent sees memory structure
3. **Targeted Loading**: Deep reads only when needed
4. **Scalability**: Works with large memory bases

### Deep Read Mode (On Demand)
- **Scope**: Full entry content
- **Token Usage**: ~500-2000 tokens per entry
- **Trigger**: When specific entry is relevant

## Recommendations
- Always use headers-first for initial context
- Deep read only for relevant entries
- This approach is production-ready