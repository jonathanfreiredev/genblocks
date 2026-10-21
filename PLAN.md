# GenBlocks — Plan de ejecución

Este documento es la fuente de verdad del plan. Recoge las decisiones cerradas y
las que van cerrando las fases, y las ordena en rebanadas ejecutables, pensadas
para que cada una se pueda revisar en `git` y entender sin perderse.

El código, los identificadores, los comentarios y los mensajes de commit van en
inglés (ver `AGENTS.md`). Este documento va en español por comodidad.

---

## 0. Cómo leer este documento

- **Secciones 1–11**: qué construimos, cómo está decidido y por qué. Contexto.
- **Sección 12**: el plan de ejecución por fases. Es el núcleo. Cada fase se
  entrega como una rebanada revisable en `git`.
- **Secciones 13–15**: variables de entorno, lo aplazado y los riesgos.

**Estado (oct 2026)**: fases **0–12 hechas**. La 11 se entregó en cuatro
rebanadas (checks estáticos, cupo mensual, moderación y caché por brief) y la 12
en una (traza opcional). La 9 se entregó en tres rebanadas y la 10 cerró con la
capa de vectores, el guard de duplicados, el reúso de imágenes, el routing de
taxonomía y las propuestas en el chat. La 13 es contenido, no código. El historial
de migraciones se consolidó en dos (initial schema + consolidada) antes de
sembrar: las vueltas de ideas no valían como historia. Las fases anteriores se
quedan escritas como se entregaron: son el registro de lo
construido, no una promesa pendiente. Las decisiones antiguas tampoco se
reescriben: cuando una cambia, la nueva dice a cuál sustituye.

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
5. **Agente conversacional**: una sola superficie, el **asistente del vault**, en
   un dialog de shadcn. Responde sobre bloques e imágenes y también convierte una
   petición en una tarea; la conversación no termina al arrancar la generación. El
   id del hilo vive en `localStorage`; el transcript, en memoria.
6. **Reintentos**: máximo **2 intentos** (1 reintento). Publica el primer intento que
   pasa todos los umbrales; si ninguno, el de mayor puntuación.
   → *Sustituida en la Fase 9 por la 30: el bucle vive dentro del harness y el
   juez es una puerta.*
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
26. **La conversación se pinta con los primitivos AI de shadcn**
    (`MessageScroller`, `Message`, `Bubble`, `Marker`, `Trace`) sobre
    `@shadcn/react`. El scroll-follow, el jump-to-latest y la conservación del
    ancla son suyos; las tools se cuentan como un `Trace` con spinner mientras
    corren y check al terminar.
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
    → *Con la puerta de la Fase 9 hay **un artefacto por tarea**: la fila sigue
    siendo donde vive lo que esa corrida produjo —código, checks, render y scores,
    que es lo único que deja legible un rechazo—, pero ya no hay lista que recorrer
    y el frontend no la enseña: se ve **el resultado**, no un historial. El
    `attempt_no` se queda en 1 y su índice único es lo que garantiza "una tarea, un
    artefacto".*
    → *La Fase 9 sustituye el bucle exterior por el del harness (decisiones 30–32).
    Se quedan la puerta, la calibración y el motivo del rechazo.*
30. **El harness es un bucle acotado, con el sandbox como ojos.** El paso de generar
    deja de ser una llamada y pasa a ser un agente (`create_agent` de LangGraph, el
    mismo motor que la conversación) que escribe, construye, **mira el render** y
    edita, hasta que decide que está. **No hace falta un DeepAgent**: lo que aporta
    aquí es ver el artefacto y tener las skills, no la planificación ni los
    sub-agentes, y el sistema de ficheros ya lo pone el sandbox. El bucle **exterior**
    de la Fase 8 (reintento ≤ 1, margen, "el más cercano") se retira en cuanto
    existe éste: hacían el mismo trabajo a distinta resolución.
    - **El render vuelve como resultado de herramienta**, y se probó antes de
      construir nada: el resultado de `look` lleva el informe y la imagen, así que
      el bucle es `create_agent` con el sandbox como una herramienta más —sin nodo
      propio— y el tope de vueltas se lleva por herramienta, no por turno del
      modelo.
31. **El juez es la puerta, no el volante.** Una corrida del juez, al final de todo.
    Si el artefacto no pasa el listón, la tarea falla con el motivo delante
    (dimensión, número y la frase del juez) y el artefacto se queda **visible en la
    tarea**, fuera de la biblioteca: **la biblioteca solo contiene piezas que
    pasaron su listón**, y eso es un invariante del producto, no una promesa.
    Reintentar es una decisión humana, con el brief delante — **y por ahora no se
    ofrece desde la interfaz**: la puerta y el endpoint están (`POST /v1/tasks`, el
    mismo encolar que usa todo lo demás), el botón no. El bucle de reintento del
    pipeline se retiró con la Fase 9 (`max_attempts` incluido): el único bucle es el
    de dentro del harness.
32. **Vueltas contadas, no guardadas.** El tope de iteraciones es un ajuste
    (`harness_max_iterations`) y **el número sale de medirlo**, no de la prudencia:
    se arranca alto, se mira la distribución real y si la vuelta n mejora el score.
    Además del tope hay parada por **no-progreso** (los mismos checks fallando, o el
    código sin cambios): eso permite ser generoso con el tope sin pagar la rueda del
    ratón. Las vueltas se cuentan (`iterations` en el detalle del paso); lo que se
    guarda es el artefacto final.
33. **Las dependencias entran, con lista blanca y una regla.** Preinstaladas en la
    imagen del sandbox —nada de `npm install` por corrida, que se lleva por delante
    los 5 s y el determinismo— y del juego de la casa: `motion`, `@base-ui/react`,
    `lucide-react`, `clsx` + `tailwind-merge`, y `class-variance-authority`. La base
    es siempre React + Tailwind v4 + primitivas.
    - **Regla de admisión: traen comportamiento, no aspecto.** Tailwind v4 no
      escanea `node_modules`, así que un paquete que traiga clases no se compilaría;
      el aspecto lo pone Tailwind y lo puntúa el juez.
    - Las **preferencias** ("motion cuando hace falta muelle, orquestación o salida;
      CSS nativo cuando basta; una primitiva cuando de verdad hay foco y teclado que
      gestionar") son una skill, no una lista.
    - Las dependencias del bloque se **deducen de sus imports** (determinista, no
      opinión del modelo) y se enseñan en el panel con el comando de instalación.
      Un import fuera de la lista es un check **fatal**: compilaría, pero el usuario
      no lo podría instalar.
    - **Dónde vive la lista**: en el scaffold (`app/harness/scaffold/package.json`).
      El check `imports` del sandbox lee los ficheros que le manda el llamante —el
      bloque, no el scaffold— y los compara con esas dependencias, así que la lista
      y lo que se instala no pueden discrepar. React y React DOM no cuentan en la
      línea de instalación del panel: son el medio, no algo que el bloque pida.
34. **El bloque es un proyecto, no un fichero.** El agente trabaja sobre varios
    ficheros (`write_file`/`read_file`) con `src/Block.tsx` como entrada, así que un
    formulario puede componetizarse. Se guarda `files` (jsonb) en `components` y en
    `generations`, y `entry` dice cuál de esos ficheros es el bloque: una ruta, no
    una copia del texto. El panel del item gana pestañas por fichero.
    → *Primero se guardó además `code`, el texto de la entrada copiado al lado, para
    no romper la lectura publicada. Al no haber clientes fuera del repo se retiró:
    `code` era `files[entry]` duplicado, y la UI ordenaba las claves para elegir
    fichero (y abría `src/App.tsx` antes que `src/Block.tsx`). Hoy `files` + `entry`
    es la única forma.*
35. **Motion con dependencia y con reglas.** `motion` más CSS nativo cuando basta.
    Dos cosas que son de checks y no de gusto: el screenshot **espera a que la
    animación aterrice** (`document.getAnimations()`, o la foto del ledger saldrá a
    medias y el juez puntuará el temblor), y `prefers-reduced-motion` es criterio de
    **accesibilidad**. El motion se puntúa dentro de `visual` por ahora; dimensión
    propia solo si los datos dicen que mueve scores.
36. **Las imágenes se generan una vez, y tarde.** Una sola pasada de imágenes cuando
    la estructura está decidida —nunca por vuelta: una imagen no cambia con la
    maquetación— seguida de **una vuelta de verificación** con las fotos reales, para
    que el artefacto no se edite después de que los ojos dejaran de mirar. Los huecos
    de relleno llevan la **proporción final** y son identificables: eso es lo que hace
    seguro el intercambio. Tope de imágenes por bloque en settings, y reemplazar un
    hueco como mucho una vez.
    - Los assets vienen **de nuestra biblioteca** (fila en `images`), nunca de fuera:
      es lo que corrige la frase de la Fase 8, que decía "ninguna imagen de fuera"
      cuando un bloque todavía no podía tener imágenes. Se enlazan en
      `component_assets` al publicar.
    - El bloque copiado carga nuestras imágenes del CDN. Es la historia de cualquier
      stock, pero **se dice en el panel**, no se deja implícito.
37. **Las skills son los principios; la rúbrica es el criterio.** El escritor lee
    skills (cómo se construye bien en este medio); el juez lee su rúbrica (cómo se
    puntúa). Las dos tienen que ser la misma tradición o el bucle oscila: el agente
    arregla lo que nadie mira y deja lo que sí se puntúa. Al escritor **no** le llegan
    la rúbrica literal ni los umbrales: quien sabe dónde está el listón escribe notas,
    no bloques. Las skills se leen con **índice + `read_skill`** (divulgación
    progresiva): el índice va en el system prompt, que es lo que se cachea.
38. **Dos fondos, y el tema es de la plataforma.** El registro cambia toda la
    biblioteca a la vez poniendo `dark` en la página, así que el `dark:` del bloque
    cuelga de esa clase (`@custom-variant` en el scaffold) y **nunca** de
    `prefers-color-scheme`: lo que sigue al sistema ignora el interruptor del
    visitante. Los colores se escriben como **pares literales**
    (`bg-white dark:bg-neutral-950`), no como tokens: el bloque se copia a proyectos
    ajenos y tiene que funcionar solo, sin arrastrar una hoja de tema. El sandbox
    fotografía la misma página en claro y en oscuro, corre axe en los dos esquemas
    (checks `accessibility` y `accessibility:dark`, con su `scheme` en cada
    violación) y **el juez recibe las dos imágenes**: un bloque que solo aguanta un
    fondo es medio bloque. Cloudinary guarda solo la clara, que es la miniatura; la
    oscura viaja al juez como bytes y no se almacena. El `look` del agente también
    enseña las dos: quien no ve el fondo que se puntúa no puede arreglarlo.
    - *El botón de la plataforma no existe todavía: necesita el render vivo. Lo que
      existe es el código que lo soporta, verificado en cada corrida.*
    - *Los 6 bloques sembrados siguen siendo claros y literales: no pasan por el
      sandbox y el interruptor aún no está. Cuando llegue, se les añade el par (o se
      re-siembran), o el toggle se limita a lo generado.*
39. **La recuperación es una mejora, nunca una dependencia.** El embedder y el
    store están detrás de un servicio que degrada: si fallan, recordar es un aviso
    en el log y buscar no encuentra nada. Un bloque se publica aunque no se pueda
    indexar, y el chat funciona aunque Voyage esté caído. Lo que sí es una puerta
    es el **guard de duplicados**: un brief que está a menos de
    `duplicate_distance` del registro no encola, y el agente enseña lo que ya
    existe. La barra se midió (duplicados 0,40–0,47; lo ajeno 0,77+) y se puede
    **argumentar**: `create_component` acepta `force` cuando la persona ha dicho
    que quiere la suya.
    - *Los bloques e imágenes que el agente encuentra viajan al diálogo como
      evento `suggestions`, no como prosa: se dibujan en un riel horizontal y cada
      tarjeta abre el item. Una sugerencia que no se puede pulsar es un párrafo.*
40. **La taxonomía la elige el modelo, pero la lista es del registro.** `spec` deja
    de ser canned: se le pasan los tipos (slug + nombre) y los cinco bloques más
    cercanos con el tipo bajo el que están archivados, y responde **un slug de esa
    lista**. Un slug que no existe no es un tipo nuevo: es un fallo de la corrida,
    como una respuesta ilegible del juez. La copia —título y descripción— sigue
    siendo determinista: nunca fue una decisión. Es la primera llamada al LLM que
    no produce el artefacto, y va antes del sandbox, así que equivocarse ahí no
    cuesta un render.
41. **Lo que un bloque no puede hacer se decide sin mirarlo.** Los dos checks
    estáticos (`assets`, `safety`) son **fatales** y corren dentro del `look`, no
    solo al final: un fallo que el agente no puede leer es un fallo que se convierte
    en tarea muerta, y el bucle de arreglo es justo lo que hace que el harness valga.
    El alcance de `safety` queda cerrado en lo que significa "esto va dentro de la
    página de otro": nada de red (`fetch`, `XMLHttpRequest`, `WebSocket`,
    `EventSource`, `sendBeacon`) y nada de ejecutar o inyectar cadenas (`eval`,
    `new Function`, `document.write`, `dangerouslySetInnerHTML`, `javascript:`).
    Es un chequeo de texto y lo dice: una URL construida en ejecución se le escapa,
    y para eso está el juez. Un comentario que menciona `fetch(` no es una llamada.
    Un proyecto bloqueado tampoco pide imágenes: primero se arregla, luego se paga.
42. **El cupo es producto, no factura.** 10 bloques por mes natural (UTC) y
    persona. Cuenta la tarea creada, falle o no: el fallo gastó sandbox e imágenes,
    y devolverlo al cupo sería regalar la corrida. No hay cortacircuitos global en
    código a propósito: el gasto se corta en los dashboards que facturan (Modal,
    OpenAI), y un segundo número aquí sería una copia que se desvía de la real. Las
    tres puertas —API, MCP, conversación— pasan por `enqueue_task` y dicen la misma
    frase. Un brief cacheado no consume cupo, porque no encoló trabajo.
43. **La moderación es una puerta, no una puntuación.** El brief se modera antes
    de que exista la tarea; la **copia que el bloque muestra** (nodos de texto y
    cadenas que leen como prosa, no el código), después del harness y antes de las
    imágenes, del render y del juez. Un rechazo de entrada no escribe nada (422);
    uno de salida deja la tarea fallida con el motivo y sin intento, porque un
    intento es un artefacto y el artefacto no se publica. Sin clave la comprobación
    está apagada y lo dice en el log; con clave y proveedor caído **falla cerrada**:
    "no pudimos comprobar" y "pasó" no pueden tener la misma forma. La copia se
    recorta a 2.500 caracteres: el free tier del modelo son 2.000 tokens por
    minuto, y un proyecto entero no cabe — un 413 no es una negativa, es una
    puerta que nunca se abre.
44. **La caché es exacta y es un recibo.** El brief normalizado (minúsculas,
    espacios colapsados) apunta al bloque que lo respondió. Un acierto no es una
    decisión de producto: no pregunta, no modera, no gasta cupo y no construye;
    devuelve una tarea `succeeded` con `cached` y un paso que lo dice, para que el
    contrato de la UI —encolar y seguir una tarea— siga siendo el mismo. Se escribe
    en la transacción que publica, se reescribe si el brief se construye dos veces,
    y un bloque borrado es un fallo de caché. La paráfrasis no entra aquí: para eso
    está el guard, que sí pregunta.
45. **La traza es una copia, y se escribe después del commit.** Postgres decide
    qué pasó; Langfuse lo cuenta. El id de la traza es nuestro (32 hex), se guarda
    en la tarea antes de que el run termine y en el intento y las imágenes al
    crearse, así que el enlace del panel resuelve aunque la corrida siga. Los
    scores se empujan después del commit del intento; los spans, mientras ocurren,
    porque el SDK los bufferiza y los exporta en un hilo de fondo. Sin las dos
    claves no hay cliente ni ids; con ellas y el proveedor caído, un warning y
    nada más. Se usa el **SDK v5 sobre OTel** porque la API de ingesta v3 de
    Langfuse Cloud se apaga el 16/11/2026 para todo lo que no sean scores: escribir
    OTLP a mano habría sido una dependencia con fecha de caducidad.

---

## 3. Arquitectura

### Puertas

- **Web (Next.js)**: galería, item, vista de tarea, dialog de generación.
- **API (FastAPI)**: lo que consume la web.
- **MCP (FastMCP)**: los mismos servicios, para agentes externos (Claude Code,
  opencode…).
- **Modal**: sandbox de ejecución y render. Efímero, CPU, sin secretos; no alcanza
  nada nuestro — el navegador sí sale a la red pública, que es lo que hace falta
  para ver un bloque con fotos o con un paquete instalado.

### Flujo de generación

```
brief → [conversación] → create_component → tarea (background)
                                              │
                        spec → harness (agente) → judge (puerta) → commit
                                   │   ▲
                         sandbox ──┘   └── render + checks
```

- **spec**: retrieval de taxonomía + vecinos (para no duplicar) + guía; escribe el
  spec y el prompt de entrega. Primer uso del LLM. Sigue siendo canned hasta la
  Fase 10.
- **harness**: **un agente** con las skills y el sandbox como herramientas. Hace su
  propio bucle —escribe, construye, **mira** el render, edita—, decide las imágenes
  (una pasada, al final, con una vuelta de verificación detrás) y entrega un
  proyecto: varios ficheros, sus dependencias y sus assets. Un solo step visible, de
  minutos, con latido de progreso.
- **judge**: una corrida al final, sobre los artefactos del harness. **Es una
  puerta**: si no pasa, no se publica nada.
- **commit**: crea el componente, enlaza los assets, sube el screenshot, lo embebe,
  fija taxonomía y publica.

Los **steps visibles** son cuatro: recuperar, generar, juzgar, publicar. El bucle del
agente no se ve edición a edición (se cuenta en `iterations`, en el detalle del
paso): lo que un lector sigue es el trabajo, no cada guardado.

### Modelo de datos (Postgres)

| Tabla | Campos clave |
|---|---|
| `categories` | id, parent_id, kind(component\|image), slug, name, level |
| `components` | id, slug, title, description, category_id, `files` jsonb, `entry` (ruta del fichero del bloque), `dependencies` jsonb, delivery_prompt, spec, winning_generation_id, created_by, license, created_at |
| `generations` | id, task_id, component_id, attempt_no, `files` jsonb, `entry`, screenshot_path, scores jsonb, verdict, rubric_version, model, langfuse_trace_id |
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
`search_images`, `get_image`, `get_task`, `list_tasks`.

**Planificación:** `plan_component`, `plan_image`.

**Escritura:** `create_component`, `generate_image`.

`vary_component` se implementa en una fase posterior; se reserva el nombre.

---

## 7. Rúbrica y bucle

Dimensiones 0–100, cada una con su umbral (no basta la media):

| Dimensión | Cómo se mide |
|---|---|
| Render | compila y pinta sin error en 3 viewports; sin overflow ni clipping; con la animación ya aterrizada |
| Accesibilidad | contraste calculado, focus visible, roles y labels; `prefers-reduced-motion` respetado |
| Visual (VLM) | jerarquía, espaciado, alineación, anticliché — y motion con intención |
| Copy | coherente y plausible (nada de lorem ipsum ni «Acme Inc.») |
| Cumplimiento | ¿hace lo que el brief pidió, y se puede copiar tal cual? |
| *Novedad* | **aplazada**: es distancia vectorial a la biblioteca, y llega con los vectores (Fase 10) |

Hoy el panel de un componente puntúa **cinco** dimensiones y el de una imagen
**tres**. La sexta, novedad, se suma cuando exista contra qué medirla.

- **Dos bucles, uno dentro del otro.** El de dentro es del **harness**: el agente
  mirando su propio render y arreglándolo, con tope de vueltas (decisión 32). El de
  fuera es del **juez**, y es una **puerta**: una corrida al final y, si no pasa, la
  tarea falla con el motivo (decisiones 30 y 31).
- **Independencia**: el agente puede —debe— autorevisarse el render, que para eso
  tiene ojos; pero **puntúa otro**: agente, run y rúbrica separados.
- **Las skills son los principios y la rúbrica es el criterio** (decisión 37): el
  escritor lee skills de este medio, el juez lee la rúbrica, y las dos tienen que ser
  la misma tradición o el bucle oscila.
- La **rúbrica vive como skill** y la lee el juez: una para componentes, otra más
  corta para imágenes. Su **versión es el hash del texto**, y se estampa en cada
  intento para poder releer un score contra el texto que lo produjo.
- Los umbrales se **calibran** contra generaciones reales, no a ojo, y **no se le
  dicen al juez**.

**Imágenes.** Las dimensiones de arriba son de un componente: una imagen no se
renderiza ni lleva copy. Su rúbrica es corta —**visual**, **prompt_fit**,
**compliance**— y pasa por el mismo juez antes de entrar en la biblioteca; quien la
llama es la tool de imágenes (Fase 9). Así el panel del item es idéntico en las dos
vistas: a la derecha, los scores de la generación y el enlace a su trace.

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

- **Modal**: CPU. Una tarea con un bucle de 3–4 vueltas son 3–4 sandbox ≈ $0.02–0.05.
- **LLM (luna)**: el coste dominante, porque cada vuelta reenvía el render (una
  imagen de ~100 KB) y la conversación. Por tarea, del orden de $0.10–0.40. Lo bajan
  la caché de prompt (skills y rúbrica van al principio y son estables), el tope de
  vueltas, la parada por no-progreso y el guard de duplicados.
- **Imágenes (BFL)**: la partida con más pico —una galería de ocho fotos cuesta más
  que el resto de la tarea junta—. De ahí el tope por bloque (decisión 36) y, desde
  la Fase 10, mirar la biblioteca **antes** de generar.
- Mitigaciones: guard de duplicados, reúso de imágenes, tope de vueltas y de
  imágenes, rate limit por usuario, caché por brief, cortacircuitos global.

---

## 10. Fuera de alcance (no implementar)

- RAG sobre código o shaders externos.
- Guías de diseño de terceros: el gusto vive en skills propias de este medio
  (decisión 37), finas y escritas para un bloque de un fichero y Tailwind genérico.
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

**Estado**: **0–12 hechas** (cada una, un commit). La 13 —sembrar y curar la
galería— es contenido, no código, y va después. Todas se quedan como se
entregaron.

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
  `search_images`, `get_image`, `list_tasks`, `get_task`.
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
  sin agente todavía).
- Subida del screenshot a **Cloudinary** (`genblocks/screenshots/`).

**Verificación**: una tarea produce un screenshot real y los informes de checks.

**Fuera**: sin agente ni skills; sin embeddings.

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

**Fuera**: todavía sin bucle de agente ni RAG. El bucle de reintento que trae esta
fase se retira en la 9, cuando el bucle viva donde tiene que vivir (decisión 30).

### Fase 9 — El harness con ojos (agente, skills y medio real)

> **Fase larga, en tres rebanadas.** La primera cambia la **forma del pipeline**; la
> segunda, la **forma del artefacto**; la tercera añade un **tipo de artefacto**
> nuevo. Cada una se revisa sola y se puede parar entre medias.

**Objetivo**: que el bloque se construya de verdad —mirándolo, arreglándolo, con las
dependencias y las animaciones que un bloque de producción necesita— y que el juez
sea la puerta, no el volante.

#### 9a — El bucle con ojos, y el medio que necesita

- El paso de generar deja de ser una llamada: es un **agente** (`create_agent` de
  LangGraph, el mismo motor que la conversación) con el **sandbox como herramienta**.
  Escribe, construye, **ve el render y los checks**, edita, y decide cuándo está.
  Tope de vueltas en settings y parada por **no-progreso**; las vueltas se cuentan
  (`iterations` en el detalle del paso), no se guardan (decisiones 30 y 32).
  - **Sonda primero**: el render no vuelve como resultado de herramienta, así que la
    vuelta se monta como **nodo del grafo** (modelo → sandbox → mensaje con el informe
    y la imagen → modelo). Se prueba antes de construir nada.
- **Skills** versionadas en `app/harness/skills/`, leídas con **índice +
  `read_skill`** (decisión 37). Finas y de este medio: accesibilidad de un bloque,
  jerarquía y composición, motion, y los clichés que este registro no publica —
  empezando por los que la Fase 8 vio fallar en vivo.
- **Dependencias**: lista blanca preinstalada en la imagen del sandbox, del juego de
  la casa y con la regla de admisión de la decisión 33. Prompt del escritor y
  sección "qué es un bloque" de la rúbrica, reescritos; las dependencias se deducen
  de los imports, se enseñan en el panel y un import fuera de la lista es un check
  **fatal**.
- El juez pasa a ser **puerta** (decisión 31): se retira el bucle exterior de la
  Fase 8 (margen y "el más cercano"), `max_attempts` queda en 1, y el motivo del
  rechazo va en el error de la tarea. El intento sigue visible en la tarea.

#### 9b — Multi-fichero y motion fino

- El agente trabaja sobre un **proyecto** (`write_file`/`read_file`): un formulario
  puede componetizarse en `Field`, `Label`, `Error`. `files` (jsonb) y `entry` en
  `components` y en `generations`, y pestañas por fichero en el panel del item
  (decisión 34).
- El screenshot **espera a que la animación aterrice** y `prefers-reduced-motion` es
  criterio de accesibilidad. El motion se puntúa dentro de `visual` (decisión 35).

#### 9c — Imágenes

- Tool `generate_image`: BFL (`flux-2-pro`), asíncrona —encolar, sondear, descargar—
  y subida a Cloudinary (`genblocks/images/`). Devuelve la URL y deja la fila en
  `images`; la rúbrica corta del juez la puntúa al entrar en la biblioteca. El nombre
  es el que reserva la sección 6; su registro en la puerta MCP (para agentes
  externos) es aparte, igual que el resto de tools del agente (decisión 25).
- **Una sola pasada, tarde, y con una vuelta de verificación detrás** (decisión 36):
  nada de imágenes por vuelta, huecos de relleno con la proporción final, tope por
  bloque en settings, y los assets enlazados en `component_assets` al publicar.

**Verificación**: un brief de cada tipo termina en un componente publicado con su
render, su score y sus dependencias declaradas; un artefacto flojo lo tumba el juez y
la tarea falla con el motivo (nada entra en la biblioteca); el A/B de los mismos cinco
briefs **con y sin skills**, comparando dimensiones, para saber si las skills sirven
de algo; y la distribución de `iterations` para fijar el tope con datos.

**Notas**: medido en vivo, con corridas reales: las vueltas fueron 1, 2, 2, 3 y 5
(mediana 2), así que el tope de 6 es techo y no objetivo. El juez tumbó dos de las
seis —un héroe por leer «una línea de copy» al pie de la letra, y una galería por
pedir cuatro veces el mismo prompt, que devolvió casi la misma foto cuatro veces— y
las dos se arreglaron donde tocaba: la primera en la rúbrica (un brief se lee como
lo leería un diseñador, no como una hoja de especificaciones) y la segunda en la
herramienta (el mismo prompt dos veces se rechaza, y la skill dice que cada imagen
es su propio asunto). Con eso, el mismo brief del héroe publicó: compliance 96 y una
sola vuelta. **La biblioteca quedó limpia de las dos**, que es lo que la puerta
promete. El spec sigue canned (la taxonomía por RAG es la Fase 10).

**Fuera**: sin RAG (guard, reúso de imágenes y taxonomía) y sin moderación.

### Fase 10 — RAG / Chroma

**Objetivo**: recuperación, guard de duplicados y reúso de imágenes.

**Cambios**
- Cliente Chroma (dev `PersistentClient`; config para Chroma Cloud).
- Colecciones `components` e `images`; embeddings con `voyage-multimodal-3`.
- Embeber el screenshot en `commit`; embeber la imagen cuando entra en la
  biblioteca.
- **Guard de duplicados** (brief ↔ componentes) antes de generar.
- **Reúso de imágenes**: el agente mira la biblioteca **antes** de generar y solo
  genera lo que falta, así que `generate_image` deja de ser el camino por defecto.
- **Routing de taxonomía** por RAG en `spec`, que deja de ser canned: es el primer
  uso real del LLM en ese paso.

**Verificación**: el guard detecta un duplicado; una imagen se reutiliza; un brief
recibe el tipo correcto.

**Entregado.** Verificado en vivo contra el dataset sembrado: un brief que repite
un bloque queda a **0,40–0,47** de distancia y se reconoce como duplicado; lo que
no tiene que ver queda en **0,77+**. El routing eligió `pricing` para un brief de
tabla de precios, con los cinco bloques más cercanos como evidencia. La biblioteca
se siembra con 12 filas recordadas en dos peticiones (Voyage free tier son 3/min).

Dos correcciones que la verificación obligó:

- `embed_text` devolvía la lista del embedder (una lista de vectores) en lugar del
  vector, así que **Chroma rechazaba toda consulta** y la búsqueda no encontraba
  nada nunca. El guard y los ejemplares estaban muertos en silencio. Hay test.
- El umbral inicial (0,18) era una suposición; con lo medido se quedó en **0,50**
  para duplicados y **0,45** para reúso de imágenes.

**Fuera**: sin guías (descartadas por ahora).

### Fase 11 — Endurecimiento

**Objetivo**: que se pueda exponer al público sin sustos.

**Cambios**
- Moderación de entrada/salida (Groq Safety).
- Rate limit por usuario y **cortacircuitos global** de gasto, comprobado antes de
  encolar.
- Caché por brief.
- **Los checks mecánicos que faltan del harness**: referencias a assets externos
  (hoy es una frase en la rúbrica y el juez lo penaliza, pero no lo impide nada) y
  el alcance definitivo de la comprobación de "seguridad" del código generado.

**Verificación**: límite y tope se activan; un brief abusivo se rechaza; un bloque
que apunta a un asset de fuera no se publica.

**Entregado (11a).** `app/harness/checks.py`: dos checks sobre el texto del
proyecto, `assets` y `safety`, ambos fatales y en la misma lista que el sandbox.
Lo importante del diseño no es el regex sino **dónde corre**: en `look`, así que el
agente se entera del fallo mientras puede arreglarlo, y antes de Modal, así que un
proyecto que apunta fuera no cuesta un render. Un bloque que no pasa los checks
tampoco pide imágenes: no se paga una foto para un proyecto que no puede
publicarse. El host permitido es configuración (`allowed_asset_hosts`), no un
literal enterrado. Tests: las cuatro formas de cargar (atributo, `<link>`, `url()`,
`@import`), `srcset` candidato a candidato, `//host`, puerto y credenciales,
comentarios que mencionan `fetch(` sin llamarlo, y el sandbox que no se llama.

**Entregado (11b).** `app/tasks/limits.py` y `enqueue_task`: **10 bloques por mes
natural** (UTC) y persona, contados sobre `tasks`. Falle o no una tarea, cuenta: un
fallo gastó sandbox e imágenes. La negativa es 429 en la API, un `ValueError` en
MCP y un texto en la tool del agente — las tres puertas dicen lo mismo. No hay
tope global en código: el gasto se corta en los dashboards de Modal y OpenAI, y un
segundo número aquí sería una copia que se desvía del real. Tests: el borde del
mes, diciembre que cruza de año, el mes pasado, las tareas de otra persona, una
tarea borrada que devuelve el cupo, y que la negativa no escribe fila.

**Entregado (11c).** `app/moderation/service.py`: Groq
`openai/gpt-oss-safeguard-20b`, JSON estricto. **Entrada**: el brief antes de que
exista la tarea (422, nada se escribe). **Salida**: la copia que el bloque muestra
—nodos de texto y cadenas que leen como prosa, no el código—, antes de las
imágenes, del render y del juez (tarea fallida, sin intento, sin gasto). Sin clave está **apagada** y lo dice en el log; con clave y proveedor
caído **falla cerrada**, porque "no pudimos comprobar" no puede parecerse a "pasó".
Verificado contra Groq real: permite una pricing page y rechaza un clon de login
bancario con su motivo.

**Entregado (11d).** `app/briefs`: tabla `brief_cache` (clave normalizada a
minúsculas y espacios, única) y `tasks.cached`. El acierto devuelve una tarea
**ya terminada** con un paso "Found in the registry" y el bloque enlazado: el
contrato de la UI no cambia, cambia el estado en que nace. No gasta cupo, no
modera y no construye. La entrada se escribe en la **misma transacción** que
publica el bloque, y se reescribe si el mismo brief se construye dos veces. La
paráfrasis no es asunto suyo: eso es el guard, que pregunta. La API responde 200
en vez de 202 cuando la tarea nace terminada, y el diálogo lo dice.

**Fuera**: nada de features nuevas.

### Fase 12 — Observabilidad (opcional)

**Objetivo**: trace sin que la observabilidad pueda tumbar el producto.

**Cambios**
- `langfuse_trace_id` nullable; push de scores en **fire-and-forget** después del
  commit en Postgres; enlace al trace en la UI (con "no disponible" si falta).
- Aquí viven también **las palabras que el ledger no guarda**: las notas y el
  resumen del juez (hoy solo viajan en el error de la tarea rechazada) y las vueltas
  del agente. El ledger tiene los números; la traza tiene el porqué.

**Verificación**: el trace aparece cuando Langfuse está configurado y la app
funciona igual cuando no lo está.

**Fuera**: Langfuse no es fuente de verdad de nada.

**Entregado (12).** El SDK **v5 de Langfuse** sobre OpenTelemetry, no la API de
ingesta: Langfuse Cloud deja de aceptar trazas por `/api/public/ingestion` el 16
de noviembre de 2026 y solo mantiene los scores, así que el SDK es el único camino
que sigue vivo sin escribir OTLP a mano. `app/observability/service.py` envuelve
el cliente para que el resto del código no sepa que existe:

- **La traza es una copia y se escribe después.** El id lo generamos nosotros y se
  guarda en `tasks.langfuse_trace_id` (antes del commit de la checklist, para que
  un lector pueda seguir una corrida en marcha), en el intento y en cada imagen.
  Los scores se empujan **después** del commit del intento: un número en Langfuse
  que Postgres no tiene es un score sin artefacto detrás.
- **Lo que el ledger no guarda.** Cada paso es un span; el del juez lleva sus
  notas, su resumen, los umbrales que falló y la versión de la rúbrica, y el del
  harness lleva **las vueltas** (una por look, con el informe del sandbox y lo que
  el proyecto tenía entonces). El checklist guarda `iterations`; la traza guarda
  el porqué.
- **No puede tumbar nada.** Sin las dos claves no se construye cliente y todos los
  ids quedan nulos; el SDK exporta desde un hilo de fondo, y cada llamada de la
  envoltura está guardada: un span que no se puede serializar deja una línea en el
  log y el paso sigue. Verificado con un colector local: el SDK manda el lote a
  `/api/public/otel/v1/traces` (cabecera `x-langfuse-ingestion-version: 4`) y los
  scores a `/api/public/scores`.
- **La UI.** El panel de evidencia ya enseñaba el id o "Not recorded"; con
  `NEXT_PUBLIC_LANGFUSE_HOST` el id es un enlace a `/trace/{id}`. Sin host, el id y
  el botón de copiar, que es lo que hay que hacer igual.

**Verificación hecha**: la suite entera corre con las claves vacías y publica
igual; con claves (contra un colector que acepta y registra) salen la traza y los
scores con el id de la tarea.

**Fuera**: nada de features nuevas; la conversación del agente no se traza, solo
la corrida que construye.

### Fase 13 — Siembra y lanzamiento

**Objetivo**: abrir la galería con archivo, no vacía.

**Cambios**
- Sembrar la librería de imágenes.
- Generar y **curar a mano** 15–20 componentes con la rúbrica puesta, empezando por
  las categorías con más peso visual (hero, pricing, testimonios, features).
- No publicar la galería hasta tenerlos.

**Verificación**: galería poblada y navegable.

**Fuera**: features nuevas.

**Herramientas de siembra**: `python -m app.seed.screenshots` renderiza los bloques
sembrados por el sandbox real y guarda la captura en Cloudinary; `python -m
app.seed.stock` genera las imágenes que el seed solo describe. Las dos son
idempotentes y se saltan lo que ya existe.

### Después (no en este plan)

- `vary_component`.
- Edición del componente por prompt y edición de su código.
- Render en vivo seguro.
- Descargar los assets con el bloque (hoy apuntan a nuestro CDN).

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
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | traza opcional; sin ambas no se envía nada |
| `LANGFUSE_HOST` | host de Langfuse (Cloud EU por defecto) |
| `VOYAGE_API_KEY` | embeddings (`voyage-multimodal-3`) |
| `CLOUDINARY_CLOUD_NAME` | storage (y `NEXT_PUBLIC_...` en el frontend, para leer) |
| `CLOUDINARY_API_KEY` | storage |
| `CLOUDINARY_API_SECRET` | storage |
| `NEXT_PUBLIC_LANGFUSE_HOST` | frontend: enlace al trace en el panel (opcional) |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | invocar el sandbox |
| `CHROMA_HOST` / `CHROMA_API_KEY` / `CHROMA_TENANT` / `CHROMA_DATABASE` | vectores (Chroma Cloud en prod) |

Los servicios `backend` y `mcp` del compose ya leen el mismo `backend/.env`.

Los **mandos del bucle** no hacen falta en `.env`: tienen valores por defecto en
`app/settings.py` y se cambian ahí o por entorno —`RUBRIC_THRESHOLDS`,
`MAX_ATTEMPTS`, `HARNESS_MAX_ITERATIONS`, `IMAGES_PER_BLOCK`—.

---

## 14. Aplazado a propósito

- Afinar los umbrales con más generaciones (la primera calibración está hecha, con
  siete).
- Alcance de la comprobación de "seguridad" del harness (Fase 11).
- Chroma: detalle de despliegue en prod.
- Proveedor de hosting del despliegue.
- **El brief como entidad duradera**: hoy reintentar crea otra tarea y el historial
  del item es el de la tarea que publicó (`parent_task_id` o una tabla `briefs` es
  lo que lo cambiaría). Se decide con uso.
- **Reintentar desde la interfaz**: la política y el endpoint están
  (`POST /v1/tasks`); el botón en la tarea fallida —con el brief delante y el
  motivo del juez al lado, sin meterlo dentro del brief— no se ofrece por ahora.
- `tw-animate-css` en el scaffold, y si el motion merece **dimensión propia** en la
  rúbrica (hoy va dentro de `visual`).
- **Dependencias fuera de la lista blanca**, declaradas por el propio bloque:
  cambia la historia de copiar y trae deriva de versiones.

---

## 15. Riesgos

- **Coste**: vueltas del agente × visitantes, más las imágenes. Mitigado con tope de
  vueltas y de imágenes, parada por no-progreso, guard de duplicados, reúso, rate
  limit y cortacircuitos.
- **Oscilación del agente**: puede arreglar una cosa y romper otra. Mitigado con la
  parada por no-progreso y el tope (decisión 32); el que avanza sigue, el que no, se
  corta.
- **Coste de las imágenes**: una galería puede costar más que el resto de la tarea
  junta. Tope por bloque y, desde la Fase 10, reúso de la biblioteca.
- **Deriva de versiones**: el bloque se construye contra nuestras dependencias
  (`motion@13`, `@base-ui/react@1.7`); copiarlo a un proyecto con otras puede pedir
  ajustes. Por eso se declaran y se enseñan en el panel.
- **Los assets viven en nuestro CDN**: copiar un bloque no copia sus imágenes. Es la
  historia de cualquier stock, pero se dice en el panel — y queda decidir si algún
  día se descargan con el bloque.
- **El listón puede dejar la biblioteca vacía**: si el juez es más duro que el
  agente, casi todo falla. Mitigado porque el escritor lee los mismos principios
  (decisión 37), y vigilado con la tasa de publicación.
- **Latencia de Modal**: arranque en frío + navegador = minutos, y ahora además unas
  vueltas. Por eso la tarea en background no es un lujo, es la UX.
- **Instancia única**: la fuente de verdad de las tareas es Postgres, no la memoria.
- **Rate limit de Groq** (free): solo afecta a moderación; el camino crítico no
  depende de Groq.
- **Si el juez se autoaprueba, el producto no vale**: la independencia
  generador/juez es la que sostiene todo el argumento.
- **Seguridad del código generado**: se ejecuta solo en el sandbox, sin secretos.
