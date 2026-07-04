> **Documento fundacional de COE.** Versión canónica y mantenida en este repositorio.
>
> En [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) permanece una copia como referencia en la visión global del ecosistema; no se actualiza allí.

> **Nota de evolución (specs operativas):** Las decisiones implementables viven en `docs/level1.md`–`level5.md`, [ingest.md](ingest.md), [renderer.md](renderer.md) y [benchmarks.md](benchmarks.md). Resumen de cierre: [spec-gaps.md](spec-gaps.md). Donde este documento difiera (p. ej. CIR «interpretable por LLM» en crudo, eliminación de información), **prevalecen las specs operativas**: hacia el LLM solo **prosa en lenguaje natural**; CIR/grafo es **interno**; no resumir en N1–N4; N5 puede omitir historial en la **vista** al LLM con benchmark OK.

# Context Optimization Engine (COE)

## Visión

La compresión del prompt es solo una parte del problema.

En la mayoría de aplicaciones basadas en LLM, el prompt representa una fracción muy pequeña de los tokens procesados. El verdadero coste proviene del **contexto**: documentos, conversaciones, resultados de herramientas, código fuente, historial de razonamiento, etc.

La hipótesis de este proyecto es que el mayor ahorro de tokens y la mayor mejora de rendimiento no se obtendrán optimizando el prompt, sino optimizando el contexto.

---

# Motivación

Un agente moderno puede construir un contexto formado por:

- Historial completo de conversación.
- Documentos recuperados mediante RAG.
- Código fuente.
- Resultados de herramientas.
- Búsquedas web.
- Memoria del agente.
- Estado interno del workflow.

Es habitual que este contexto alcance decenas o cientos de miles de tokens.

Sin embargo, gran parte de esa información es:

- Redundante.
- Repetitiva.
- Implícita.
- Fácilmente reconstruible.
- Poco relevante para la consulta actual.

Enviar siempre el contexto completo supone un elevado coste económico y computacional.

---

# Objetivo

Construir un componente capaz de transformar un gran volumen de información en una representación semántica mucho más compacta sin perder la información necesaria para responder correctamente.

No se trata de resumir el contexto.

Se trata de **cambiar su representación**.

---

# Arquitectura propuesta

```
Fuentes de información
────────────────────────────────────

Conversaciones
Documentos
Código
RAG
Herramientas
Memoria
Logs

        │
        ▼

Context Optimization Engine

        │
        ▼

Representación optimizada

        │
        ▼

LLM
```

---

# Niveles de optimización

## Nivel 1 – Eliminación de redundancias

Detectar información repetida.

Ejemplo:

```
Documento A
Empresa: ACME

Documento B
Empresa: ACME

Documento C
Empresa: ACME
```

Representación optimizada:

```
Empresa=ACME

Referencias:
A
B
C
```

---

## Nivel 2 – Factorización

Agrupar información relacionada.

Entrada:

```
Juan trabaja en ACME.

Juan creó Proyecto X.

Juan aprobó el presupuesto.
```

Salida:

```
Juan
 ├ empresa = ACME
 └ acciones
      ├ creó Proyecto X
      └ aprobó presupuesto
```

La información no desaparece.

Simplemente deja de repetirse.

---

## Nivel 3 – Representación estructurada

Transformar lenguaje natural en estructuras más compactas.

Ejemplo:

```
Juan conoce a Pedro.

Pedro trabaja en ACME.

Juan trabaja en ACME.
```

Representación:

```
Juan
 ├ empresa → ACME
 └ conoce → Pedro

Pedro
 └ empresa → ACME
```

Muchos LLM interpretan este tipo de estructuras con gran facilidad.

---

## Nivel 4 – Grafo de conocimiento

En lugar de almacenar texto, mantener un grafo semántico actualizado.

Cada nodo representa:

- personas
- organizaciones
- documentos
- conceptos
- relaciones

Las consultas reconstruyen únicamente la parte necesaria.

---

## Nivel 5 – Estado semántico

En lugar de enviar continuamente todo el historial, el agente mantiene un estado interno.

Cada interacción únicamente modifica dicho estado.

El contexto enviado al modelo pasa a ser una vista del estado, no el historial completo.

Esto recuerda al funcionamiento de sistemas como Git:

- historial completo
- estado actual
- diferencias (diff)

---

# Diferencia respecto a un resumen

Un resumen elimina información.

Una optimización de contexto cambia la forma de representarla.

Ejemplo:

Resumen:

```
Juan trabaja en ACME y creó el Proyecto X.
```

Optimización:

```
Juan{
 empresa=ACME
 creó=Proyecto X
}
```

El objetivo no es reducir contenido.

Es reducir representación.

---

# Context Intermediate Representation (CIR)

Se propone definir una representación intermedia del contexto.

Análoga a LLVM IR en compiladores.

Características:

- Compacta.
- Semánticamente estable.
- Independiente del idioma (labels post-L0).
- **Optimizable** por el pipeline (N1–N5).
- **Proyectable a prosa** para el LLM vía Renderer — el modelo **no** recibe CIR crudo en producción (ver [renderer.md](renderer.md)).

Ejemplo conceptual (**representación interna**, no salida al LLM):

```
entity{
 id=juan
 company=acme
 knows=pedro
 actions{
     create(project_x)
     approve(budget)
 }
}
```

---

# Arquitectura futura

```
Información bruta

        │

        ▼

Parser semántico

        │

        ▼

Knowledge Graph

        │

        ▼

Context Optimizer

        │

        ▼

Context IR

        │

        ▼

Adaptador específico del modelo

        │

        ▼

GPT / Claude / Gemini / Llama
```

---

# Posibles técnicas

- Deduplicación.
- Agrupación semántica.
- Normalización.
- Representación mediante grafos.
- Compresión jerárquica.
- **Vista acotada** del estado acumulado (N5), con historial completo en store — no resumen libre.
- Codificación estructurada **interna**.
- Aprendizaje automático (investigación).
- Optimización específica por modelo (Model Adapter, post-Renderer).

---

# Métricas

Ver especificación operativa [benchmarks.md](benchmarks.md): comprensión, redacción, latencia COE (`t_coe`), ratio documentado.

Conceptos fundacionales:

- Ratio de compresión.
- Ahorro de tokens.
- Latencia.
- Calidad de respuesta y recuperación factual.
- Pérdida semántica (gate en benchmarks, no solo ratio).

---

# Relación con Prompt Compression Middleware

Ambos componentes son complementarios.

```
Usuario
    │
    ▼

Prompt Compiler

    │

    ▼

Context Optimization Engine

    │

    ▼

Model Adapter

    │

    ▼

LLM
```

El Prompt Compiler optimiza la instrucción.

El Context Optimization Engine optimiza el conocimiento disponible.

El Model Adapter adapta la representación al modelo concreto.

---

# Hipótesis de investigación

Los LLM actuales procesan principalmente texto porque es el formato de entrenamiento, no porque sea necesariamente la representación más eficiente.

Es probable que exista una representación intermedia del conocimiento significativamente más compacta que el lenguaje natural y que preserve prácticamente toda la información necesaria para el razonamiento.

Descubrir o aprender dicha representación podría reducir de forma importante el consumo de tokens y la latencia sin afectar de manera apreciable a la calidad de las respuestas.

---

# Analogía con los compiladores

La evolución de los compiladores ofrece una analogía útil:

```
Lenguaje de programación
        │
        ▼
Árbol sintáctico (AST)
        │
        ▼
Representación intermedia (LLVM IR)
        │
        ▼
Optimizaciones
        │
        ▼
Código máquina
```

De forma análoga, una arquitectura para LLM podría seguir este flujo:

```
Lenguaje natural
        │
        ▼
Representación semántica
        │
        ▼
Context Intermediate Representation (CIR)
        │
        ▼
Optimizaciones
        │
        ▼
Representación específica del modelo
        │
        ▼
LLM
```

En esta visión, el contexto deja de ser simplemente un conjunto de textos y pasa a convertirse en una estructura optimizable, del mismo modo que un compilador transforma un programa en una representación interna antes de generar el código ejecutable.

---

# Visión a largo plazo

El objetivo final no es desarrollar un simple compresor de contexto, sino una **capa de optimización universal para sistemas basados en LLM**.

Esta capa actuaría como un compilador del conocimiento, transformando información heterogénea en una representación compacta, optimizada y adaptada dinámicamente al modelo de destino.

La optimización dejaría de centrarse únicamente en el entrenamiento o la inferencia del modelo y pasaría también a optimizar el flujo de información entre agentes, herramientas y modelos de lenguaje.
