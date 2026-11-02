# Guion visual: qué entregar a quien dibuja

Leer en el paso 5, al dibujar la primera figura que no sea una vista explotada. Esta skill decide qué se
ve y en qué orden; el trazo lo pone otra skill o un script propio. El guion evita que quien dibuja vuelva a
decidir el contenido o meta piezas que el modelo no tiene.

## El guion, figura por figura

```
Figura <nivel>-<slug> · dibuja: <skill de dibujo instalada | script propio>
Título (afirmativo): <figuras[i].titulo>
Tipo visual: <flujo | calles | secuencia | estados | layer stack | nested | tree | dependency graph | quadrant | red>
Piezas (solo estas, con estos nombres): <id → nombre, en el orden del flujo>
Relaciones a dibujar: <de → a (tipo, etiqueta)>
Destacar: <la pieza que responde a la pregunta foco>; el resto en tono neutro
Etiquetas sobre la figura, no en leyenda aparte
Marca: <ruta del JSON de marca | ninguna>
Salida: SVG en <carpeta>/figuras/<fichero>, con viewBox y sin width/height fijos
```

Una figura, una afirmación: si para demostrar el título hacen falta dos ideas, son dos figuras.

## Qué skill de dibujo, si hay alguna instalada

La skill no depende de ninguna en concreto: se usa la que esté instalada y encaje con el tipo visual, y en
`figuras[].skill` va su nombre. Tres familias que funcionan bien:

**Diagramas editoriales** (flujo, calles, secuencia, estados, capas, árbol, mapa, cuadrante), como
`diagram-design`. Pedir el tipo por su nombre en inglés (`flowchart`, `swimlane`, `sequence`, `state
machine`, `layer stack`, `nested`, `tree`, `dependency graph`, `quadrant`). Si pregunta por un *style guide*
o por tokens de color, darle los del fichero de marca (`primario`, `secundario`, `fuente`), o su perfil por
defecto si la página va con `--marca ninguna`. Pedir la salida SVG, no solo HTML, para incrustarla.

**Diagramas de red y de arquitectura cloud con iconos oficiales** (suscripciones, túneles, servicios con
su icono), como `diagrama-microsoft-learn` para Azure. Su inventario de componentes es el modelo: pasarle
las piezas como componentes y el `flujo` como el camino del tráfico. Para la página se incrusta el SVG o el
PNG. En documentación de cliente o de auditoría, alto nivel: sin IPs públicas ni nombres de servidor.

**Figuras interactivas** (cuando el nivel 2 gana con zoom y puntos clicables), como `grafico-interactivo`.
Cada pieza con hijos es un punto; sus hijos, los satélites. Solo si el lector va a explorar la figura en una
web: para un PDF o un correo no aporta nada y cuesta mantenimiento.

**`explosionado.py`** (tipo físico). No necesita guion: lee el modelo. Los comandos están en el paso 5
de SKILL.md; toma el título de la figura del modelo cuyas piezas coinciden con las que dibuja, `--destacar`
pone una sola pieza en color y `--subconjunto` abre una pieza con hijos en su propia figura.

## Sin skill de dibujo instalada

Se dibuja con un script propio (Python sin dependencias, SVG escrito a mano) que siga el guion al pie de la
letra, y en el modelo la figura lleva `"skill": "propio"`. Reglas mínimas para que encaje en la página:

- Fondo blanco o transparente y tinta oscura: la página la pone sobre una lámina blanca en los dos temas.
- `viewBox` y `preserveAspectRatio="xMidYMid meet"`, sin `width`/`height` fijos; `font-family` del fichero
  de marca o `system-ui`.
- Colores de marca solo para la pieza destacada y los acentos; el resto, grises.
- Texto de 13 px o más en un `viewBox` de 1240 de ancho; nada de leyendas aparte.
- Comprobar que parsea con `xml.etree` antes de ensamblar.

## Revisar cada figura antes de ensamblar

- El título afirma lo mismo que `figuras[i].titulo`; no es un rótulo («Arquitectura»).
- Solo aparecen las piezas del guion, con los nombres del modelo (la lista de la página los repite).
- ≤ 6 piezas nuevas; una destacada; las etiquetas sobre la figura.
- La forma explica sin texto (isomorfismo): un flujo se lee de izquierda a derecha o de arriba abajo; lo
  que contiene envuelve; lo que decide bifurca.
- El SVG parsea (`xml.etree`), no tiene `width`/`height` fijos y pesa lo razonable (< 300 KB).
- Si quien dibuja añadió piezas o cambió nombres, se corrige la figura, no el modelo.
