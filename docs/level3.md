# Nivel 3 — Representación estructurada

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-3--representación-estructurada).  
> Nivel anterior: [level2.md](level2.md) · Índice: [levels.md](levels.md) · Locale: [i18n.md](i18n.md)

**Estado:** ✅ Spec aprobada · sin implementar

## Alineación con la visión fundacional

| Principio ([COE].md) | Cómo lo cumple N3 |
|----------------------|-------------------|
| **Cambiar representación**, no resumir | Estructura interna + `render_prose()` con mismos hechos |
| Camino hacia **CIR** | `StructuredContext` / borrador CIR para N4; texto validado en paralelo |
| El **LLM** es el consumidor | Solo `render_prose()` hacia el modelo; benchmark texto vs texto |
| Sin inferencia libre opaca | Propagación explícita; locale pack; passthrough si falla comprensión |
| Composición N1→N2→**N3**→N4 | Entrada `FactorizationResult`; salida dual (prosa + estructura) |

[COE]: Context%20Optimization%20Engine%20(COE).md

## Objetivo

Transformar hechos factorizados en **estructuras anidadas con relaciones tipadas** entre entidades, más compactas que el lenguaje natural repetitivo. Primer paso hacia el [CIR](Context%20Optimization%20Engine%20(COE).md#context-intermediate-representation-cir) sin grafo persistente.

N3 es **deliberadamente comprometido**: alejarse de prosa lineal aumenta el riesgo para el LLM. Eso es coherente con la visión (cambiar representación hacia CIR), pero impone una regla no negociable: **toda estructura intermedia debe poder proyectarse a lenguaje natural** para el destino, y esa proyección es lo que se valida en comprensión.

## Naturaleza del procesado

| Aspecto | Nivel 3 |
|---------|---------|
| **Persistencia** | No. Stateless. |
| **Tipo de matching** | **Estructural / relacional** — enlaces explícitos entre entidades ya nombradas |
| **Unidad** | Entidad + relación + objetivo (tripletas o árboles) |
| **Dependencia** | Diseñado para ejecutarse **después de N2** (bundle en `target_lang` si L0 activo) |
| **Locale** | Patrones de relación en **locale pack** — [i18n.md](i18n.md) |
| **Salida hacia el LLM** | Siempre **texto en lenguaje natural** (`render_prose()`), no el árbol/`entity{}` crudo |
| **Salida hacia N4 / CIR** | `StructuredContext` estructurado (para almacenamiento y procesamiento automático futuros) |

N3 **fusiona información redundante entre entidades** cuando la relación es explícita en el texto, no por inferencia semántica profunda:

**Input (post-N2; example in English):**

```
Juan knows Pedro.
Pedro works at ACME.
Juan works at ACME.
```

**Internal structure** (not sent to the LLM as-is):

```
Juan
 ├ company → ACME
 └ knows → Pedro

Pedro
 └ company → ACME
```

**Text projection for the LLM** (`render_prose()` — illustrative):

```
Juan works at ACME and knows Pedro.
Pedro works at ACME.
```

The internal tree is **more compact** for pipeline and future N4; the **prose projection** is what the destination LLM reads. Both must stay in sync: every relation in the structure appears in the text version.

Here `company → ACME` for Juan **was not on a single line**; N3 builds structure from N2-parsed facts via **explicit propagation** (e.g. shared attribute value), not free inference.

**Out of scope:**

```
Juan and Pedro are colleagues.  → do not infer "knows" without explicit pattern
ACME is Juan's employer.        → requires mapped lexical pattern, not free LLM in v1
```

## Representación dual: estructura + texto

N3 mantiene **dos caras** del mismo contenido:

| Cara | Formato | Consumidor | Propósito |
|------|---------|------------|-----------|
| **Interna** | `StructuredContext` / borrador CIR | N4, store futuro, procesamiento automático | Compactación, deduplicación relacional, evolución hacia grafo |
| **Externa (LLM)** | Prosa en `target_lang` | LLM destino | Comprensión; **única** salida autorizada hacia el modelo |

Principios:

1. **El LLM no recibe** árboles ASCII, `entity{}` ni JSON de relaciones salvo experimento explícito fallido en benchmark.
2. **`render_prose()` es obligatorio** y debe ser **reversible en contenido** respecto a la estructura (mismos hechos, mismas entidades nombradas explícitamente).
3. La estructura anidada **facilita** almacenamiento y procesamiento posterior (N4, N5); **no sustituye** la prueba de que el texto generado preserve el significado.
4. Si en el futuro el procesamiento automático opera sobre CIR/grafo, el camino de ida y vuelta pasa por reglas de serialización documentadas, no por omitir la proyección textual.

Política alineada con N2: sin pronombres ambiguos en `render_prose()`; nombres de entidad explícitos; passthrough parcial si la proyección no supera el benchmark.

## Entrada / salida

**Entrada:** `FactorizationResult` de N2.

**Salida:** `StructuredContext` con:

- `entities[]` — nodos con `id`, `relations[]` (`type`, `target`, `value`)
- `global_facts[]` — hechos sin entidad única (heredados de N1 `shared_facts`)
- `schema_version` — versión del formato estructurado (pre-CIR)
- `prose` — proyección en lenguaje natural (**derivada**, validada; no entrada manual)
- métricas

Formato interno orientativo (acercamiento a CIR; **no** enviar al LLM):

```
entity{id=juan, relations=[
  {type=company, value=ACME},
  {type=knows, target=pedro}
]}
entity{id=pedro, relations=[
  {type=company, value=ACME}
]}
```

## Reglas de estructuración (v1)

1. **Relaciones explícitas** — mapped patterns per **locale pack** (reference: `en`).
2. **Attribute deduplication** — if `company=ACME` appears in several facts for the same entity, one edge/attribute only.
3. **Cross-references** — `knows → Pedro` points to `entity{id=pedro}`, does not repeat prose.
4. **Passthrough** — entradas en `unparsed` de N2 se incluyen como bloques literales al final.

## API prevista

```python
from coe.level3 import structure_context

result = structure_context(factorization_result)
result.render_prose()   # → LLM (lenguaje natural obligatorio)
result.render_debug()   # árbol / entity{} — solo logs, tests, N4
result.to_cir_draft()   # borrador serializable hacia CIR formal
```

## Validación: comprensión LLM (obligatoria)

Misma filosofía que [level2.md](level2.md): el criterio de éxito no es la elegancia del árbol sino **equivalencia de comprensión** frente al contexto en claro de partida.

### Protocolo

1. **Contexto original crudo** — pre-L0, pre-COE ([benchmarks.md](benchmarks.md)).
2. **Contexto optimizado** — salida **`render_prose()`** de N3 (no la estructura interna).
3. Misma pregunta respondible solo con el contexto; **Respuesta A** vs **Respuesta B** con el mismo LLM evaluador barato.
4. Similitud semántica A↔B ≥ 0,90; recuperación factual ≥ 0,95 (umbrales alineados con N2).

### Interpretación

| Resultado | Conclusión |
|-----------|------------|
| Comprensión OK + compresión útil | N3 válido para ese perfil de contexto |
| Comprensión OK pero poca compresión | Aceptable; valor en estructura para N4/N5 |
| **Pérdida semántica alta** | **Hemos fallado** — revisar reglas, empeorar `render_prose()`, passthrough o no activar N3 |

La estructura intermedia puede ser correcta para almacenamiento y aun así **inválida para COE** si la proyección textual no pasa el benchmark. El test siempre compara **texto claro vs texto claro** desde la perspectiva del LLM.

Casos de test: incluir bundles donde N3 aporta deduplicación relacional (p. ej. `company → ACME` compartida) y verificar que `render_prose()` no omita hechos respecto al original.

## Reglas de integridad

- Reconstrucción: desde `StructuredContext` debe poder regenerarse **`render_prose()`** con superset factual equivalente al input de N2.
- Toda relación en `entities[]` debe aparecer en `prose` (trazabilidad estructura → texto).
- No eliminar entidades ni relaciones presentes en la entrada parseada.
- Identificadores de entidad estables dentro del bundle (`juan`, `pedro` derivados de normalización del nombre).

## Límites previstos (v1)

- Conjunto **cerrado de tipos de relación** (`company`, `knows`, `action`, …) por locale pack.
- Sin razonamiento transitivo general (no inferir `A→C` desde `A→B` y `B→C` salvo regla explícita documentada).
- Sin persistencia; la estructura del bundle es input de N4, no un store.
- CIR formal (gramática, validación) — fase posterior; N3 produce **borrador** compatible.
- **`render_prose()` obligatorio** hacia el LLM; estructura interna reservada a pipeline posterior.

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N2** | Consume factorized entities; comprehension benchmark extended to **`render_prose()`** |
| **N4** | Consumes internal `StructuredContext`; LLM receives **`render_prose()`** from N4 (or N3 passthrough if N4 off) |
| **CIR** | Bridge factored text ↔ CIR draft; textual projection validated in parallel |

## Siguiente nivel

→ [level4.md](level4.md) — grafo del bundle ✅ spec aprobada

→ [level5.md](level5.md) — estado semántico ✅ spec aprobada

## Preguntas abiertas

- [ ] ¿Cuándo congelar gramática CIR vs. `StructuredContext` flexible?
- [ ] ¿Relaciones inversas automáticas o solo direccionales?
- [ ] Plantillas de `render_prose()` por locale (oraciones fijas vs. generador rule-based)?
- [ ] ¿Umbral de compresión mínimo para activar N3 si comprensión OK pero ahorro ~0?
