# Nivel 5 — Estado semántico

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-5--estado-semántico).  
> Nivel anterior: [level4.md](level4.md) · Índice: [levels.md](levels.md)

**Estado:** spec en revisión · sin implementar

## Objetivo

Mantener un **estado semántico persistente** entre turnos de conversación o sesiones de agente, de modo que al LLM se le envíe una **vista materializada** del estado actual (y opcionalmente un diff reciente), no el historial completo ni todo el contexto acumulado.

Analogía Git:

| Concepto Git | Equivalente N5 |
|--------------|----------------|
| Repositorio | **State Store** |
| Commit | Snapshot del grafo/estado tras un turno |
| Working tree | Estado pendiente de consolidar |
| Diff | Delta desde el último snapshot enviado al LLM |
| Checkout | **StateView** serializada para el modelo |

## Naturaleza del procesado

| Aspecto | Nivel 5 |
|---------|---------|
| **Persistencia** | **Sí.** Primer nivel con **State Store** durable (o session-scoped configurable). |
| **Tipo de matching** | **Temporal / diff** — qué cambió respecto al estado previo |
| **Unidad** | Delta sobre `ContextGraph` + metadatos de turno |
| **Dependencia** | Diseñado para ejecutarse **después de N4** (o N3 si N4 desactivado, con grafo mínimo) |

N5 **sí puede omitir información** del historial en la **vista enviada al LLM**, pero el historial completo permanece en el State Store y es recuperable. Esto difiere de N1–N4, que no eliminan información del bundle procesado.

Distinción crítica:

| | N1–N4 | N5 |
|---|-------|-----|
| Pérdida en salida | No — reorganización total reversible del bundle |
| Historial al LLM | Bundle (optimizado) del turno | Vista + diff; historial crudo no enviado |
| Store | Ninguno | State Store obligatorio |

## Entrada / salida

**Entrada:**

- `ContextGraph` del turno actual (salida de N4)
- `session_id` — identificador de sesión o agente
- `SemanticState` previo — cargado del State Store (vacío en primer turno)
- `turn_metadata` — timestamp, id de mensaje, query del usuario

**Salida:**

- `StateView` — texto/estructura compacta para el LLM
- `SemanticState` actualizado — persistido en State Store
- `commit_id` — referencia al snapshot
- métricas (tokens en vista vs. historial total acumulado)

Componentes del State Store (previstos):

```
SemanticState
├── session_id
├── head: commit_id              # snapshot actual
├── graph: ContextGraph          # materializado en head
├── history: Commit[]            # snapshots anteriores
└── config: { retention, max_tokens_view }
```

**StateView** (lo que ve el LLM):

```
# state:session_abc head:c42
# delta desde c41: +edge(juan→proyecto_x:creó), ~node:acme.budget=50k

[vista materializada del subgrafo relevante]
```

## Operaciones (v1)

1. **Load** — recuperar `SemanticState` por `session_id`.
2. **Merge** — integrar `ContextGraph` del turno en el grafo acumulado (nuevos nodos/aristas, actualización de propiedades).
3. **Commit** — crear snapshot inmutable con mensaje de turno.
4. **Materialize view** — generar `StateView` según presupuesto de tokens y `query_context`.
5. **Diff** — calcular delta respecto al último snapshot enviado al LLM (opcional en la vista).

## API prevista

```python
from coe.level5 import update_semantic_state
from coe.storage import StateStore

store = StateStore("./data/sessions")  # o backend remoto

result = update_semantic_state(
    graph=context_graph,
    session_id="agent-123",
    store=store,
    max_view_tokens=8000,
    query_context="Estado del presupuesto ACME",
)
result.view.render()      # para el LLM
result.commit_id          # para trazabilidad
```

## Reglas de integridad

- Ningún **commit** pierde información: merge conserva nodos/aristas previos salvo **supersión explícita** documentada (p. ej. corrección de hecho erróneo con flag `retracts`).
- Toda arista en la vista debe existir en el grafo del `head` o en el diff adjunto.
- Política de retención configurable (TTL, max commits); archivado, no borrado silencioso.

## Límites previstos (v1)

- Store **local** (filesystem/SQLite); backend distribuido en fase posterior.
- Materialización de vista con heurísticas (subgrafo + diff), sin LLM para selección en v1.
- Un `session_id` por conversación; multi-agente compartiendo store — diseño posterior.
- Conflictos de merge (dos fuentes contradicen un hecho) — marcar `conflict` en nodo, no resolver automáticamente en v1.

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N1–N3** | Preparan el bundle del turno antes de acumular en estado |
| **N4** | Define el modelo de grafo que N5 persiste y versiona |
| **architecture.md** | State Store es pieza transversal activada solo con N5 |

## Preguntas abiertas

- [ ] ¿Store por sesión, por usuario, o por agente?
- [ ] ¿Vista al LLM: solo materialización o materialización + diff siempre?
- [ ] ¿Integración con memoria externa del agente (Mem0, etc.) o store propio COE?
- [ ] ¿Retracción/corrección de hechos: protocolo explícito en spec de merge?

## Riesgos de diseño

- **Complejidad operativa** — N5 introduce el mayor salto (persistencia, merges, retención).
- **Coherencia con N1–N4** — la vista puede ser más pequeña que el bundle optimizado; validar calidad E2E con benchmarks antes de producción.
