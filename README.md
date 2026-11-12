<div align="center">

<img src="https://images.segmind.com/generations/8aa288dd-101b-44f6-93ca-a50fe89ea2b3/7a70afc9ad5052b713213588bb8f0157.png" alt="Vista explotada isométrica de un SSD NVMe" width="100%">

# despiece

**Una skill de Claude Code que desarma cualquier cosa por niveles y te la explica con figuras.**

Un objeto físico, un proceso, un sistema o una idea: `/despiece` lo abre capa por capa,
dibuja cada nivel y te hace tres preguntas para comprobar que lo entendiste de verdad.

[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-3e7cb1?style=flat-square)](SKILL.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B%20·%20sin%20dependencias-1f2933?style=flat-square)](scripts/)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-7b8794?style=flat-square)](LICENSE)
[![t28.io](https://img.shields.io/badge/por-t28.io-3e7cb1?style=flat-square)](https://t28.io)

</div>

---

## ¿Qué hace?

Le pedís `/despiece SSD NVMe` (o `una turbina`, `el pipeline de CI`, `la inflación`) y la skill:

1. **Arma un modelo** del objeto en JSON: piezas, de qué depende cada una, orden de montaje y fuente de cada dato. Lo valida antes de dibujar nada.
2. **Dibuja cada nivel** como figura SVG. Para objetos físicos, una **vista explotada isométrica**: las piezas separadas sobre el eje de montaje, de abajo arriba, con llamadas numeradas.
3. **Ensambla una página HTML** (modo claro y oscuro) que se lee de arriba abajo: nivel 0 → nivel 1 → nivel 2…
4. **Te pone a prueba**: tres frases al estilo Feynman y una predicción. Si no las podés contestar, todavía no lo entendiste.

Con `--interactivo`, el mismo modelo sale como una página que **se abre y se recorre con el scroll**: se arma al
cargar, se desmonta pieza a pieza, sigue el flujo paso a paso y te deja entrar en la pieza que decide.
[Mirá la demo interactiva](docs/interactivo.md).

> Sin dependencias: Python 3.10 o superior y nada más. La figura sale con `viewBox`, así que escala donde la pongas.
> Node 22 solo hace falta para capturar la página interactiva, y es opcional.

<p align="center">
  <a href="docs/demo/iso/n1-explosion.svg"><img src="docs/demo/iso/n1-explosion.svg" alt="Nivel 1: vista explotada del SSD con la controladora destacada" width="90%"></a>
  <br><sub>Nivel 1 del ejemplo: SSD NVMe con la controladora destacada. Pieza con «+» = tiene su propia figura.</sub>
</p>

---

<details>
<summary><b>🚀 Instalación en 30 segundos</b></summary>

<br>

Cloná el repo dentro de tu carpeta de skills de Claude Code:

```bash
# skills personales (todas tus sesiones)
git clone https://github.com/javierledesma28/skill-despiece ~/.claude/skills/despiece

# o solo para un proyecto
git clone https://github.com/javierledesma28/skill-despiece .claude/skills/despiece
```

Abrí Claude Code y probá:

```
/despiece SSD NVMe
```

Los scripts corren con Python 3.10 o superior, sin instalar paquetes. Si querés usarlos sueltos:

```bash
python -I scripts/validar_modelo.py assets/ejemplo-fisico.json
python -I scripts/explosionado.py assets/ejemplo-fisico.json --salida figuras/n1.svg --destacar controladora
python -I scripts/ensamblar.py assets/ejemplo-fisico.json --figuras figuras/ --salida despiece.html
python -I scripts/ensamblar.py assets/ejemplo-fisico.json --salida interactivo.html --interactivo
```

Paso a paso para Mac y Windows, con lo que puede fallar, en [docs/instalacion.md](docs/instalacion.md).

</details>

<details>
<summary><b>🧅 Cómo piensa el despiece: niveles, no listas</b></summary>

<br>

La skill no hace un resumen. Construye una **jerarquía** y la recorre:

| Nivel | Pregunta que responde | Ejemplo (SSD) |
|---|---|---|
| **0** | ¿Qué es y para qué sirve, en una frase? | Un disco sin partes móviles que guarda datos en chips. |
| **1** | ¿De qué piezas está hecho y en qué orden se arman? | PCB → conector M.2 → chips NAND → controladora → DRAM. |
| **2** | ¿Qué hay dentro de cada pieza que importa? | Dentro de la NAND: celdas, páginas, bloques, planos. |
| **n** | …hasta donde el objeto lo aguante y vos lo pidas. | |

Reglas que respeta en cada figura (vienen de Agrawala 2003/2008 y de los cortes de Stephen Biesty):

- Las piezas se separan **sobre un solo eje**, el de montaje, y lo mínimo para verse.
- Una pieza con hijos se dibuja **cerrada** y se abre en otra figura. Nunca todo a la vez.
- Con `--destacar`, **una sola** pieza va en color; el resto queda en gris.
- Las llamadas van numeradas, con guía en codo hasta la lista, para que **no se crucen**.
- Cada dato lleva **fuente**. Lo que no la tiene se marca como `▲ supuesto`.

</details>

<details>
<summary><b>🧩 Las ocho formas de pieza</b></summary>

<br>

Cada pieza se dibuja como un sólido isométrico con la silueta de su papel. Podés fijarla con el campo `"forma"` en el JSON; si no está, se infiere del nombre.

| Forma | Qué dibuja | Se infiere de… |
|---|---|---|
| `placa` | Placa fina con pistas, vías, huellas punteadas, taladros, serigrafía y muesca de llave | pcb, placa, board, tarjeta |
| `chip` | Encapsulado con bisel, brillo, pines en dos lados y marca de pin 1; `cantidad` dibuja una fila | chip, nand, dram, controladora, soc, cpu, gpu, sensor… |
| `conector` | Cuerpo con ranura, pestañas y lengüeta dorada con contactos alternos | conector, puerto, socket, slot, usb, hdmi, rj45… |
| `modulo` | Bloque con bisel superior y rejilla lateral | *(raíz sin pista)* |
| `carcasa` | Bandeja abierta con paredes finas, tornillos en esquinas y rejilla de ventilación | carcasa, tapa, chasis, case, caja |
| `disipador` | Base más aletas, con sombra entre aletas | disipador, heatsink, ventilador, radiador |
| `cable` | Cinta plana con conductores paralelos | cable, cinta, flex, bus, antena |
| `capa` | Loseta fina con retícula, para partes lógicas o internas | *(pieza hija sin pista)* |

Cada pieza proyecta una sombra tenue sobre la de abajo, lo que vende la separación sin agregar ruido.

<p align="center">
  <a href="docs/demo/iso/n2-nand.svg"><img src="docs/demo/iso/n2-nand.svg" alt="Nivel 2: dentro de la NAND" width="80%"></a>
  <br><sub>Nivel 2: dentro de la NAND. Las hijas lógicas salen como «capa».</sub>
</p>

</details>

<details>
<summary><b>🎨 Marca propia (opcional)</b></summary>

<br>

Por defecto la figura es neutra: la skill no trae la marca de nadie. Si querés la tuya, pasale un JSON:

```json
{
  "nombre": "Think28",
  "primario": "#1f2933",
  "secundario": "#3e7cb1",
  "fuente": "Inter, system-ui, sans-serif",
  "pie": "t28.io",
  "lema": "ENTENDER ES DESARMAR"
}
```

```bash
python -I scripts/explosionado.py modelo.json --salida n1.svg --marca mi-marca.json
```

`assets/marca-ejemplo.json` muestra todos los campos. El color secundario es el que se usa para la pieza destacada.

</details>

<details>
<summary><b>📁 Qué hay en el repo</b></summary>

<br>

```
despiece/
├── SKILL.md                  ← lo que lee Claude Code: flujo, reglas, cuándo delegar
├── scripts/
│   ├── validar_modelo.py     ← valida el JSON antes de dibujar (códigos de salida claros)
│   ├── explosionado.py       ← vista explotada isométrica → SVG
│   ├── ensamblar.py          ← página HTML claro/oscuro con todos los niveles
│   ├── isometrico.py         ← geometría y alturas de la página interactiva
│   ├── interactiva.py        ← página interactiva (--interactivo)
│   └── capturar-cdp.mjs      ← captura en tiempo real para revisarla (Node 22, opcional)
├── references/               ← guion visual, formato del modelo, pruebas de comprensión
├── assets/
│   ├── ejemplo-fisico.json   ← SSD NVMe, el ejemplo de todas las demos
│   ├── ejemplo-sistema.json  ← un sistema, para ver el otro camino
│   ├── plantilla-interactiva.html
│   └── marca-ejemplo.json
├── evals/                    ← casos para comprobar que la skill no se rompe
├── docs/demo/iso/            ← SVG de demostración
├── docs/interactivo/         ← la página interactiva del SSD y sus capturas
└── CHANGELOG.md
```

Los scripts corren con `python -I` (modo aislado) a propósito: nada de tu entorno los puede ensuciar.

</details>

<details>
<summary><b>🗺️ Hoja de ruta</b></summary>

<br>

- [x] Modelo validado con fuentes por dato
- [x] Vista explotada isométrica con siluetas por tipo de pieza
- [x] Página HTML claro/oscuro con pruebas de comprensión
- [x] [Página interactiva](docs/interactivo.md) que se abre y se recorre con el scroll (1.2.0, solo físico)
- [ ] **Explorador interactivo** con zoom semántico: acercás una pieza y se abre; te alejás y se cierra
- [ ] Figuras propias para `proceso`, `sistema` e `idea` (hoy se delegan a una skill de diagramas)
- [ ] Exportar un nivel a PNG/PDF desde la propia página

Si estás leyendo esto en la rama `vista-isometrica`, mirá [HANDOFF.md](HANDOFF.md): ahí está lo que falta para cerrar el PR.

</details>

---

<div align="center">

Hecho por [Javier Ledesma](https://github.com/javierledesma28) · [t28.io](https://t28.io) · Licencia MIT

<sub>Si lo usás para entender algo que te tenía trabado, contame qué fue.</sub>

</div>
