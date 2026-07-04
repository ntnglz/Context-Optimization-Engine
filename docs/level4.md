# Nivel 4 — Grafo de conocimiento

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-4--grafo-de-conocimiento).  
> Nivel anterior: [level3.md](level3.md) · Índice: [levels.md](levels.md)

**Estado:** ✅ Spec aprobada · sin implementar

## Alineación con la visión fundacional

| Principio ([COE].md) | Cómo lo cumple N4 |
|----------------------|-------------------|
| **Cambiar representación** hacia CIR/grafo | `ContextGraph` interno; no resumen |
| **Cero pérdida** vs entrada del nivel | Invariante grafo + `orphans` ⊇ `StructuredContext` |
| El **LLM** consume lenguaje natural | `render_prose()` obligatorio; benchmark texto vs texto |
| Optimizar **contexto** (no solo tokens al LLM) | `internal_ratio`, slice, complejidad \|V\|/\|E\| |
| Puente a **N5** (estado persistente) | Modelo de grafo que N5 versionará |

[COE]: Context%20Optimization%20Engine%20(COE).md

## Objetivo

Representar el contexto del **bundle actual** como un **grafo semántico** (nodos + aristas): representación **interna** orientada a consulta, slice y evolución hacia N5/CIR. Hacia el LLM sigue mandando **prosa en lenguaje natural** (`render_prose()`), validada por benchmark — igual que N3.

## Invariante: cero pérdida respecto a la entrada de N4

Todo lo que recibe N4 (`StructuredContext` de N3) debe tener **representación en el grafo o en `orphans`**:

| Origen en N3 | Representación en N4 |
|--------------|----------------------|
| `entities[]` + `relations[]` | Nodos y aristas tipadas |
| `global_facts[]` | Nodos `concept`/`chunk` o aristas globales; nunca descartados |
| `prose` (referencia) | Verificable vía `render_prose()` reconstruido |
| Contenido no graficable | `orphans[]` literal (herencia N2 `unparsed`, etc.) |

**Regla:** no existe “información absorbida y olvidada” en la materialización. Si un hecho de N3 no se modela como nodo/arista, debe estar en `orphans` con `source_refs`. La suma **grafo + orphans** es un superset factual de la entrada.

Esto es distinto del criterio hacia el **LLM**: ahí importa comprensión (benchmark), no solo existencia en el grafo.

## Naturaleza del procesado

| Aspecto | Nivel 4 |
|---------|---------|
| **Persistencia** | **No entre invocaciones.** El grafo se materializa en memoria a partir del bundle del turno. No es el State Store (eso es N5). |
| **Tipo de matching** | **Topológico** — identidad de nodos y aristas, no similitud textual |
| **Unidad** | Nodo (persona, org, documento, concepto) + arista tipada |
| **Dependencia** | Diseñado para ejecutarse **después de N3** |
| **Salida interna** | `ContextGraph` — procesamiento, slice, métricas de complejidad |
| **Salida hacia el LLM** | `render_prose()` — lenguaje natural obligatorio (no tripletas/`node:` crudas) |
| **Pérdida vs entrada N4** | **Ninguna** (invariante grafo + orphans) |

Distinción importante respecto a N5:

| | N4 | N5 |
|---|----|----|
| Alcance | Contexto **de esta petición** | Estado **acumulado entre turnos** |
| Vida | Se crea y descarta (o serializa en salida) | Persiste en State Store |
| Analogía | AST del programa actual | Repositorio Git |

## Representación dual (como N3)

| Cara | Formato | Consumidor | Métrica de “espacio” |
|------|---------|------------|----------------------|
| **Interna** | `ContextGraph` (nodos, aristas, `orphans`) | N5, slice, análisis, CIR | Tokens de `serialize_internal()`; **complejidad** \|V\|, \|E\| |
| **Externa (LLM)** | `render_prose()` | LLM destino | Tokens de prosa; benchmark A/B |

El **ahorro de organización** se mide primero en la **representación interna**: un grafo deduplica nodos compartidos (p. ej. una sola entidad `ACME` con múltiples aristas entrantes). La **complejidad del grafo** (más nodos/aristas) refleja riqueza relacional del contexto, no error del optimizador.

### ¿Puede `render_prose()` de N4 ser más extensa que la de N3?

**Sí, puede ocurrir** — y no implica fallo automático del nivel.

| Situación | Por qué la prosa N4 crece | ¿Es problema? |
|-----------|----------------------------|---------------|
| Grafo **denso** (muchos nodos/aristas) | Materializar el grafo a prosa puede **enumerar** relaciones que N3 agrupaba en un árbol compacto | No, si comprensión OK y el objetivo es **slice** o fidelidad explícita |
| **Slice** amplio (`max_hops` alto) | Se incluyen más hechos que el árbol N3 mostraba junto | Evaluar presupuesto de tokens |
| Plantilla de prosa **conservadora** | Nombres completos repetidos para evitar ambigüedad (política N2/N3) | Aceptable si benchmark ≥ umbral |
| Materialización **verbosa** | Tripletas expandidas a oraciones completas una a una | Optimizar plantillas; comparar con N3 |

| Situación | Conclusión |
|-----------|------------|
| Prosa N4 **más larga** y comprensión **igual o mejor** | N4 válido; valor en organización interna / slice / camino a N5 |
| Prosa N4 **más larga** y comprensión **peor** | **Fallo** — revisar materialización o desactivar N4 |
| Prosa N4 **más corta** (slice acertado) y comprensión OK | Caso ideal para RAG con `query_context` |

**Implicación de diseño:** COE debe registrar **dos ratios de compresión**:

1. **`internal_ratio`** — tamaño grafo serializado vs contexto original (organización interna).
2. **`prose_ratio`** — tamaño `render_prose()` vs original (lo que “ve” el LLM).

N4 puede mejorar (1) y empeorar (2) a la vez; la decisión de activar N4 depende del objetivo del despliegue (contexto completo vs subgrafo relevante) y del benchmark.

## Entrada / salida

**Entrada:** `StructuredContext` de N3.

**Salida:** `ContextGraph` con:

- `nodes[]` — `{ id, kind, labels[], properties{}, source_refs[] }`
- `edges[]` — `{ from, to, type, properties{} }`
- `orphans[]` — texto no graficable (heredado de cadenas anteriores)
- `query_slice` — subgrafo seleccionado si hay `query_context` (opcional)
- `prose` — proyección en lenguaje natural (**derivada** del grafo activo + `orphans`)
- `complexity` — `{ node_count, edge_count, orphan_count }`
- métricas — `internal_ratio`, `prose_ratio`, latencia

Tipos de nodo previstos (v1): `person`, `organization`, `document`, `concept`, `chunk`.

Tipos de arista previstos (v1): heredados de N3 (`company`, `knows`, `action`, `reference`, `contains`, …).

## Operaciones (v1)

1. **Materializar** — `StructuredContext` → nodos/aristas; **cero pérdida** (invariante).
2. **Deduplicar nodos** — fusionar mismo `id` canónico; aristas se unen, no se eliminan hechos.
3. **Slice por consulta** (opcional) — subgrafo por proximidad desde entidades en `query_context`.
4. **`serialize_internal()`** — grafo compacto para logs, N5, métricas (**no** enviar al LLM por defecto).
5. **`render_prose()`** — materializar grafo activo + `orphans` a lenguaje natural para el LLM.

Ejemplo **interno** (depuración / CIR; no es salida al LLM):

```
node:juan:person { company→ACME }
node:pedro:person { company→ACME }
edge:juan→pedro:knows
orphan_count:0
complexity: { nodes: 3, edges: 3 }
```

Ejemplo **`render_prose()`** (ilustrativo; puede ser más corto o más largo que N3):

```
Juan works at ACME and knows Pedro.
Pedro works at ACME.
```

## API prevista

```python
from coe.level4 import build_context_graph

graph = build_context_graph(structured_context, query_context="What does Juan know about ACME?")
active = graph.slice_for_query(max_hops=2) if query_context else graph

active.render_prose()          # → LLM
active.serialize_internal()    # → métricas, N5, logs
active.complexity              # node_count, edge_count
```

Parámetros previstos:

- `max_hops` — profundidad del subgrafo para la consulta
- `include_orphans` — incluir o no texto no graficable

## Validación: comprensión y comparación con N3

Además del invariante de **cero pérdida** (tests estructurales: todo hecho de N3 aparece en grafo ∪ orphans), N4 exige benchmark de comprensión como N2/N3.

### Protocolo ampliado

| Comparación | Qué valida |
|-------------|------------|
| **Original vs `render_prose()` N4** | Comprensión LLM (umbrales ≥0,90 / ≥0,95) |
| **N3 `render_prose()` vs N4 `render_prose()`** | Que el grafo no degrade respecto al árbol N3 |
| **Original vs N3** (baseline) | Regresión si N4 no mejora slice ni `internal_ratio` |

Preguntas de test respondibles solo con el contexto; mismo LLM evaluador barato; **`target_lang`** tras L0.

### Interpretación

- **Pérdida semántica alta** en original vs N4 → **fallo** (aunque el grafo sea completo internamente).
- Prosa N4 **más extensa** que N3 pero comprensión OK → **aceptable** si el despliegue prioriza slice, trazabilidad o preparación N5.
- Prosa N4 más extensa **y** comprensión peor → **fallo**; preferir N3 o passthrough.
- **`internal_ratio`** mejora y **`prose_ratio`** empeora → documentar; decisión de producto, no bug per se.

## Reglas de integridad

- **Cero pérdida vs N3:** cada entidad, relación y `global_fact` → nodo, arista o `orphans`.
- Todo nodo/arista debe trazar a `source_refs`.
- Fusionar nodos solo con **mismo id canónico**; aristas fusionadas, hechos preservados.
- `render_prose()` debe reflejar el **subgrafo activo** (grafo completo o slice) **más** `orphans` incluidos.
- Reconstrucción factual: unión grafo + orphans ≡ superset de la entrada N3.

## Límites previstos (v1)

- Grafo **efímero** por petición; sin escritura en State Store.
- Slice por consulta con heurísticas simples (keywords / entidades en query), sin LLM reranker en v1.
- Sin razonamiento OWL/RDF completo; modelo de propiedades plano.
- **`render_prose()` obligatorio** hacia el LLM; `serialize_internal()` no sustituye benchmark.
- Métricas duales: **`internal_ratio`** + **`prose_ratio`** + **`complexity`**.

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N3** | Fuente de entidades y relaciones |
| **N5** | N5 **persiste** evolución del grafo entre turnos; N4 define el modelo de grafo que N5 versionará |
| **CIR** | El grafo es candidato a forma concreta de CIR serializado |

- Tamaño acotado (p. ej. máx. 10k nodos por bundle; configurable).

## Preguntas abiertas

- [ ] Plantillas `render_prose()` desde grafo: minimizar longitud vs maximizar claridad.
- [ ] ¿Slice obligatorio con `query_context` o grafo completo si cabe en presupuesto?
- [ ] ¿Umbral de \|E\|/\|V\| a partir del cual advertir “prosa N4 probablemente > N3”?
- [ ] ¿N4 sin N3? — por defecto **no** en v1.
