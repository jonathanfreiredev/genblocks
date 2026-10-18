# GenBlocks — Plan de ejecución

Este documento es la fuente de verdad del plan. Recoge las decisiones ya
cerradas en la fase de diseño y las ordena en rebanadas ejecutables, pensadas
para que cada una se pueda revisar en `git` y entender sin perderse.

El código, los identificadores, los comentarios y los mensajes de commit van en
inglés (ver `AGENTS.md`). Este documento va en español por comodidad.

---

## 0. Cómo leer este documento

- **Secciones 1–11**: qué construimos, cómo está decidido y por qué. Contexto.
- **Sección 12**: el plan de ejecución por fases. Es el núcleo. Cada fase se
  entrega como una rebanada revisable en `git`.
- **Secciones 13–16**: variables de entorno, lo aplazado, riesgos y fuera de
  alcance.

Principio de construcción: **rebanadas verticales finas, con dobles ("fakes")
primero**. Antes de depender de Modal, Chroma o del LLM real, el sistema se cierra
de punta a punta con implementaciones deterministas. Así se puede desarrollar,
probar y revisar sin gastar dinero ni depender de terceros, y cada pieza real se
enchufa después detrás de su contrato.

---

## 1. Qué es GenBlocks

Un ecosistema abierto de bloques UI creados por la comunidad con IA. Cualquiera
escribe un brief y obtiene un componente listo para pegar. Todos los bloques son
públicos y gratuitos, y **cada bloque se valida antes de publicarse**: un juez con
rúbrica puntúa cada intento y exige un mínimo. Los intentos que no llegaron al
listón se quedan a la vista.

El diferenciador no es generar (eso es lo común), es que **la calidad se
comprueba, no se promete, y esa comprobación es pública**.

Archivo base: el template `mcp-stack` (backend FastAPI + MCP, frontend Next.js 16,
Supabase Auth, Postgres, multi-tenancy por organización).

---

## 2. Decisiones cerradas

1. **Un dominio, dos puertas**: la lógica vive en servicios; API y MCP la invocan.
   Ninguna puerta reimplementa reglas.
2. **Tool = adaptador delgado**: valida el esquema, llama al servicio, devuelve un
   tipo Pydantic. El llamante sale del token, nunca de un argumento.
3. **Organizaciones se quedan** en el template, pero un usuario **no** necesita
   pertenecer a ninguna.
4. **Patrón B para el agente**: el bucle del agente corre en el backend; **Modal es
   el sandbox** (filesystem + ejecución + navegador) y **no tiene secretos**. Es el
   patrón "sandbox as tool" del propio ecosistema DeepAgents.
5. **Agente conversacional**: una sola superficie, la **conversación de creación**,
   en un dialog de shadcn. Termina al arrancar la generación. Sin chat de colección.
6. **Reintentos**: máximo **2 intentos** (1 reintento). Publica el primer intento que
   pasa todos los umbrales; si ninguno, el de mayor puntuación.
7. **Juez independiente del generador**: agente, skill y run separados. Es
   inquebrantable: si decide quien crea, la evaluación es teatro.
8. **El juez consume los artefactos del harness** (screenshots + informes); no
   vuelve a renderizar.
9. **Imágenes dentro del agente**: no son tareas de background; son una tool.
10. **RAG**: se embebe el **screenshot**, no el código. Embedder único
    **`voyage-multimodal-3`** (cross-modal). `text-embedding-3-large` descartado.
11. **Almacenamiento**: **Cloudinary** para imágenes y screenshots, bajo una raíz
    `genblocks/` con dos carpetas que escribe el sistema (`images/`,
    `screenshots/`) y una manual (`web/`) para estáticas de la web; Chroma guarda
    vector + metadata (incluida la URL). Sin ficheros locales. Se guarda el
    `public_id` sin transformación; la transformación se aplica al renderizar.
12. **Chroma**: dev con `PersistentClient` local; **prod Chroma Cloud**.
13. **Datos**: Postgres es la fuente de verdad de scores y estado; Langfuse es una
    copia/trace **opcional** en v1 (`trace_id` nullable), en fire-and-forget.
14. **Tareas**: background con steps persistidos en Postgres, que es además la
    **cola**. El worker reclama con `FOR UPDATE SKIP LOCKED` en la misma
    transacción que cambia el estado: no hay broker con el que desincronizarse ni
    ventana entre "crear la tarea" y "encolarla" en la que el trabajo se pierda, y
    la durabilidad la da la fila, no un segundo sistema. Una tarea en `running` que
    encuentra un arranque es de un worker que ya no existe → se reconcilia a
    `interrupted`. **Redis queda fuera de v1**: si algún día hay más de una
    instancia, entra detrás de la misma interfaz de encolado.
15. **Progreso de la tarea**: checklist por **polling**. **Streaming solo en la
    conversación**.
16. **Seguridad de render en vivo**: v1 muestra el **screenshot**; el render en
    vivo seguro se decide más tarde.
17. **Licencia**: MIT para lo generado.
18. **Taxonomía**: **dos niveles** ahora (Componentes/Imágenes → tipo). El nivel 3
    no se usa ni se documenta; si algún día hace falta, `parent_id` ya lo soporta.
19. **Despliegue**: se decide al final (probablemente un servicio barato).
20. **Panel de generación uniforme**: al abrir un componente o una imagen se ven,
    a la derecha, los scores de su generación y el enlace a su trace. Las imágenes
    también se puntúan, con su propia rúbrica corta (ver sección 7).
21. **Los intentos son de la tarea, no del componente**: `generations` cuelga de
    `tasks`, y el `Component` nace en el `commit`. Así `components` contiene **solo
    piezas publicadas** — un invariante de la tabla, no una regla que haya que
    recordar en cada consulta— y un intento rechazado sigue existiendo aunque no
    llegue a componente. Al publicar, el componente se estampa en todos los
    intentos de la tarea, para poder mostrar el historial completo.
22. **Las tareas también se leen por la API**: `GET /v1/tasks` (solo las del
    llamante), `GET /v1/tasks/{id}` (checklist + intentos) y
    `GET /v1/components/{id}/generations` (historial público de la pieza). La
    Fase 2 las dejó fuera porque su API eran los catálogos; la vista de tarea de
    la Fase 3 las necesita **por la puerta de la web**, no solo por MCP, y la
    propiedad la comprueba el servicio, no el router.
23. **El espécimen de un bloque es su código; el de una imagen, su receta.** No hay
    screenshots todavía (los produce la Fase 7, los sube la Fase 9) y las imágenes
    sembradas tienen `path` pero no asset. Ni la celda ni el panel del item lo
    disimulan: enseñan la receta y un `AWAITING ASSET` mono con el modelo y las
    dimensiones. Cuando el asset exista y `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` esté
    puesto, la misma pieza enseña la foto sin tocar código.
24. **El conjunto de datos de desarrollo es un seed, no fixtures**:
    `python -m app.seed.vault`, idempotente, con ids derivados de `uuid5` y un
    `--owner EMAIL` para colgar las tareas de una cuenta que ya haya entrado una
    vez. El código de los bloques sembrados usa **Tailwind genérico**: una pieza
    del vault se copia a cualquier proyecto, y con nuestros tokens
    (`bg-paper`, `bg-spot-primary`) solo renderizaría aquí.
25. **Las tools del agente son las de la puerta MCP, sin el transporte**: el
    agente conversacional vive en el backend (decisión 4) y llama a los **mismos
    servicios** con los **mismos nombres** (`search_components`,
    `create_component`), pero **in-process**, no como cliente de nuestro propio
    servidor MCP. La decisión 2 ya dice que una tool es un adaptador delgado
    sobre el servicio: un salto de red a casa añadiría un hop, un token de más y
    el esquema en un segundo sitio, sin cambiar qué se ejecuta. El MCP se queda
    como la puerta de los agentes externos. El llamante se ata **al construir**
    las tools, una vez por conversación, así que ningún argumento puede cambiar
    de dueño.
26. **La conversación se pinta con los primitivos de shadcn** (`Message`,
    `Bubble`) y el scroll-follow se escribe aquí. `message-scroller` arrastra
    `@shadcn/react` y un import del repo de shadcn, y lo que aporta —seguir el
    final mientras llega el stream— son unas líneas propias.
27. **El harness es un sandbox con contrato JSON y veredicto propio**: la
    comprobación corre como **app de Modal** (`app/harness/modal_app.py`,
    `modal deploy` desde `backend/`) a la que el backend llama **por nombre**
    (`app/harness/sandbox.py`). Dentro no hay ningún secreto y no alcanza nada
    nuestro: se le mandan ficheros y devuelve informes y el PNG del render. Lo
    que encuentra se guarda en **`generations.checks`** (jsonb), para que el
    juez de la Fase 8 y el panel del item lean lo mismo que se comprobó. Tres
    comprobaciones **bloquean** la publicación —tipos, build, render—: un bloque
    que no compila no es un intento publicable. El resto (lint, encaje en cada
    viewport, accesibilidad) es **evidencia**, no puerta: un bloque 40px más
    ancho que un móvil es una opinión, y quien opina llega en la Fase 8. El
    screenshot se sube **en el paso del harness** (Fase 7) y no en el commit de
    la Fase 9 como insinuaba la nota de la decisión 23: el intento lleva su
    render desde que existe, y el juez lo necesita antes de publicar.
28. **El juez puntúa a ciegas, y su rúbrica es una skill con versión de texto.**
    Es un agente aparte (`app/judge/`) que no ve la conversación que produjo el
    brief y no puede tocar la pieza: recibe el brief, el código, lo que encontró
    el sandbox y el render, y devuelve un número y una frase por dimensión más un
    resumen. La rúbrica vive como documento en el repo
    (`app/judge/rubrics/*.md`) y su **versión es el hash del texto y de la lista
    de dimensiones**, no un número que alguien recuerde subir: un score siempre
    se puede releer contra el texto que lo produjo, y una versión que cambió sin
    motivo no puede existir. Las dimensiones de componente son **cinco** —render,
    accessibility, visual, copy, compliance—: *novedad* no se puntúa todavía
    porque es una distancia contra la biblioteca y la biblioteca no tiene
    vectores hasta la Fase 10; un juez que la adivinara estaría contestando a
    otra pregunta con el mismo nombre. Los **umbrales no se le dicen al juez**:
    quien sabe dónde está el listón puntúa contra el listón, y el veredicto deja
    de ser una lectura independiente. Sus notas y su resumen alimentan al
    reintento y no se guardan: el ledger tiene los números (decisión 13) y la
    traza con las palabras llega con la Fase 12.
29. **El bucle publica el primer intento que pasa todos los umbrales; si ninguno,
    el que quedó más cerca.** Reintento máximo 1 (`settings.max_attempts`), y "más
    cerca" es el **margen**: la menor distancia a un umbral entre las dimensiones
    medidas, no la media — la media deja que un bloque esconda la dimensión que
    falló, que es justo lo que el ledger se niega a hacer. Un reintento se lleva
    el **motivo por escrito** (los checks que fallaron o las notas del juez):
    un segundo intento sin él es otra tirada de los mismos dados al precio de
    otro sandbox. Un intento que el sandbox rechaza **también se reintenta** si
    queda alguno: el código que no compila es lo más arreglable que hay. El
    checklist crece con el bucle: los pasos del primer intento se escriben al
    abrir la tarea y un reintento inserta los suyos por delante del paso de
    publicación, que baja de sitio, para que el orden siga siendo el orden. Un
    intento tumbado queda `rejected` —por el sandbox o por el juez—; `candidate`
    es solo lo que nadie ha tumbado todavía.

---

## 3. Arquitectura

### Puertas

- **Web (Next.js)**: galería, item, vista de tarea, dialog de generación.
- **API (FastAPI)**: lo que consume la web.
- **MCP (FastMCP)**: los mismos servicios, para agentes externos (Claude Code,
  opencode…).
- **Modal**: sandbox de ejecución y render. Fuera de la red, efímero, CPU.

### Flujo de generación

```
brief → [conversación] → create_component → tarea (background)
                                              │
        spec → assets(imágenes, dentro del harness) → harness → judge
                                                      ▲          │
                                                      └── retry ─┘ (máx 1)
                                                                 │
                                                              commit
```

- **spec**: retrieval de taxonomía + vecinos (para no duplicar) + guía; escribe el
  spec y el prompt de entrega. Primer uso del LLM.
- **harness**: el DeepAgent hace una checklist, decide imágenes, las genera y las
  sube a Cloudinary, construye el componente y ejecuta las comprobaciones
  (TypeScript, lint, compilación, render en 3 viewports, accesibilidad, seguridad).
  Un solo step visible, de minutos, con latido de progreso.
- **judge**: puntúa sobre los artefactos del harness. Decide reintentar o pasar.
- **commit**: crea el componente y lo estampa en todos los intentos de la tarea,
  sube el screenshot, lo embebe, fija taxonomía y publica.

Los **steps visibles** son los nodos del grafo (harness intento 2, judge intento 2…).
El DeepAgent es **un** step.

### Modelo de datos (Postgres)

| Tabla | Campos clave |
|---|---|
| `categories` | id, parent_id, kind(component\|image), slug, name, level |
| `components` | id, slug, title, description, category_id, code, delivery_prompt, spec, winning_generation_id, created_by, license, created_at |
| `generations` | id, task_id, component_id, attempt_no, code, screenshot_path, scores jsonb, verdict, rubric_version, model, langfuse_trace_id |
| `images` | id, prompt, path, width, height, category_id, created_by, license, model, scores jsonb, rubric_version, langfuse_trace_id |
| `component_assets` | component_id, image_id, slot |
| `tasks` | id, kind, status, brief, component_id, created_by, created_at, finished_at, error, langfuse_trace_id |
| `task_steps` | id, task_id, index, name, status, detail jsonb, started_at, finished_at |

### Chroma (2 colecciones)

- `components`: vector del screenshot + metadata (categoría, tipo, ratio, paleta,
  novedad).
- `images`: vector de la imagen + metadata (categoría, ratio, paleta).

Metadata como filtro duro → retrieval híbrido: Chroma filtra, el vector ordena.

### Cloudinary (carpetas)

```
genblocks/
├── images/       # stock de imágenes generadas
├── screenshots/  # renders de componentes
└── web/          # estáticas de la web (se crean a mano)
```

El prefijo `genblocks/` lo impone el código; nunca se escribe fuera de ese árbol.

---

## 4. Taxonomía semilla (2 niveles)

Nivel 1 = `kind` (Componentes / Imágenes). Nivel 2 = tipo. Se siembra a mano, amplio
para que la galería no salga genérica.

**Componentes (25 tipos):** Hero · Navbar · Footer · Features · CTA · Pricing ·
Testimonials · Social proof · Stats · FAQ · Contact · Forms/Auth · Cards · Gallery ·
Blog · Team · Tables · Dashboard · Charts · States · Onboarding · Banners ·
Integrations · Timeline · Newsletter/Waitlist.

**Imágenes (8 tipos):** Illustration · Abstract/Background · Texture/Pattern ·
Product/UI mockup · Photography · Spot/Icon · Avatar · Scene.

La asignación la hace `spec` por RAG (definiciones + ejemplares). Si nada encaja,
propone un tipo nuevo en estado `pendiente` (curaduría manual). Nunca crea tipos
por su cuenta en producción.

---

## 5. Modelos y proveedores

| Trabajo | Proveedor / modelo |
|---|---|
| Conversación, spec, harness, juez | **OpenAI `gpt-6-luna`** |
| Juez (agente separado con su skill) | **`gpt-6-luna`** (mismo modelo, agente distinto) |
| Moderación | **Groq Safety GPT OSS 20B** |
| Embeddings | **Voyage `voyage-multimodal-3`** |
| Imágenes (stock) | **Black Forest Labs `flux-2-pro`** (FLUX.2, API asíncrona) |
| Sandbox | **Modal CPU** |

Notas:

- `gpt-6-luna` tiene visión y tool calling, así que cubre también "los ojos" del
  harness y del juez. Groq solo se usa para moderación (gratis).
- **BFL es asíncrono**: la petición devuelve `id` + `polling_url`, se sondea hasta
  `Ready` y el `sample` es temporal — se descarga y se sube a Cloudinary, nunca se
  guarda la URL de BFL.
- **Caché de prompt**: luna cobra el input cacheado a $0.01 vs $0.10. Poner lo
  estable (system, skills, rúbrica) al principio del prompt y lo variable al final.
- **Groq free tier** tiene límites de rate; el camino crítico no depende de él.

---

## 6. Tools MCP (nombres finales)

> Un nombre publicado **nunca se renombra**. Estos quedan congelados.

**Lectura:** `list_categories`, `search_components`, `get_component`,
`search_images`, `get_task`, `list_tasks`.

**Escritura:** `create_component`, `generate_image`, `vary_component`.

`vary_component` se implementa en una fase posterior; se reserva el nombre.

---

## 7. Rúbrica y bucle

Dimensiones 0–100, cada una con su umbral (no basta la media):

| Dimensión | Cómo se mide |
|---|---|
| Render | compila y pinta sin error en 3 viewports; sin overflow ni clipping |
| Accesibilidad | contraste calculado, focus visible, roles y labels |
| Visual (VLM) | jerarquía, espaciado, alineación, anticliché |
| Copy | coherente y plausible (nada de lorem ipsum ni "Acme Inc.") |
| Novedad | distancia vectorial a los componentes más cercanos |
| Cumplimiento | ¿hace lo que su propio spec dijo que haría? |

- **Independencia**: el agente del sandbox puede autorevisarse el render; puntúa
  otro. El juez es un agente separado con su propia skill.
- La **rúbrica vive como skill** y la lee el juez: una para componentes, otra más
  corta para imágenes.
- Los umbrales se **calibran** con 5–10 generaciones de prueba, no a ojo.

**Imágenes.** Las dimensiones de arriba son de un componente: una imagen no se
renderiza ni lleva copy. Su rúbrica es corta —**Calidad visual**, **Ajuste al
prompt**, **Cumplimiento**— y pasa por el mismo juez antes de entrar en la
biblioteca. Así el panel del item es idéntico en las dos vistas: a la derecha, los
scores de la generación y el enlace a su trace.

---

## 8. Seguridad

- **Render en vivo**: fuera de v1. Se muestra el screenshot; el render seguro
  (iframe aislado, origen distinto, CSP) se decide después.
- **Anti-inyección**: todo input externo (brief, retrieval) es dato, nunca
  instrucción; allowlist fija de tools; validación por esquema; el llamante sale
  del token; secretos fuera del sandbox; el código generado solo corre en el
  sandbox.
- **Moderación**: de entrada (brief) y de salida. Groq Safety GPT OSS 20B.
- **Abuso**: rate limit por usuario y **cortacircuitos global** (tope de gasto)
  comprobado antes de encolar.

---

## 9. Coste

- **Modal**: CPU. Una tarea ≈ $0.02. A 10/día ≈ $6–12/mes. La capa gratuita de $30
  sobra.
- **LLM (luna)**: ≈ $0.05–0.20 por tarea (2 intentos). A 10/día ≈ $15–60/mes. Lo
  bajan el tope de iteraciones, la caché de prompt y el guard de duplicados.
- Mitigaciones: guard de duplicados, reúso de imágenes, tope de 2 intentos, rate
  limit por usuario, caché por brief, cortacircuitos global.

---

## 10. Fuera de alcance (no implementar)

- RAG sobre código o shaders externos.
- Guías de diseño curadas (se evalúan más adelante; el gusto vive en skills).
- Imágenes de bancos externos tipo Unsplash.
- Imágenes como tareas de background.
- Tipos de item que no sean componente o imagen.
- Subida manual de componentes.
- Edición del componente por prompt o edición de su código (fase posterior).
- Render en vivo del componente (v1 muestra screenshot).
- `vary_component` (nombre reservado, se implementa después).

---

## 11. Principios de ingeniería

- Servicios de dominio con la autorización dentro; routers y tools, delgados.
- Imports absolutos desde `app` (backend). `@/` en frontend.
- Tests con cada cambio de lógica: pytest (unit/integration) y Vitest/Playwright.
- Frontend: usar skills de diseño y usar shadcn antes de crear componentes.
  `DESIGN.md` es la fuente de verdad visual.
- Cambios mínimos y reversibles; una rebanada, un motivo.

---

## 12. Plan de ejecución

Cada fase es una rebanada revisable. Formato: **Objetivo**, **Cambios**,
**Verificación** y **Fuera de este paso**.

### Fase 0 — Preparación: settings y entorno

**Objetivo**: dejar el backend listo para los nuevos proveedores, sin lógica nueva.

**Cambios**
- `backend/app/settings.py`: añadir campos — `groq_api_key`, `openai_api_key`,
  `voyage_api_key`, `cloudinary_cloud_name/_api_key/_api_secret`, nombres de modelo
  (luna, safety, voyage, imagen), `modal_token_id/_secret`, `chroma_*`, tope de
  intentos (`max_attempts = 2`), y umbrales de rúbrica (placeholders).
- `backend/.env.example`: placeholders documentados (nunca tocar `.env` real).
- `backend/pyproject.toml`: dependencias base de la fase que las use (se añaden por
  fase, no todas de golpe).

**Verificación**: `uv sync`; el backend arranca; test unitario de settings.

**Fuera**: no se llama a ningún proveedor todavía.

### Fase 1 — Dominio y datos (lectura pública)

**Objetivo**: las 7 tablas, sus servicios de lectura y la taxonomía sembrada.

**Cambios**
- Modelos en `backend/app/categories/`, `components/`, `generations/`, `images/`,
  `tasks/` (uno por dominio, siguiendo el patrón de `users/` y `organizations/`).
- Migración Alembic (importar modelos en `alembic/env.py`).
- Servicios de lectura + esquemas Pydantic.
- Autorización: lectura pública; escritura autenticada (se usará más tarde).
- Seed de categorías (script/CLI) con la taxonomía de la sección 4.
- Tests unit + integration.

**Verificación**: `uv run alembic upgrade head`; `uv run pytest`; las categorías
aparecen en la base.

**Fuera**: sin endpoints HTTP ni tools MCP todavía.

### Fase 2 — API de lectura + tools MCP de lectura

**Objetivo**: exponer la lectura por las dos puertas.

**Cambios**
- Endpoints `/v1`: `categories`, `components` (list + search + get), `images`.
- Tools MCP de lectura: `list_categories`, `search_components`, `get_component`,
  `search_images`, `list_tasks`, `get_task`.
- Paginación con `app/pagination.py`.

**Verificación**: consultar desde **opencode** (MCP) y con `curl`; tests de
integración de endpoints.

**Fuera**: escritura. Las **lecturas de tareas** se aplazaron aquí y llegaron en la
Fase 3, que las necesita por la puerta de la web (ver decisión 22).

### Fase 3 — Frontend: galería, item y tarea (datos sembrados)

**Objetivo**: la cara pública, contra datos de ejemplo.

**Cambios**
- La **galería** es la portada: rail lateral con la taxonomía (los dos kinds y sus
  tipos) y el botón **"Generar con IA"**, buscador, y una **hoja** de celdas que
  comparten las reglas — marca de registro, tipo, título, una línea de meta. Misma
  rejilla para bloques e imágenes.
- **Dialog del item**, con la dirección como estado (`?item=`): a la izquierda el
  espécimen (código + prompt de entrega en un bloque; la imagen + su receta en una
  imagen), a la derecha la evidencia (veredicto, score por dimensión, trace y el
  **ledger de intentos**, que se puede recorrer para leer el intento rechazado).
- **Vistas de tarea** (`/tasks` y `/tasks/[id]`) con la **checklist** que escribe el
  worker; solo el dueño las ve.
- **Fuera de la web** el playground y toda la landing heredada del template
  (`mcp-stack`), que contaba otro producto: el relato propio se escribirá desde
  cero cuando toque.
- Endpoints que faltaban para que esto fuera real (decisión 22) y el **seed** de
  desarrollo (decisión 24).
- Tests de componente, de lib y e2e del vault.

**Verificación**: `pnpm dev` y navegar; `pnpm test:run`; `pnpm test:e2e`
(la suite e2e del vault necesita el stack arriba y el seed corrido).

**Notas**: aplicar skills de diseño y shadcn. El demo **de frontend** (playground) se
retira aquí; el de **backend** (`app/demo/`) se retira en la Fase 6.

**Fuera**: no hay creación real. Las tareas sembradas se cuelgan de una cuenta con
`python -m app.seed.vault --owner <email>` después de entrar una vez: hasta
entonces no las ve nadie, que es justo lo que promete el aislamiento.

### Fase 4 — Runner de tareas + pipeline fake

**Objetivo**: el ciclo de vida de una tarea funciona de punta a punta, sin LLM ni
Modal.

**Cambios**
- Escritura en el servicio de tareas: crear (la tarea nace `pending`) y
  **reconciliación al arrancar** (tarea en `running` huérfana → `interrupted`, con
  sus steps abiertos cerrados, para que la checklist no siga diciendo que se
  trabaja).
- Runner en el **dominio** (`app/tasks/runner.py`): reclamar, abrir la checklist
  entera como `pending` y cerrar cada step con su detalle conforme avanza. El bucle
  del worker vive en el mismo módulo y lo arranca el lifespan de la API.
- Las dos puertas: `POST /v1/tasks` (202) y la tool MCP `create_component`. Ninguna
  espera: las dos escriben la misma fila y devuelven la tarea para seguirla.
- Pipeline **canned** (`app/tasks/canned.py`): spec, bloque y scores fijos. El
  intento se queda **sin `model`** y con `rubric_version = canned-v1`, para que una
  pieza canned no se pueda confundir con una juzgada.

**Verificación**: crear una tarea; ver los steps progresar en la base; la tarea
termina con un componente. Tests del runner (reclamo, reconciliación, fallo por
taxonomía ausente, bucle completo) y de la copia canned.

**Notas**: la tool de escritura **valida el brief con el mismo tipo que la API**
(`TaskCreate`): el esquema que publica al modelo describe el brief, pero no impide
que le manden otra cosa. El **screenshot placeholder no se escribe**: hasta que
haya render (Fase 7), `screenshot_path` se queda nulo, que es lo que la UI ya sabe
leer (decisión 23). La checklist usa los mismos nombres que las tareas sembradas,
más la línea de moderación, que llega con la moderación (Fase 11).

**Fuera**: sin LLM, sin Modal, sin UI nueva (se usa la de la Fase 3). Sin reintento:
el juez canned publica siempre, y el bucle de 2 intentos llega con el juez real
(Fase 8).

### Fase 5 — Frontend: dialog de generación (conversación fake) y tarea en vivo

**Objetivo**: cerrar la rebanada vertical visible.

**Cambios**
- Dialog de shadcn para la conversación; botón en la barra lateral.
- Conversación **fake** (sin LLM): pregunta → confirma → crea la tarea → enlace.
- Polling de la tarea y checklist en vivo.

**Verificación**: recorrer el flujo completo hasta ver el componente publicado
(fake).

**Fuera**: sin LLM real.

### Fase 6 — Agente conversacional real (streaming)

**Objetivo**: sustituir la conversación fake por un grafo LangGraph real.

**Cambios**
- Grafo conversacional (LangGraph) con `gpt-6-luna`. Tools: `search_components` y
  `create_component`. Memoria por sesión en memoria.
- Extracción de brief robusta (validación de esquema antes de crear la tarea).
- **Streaming SSE** backend → dialog. UI de conversación con componentes AI de
  shadcn.
- Retirar `backend/app/demo/` (el agente nuevo reemplaza el demo).

**Verificación**: conversar de verdad; el agente llama `create_component`; ver el
streaming.

**Fuera**: el harness sigue siendo fake.

### Fase 7 — Sandbox de Modal (harness sin agente)

**Objetivo**: construir y renderizar de verdad en un entorno aislado.

**Cambios**
- Función Modal (CPU): recibe ficheros, corre `tsc`, lint, build, renderiza con
  Playwright en 3 viewports, accesibilidad básica, y devuelve artefactos
  (screenshots + informes). Sin secretos dentro.
- Integrar como `harness` con un generador **simple** (una llamada a `gpt-6-luna`,
  no DeepAgent todavía).
- Subida del screenshot a **Cloudinary** (`genblocks/screenshots/`).

**Verificación**: una tarea produce un screenshot real y los informes de checks.

**Fuera**: sin DeepAgent ni skills; sin embeddings.

### Fase 8 — Juez + rúbrica (reintento ≤ 1)

**Objetivo**: introducir el juicio y el bucle de reintento.

**Cambios**
- Rúbrica como **skill** (una fuente): una para componentes, otra corta para imágenes.
- **Agente juez** separado con `gpt-6-luna`, puntúa desde los artefactos del harness.
- Umbrales en settings; veredicto; **reintento máximo 1** (2 intentos totales).
- La **rúbrica de imágenes** puntúa cada imagen al entrar en la biblioteca y escribe
  `scores`, `rubric_version` y `langfuse_trace_id` en `images`.

**Verificación**: el juez puntúa un candidato; el reintento se dispara y se respeta
el tope. Calibrar umbrales con varias generaciones.

**Notas**: los umbrales se calibraron contra las primeras generaciones reales: el
juez puntúa el trabajo bueno entre 75 y 100, así que los listones quedan justo
dentro de esa banda y suben donde no hay gusto que valga —render, accesibilidad y
cumplimiento—. Medido en vivo: de siete tareas, cinco publicaron al primer
intento, una se arregló en el segundo y en otra ningún intento pasó el listón, así
que se publicó el más cercano con su número flojo a la vista. La rúbrica de
imágenes y su llamada existen y están probadas, pero **su llamante es la tool de
imágenes de la Fase 9**: hasta entonces ninguna imagen entra en la biblioteca, y
las sembradas no tienen asset que mirar. **Pendiente**: que un bloque no pueda
depender de la red es hoy una frase en la rúbrica y en el prompt —el juez lo
penaliza, y lo hizo— pero el check mecánico (referencias a assets externos) es
trabajo de endurecimiento (Fase 11).

**Fuera**: todavía sin DeepAgent ni RAG.

### Fase 9 — Harness DeepAgent + skills + tool de imágenes

**Objetivo**: la generación real de calidad.

**Cambios**
- Sustituir el generador simple por el **DeepAgent** (`gpt-6-luna`) con:
  - **Skills** versionadas en el repo (diseño, accesibilidad) montadas en el sandbox.
  - Bucle interno (compila / se ve) y bucle externo (juez).
  - Tope duro de iteraciones internas (control de coste).
- **Tool de imágenes**: genera con BFL (`flux-2-pro`), sube a Cloudinary
  (`genblocks/images/`) → (embedding en Fase 10) → devuelve la URL. El agente
  decide cuántas y sus prompts antes de construir. La API es asíncrona: se encola,
  se sondea y se descarga la imagen.

**Verificación**: generación real de punta a punta con imágenes.

**Fuera**: sin RAG (guard y reúso llegan en la Fase 10).

### Fase 10 — RAG / Chroma

**Objetivo**: recuperación, guard de duplicados y reúso de imágenes.

**Cambios**
- Cliente Chroma (dev `PersistentClient`; config para Chroma Cloud).
- Colecciones `components` e `images`; embeddings con `voyage-multimodal-3`.
- Embeber el screenshot en `commit`; embeber la imagen en la tool de imágenes.
- **Guard de duplicados** (brief ↔ componentes) antes de generar.
- **Reúso de imágenes** en `assets`.
- **Routing de taxonomía** por RAG en `spec`.

**Verificación**: el guard detecta un duplicado; una imagen se reutiliza; un brief
recibe el tipo correcto.

**Fuera**: sin guías (descartadas por ahora).

### Fase 11 — Endurecimiento

**Objetivo**: que se pueda exponer al público sin sustos.

**Cambios**
- Moderación de entrada/salida (Groq Safety).
- Rate limit por usuario y **cortacircuitos global** de gasto, comprobado antes de
  encolar.
- Caché por brief.
- Comprobación de "seguridad" del harness: alcance definitivo.

**Verificación**: límite y tope se activan; un brief abusivo se rechaza.

**Fuera**: nada de features nuevas.

### Fase 12 — Observabilidad (opcional)

**Objetivo**: trace sin que la observabilidad pueda tumbar el producto.

**Cambios**
- `langfuse_trace_id` nullable; push de scores en **fire-and-forget** después del
  commit en Postgres; enlace al trace en la UI (con "no disponible" si falta).

**Verificación**: el trace aparece cuando Langfuse está configurado y la app
funciona igual cuando no lo está.

**Fuera**: Langfuse no es fuente de verdad de nada.

### Fase 13 — Siembra y lanzamiento

**Objetivo**: abrir la galería con archivo, no vacía.

**Cambios**
- Sembrar la librería de imágenes.
- Generar y **curar a mano** 15–20 componentes con la rúbrica puesta, empezando por
  las categorías con más peso visual (hero, pricing, testimonios, features).
- No publicar la galería hasta tenerlos.

**Verificación**: galería poblada y navegable.

**Fuera**: features nuevas.

### Después (no en este plan)

- `vary_component`.
- Edición del componente por prompt y edición de su código.
- Render en vivo seguro.
- Guías curadas.

---

## 13. Variables de entorno

Todas en **`backend/.env`** (server-only), salvo el nombre del cloud de Cloudinary:
el navegador lo necesita para **leer** las imágenes del stock, y va en
`frontend/.env` como `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`. El backend sube; el
frontend solo pinta.

| Variable | Para qué |
|---|---|
| `OPENAI_API_KEY` | `gpt-6-luna` (agente, spec, harness, juez) |
| `BFL_API_KEY` | imágenes del stock (`flux-2-pro`) |
| `GROQ_API_KEY` | moderación (Safety GPT OSS 20B) |
| `VOYAGE_API_KEY` | embeddings (`voyage-multimodal-3`) |
| `CLOUDINARY_CLOUD_NAME` | storage (y `NEXT_PUBLIC_...` en el frontend, para leer) |
| `CLOUDINARY_API_KEY` | storage |
| `CLOUDINARY_API_SECRET` | storage |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | invocar el sandbox |
| `CHROMA_HOST` / `CHROMA_API_KEY` / `CHROMA_TENANT` / `CHROMA_DATABASE` | vectores (Chroma Cloud en prod) |

Los servicios `backend` y `mcp` del compose ya leen el mismo `backend/.env`.

---

## 14. Aplazado a propósito

- Umbrales exactos de la rúbrica (calibrar con 5–10 generaciones).
- Alcance de la comprobación de "seguridad" del harness.
- Chroma: detalle de despliegue en prod.
- Proveedor de hosting del despliegue.

---

## 15. Riesgos

- **Coste**: 2 intentos × visitantes. Mitigado con guard de duplicados, reúso de
  imágenes, tope de intentos, rate limit y cortacircuitos.
- **Latencia de Modal**: arranque en frío + navegador = minutos. Por eso la tarea en
  background no es un lujo, es la UX.
- **Instancia única**: la fuente de verdad de las tareas es Postgres, no la memoria.
- **Rate limit de Groq** (free): solo afecta a moderación; el camino crítico no
  depende de Groq.
- **Si el juez se autoaprueba, el producto no vale**: la independencia
  generador/juez es la que sostiene todo el argumento.
- **Seguridad del código generado**: se ejecuta solo en el sandbox, sin secretos.
