# Nivel 2 — Factorización

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-2--factorización).  
> Nivel anterior: [level1.md](level1.md) · Índice: [levels.md](levels.md) · Locale: [i18n.md](i18n.md)

**Estado:** spec en revisión · sin implementar

## Objetivo

Agrupar hechos que comparten la **misma entidad** (sujeto repetido) bajo un único bloque, eliminando la repetición del nombre de entidad en lenguaje natural. La información no desaparece; deja de repetirse la mención explícita del sujeto.

## Naturaleza del procesado

| Aspecto | Nivel 2 |
|---------|---------|
| **Persistencia** | No. Stateless: consume la salida de N1 (o equivalente) y devuelve `FactorizationResult`. |
| **Tipo de matching** | **Estructural** sobre texto: misma cadena de entidad como sujeto, no equivalencia semántica libre |
| **Unidad** | Oración o línea con patrón `entidad + predicado` |
| **Dependencia** | Diseñado para ejecutarse **después de N1** (y tras [L0](l0-ingest.md) si aplica) |
| **Locale** | Patrones en **locale pack** (`locale` en options); repo de referencia en **inglés** — ver [i18n.md](i18n.md) |

N2 **no** fusiona frases que dicen lo mismo con palabras distintas. Solo agrupa cuando la **misma forma de entidad** aparece repetida como sujeto:

**Sí factoriza** (ejemplo en inglés; equivalentes por locale pack):

```
Juan works at ACME.
Juan created Project X.
Juan approved the budget.
```

**No factoriza** (entity not repeated syntactically as subject):

```
Juan works at ACME.
He created Project X.          ← pronoun, not "Juan"
```

**No factoriza** (same meaning, different surface form):

```
Juan works at ACME.
Employee Juan is at ACME.   ← subject not syntactically identical
```

La resolución de pronombres o alias de entidad queda **fuera de N2** (posible extensión futura o nivel auxiliar con LLM).

## Riesgo de comprensión por el LLM

N1 solo reordena líneas idénticas; el texto sigue siendo **prosa reconocible**. N2 es el **primer nivel que puede comprometer la comprensión**: deja de presentar oraciones completas repetidas y pasa a **bloques por entidad** con acciones colgadas del sujeto.

Principio rector: **el lector del contexto optimizado es un LLM entrenado en lenguaje natural**, no un parser interno. Toda decisión de representación debe evaluarse desde esa perspectiva.

### Sustitución por referencias vs. pronombres

| Técnica | Riesgo | Política N2 |
|---------|--------|-------------|
| Agrupar bajo nombre de entidad (`Juan → acciones…`) | Bajo si el **nombre se repite explícito** en la cabecera del bloque | ✅ Permitido |
| Referencias opacas (`[E1]`, `entity:7`) | Medio-alto sin leyenda clara | ❌ No en salida al LLM (solo depuración interna) |
| Pronombres (`Él creó…`) | **Alto** con varias entidades del mismo género/rol | ❌ **Prohibido** en salida renderizada |
| Omitir el sujeto en acciones anidadas | Medio: depende de que la cabecera desambigue | ✅ Solo si la entidad está **una vez** en cabecera y las acciones son claramente suyas |

Con **una sola entidad** factorizada, omitir la repetición de «Juan» en las acciones anidadas suele ser seguro porque la cabecera fija el sujeto. Con **varias entidades** en el mismo contexto, la salida **debe mantener nombres explícitos** en cabeceras y evitar cualquier forma que obligue a resolver coreferencia (pronombres, referencias cruzadas implícitas).

**Ejemplo problemático (no permitido en render):**

```
Juan → acciones: creó Proyecto X
Pedro → acciones: lo aprobó        ← "lo" ambiguo
```

**Preferible:**

```
Juan → acción: creó Proyecto X
Pedro → acción: aprobó el presupuesto de Proyecto X
```

O, si la compresión no compensa el riesgo, **passthrough**: dejar la oración original en `unparsed`.

### Umbral de factorización

N2 **no factoriza** si la ganancia de tokens no supera un margen mínimo **o** si el número de entidades en el mismo bundle supera un umbral configurable (v1 propuesto: factorizar con cautela cuando hay **>3 entidades** con acciones entrelazadas). Parámetro previsto: `max_entities_for_aggressive_factorization`.

### Variantes de render (a validar con tests)

El Renderer de N2 debería soportar al menos dos modos, elegidos por benchmark:

| Modo | Forma | Cuándo |
|------|-------|--------|
| `structured` | Árbol / `entity:` (más compacto) | Pocas entidades, tests E2E OK |
| `prose_compact` | Oraciones cortas con sujeto explícito repetido | Muchas entidades o tests por debajo del umbral |
| `passthrough` | Sin factorizar | Comprensión < umbral en tests |

La elección del modo puede ser automática según métricas del benchmark de comprensión, no solo ratio de tokens.

## Entrada / salida

**Entrada:** `DeduplicationResult` de N1 (`shared_facts` + `unique_blocks`), o `ContextBlock[]` si N1 está desactivado (el nivel debe normalizar internamente).

**Salida:** `FactorizationResult` con:

- `entities[]` — cada entidad con `name`, `attributes[]`, `actions[]`, `source_refs[]`
- `unparsed[]` — líneas u oraciones que no encajan en ningún patrón (se pasan sin modificar)
- métricas de tokens estimados

Ejemplo (documento fundacional):

```
Juan
 ├ empresa = ACME
 └ acciones
      ├ creó Proyecto X
      └ aprobó presupuesto
```

Serialización orientativa para el Renderer:

```
entity:Juan
  empresa=ACME
  acción: creó Proyecto X
  acción: aprobó presupuesto
```

## Patrones de extracción (v1)

Patrones definidos en **locale packs** (`locales/{locale}/factorization_patterns.yaml`), no hardcodeados. Ejemplos de referencia **`en`**:

| Pattern | Example | Extraction |
|---------|---------|------------|
| `X works at Y` | Juan works at ACME | `entity=Juan`, `attr: company=Y` |
| `X verb …` | Juan created Project X | `entity=Juan`, `action: created Project X` |
| `key=value` line (post-N1) | `Company=ACME` in shared_facts | Do not re-factorize; already compact |

Reglas:

- Entity = leading tokens until first recognized verb (closed list **per locale** in v1).
- Sentences without explicit subject → `unparsed`.
- Same entity across blocks → merge into one node with unified refs.
- **`locale`** in `OptimizeOptions` selects the pack; must align with **`target_lang`** after L0.

## API prevista

```python
from coe.level2 import factorize_context

result = factorize_context(deduplication_result)  # salida de N1
result.render()
result.to_json()
```

Parámetros previstos:

- `locale` — locale pack for patterns (default **`en`** in reference tests; not tied to Spanish)
- `entity_patterns` — extend verb/attribute patterns within a locale pack

## Reglas de integridad

- Toda oración parseada debe poder **reconstruirse** a partir de `entities` + `unparsed`.
- N2 no elimina `shared_facts` de N1; los preserva o referencia sin re-factorizar.
- Si no hay entidades repetidas, la salida es equivalente a la entrada (passthrough).

## Validación: tests de comprensión (obligatorios desde N2)

N1 puede validarse con **integridad sintáctica** (reconstrucción + tests unitarios). A partir de N2 hace falta un **benchmark de comprensión**: el contexto optimizado debe permitir al LLM responder **igual de bien** que con el contexto original.

### Protocolo (adaptado de PCM E2E)

Para cada caso del dataset:

1. Fijar una **pregunta** respondible solo con el contexto (p. ej. «¿Quién aprobó el presupuesto?»).
2. **Respuesta A** — LLM evaluador + contexto **original**.
3. **Respuesta B** — mismo LLM + contexto **optimizado** (salida N1+N2).
4. Medir **similitud semántica** entre A y B (embeddings o normalización de respuesta).
5. Medir **recuperación factual** (¿B menciona los hechos clave? F1 sobre entidades/hechos esperados).

Criterio de aprobación del nivel (v1 propuesto):

| Métrica | Umbral |
|---------|--------|
| Similitud media A vs. B | ≥ 0,90 |
| Recuperación factual | ≥ 0,95 |
| Ratio de compresión | documentado; no bloquea si comprensión falla |

Ejecutar benchmarks en **`target_lang`** del despliegue (tras L0 si aplica). Incluir casos multilingües: entrada en idioma distinto → L0 → N1+N2 → evaluación.

Si no se cumple el umbral → bajar agresividad (modo `prose_compact` o passthrough parcial).

### LLM evaluador (coste y volumen)

En PCM se usó **Mistral** como upstream de prueba (API de pago). En COE las pruebas serán **numerosas y repetitivas**; basta un modelo barato o gratuito porque importa la **comparación A vs. B**, no la calidad absoluta del evaluador.

Opciones previstas (orden de preferencia para CI/local):

| Opción | Coste | Notas |
|--------|-------|-------|
| **Ollama local** | Gratis | Mismo enfoque que el compresor PCM; modelos 3B–8B (`qwen3`, `llama3`, `mistral-small`) |
| **Groq** | Tier gratuito con límites | Inferencia rápida; útil para batches moderados |
| **Google Gemini API** | Tier gratuito | Cuota diaria; alternativa cloud |
| **OpenRouter / Together** | Modelos muy baratos | Para CI si Ollama no está disponible |
| **Mistral API** | Pago | Reservar para validación final puntual, no para miles de casos |

Requisito: el **mismo modelo y temperatura** en A y B por caso. Ubicación prevista del harness: `scripts/comprehension_benchmark.py` + `data/comprehension_cases.json` (por crear al implementar).

## Límites previstos (v1)

- **Locale packs** — reference implementation for **`en`**; **`zh`** and others via separate packs (see [i18n.md](i18n.md)).
- Closed verb lists **per locale**; no heavy NLP in v1.
- Sin resolución de pronombres ni coreferencia en **entrada ni salida**.
- Sin LLM dentro del pipeline N2 en v1; LLM solo en **harness de prueba**.
- Stateless; sin grafo global (eso es N4).

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N1** | Entrada preferida; N1 quita duplicados exactos antes de buscar sujetos repetidos |
| **N3** | N3 consume árboles planos de N2 y añade relaciones cruzadas (`conoce →`, `empresa →`) |
| **N4** | N4 proyecta entidades/atributos de N2/N3 como nodos del grafo |

## Preguntas abiertas

- [ ] Closed verb list vs. domain-configurable patterns per locale?
- [ ] Treat N1 `shared_facts` as global attributes or skip factorization?
- [ ] Default render mode: `structured` vs. `prose_compact`?
- [ ] Entity threshold (`>3`) and minimum token savings to factorize?
- [ ] Default Ollama model for harness (align with PCM or multilingual model)?
