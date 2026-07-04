# Nivel 3 — Representación estructurada

> Definición conceptual: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-3--representación-estructurada).  
> Nivel anterior: [level2.md](level2.md) · Índice: [levels.md](levels.md) · Locale: [i18n.md](i18n.md)

**Estado:** spec en revisión · sin implementar

## Objetivo

Transformar hechos factorizados en **estructuras anidadas con relaciones tipadas** entre entidades, más compactas que el lenguaje natural repetitivo. Primer paso hacia el [CIR](Context%20Optimization%20Engine%20(COE).md#context-intermediate-representation-cir) sin grafo persistente.

## Naturaleza del procesado

| Aspecto | Nivel 3 |
|---------|---------|
| **Persistencia** | No. Stateless. |
| **Tipo de matching** | **Estructural / relacional** — enlaces explícitos entre entidades ya nombradas |
| **Unidad** | Entidad + relación + objetivo (tripletas o árboles) |
| **Dependencia** | Diseñado para ejecutarse **después de N2** (bundle en `target_lang` si L0 activo) |
| **Locale** | Patrones de relación en **locale pack** — [i18n.md](i18n.md) |

N3 **fusiona información redundante entre entidades** cuando la relación es explícita en el texto, no por inferencia semántica profunda:

**Entrada (post-N2 o equivalente):**

```
Juan conoce a Pedro.
Pedro trabaja en ACME.
Juan trabaja en ACME.
```

**Salida:**

```
Juan
 ├ empresa → ACME
 └ conoce → Pedro

Pedro
 └ empresa → ACME
```

Aquí `empresa → ACME` para Juan **no estaba en una sola línea**; N3 deduce la estructura a partir de hechos ya parseados en N2, aplicando reglas de **propagación explícita** (p. ej. mismo valor de atributo `empresa` en hechos vinculados), no inferencia libre.

**Fuera de alcance:**

```
Juan y Pedro son colegas.     → no inferir "conoce" sin patrón explícito
ACME es la empresa de Juan.   → requiere patrón léxico mapeado, no LLM libre en v1
```

## Entrada / salida

**Entrada:** `FactorizationResult` de N2.

**Salida:** `StructuredContext` con:

- `entities[]` — nodos con `id`, `relations[]` (`type`, `target`, `value`)
- `global_facts[]` — hechos sin entidad única (heredados de N1 `shared_facts`)
- `schema_version` — versión del formato estructurado (pre-CIR)
- métricas

Formato interno orientativo (acercamiento a CIR):

```
entity{id=juan, relations=[
  {type=empresa, value=ACME},
  {type=conoce, target=pedro}
]}
entity{id=pedro, relations=[
  {type=empresa, value=ACME}
]}
```

## Reglas de estructuración (v1)

1. **Relaciones explícitas** — mapped patterns per **locale pack** (reference: `en`).
2. **Deduplicación de atributos** — si `empresa=ACME` aparece en varios hechos de la misma entidad, una sola arista/atributo.
3. **Referencias cruzadas** — `conoce → Pedro` apunta a `entity{id=pedro}`, no repite texto.
4. **Passthrough** — entradas en `unparsed` de N2 se incluyen como bloques literales al final.

## API prevista

```python
from coe.level3 import structure_context

result = structure_context(factorization_result)
result.render()       # árbol o notación compacta
result.to_cir_draft() # borrador serializable hacia CIR formal
```

## Reglas de integridad

- Reconstrucción: desde `StructuredContext` debe poder regenerarse un superset textual equivalente al input de N2.
- No eliminar entidades ni relaciones presentes en la entrada parseada.
- Identificadores de entidad estables dentro del bundle (`juan`, `pedro` derivados de normalización del nombre).

## Límites previstos (v1)

- Conjunto **cerrado de tipos de relación** (`empresa`, `conoce`, `acción`, …).
- Sin razonamiento transitivo general (no inferir `A→C` desde `A→B` y `B→C` salvo regla explícita documentada).
- Sin persistencia; el grafo completo del bundle es input de N4, no un store.
- CIR formal (gramática, validación) — objetivo de fase posterior; N3 produce **borrador** compatible.

## Relación con otros niveles

| Con | Relación |
|-----|----------|
| **N2** | Consume entidades/atributos/acciones factorizadas |
| **N4** | Proyecta `StructuredContext` a `ContextGraph` (nodos/aristas normalizados) |
| **CIR** | N3 es el puente entre texto factorizado y CIR definitivo |

## Preguntas abiertas

- [ ] ¿Cuándo se congela la gramática CIR vs. seguir con `StructuredContext` flexible?
- [ ] ¿Relaciones inversas automáticas (`Pedro conocido_por Juan`) o solo direccionales?
- [ ] ¿Renderer prefiere árbol ASCII o `entity{…}` estilo fundacional?
