# Nivel 4 — Grafo de conocimiento

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-4--grafo-de-conocimiento).  
> Nivel anterior: [level3.md](level3.md) · Índice: [levels.md](levels.md)

**Estado:** spec en revisión · sin implementar

## Objetivo

Representar el contexto del **bundle actual** como un **grafo semántico** (nodos + aristas) en lugar de texto o árboles anidados, de modo que consultas sobre el contexto reconstruyan **solo la subgrafo necesaria** para la petición.

## Naturaleza del procesado

| Aspecto | Nivel 4 |
|---------|---------|
| **Persistencia** | **No entre invocaciones.** El grafo se materializa en memoria a partir del bundle del turno. No es el State Store (eso es N5). |
| **Tipo de matching** | **Topológico** — identidad de nodos y aristas, no similitud textual |
| **Unidad** | Nodo (persona, org, documento, concepto) + arista tipada |
| **Dependencia** | Diseñado para ejecutarse **después de N3** |

Distinción importante respecto a N5:

| | N4 | N5 |
|---|----|----|
| Alcance | Contexto **de esta petición** | Estado **acumulado entre turnos** |
| Vida | Se crea y descarta (o serializa en salida) | Persiste en State Store |
| Analogía | AST del programa actual | Repositorio Git |

## Entrada / salida

**Entrada:** `StructuredContext` de N3.

**Salida:** `ContextGraph` con:

- `nodes[]` — `{ id, kind, labels[], properties{}, source_refs[] }`
- `edges[]` — `{ from, to, type, properties{} }`
- `orphans[]` — texto no graficable (heredado de cadenas anteriores)
- `query_slice` — subgrafo seleccionado si hay `query_context` (opcional)

Tipos de nodo previstos (v1): `person`, `organization`, `document`, `concept`, `chunk`.

Tipos de arista previstos (v1): heredados de N3 (`empresa`, `conoce`, `acción`, `referencia`, `contiene`).

## Operaciones (v1)

1. **Materializar** — convertir árboles/entidades de N3 en nodos y aristas normalizados.
2. **Deduplicar nodos** — fusionar nodos con mismo `id` canónico dentro del grafo.
3. **Slice por consulta** (opcional) — dado `query_context`, extraer subgrafo por proximidad (hops desde entidades mencionadas en la query).
4. **Serializar** — emitir representación compacta para el LLM (lista de tripletas, notación CIR, o DOT simplificado).

Ejemplo conceptual de salida serializada:

```
node:juan:person { empresa→ACME }
node:pedro:person { empresa→ACME }
edge:juan→pedro:conoce
ref:chunk_A,chunk_B
```

## API prevista

```python
from coe.level4 import build_context_graph

graph = build_context_graph(structured_context, query_context="¿Qué sabe Juan de ACME?")
view = graph.slice_for_query(max_hops=2)
view.render()
```

Parámetros previstos:

- `max_hops` — profundidad del subgrafo para la consulta
- `include_orphans` — incluir o no texto no graficable

## Reglas de integridad

- Todo nodo/arista debe trazar a `source_refs` (bloque o línea de origen).
- Fusionar nodos solo con **mismo id canónico** (normalización de N2/N3), no por similitud de embedding.
- `orphans` + subgrafo serializado deben cubrir **toda** la información de N3.

## Límites previstos (v1)

- Grafo **efímero** por petición; sin escritura en State Store.
- Slice por consulta con heurísticas simples (keywords / entidades en query), sin LLM reranker en v1.
- Sin razonamiento OWL/RDF completo; modelo de propiedades plano.
- Tamaño acotado (p. ej. máx. 10k nodos por bundle; configurable).

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N3** | Fuente de entidades y relaciones |
| **N5** | N5 **persiste** evolución del grafo entre turnos; N4 define el modelo de grafo que N5 versionará |
| **CIR** | El grafo es candidato a forma concreta de CIR serializado |

## Preguntas abiertas

- [ ] ¿Formato de serialización al LLM: tripletas, JSON-LD subset, o notación `entity{}`?
- [ ] ¿Slice obligatorio cuando hay `query_context` o siempre grafo completo si cabe en presupuesto?
- [ ] ¿N4 puede ejecutarse sin N3 (proyección directa desde N2)? — por defecto **no** en v1.
