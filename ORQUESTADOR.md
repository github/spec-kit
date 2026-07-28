# Sistema Orquestador Multi-Modelo

> Definición global del sistema de tomi. Documento vivo — se actualiza a medida que se define.

## Idea global

El sistema es un **orquestador con asignación por complejidad de tarea**.

1. **Todo comando entra por el modelo principal** — es la única puerta de entrada.
2. **El principal NUNCA resuelve.** Su único rol es de comunicador: recibe, clasifica, deriva y devuelve la respuesta.
3. **Un clasificador de complejidad** evalúa cada tarea y determina su nivel.
4. **La asignación del modelo es dinámica por complejidad** — NO hay modelos fijos por sector/dominio.
5. **El modelo asignado resuelve**, y la respuesta vuelve al usuario a través del comunicador.
6. **El concepto es portable**: funciona en cualquier entorno/CLI. El "qué" es fijo; el "cómo" depende de lo que cada CLI soporte.

## Flujo

```
comando → comunicador principal → clasificador de complejidad
                                        │
                    ┌── nivel 1 ────────┼──→ modelo ?
                    ├── nivel 2 ────────┼──→ modelo ?
                    ├── nivel 3 ────────┼──→ modelo ?
                    ├── nivel 4 ────────┼──→ modelo ?
                    └── nivel 5 ────────┴──→ modelo ?
```

## Complejidad

- **5 niveles** de complejidad. **Nivel 3 = el más usado** (ahí cae la mayoría del trabajo real). Nivel 1 = tareas triviales y rápidas. Nivel 5 = lo más complejo, excepcional, casi no se usa.

| Nivel | Nombre | Criterio | Ejemplos |
|---|---|---|---|
| 1 | Trivial | Preguntas directas, lookups, comandos de una línea, formato | "¿qué hace este flag?", "listame los archivos" |
| 2 | Simple | Cambios acotados en un solo archivo, bugs obvios con error claro | "arreglá este typo", "corré los tests" |
| 3 | Moderada | Lógica en varios archivos, features chicas, refactors localizados | "agregá este endpoint", "escribí tests de X" |
| 4 | Compleja | Decisiones de diseño, features grandes, debugging sin causa obvia | "encontrá por qué es lento", "migrá este sistema" |
| 5 | Crítica | Arquitectura completa, decisiones irreversibles, seguridad | "diseñá el sistema de cero", "reestructurá el repo" |

## Método de clasificación de modelos

**No se guarda ninguna tabla estática.** Los niveles se recalculan siempre con este método (implementado en `orquestador_clasificar.py`).

### Fuentes de datos (3 llamadas JSON, sin navegador ni scraping)

| Dato | Endpoint | Campo |
|---|---|---|
| Precio + contexto | `openrouter.ai/api/v1/models` | `pricing.prompt/completion`, `context_length` |
| Inteligencia | `openrouter.ai/api/frontend/v1/rankings/benchmarks` | `data.aaData.percentilesBySlug[slug].intelligence` (percentil 0-100 de Artificial Analysis) |
| Velocidad | `openrouter.ai/api/frontend/v1/rankings/performance` | `p50_throughput` (tok/s), `p50_latency` (ms) |

Lo que NO funciona (descartado): la API `/endpoints` tiene los campos de velocidad vacíos; la página `/rankings` es JS puro.

### Pasos

1. **Listar modelos del CLI** — `opencode models` (o equivalente del CLI elegido).
2. **Traer los 3 JSON** de arriba.
3. **Matchear** modelo del CLI ↔ slug OpenRouter:
   - Normalizar: quitar prefijo de proveedor, sufijos `-review`/`-highspeed`/`-thinking`/`-free`, fechas `-20251001`, tilde `~`.
   - Las variantes heredan los datos del modelo base.
   - Alias manuales cuando el slug difiere (ej: `fable-5`→`claude-5-fable-...`, `haiku-4.5`→`claude-4.5-haiku-...`, `kimi-latest`→`kimi-k3`).
4. **Calcular por modelo**:
   - `intel` = percentil de inteligencia (0-100). Es **relativo**: baja cuando salen modelos nuevos mejores.
   - `velocidad` = mejor `p50_throughput` entre proveedores.
   - `precio blend` = `0.75 × $entrada + 0.25 × $salida` (uso agéntico: domina la entrada).
   - `costo-beneficio` = `intel ÷ max(blend, 0.05)`.
5. **Asignar nivel por benchmark** (la capacidad define el techo de lo que puede resolver):
   - N5 (crítica): intel ≥ 94
   - N4 (compleja): 85–93
   - N3 (moderada, la más usada): 60–84
   - N2 (simple): 40–59
   - N1 (trivial): < 40
   - **Sin benchmark** → respaldo por datos reales: precio ≤ $0.30/M → N1; rápido (>100 tok/s) y < $1/M → N2; si no, N3.
6. **Elegir el modelo de cada nivel**: el de mejor costo-beneficio, prefiriendo contexto ~1M. Ojo: C/B alto con bench bajo no sirve (barato pero no resuelve).

### Salida

Mapa `nivel → lista ordenada de modelos` (primario + alternativas) para ese CLI. Válido hasta que cambien los modelos del CLI o salgan modelos nuevos (el percentil es relativo) → re-correr el script.

### Cadena de respaldo (fallback)

1. Todo trabajo empieza con el **primer modelo** de la lista de su nivel.
2. Si el modelo **no conecta o no está disponible** (rate limit, cuota agotada, caída del proveedor, contexto insuficiente) → seguir con el **siguiente de la lista**, pasándole el estado de la tarea (progreso, archivos tocados, tests, trabajo restante) para que **continúe** y no arranque de cero.
3. Nunca reintentar el mismo modelo fallido en loop. Si la lista se agota → parar y reportar todos los intentos y fallos.
4. El fallback es **solo por disponibilidad**: errores de código/tests se diagnostican normal, no se tapan cambiando de modelo.
5. Las alternativas deben ser de **proveedores distintos** cuando sea posible, para que agotar una cuota no tumbe toda la cadena.
6. Si el siguiente de la lista es `manual` → pausar con instrucciones exactas para cambiar de modelo.

- **Quién clasifica en runtime: el propio modelo comunicador.** No hay pieza separada — el principal estima el nivel (1-5) de cada tarea/paso usando la tabla de criterios, y deriva. Clasificar es parte de su rol de comunicador; lo que sigue prohibido es *resolver*.

## Arquitectura en spec-kit (13 comandos)

El orquestador se reparte en dos piezas:

**1. `models` — el comando especial (configuración)**
- Detecta el CLI/runtime que hospeda la conversación y descubre sus modelos disponibles.
- Clasifica los modelos con el **método universal** (5 niveles + datos OpenRouter) — capa 1.
- Materializa la incorporación según el CLI — **capa 2, distinta en cada CLI**: subagentes con modelo fijado (OpenCode), agentes nombrados (Claude Code), config nativa (Codex), modo manual (IDEs).
- Escribe `models.json`: mapa `nivel → modelo` + ejecutor por modelo (`native_subagent` / `current_session` / `manual`).

**2. Los otros 12 comandos — llevan el orquestador incorporado**

Ningún comando ejecuta todo con el modelo actual. Cada comando, al llegar a un paso de trabajo:
1. Clasifica la complejidad del paso (1-5).
2. Consulta `models.json` para ver qué modelo/agente corresponde.
3. Deriva el paso al agente de ese nivel (o lo ejecuta directo si coincide).

Un mismo comando puede mezclar niveles: pasos triviales → N1, arquitectura → N5. **El orquestador viaja dentro de cada comando**, no es un servicio externo.

## Restricciones de implementación

- **La unidad de delegación no es el modelo, es el agente.** Un modelo no puede llamar a otro modelo directamente — se invoca al agente que tiene ese modelo configurado.
- **El mecanismo concreto depende del CLI** elegido al inicializar (ej: en opencode → subagentes, cada uno con su modelo).
- Al hacer `init` se especifica con qué CLI se trabaja, y ahí el orquestador toma forma concreta.

## Ejemplo de materialización (opencode)

```
agente principal (orquestador)
  modelo: principal
  regla: NO resolver, solo clasificar complejidad y delegar

subagentes (uno por nivel de complejidad)
  nivel-1 → modelo ?
  nivel-2 → modelo ?
  nivel-3 → modelo ?
  nivel-4 → modelo ?
  nivel-5 → modelo ?
```
