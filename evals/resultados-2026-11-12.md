# Resultados de evaluación — despiece 2.0.0 (diseño agnóstico) — 2026-11-12

Evaluación de la 2.0.0, que cambia el modelo a dos ejes (`orden` y `padre`), añade `eje` y `rol`, dibuja la
vista explotada en los cuatro tipos y abre piezas a demanda. Se corrieron los dos casos nuevos, 6
(`idea-historia-explotada`) y 7 (`abrir-a-demanda-red`), y las 26 consultas de `trigger_queries.json`, cuatro
de ellas nuevas. Los casos 1 a 5 no se repitieron. Los resultados anteriores están en
[resultados-2026-11-02b.md](resultados-2026-11-02b.md).

Modelo principal de la sesión: Claude Opus 5.5. Calidad: Sonnet y Haiku, con y sin skill. Activación: Sonnet,
Haiku y Opus, un pase cada uno. Los transcripts no se guardan; aquí va el resumen con la evidencia que se
comprobó sobre los ficheros que dejó cada subagente.

## Activación

Por subagentes, como en la 1.1.1 y la 1.2.0: `claude -p` seguía sin sesión. Cada subagente recibe las 35
skills instaladas con su descripción y las 26 consultas barajadas con otra semilla (11, 23 y 37), y elige la
skill que invocaría primero o ninguna.

Consultas nuevas, para la frontera que abre la 2.0.0 (historias, auditorías, árboles):

- **Entrenamiento, debe activar**: «desarmame la historia argentina del siglo XX por etapas, que no entiendo
  por qué hubo tantos golpes».
- **Entrenamiento, no debe activar**: «haceme una línea de tiempo con los presidentes argentinos desde 1983,
  una barra por mandato». Ya se sabe qué figura se quiere: es de `diagram-design`.
- **Validación, debe activar**: «qué partes tiene una auditoría ISO 27001 y qué tiene que pasar antes de qué,
  para explicárselo a los nuevos».
- **Validación, no debe activar**: «dibujá el árbol genealógico de los Darwin como organigrama, con una caja
  por persona».

| Pase | Modelo | Entrenamiento (15) | Validación (11) | Total |
|---|---|---|---|---|
| 1 | Sonnet | 15/15 | 10/11 | 25/26 |
| 2 | Haiku | 15/15 | 10/11 | 25/26 |
| 3 | Opus 5.5 | 15/15 | 10/11 | 25/26 |

**75/78.** Las cuatro consultas nuevas acertaron en los tres pases: la historia y la auditoría fueron a
`despiece`; la línea de tiempo y el organigrama, a `diagram-design`. Los tres fallos son la misma consulta de
validación de la 1.2.0, «quiero ver cómo se desarma una placa base pieza a pieza en una página que se recorra
con el scroll, tipo 3D». Ahora la mandan a `modern-web-guidance` los tres modelos; en la 1.2.0, Haiku la
mandaba a `despiece`.

**No se tocó la descripción.** El método la ajusta solo con fallos de entrenamiento, y este es de validación.
Sigue valiendo la lectura de la 1.2.0: el formato del entregable le gana al verbo. Para la página interactiva
conviene pedir el despiece de forma explícita (`/despiece …`).

## Calidad: caso 6, la Revolución Industrial

Encargo: «Despiezame la historia de la Revolución Industrial en Gran Bretaña para una clase de secundaria:
qué tuvo que pasar antes de qué y qué entra dentro de cada etapa. Quiero una figura por nivel, no un texto
largo.»

Cuatro subagentes limpios, cada uno en su carpeta, sin poder preguntar, sin marca y sin tocar ninguna nube.
Los de «con» tenían la orden de invocar `despiece` y seguirla entera; los de «sin», la prohibición de
invocarla o leer su carpeta. Calificación con `validar_modelo.py` sobre cada `modelo.json`, el subtítulo
leído de cada SVG y la respuesta de cada uno.

| Aserción | Con skill, Sonnet | Con skill, Haiku | Sin skill, Sonnet | Sin skill, Haiku |
|---|---|---|---|---|
| 1. Dice el tipo y por qué, sin forzarlo a físico | ✓ | ✗ | ✗ | ✗ |
| 2. Raíces con `orden` y `rol`; `eje` de ≤ 70 | ✓ | ✓ | ✗ | ✗ |
| 3. Pasa `validar_modelo.py` | ✓ | ✓ | ✗ | ✗ |
| 4. Nivel 1 de `explosionado.py`, con el eje en el subtítulo | ✓ | ✓ | ✗ | ✗ |
| 5. Abre etapas con `--subconjunto`; hijas con `padre` | ✓ | ✓ | ✓ (espíritu) | ✓ (espíritu) |
| 6. Sin hardware ni metáforas mecánicas | ✓ | ✓ | ✓ | ✓ |
| 7. Fuente o supuesto en cada pieza | ✓ | ✓ | ✗ | ✗ |
| 8. Tres frases y predicción | ✓ | ✓ | ✗ | ✗ |
| **Total** | **8/8** | **7/8** | **2/8** | **2/8** |

- **Con skill, Sonnet.** Tipo proceso, 5 etapas con `rol: etapa` y `eje` «la cronología, de lo más antiguo a
  lo más reciente», y las cinco abiertas, cuatro con su propio `eje` («la cronología, de 1733 a 1769»…). En
  total, 24 piezas, una fuente principal y un supuesto. Seis figuras de `explosionado.py`, y la página sin
  avisos. Predicción: una hilandería de 1783 que depende de un río.
- **Con skill, Haiku.** Mismo tipo y eje, 5 raíces y dos etapas abiertas, con tres supuestos marcados.
  Cierra con tres frases y una predicción. Falla la 1: el modelo dice `proceso`, pero la respuesta no lo
  dice. Las dos etapas abiertas no tienen `eje`, y su subtítulo cae en el genérico «el orden de los pasos»,
  que no describe unas condiciones previas.
- **Sin skill, Sonnet.** Siete figuras propias (SVG y PNG) en tres niveles y una aclaración honesta en la
  figura del nivel 1: el orden marca qué hizo falta primero, no un calendario. Sin modelo, sin tipo y sin
  puertas. Las fechas salen de memoria, y los pies citan a Ashton y Allen sin haberlos consultado.
- **Sin skill, Haiku.** Un HTML con tres bloques por nivel, sin SVG, con las fechas de memoria y una pregunta
  de comprobación. No trae tres frases.

## Calidad: caso 7, abrir el NSG sobre un modelo hecho

Encargo: «Ya tengo el despiece de la red hecho en despiece-red/modelo.json. Ahora abrime el grupo de
seguridad (NSG): qué tiene adentro y en qué orden se evalúa. No me rehagas lo demás.» Cada carpeta llevaba
`assets/ejemplo-red-nube.json` como `despiece-red/modelo.json` y sus dos figuras, con el hash anotado para
comprobar que no se regeneraban.

| Aserción | Con skill, Sonnet | Con skill, Haiku | Sin skill, Sonnet | Sin skill, Haiku |
|---|---|---|---|---|
| 1. Parte del modelo; no cambia lo ya abierto | ✓ | ✓ | ✓ | ✓ |
| 2. Hijas con `padre: nsg` y `orden` único | ✓ (5) | ✓ (3) | ✓ (5) | ✗ |
| 3. `eje` en el NSG y en el subtítulo de la figura nueva | ✓ | ✓ | ✗ | ✗ |
| 4. `profundidad` solo si hace falta (≤ 4) | ✓ | ✓ | ✓ | ✓ (sin cambios) |
| 5. Pasa `validar_modelo.py` | ✓ | ✓ | ✓ (2 avisos) | ✓ (sin tocar) |
| 6. Solo la figura nueva, con `explosionado.py --subconjunto` | ✓ | ✓ | ✗ | ✗ |
| 7. No toca la nube ni pide tenant | ✓ | ✓ | ✓ | ✓ |
| 8. Solo lo nuevo, con tres frases y predicción | ✗ | ✗ | ✗ | ✗ |
| **Total** | **7/8** | **7/8** | **5/8** | **4/8** |

- **Los dos con skill** añadieron las hijas al mismo modelo, cambiaron de la pieza `nsg` solo su `eje` y
  dibujaron solo `n2-nsg.svg`: las dos figuras anteriores conservan su hash. **Ninguno cerró con tres frases ni
  predicción**, porque el paso 8 de `SKILL.md` no las pedía.
- **Haiku con skill** no metió el orden entre el NSG de la subred y el de la NIC, porque «la página consultada
  no lo confirma». Sonnet, con y sin skill, lo sacó de «How network security groups filter network traffic».
- **Sin skill, Sonnet** dedujo el formato leyendo el modelo existente: `padre`, `orden`, `rol`, `eje` en el NSG
  y una fuente nueva. El modelo enseña el método casi solo. Lo que no hace es usar `explosionado.py`: dibuja
  la figura a mano, la apunta como `"skill": "manual"` y su subtítulo no dice qué ordena el eje. Tampoco cierra
  con las puertas.
- **Sin skill, Haiku** dejó el detalle en un `nsg-detalle.json` aparte, sin `padre`, y no hizo figura.

**Calidad total: 29/32 con skill frente a 13/32 sin ella.**

## Qué cambió por las evals

- **`SKILL.md`, paso 8.** Al abrir una pieza, la entrega lleva tres frases y una predicción sobre ese nivel:
  las puertas valen también ahí. Y si las hijas llevan `orden`, la pieza abierta lleva `eje`. Origen: la
  aserción 8 del caso 7, que fallaron los dos subagentes con skill.
- **`SKILL.md`, paso 7.** La entrega empieza por el tipo elegido y por qué, en una línea. Origen: la aserción 1
  del caso 6, que falló Haiku con skill aunque el modelo lo decía.
- **`validar_modelo.py`, aviso nuevo.** Fuera del tipo físico, avisa si una pieza tiene hijas con `orden` y no
  tiene `eje`: su subtítulo caería en el genérico. Detecta las dos etapas de Haiku y la de antecedentes de
  Sonnet; los nueve ejemplos siguen sin avisos. `probar_validador.py`: 57/57.
- **`references/modelo.md`.** `figuras[].skill` lleva `explosionado` cuando la figura sale de
  `explosionado.py`, en cualquier tipo. `propio` queda para un script hecho para ese despiece. Sonnet con
  skill apuntó `propio` en seis figuras que eran de `explosionado.py`.
- Sin cambios en la descripción: ver «Activación».

## Observaciones

- **Sin re-ejecución tras los arreglos**, como en las versiones anteriores. Los cambios son de texto y una
  regla del validador con su prueba. Si en uso real un despiece abierto a demanda vuelve a entregarse sin
  puertas, el caso 7 es el que hay que repetir.
- **El modelo es la mejor documentación del formato.** Sin skill, Sonnet en el caso 7 llegó a 5/8 solo con
  leer el modelo de partida. Lo que la skill añade es la figura coherente con el eje y las puertas.
- **Los subagentes siguen heredando las instrucciones globales del entorno.** Se les dijo «sin marca» y lo
  respetaron. Es el mismo recordatorio que en la 1.1.1 y la 1.2.0.
