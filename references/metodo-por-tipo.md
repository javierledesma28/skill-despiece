# Método por tipo de objeto

Leer al clasificar (paso 2) y al escribir el modelo (paso 4). Cada tipo tiene un eje de despiece, una
técnica probada y un orden de revelado; lo que no cambia es la regla de 3–7 piezas por nivel y el
«nombrar antes de explicar».

## Contenido

1. Cómo clasificar y qué hacer con los casos mixtos
2. Físico: vista explotada
3. Proceso: eje temporal
4. Sistema: funciones y flujo
5. Idea: eje lógico
6. La vista explotada fuera de lo físico
7. Orden de revelado común y anti-patrones

## 1. Clasificar

| Tipo | Qué es | Eje | Pregunta que lo delata |
|---|---|---|---|
| Físico | Un aparato, un equipo, una pieza de hardware | Espacial | «¿qué tiene dentro?», «¿qué pieza hace qué?» |
| Proceso | Pasos con actores y tiempo: una activación por PIM, un despliegue, un alta | Temporal | «¿qué pasa primero?», «¿quién decide?» |
| Sistema | Componentes que se hablan: una arquitectura, una red, el camino de una petición | Funcional y de flujo | «¿por dónde pasa?», «¿por qué falla aquí?» |
| Idea | Un concepto, un modelo, una decisión de diseño | Lógico | «¿qué aporta?», «¿en qué se diferencia de…?» |

**Casos mixtos: manda la pregunta foco.** Un firewall es físico si la pregunta es «qué cable va dónde»
y sistema si es «por qué bloquea esto». Una landing zone es idea si se pregunta «qué aporta» y sistema
si se pregunta «por dónde sale el tráfico». Si el usuario mezcla las dos, se elige una y se dice.

## 2. Físico: vista explotada

Fuentes del método: Agrawala et al. (2003) sobre instrucciones de montaje y Li et al. (2008) sobre vistas
explotadas; el estilo de Biesty (el objeto se abre sin dejar de reconocerse).

- **Piezas** = lo que se puede separar o señalar: carcasa, placa, módulos, conectores. Lo que no se ve
  pero decide el comportamiento (una caché, un firmware) también es pieza si responde a la pregunta foco.
- **`orden`** en cada raíz: el desmontaje es el montaje al revés y la figura se lee de abajo arriba
  (`orden_montaje`, su nombre antiguo, sigue valiendo).
- **Subconjuntos antes que piezas**: una pieza con hijos se dibuja cerrada («contiene N piezas») y se abre
  en una figura aparte (`--subconjunto`). Nunca explotar todo a la vez.
- **Una pieza destacada por figura** (`--destacar`): la que responde a la pregunta foco.
- **Fuentes**: hoja de datos o manual del fabricante, especificación del estándar (PCI-SIG, NVMe, IEC),
  teardowns publicados. Lo que se sabe «de oídas» va como `supuesto: true`.
- **Figura**: `explosionado.py` (isométrica, numerada, con lista de piezas). Si hace falta un corte, no
  está en esta skill: decirlo y ofrecer la vista explotada.

## 3. Proceso: eje temporal

Fuentes del método: IDEF0 (entrada, control, salida, mecanismo; 3–6 cajas por diagrama) y las
instrucciones paso a paso de Agrawala (un paso significativo por figura, lo nuevo visible).

- **Piezas** = pasos o estados, no personas. Los actores van en `relaciones` (`controla`) o como calles.
- **`flujo`** obligatorio: el orden en que ocurre. Las bifurcaciones se modelan como relaciones `causa`
  con etiqueta («si no hay aprobador en 24 h»).
- **Nivel 2** = dentro de un paso (qué comprueba, qué decide, qué registra).
- **Fuentes**: documentación oficial del procedimiento, el runbook o pipeline real, el log de una
  ejecución. En Azure, el activity log o el audit log del servicio, con tenant y suscripción explícitos.
- **Figura**: flujo si hay un solo actor; calles (swimlanes) si hay varios; IDEF0 si importa qué controla
  cada paso. Las tres las dibuja una skill de diagramas editoriales (p. ej. `diagram-design`) o, sin ella,
  un script propio que siga el guion.

## 4. Sistema: funciones y flujo

Fuentes del método: C4 (contexto → contenedores → componentes; casi siempre bastan dos niveles), FAST
(cada función es verbo + sustantivo; a la derecha «cómo», a la izquierda «por qué»), Meadows (elementos,
interconexiones y propósito) y la tradición «what happens when…» de seguir una petición.

- **Piezas** = componentes con una función cada uno (`funcion` en verbo + complemento). Si una pieza
  hace «varias cosas», o se parte o es un subconjunto.
- **`flujo`** obligatorio: el camino de una petición, un paquete o un dato concreto, de la entrada a la
  salida. Es lo que convierte un inventario en una explicación.
- **Relaciones** con tipo: `flujo` (por donde pasa), `controla` (quién decide), `depende`, `dato`.
- **Nivel 2** = dentro del componente que responde a la pregunta foco; los demás se quedan cerrados.
- **Fuentes**: el repo de conocimiento del ámbito (sus docs y hallazgos), la configuración real leída
  con tenant y suscripción explícitos (solo lectura), Microsoft Learn para el comportamiento del
  servicio. Nunca inventar arquitectura: lo no verificado es `supuesto: true`.
- **Figura**: flujo para el camino de una petición; C4 (`layer stack` o `nested` en `diagram-design`)
  para la estructura; secuencia si importa el orden de los mensajes; estados si el componente cambia de
  modo; red o nube con iconos oficiales → una skill de diagramas de red o de arquitectura cloud, si la hay
  (p. ej. `diagrama-microsoft-learn` para Azure).

## 5. Idea: eje lógico

Fuentes del método: primeros principios y cinco porqués; MECE y la pirámide de Minto (árboles de «por qué»
y de «cómo»); mapas conceptuales de Novak (pregunta foco, 15–25 conceptos, proposiciones con palabras de
enlace); la prueba de Feynman; la escalera de abstracción de Bret Victor.

- **Piezas** = los componentes de la idea: supuestos, mecanismos, consecuencias, criterios. Deben ser
  mutuamente excluyentes y cubrir el todo (MECE); el validador avisa si un padre tiene un solo hijo.
- **`flujo`** opcional: el orden de la argumentación («primero el problema, después el principio,
  después la consecuencia»).
- **Lo concreto antes que lo abstracto**: el nivel 0 arranca con un ejemplo o una situación real, y la
  definición llega al final. Nunca al revés.
- **Metáfora** solo si cabe en una frase y el lector no es del dominio; se anota en `malentendidos` qué
  parte de la metáfora no vale.
- **Fuentes**: el documento donde la idea se definió (una decisión de diseño, un estándar, un libro), con
  cita; si es una idea propia del equipo, la conversación o el hallazgo donde se tomó.
- **Figura**: árbol (`tree`) para la descomposición MECE, mapa conceptual (`dependency graph`) para la
  red de conceptos, `quadrant` o `Venn` para comparar; small multiples para «esto frente a aquello».

## 6. La vista explotada fuera de lo físico

`explosionado.py` dibuja cualquier tipo: lo que cambia es qué significa el eje. Se apila de abajo arriba
lo que tiene que existir antes, y cada pieza toma la silueta de su `rol` (tabla en
[modelo.md](modelo.md)). Los ejemplos de esta tabla son eso, ejemplos: el caso concreto decide.

| Tipo | `orden` es… | `eje`, por ejemplo | Roles que suelen salir |
|---|---|---|---|
| Proceso | el orden de los pasos | «el orden de los pasos, del pedido al despliegue» | `etapa`, `componente`, `interfaz` |
| Sistema | el despliegue o el camino de una petición | «el despliegue, de la red a las máquinas» | `base`, `capa`, `componente`, `interfaz`, `enlace`, `contenedor` |
| Idea | la cronología, la profundidad o la cadena causal | «la cronología, de lo más antiguo a lo más reciente» | `etapa`, `componente`, `enlace`, `limite` |

Cuando la pregunta foco es por dónde pasa algo, la vista explotada no basta: la figura del nivel es la de
flujo, red o secuencia, delegada (secciones 3 y 4), y la explotada puede acompañarla.

## 7. Orden de revelado común

1. **Nivel 0**: el todo, reconocible y con su frontera (qué entra y qué queda fuera). Título afirmativo.
2. **Nivel 1**: nombrar las piezas antes de explicar el mecanismo (preentrenamiento de Mayer). 3–7.
3. **Después, seguir el flujo**: la petición, la energía, el dato o el argumento, de entrada a salida.
4. **Nivel 2** solo donde la respuesta a la pregunta foco cambia. Los demás componentes se quedan cerrados.
5. **Lo accesorio al final**, o fuera.

**Anti-patrones** (Evans, Case, Mayer): empezar por definiciones; explotar todo a la vez; que el objeto
deje de reconocerse; leyendas lejos de la figura; texto que repite lo que la figura ya dice; profundidad
desigual entre etapas; interactividad sin propósito; el «qué» sin el «por qué»; analogías forzadas.
