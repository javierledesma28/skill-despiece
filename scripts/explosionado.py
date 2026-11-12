"""Dibuja una vista explotada isométrica (SVG) de un modelo de despiece, de cualquier tipo.

Usage: python -I explosionado.py MODELO.json --salida FIGURA.svg
                                  [--subconjunto ID] [--destacar ID] [--marca RUTA.json|ninguna] [--titulo TEXTO]

Reglas que aplica (Agrawala 2003/2008, Biesty): las piezas se separan sobre un solo eje, el de
dependencia, lo mínimo para verse; de abajo arriba va el campo «orden» de cada pieza (la 1 queda abajo):
el montaje en un aparato, el despliegue en un sistema, la cronología en una historia, la profundidad en un
terreno. Sin «orden», el del flujo y, si no, el de escritura. El subtítulo dice qué ordena el eje: el
campo «eje» del modelo («la cronología, de lo más antiguo a lo más reciente») o, si falta, uno según el
tipo; en un subconjunto, el «eje» de la pieza que se abre. Si las piezas no traen «orden» ni están en el
flujo, el subtítulo no afirma ningún orden. Una pieza con hijos se dibuja cerrada y se abre en otra figura con --subconjunto; con --destacar
una sola pieza va en color y el resto queda en gris. Llamadas numeradas con línea guía hasta la lista de
piezas, a la derecha, para que las guías no se crucen.

Silueta de cada pieza, por este orden:
  1. «forma», si la pieza la trae: placa | chip | conector | modulo | carcasa | disipador | cable | capa.
  2. «rol», el papel abstracto, que no sabe del dominio: base → placa · etapa y capa → capa ·
     componente → chip · interfaz → conector · enlace → cable · contenedor y limite → carcasa ·
     regulador → disipador · bloque → modulo.
  3. En tipo fisico, el nombre («pcb», «conector», «disipador»…); en los demás tipos no se adivina.
  4. Si nada de eso: módulo en una raíz y capa (loseta con retícula) en una pieza hija.

--marca acepta la ruta de un JSON con la marca del proyecto (assets/marca-ejemplo.json enseña los campos)
o «ninguna», el valor por defecto: la skill no trae la marca de ninguna organización.
Entrada: un modelo validado con validar_modelo.py; «orden_montaje» vale como alias de «orden».
Salida: el SVG (sin width/height fijos: viewBox y preserveAspectRatio, para que el contenedor mande)
y en stdout JSON {"salida", "piezas", "viewBox", "destacada", "subconjunto", "formas"}.
Códigos de salida: 0 OK · 1 el SVG generado no es XML válido (no se escribe nada) · 2 argumentos,
fichero o marca inválidos.
Ejemplo:
  python -I explosionado.py assets/ejemplo-fisico.json --salida figuras/n1-explosion.svg --destacar controladora
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

MARCA_NINGUNA = {"primario": "#1f2933", "secundario": "#3e7cb1", "fuente": "system-ui, sans-serif", "pie": "", "lema": ""}
CAMPOS_MARCA = {"nombre", "primario", "secundario", "fuente", "pie", "lema"}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
TINTA, GRIS, LINEA, PAPEL = "#1f2933", "#7b8794", "#cbd2d9", "#ffffff"
# Lienzo: escena isométrica a la izquierda, lista de piezas a la derecha.
W, X_LISTA, X_LLAMADA, TOP, SEP = 1240, 720, 632, 128, 104
COS, SIN = math.cos(math.radians(30)), math.sin(math.radians(30))
ESCENA_CX, ESCENA_W = 330, 560  # centro horizontal de la escena en pantalla

# Formas: (ancho x, fondo y, alto z) en unidades de escena, y cómo se colocan.
FORMAS = {
    "placa":     dict(w=300, d=170, h=6),
    "chip":      dict(w=84, d=84, h=10),          # encapsulado con pines a los lados y bisel
    "conector":  dict(w=240, d=26, h=18, dy=62),  # bloque con lengüeta de contactos dorados
    "modulo":    dict(w=150, d=100, h=36),        # bloque con bisel y rejilla
    "carcasa":   dict(w=330, d=196, h=48),        # bandeja abierta, paredes finas
    "disipador": dict(w=220, d=120, h=30),        # base + aletas
    "cable":     dict(w=260, d=16, h=8, dy=-50),  # cinta plana con pliegue
    "capa":      dict(w=170, d=120, h=5),         # loseta fina con retícula: partes lógicas o internas (celdas, bloques, firmware)
}
PISTAS = [  # palabra en el nombre → forma (se evalúan en orden)
    (r"\b(pcb|placa|board|mainboard|tarjeta)\b", "placa"),
    (r"\b(conector|connector|puerto|socket|zócalo|zocalo|slot|usb|hdmi|ethernet|rj45)\b", "conector"),
    (r"\b(carcasa|tapa|chasis|case|caja|cubierta|bastidor)\b", "carcasa"),
    (r"\b(disipador|heatsink|ventilador|fan|radiador)\b", "disipador"),
    (r"\b(cable|cinta|flex|bus|cableado|antena)\b", "cable"),
    (r"\b(chip|nand|dram|ram|controladora|controlador|soc|cpu|gpu|memoria|flash|regulador|pmic|sensor|ic)\b", "chip"),
]


def cargar_marca(valor: str) -> dict:
    """«ninguna» → figura neutra; una ruta → JSON con los campos de assets/marca-ejemplo.json (los que
    falten toman el valor neutro). Lanza ValueError con un mensaje accionable si algo no sirve."""
    if valor in ("", "ninguna"):
        return dict(MARCA_NINGUNA)
    ruta = Path(valor)
    if not ruta.is_file():
        raise ValueError(f"--marca «{valor}»: no existe. Usar «ninguna» o la ruta de un JSON como assets/marca-ejemplo.json.")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise ValueError(f"--marca {ruta}: JSON inválido ({ex}).") from None
    if not isinstance(datos, dict):
        raise ValueError(f"--marca {ruta}: debe ser un objeto JSON con los campos {sorted(CAMPOS_MARCA)}.")
    raras = set(datos) - CAMPOS_MARCA
    if raras:
        raise ValueError(f"--marca {ruta}: campos desconocidos {sorted(raras)}; los válidos son {sorted(CAMPOS_MARCA)}.")
    mk = dict(MARCA_NINGUNA)
    mk.update({k: str(v) for k, v in datos.items() if k in MARCA_NINGUNA})
    if not mk["pie"] and datos.get("nombre"):
        mk["pie"] = str(datos["nombre"])
    for campo in ("primario", "secundario"):
        if not HEX.match(mk[campo]):
            raise ValueError(f"--marca {ruta}: «{campo}» debe ser un color #rrggbb, no «{mk[campo]}».")
    return mk


def _utf8_stdout() -> None:
    # La consola de Windows es cp1252: sin esto, «» y acentos salen rotos en stdout y stderr.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def recortar(texto: str, n: int) -> str:
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def envolver(texto: str, n: int, lineas: int = 2) -> list[str]:
    """Parte el texto por palabras en hasta `lineas` líneas de `n` caracteres; la última se recorta con «…»."""
    palabras = " ".join(str(texto).split()).split(" ")
    salida: list[str] = []
    actual = ""
    for i, w in enumerate(palabras):
        candidata = (actual + " " + w).strip()
        if len(candidata) <= n or not actual:
            actual = recortar(candidata, n)
            continue
        salida.append(actual)
        actual = recortar(w, n)
        if len(salida) == lineas - 1:
            resto = " ".join(palabras[i:])
            return salida + [recortar(resto, n)]
    if actual:
        salida.append(actual)
    return salida[:lineas]


def mezclar(hexcolor: str, t: float, con: str = "#ffffff") -> str:
    """Mezcla dos colores #rrggbb (t = cuánto del segundo)."""
    a = [int(hexcolor.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(con.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# Rol abstracto → silueta: la tabla que hace a la figura independiente del dominio.
ROL_A_FORMA = {"base": "placa", "etapa": "capa", "capa": "capa", "componente": "chip", "interfaz": "conector",
               "enlace": "cable", "contenedor": "carcasa", "limite": "carcasa", "regulador": "disipador",
               "bloque": "modulo"}
EJE_POR_TIPO = {"fisico": "el orden de montaje", "proceso": "el orden de los pasos",
                "sistema": "el orden de dependencia", "idea": "el orden de dependencia"}


def orden_de(p: dict) -> int | None:
    v = p.get("orden", p.get("orden_montaje"))
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def forma_de(p: dict, tipo: str = "fisico") -> str:
    f = p.get("forma")
    if isinstance(f, str) and f in FORMAS:
        return f
    if p.get("rol") in ROL_A_FORMA:
        return ROL_A_FORMA[p["rol"]]
    nombre = str(p.get("nombre", "")).lower()
    # Las pistas por nombre son de hardware: en un proceso o una idea, «bus» o «memoria» no son piezas físicas.
    for patron, forma in PISTAS if tipo == "fisico" else []:
        if re.search(patron, nombre):
            return forma
    # Sin pista en el nombre: una raíz es un módulo; una pieza interior (hija) suele ser lógica → capa.
    return "capa" if p.get("padre") else "modulo"


class Iso:
    """Proyección isométrica: x hacia la derecha-abajo, y hacia la izquierda-abajo, z hacia arriba."""

    def __init__(self, ox: float, oy: float):
        self.ox, self.oy = ox, oy

    def p(self, x: float, y: float, z: float) -> tuple[float, float]:
        return (self.ox + (x - y) * COS, self.oy + (x + y) * SIN - z)

    def pts(self, *coords: tuple[float, float, float]) -> str:
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(*c) for c in coords))

    def caja(self, cx: float, cy: float, z: float, w: float, d: float, h: float, col: dict, sw: float, extra: str = "") -> str:
        """Un prisma con tres caras visibles: superior, frontal-izquierda (y+) y frontal-derecha (x+)."""
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
        s = []
        s.append(f'<polygon points="{self.pts((x0, y1, z), (x1, y1, z), (x1, y1, z + h), (x0, y1, z + h))}" fill="{col["izq"]}" stroke="{col["borde"]}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
        s.append(f'<polygon points="{self.pts((x1, y1, z), (x1, y0, z), (x1, y0, z + h), (x1, y1, z + h))}" fill="{col["der"]}" stroke="{col["borde"]}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
        s.append(f'<polygon points="{self.pts((x0, y0, z + h), (x1, y0, z + h), (x1, y1, z + h), (x0, y1, z + h))}" fill="{col["sup"]}" stroke="{col["borde"]}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
        return "\n".join(s)


def _chip(iso: Iso, cx: float, cy: float, z: float, w: float, d: float, h: float, col: dict, sw: float) -> list[str]:
    """Encapsulado: cuerpo con bisel superior, pines en los dos lados visibles y marca de pin 1."""
    s = [iso.caja(cx, cy, z, w, d, h, col, sw)]
    # Bisel: rectángulo interior más claro en la cara superior.
    b = 10
    s.append(f'<polygon points="{iso.pts((cx - w/2 + b, cy - d/2 + b, z + h + 0.1), (cx + w/2 - b, cy - d/2 + b, z + h + 0.1), (cx + w/2 - b, cy + d/2 - b, z + h + 0.1), (cx - w/2 + b, cy + d/2 - b, z + h + 0.1))}" fill="{col["borde"]}" fill-opacity="0.08" stroke="{col["borde"]}" stroke-width="0.7" stroke-opacity="0.6"/>')
    # Pines: pequeños salientes en las caras izquierda (y+) y derecha (x+).
    n = 7
    for k in range(n):
        t = (k + 0.5) / n
        # cara y+ (izquierda en pantalla): pines a lo largo de x
        xx = cx - w/2 + t * w
        s.append(f'<polygon points="{iso.pts((xx - 3, cy + d/2, z), (xx + 3, cy + d/2, z), (xx + 3, cy + d/2 + 7, z - 1), (xx - 3, cy + d/2 + 7, z - 1))}" fill="{col["der"]}" stroke="{col["borde"]}" stroke-width="0.6"/>')
        # cara x+ (derecha): pines a lo largo de y
        yy = cy - d/2 + t * d
        s.append(f'<polygon points="{iso.pts((cx + w/2, yy - 3, z), (cx + w/2, yy + 3, z), (cx + w/2 + 7, yy + 3, z - 1), (cx + w/2 + 7, yy - 3, z - 1))}" fill="{col["der"]}" stroke="{col["borde"]}" stroke-width="0.6"/>')
    # Brillo diagonal sobre la tapa (medio triángulo más claro).
    s.append(f'<polygon points="{iso.pts((cx - w/2 + b, cy - d/2 + b, z + h + 0.15), (cx + w/2 - b, cy - d/2 + b, z + h + 0.15), (cx - w/2 + b, cy + d/2 - b, z + h + 0.15))}" fill="#ffffff" fill-opacity="0.35"/>')
    px, py = iso.p(cx - w/2 + 16, cy - d/2 + 16, z + h + 0.2)
    s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{col["borde"]}"/>')
    return s


def dibujar_pieza(iso: Iso, p: dict, forma: str, z: float, col: dict, sw: float) -> tuple[str, tuple[float, float], float]:
    """Devuelve (svg, punto de anclaje derecho para la llamada, alto total de la pieza)."""
    f = FORMAS[forma]
    w, d, h = f["w"], f["d"], f["h"]
    cy = f.get("dy", 0)
    s: list[str] = []
    cantidad = p.get("cantidad") if isinstance(p.get("cantidad"), int) and p.get("cantidad", 1) > 1 else 1
    if forma == "chip":
        n = min(cantidad, 6)
        paso = w + 26
        x0 = -(n - 1) * paso / 2
        for k in range(n):
            s += _chip(iso, x0 + k * paso, 0, z, w, d, h, col, sw)
        ancho_total = (n - 1) * paso + w
        ancla = iso.p(ancho_total / 2 + 7, 0, z + h / 2)
        return "\n".join(s), ancla, h
    if forma == "placa":
        s.append(iso.caja(0, 0, z, w, d, h, col, sw))
        # Pistas: trazos finos en L con vías, sobre la cara superior.
        for k, (yy, largo) in enumerate(((-52, 0.78), (-18, 0.62), (14, 0.84), (46, 0.55))):
            a = iso.p(-w/2 + 24, yy, z + h + 0.1)
            m_ = iso.p(-w/2 + 24 + (w - 48) * largo, yy, z + h + 0.1)
            b = iso.p(-w/2 + 24 + (w - 48) * largo, yy + 14, z + h + 0.1)
            s.append(f'<polyline points="{a[0]:.1f},{a[1]:.1f} {m_[0]:.1f},{m_[1]:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{col["borde"]}" stroke-width="0.9" stroke-opacity="0.5"/>')
            s.append(f'<circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="1.6" fill="{col["borde"]}" fill-opacity="0.6"/>')
        # Huellas (pads) donde irán los chips: rectángulos punteados.
        for xx in (-70, 10, 90):
            s.append(f'<polygon points="{iso.pts((xx - 30, -30, z + h + 0.1), (xx + 30, -30, z + h + 0.1), (xx + 30, 30, z + h + 0.1), (xx - 30, 30, z + h + 0.1))}" fill="none" stroke="{col["borde"]}" stroke-width="0.7" stroke-dasharray="3,3" stroke-opacity="0.5"/>')
        # Taladros de fijación.
        for xx, yy in ((-w/2 + 16, -d/2 + 16), (w/2 - 16, -d/2 + 16), (-w/2 + 16, d/2 - 16), (w/2 - 16, d/2 - 16)):
            px, py = iso.p(xx, yy, z + h + 0.1)
            s.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="4.5" ry="2.6" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="0.9"/>')
        # Muesca de la llave en el borde del conector (lado y+).
        s.append(f'<polygon points="{iso.pts((40, d/2, z - 0.1), (52, d/2, z - 0.1), (52, d/2 - 10, z + h + 0.1), (40, d/2 - 10, z + h + 0.1))}" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="0.8"/>')
        # Serigrafía: pasivos pequeños (pares de pads) repartidos por la placa.
        for (xx, yy) in ((-120, -60), (-105, -60), (-120, 55), (-105, 55), (120, -62), (135, -62), (60, 60), (75, 60), (-20, -66), (-5, -66)):
            s.append(f'<polygon points="{iso.pts((xx - 4, yy - 3, z + h + 0.1), (xx + 4, yy - 3, z + h + 0.1), (xx + 4, yy + 3, z + h + 0.1), (xx - 4, yy + 3, z + h + 0.1))}" fill="{col["borde"]}" fill-opacity="0.25"/>')
        # Línea de contorno de la serigrafía alrededor del área de los chips.
        s.append(f'<polygon points="{iso.pts((-108, -40, z + h + 0.1), (128, -40, z + h + 0.1), (128, 40, z + h + 0.1), (-108, 40, z + h + 0.1))}" fill="none" stroke="{col["borde"]}" stroke-width="0.6" stroke-opacity="0.35"/>')
        # Canto inferior más oscuro: grosor de la placa.
        s.append(f'<polyline points="{iso.pts((-w/2, d/2, z), (w/2, d/2, z), (w/2, -d/2, z))}" fill="none" stroke="{col["borde"]}" stroke-width="1.4" stroke-opacity="0.6"/>')
    elif forma == "conector":
        # Cuerpo bajo y, delante, la lengüeta de contactos (más baja, más ancha, dorada).
        s.append(iso.caja(0, cy - 6, z, w, d - 12, h, col, sw))
        leng_h = 4
        s.append(iso.caja(0, cy + d/2 - 2, z, w - 20, 10, leng_h, {"sup": "#e8d9a8", "izq": "#d8c48a", "der": "#c9b273", "borde": col["borde"]}, sw * 0.8))
        for k in range(18):
            xx = -w/2 + 18 + k * (w - 36) / 17
            a = iso.p(xx, cy + d/2 - 7, z + leng_h + 0.2)
            b = iso.p(xx, cy + d/2 + 3, z + leng_h + 0.2)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{"#b89b55" if k % 2 else col["borde"]}" stroke-width="{1.4 if k % 2 else 0.8}" stroke-opacity="0.6"/>')
        # Ranura del cuerpo (donde entra la lengüeta de la placa) y dos pestañas de fijación.
        s.append(f'<polygon points="{iso.pts((-w/2 + 10, cy - 6, z + h - 4), (w/2 - 10, cy - 6, z + h - 4), (w/2 - 10, cy - 6 + 3, z + h - 4), (-w/2 + 10, cy - 6 + 3, z + h - 4))}" fill="{col["borde"]}" fill-opacity="0.35"/>')
        for xx in (-w/2 + 6, w/2 - 6):
            s.append(iso.caja(xx, cy - 6, z + h, 8, d - 12, 5, col, sw * 0.7))
        # Muesca de llave en la lengüeta.
        s.append(f'<polygon points="{iso.pts((40, cy + d/2 - 7, z + leng_h + 0.3), (52, cy + d/2 - 7, z + leng_h + 0.3), (52, cy + d/2 + 3, z + leng_h + 0.3), (40, cy + d/2 + 3, z + leng_h + 0.3))}" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="0.7"/>')
    elif forma == "carcasa":
        # Bandeja: base fina + cuatro paredes; el interior se ve.
        s.append(iso.caja(0, 0, z, w, d, 4, col, sw))
        t = 8
        s.append(iso.caja(0, -d/2 + t/2, z + 4, w, t, h - 4, col, sw))          # pared trasera (y-)
        s.append(iso.caja(-w/2 + t/2, 0, z + 4, t, d, h - 4, col, sw))          # pared izquierda (x-)
        s.append(iso.caja(w/2 - t/2, 0, z + 4, t, d, h - 4, col, sw, ' fill-opacity="0.9"'))  # pared derecha (x+)
        s.append(iso.caja(0, d/2 - t/2, z + 4, w, t, h - 4, col, sw, ' fill-opacity="0.9"'))  # pared frontal (y+)
        # Tornillos en las cuatro esquinas de las paredes.
        for xx, yy in ((-w/2 + 12, -d/2 + 12), (w/2 - 12, -d/2 + 12), (-w/2 + 12, d/2 - 12), (w/2 - 12, d/2 - 12)):
            px, py = iso.p(xx, yy, z + h + 0.2)
            s.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="3.6" ry="2.1" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="0.8"/>')
            s.append(f'<line x1="{px - 2.2:.1f}" y1="{py:.1f}" x2="{px + 2.2:.1f}" y2="{py:.1f}" stroke="{col["borde"]}" stroke-width="0.7"/>')
        # Rejilla de ventilación en la pared frontal.
        for k in range(8):
            xx = -w/2 + 40 + k * 22
            a = iso.p(xx, d/2, z + 14); b = iso.p(xx, d/2, z + h - 10)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="1" stroke-opacity="0.5"/>')
    elif forma == "disipador":
        base = 6
        s.append(iso.caja(0, 0, z, w, d, base, col, sw))
        n = 9
        for k in range(n):
            xx = -w/2 + 12 + k * (w - 24) / (n - 1)
            if k > 0:  # sombra entre aletas, sobre la base
                s.append(f'<polygon points="{iso.pts((xx - 9, -d/2 + 6, z + base + 0.1), (xx - 2.5, -d/2 + 6, z + base + 0.1), (xx - 2.5, d/2 - 6, z + base + 0.1), (xx - 9, d/2 - 6, z + base + 0.1))}" fill="{col["borde"]}" fill-opacity="0.12"/>')
            s.append(iso.caja(xx, 0, z + base, 5, d - 12, h - base, col, sw * 0.7))
    elif forma == "cable":
        # Cinta plana con un pliegue en zigzag y conductores paralelos.
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
        for k in range(1, 6):
            yy = cy - d/2 + k * d / 6
            a = iso.p(-w/2 + 6, yy, z + h + 0.1); b = iso.p(w/2 - 6, yy, z + h + 0.1)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="0.7" stroke-opacity="0.5"/>')
    elif forma == "capa":
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
        # Retícula sobre la loseta: sugiere celdas/bloques sin pretender fidelidad.
        nx, ny = 6, 4
        for k in range(1, nx):
            xx = -w/2 + k * w / nx
            a = iso.p(xx, -d/2, z + h + 0.1); b = iso.p(xx, d/2, z + h + 0.1)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="0.7" stroke-opacity="0.45"/>')
        for k in range(1, ny):
            yy = -d/2 + k * d / ny
            a = iso.p(-w/2, yy, z + h + 0.1); b = iso.p(w/2, yy, z + h + 0.1)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="0.7" stroke-opacity="0.45"/>')
        # Una celda rellena como «unidad» de la retícula.
        s.append(f'<polygon points="{iso.pts((-w/2, -d/2, z + h + 0.2), (-w/2 + w/nx, -d/2, z + h + 0.2), (-w/2 + w/nx, -d/2 + d/ny, z + h + 0.2), (-w/2, -d/2 + d/ny, z + h + 0.2))}" fill="{col["borde"]}" fill-opacity="0.18"/>')
    else:  # modulo: bloque con bisel superior y etiqueta
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
        b = 12
        s.append(f'<polygon points="{iso.pts((-w/2 + b, cy - d/2 + b, z + h + 0.1), (w/2 - b, cy - d/2 + b, z + h + 0.1), (w/2 - b, cy + d/2 - b, z + h + 0.1), (-w/2 + b, cy + d/2 - b, z + h + 0.1))}" fill="{PAPEL}" fill-opacity="0.5" stroke="{col["borde"]}" stroke-width="0.8" stroke-opacity="0.7"/>')
        for k in range(5):
            yy = cy - d/2 + 18 + k * 12
            a = iso.p(w/2, yy, z + 8); b2 = iso.p(w/2, yy, z + h - 8)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}" stroke="{col["borde"]}" stroke-width="1" stroke-opacity="0.45"/>')
    ancla = iso.p(w / 2, cy, z + h / 2)
    return "\n".join(s), ancla, h


def paleta(mk: dict, destacada: bool, apagada: bool) -> tuple[dict, float]:
    if destacada:
        c = mk["secundario"]
        return {"sup": mezclar(c, 0.78), "izq": mezclar(c, 0.55), "der": mezclar(c, 0.38), "borde": mezclar(c, 0.25, "#000000")}, 1.6
    if apagada:
        return {"sup": "#fbfcfd", "izq": "#f1f4f7", "der": "#e7ebef", "borde": "#c3ccd5"}, 1.0
    return {"sup": "#f6f8fa", "izq": "#e3e8ed", "der": "#d0d7de", "borde": "#8a97a4"}, 1.2


def main(argv: list[str]) -> int:
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modelo")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--subconjunto", default=None, help="id de la pieza cuyos hijos se explotan")
    ap.add_argument("--destacar", default=None, help="id de la única pieza que va en color")
    ap.add_argument("--marca", default="ninguna", help="ruta de un JSON de marca (ver assets/marca-ejemplo.json) o «ninguna»")
    ap.add_argument("--titulo", default=None, help="título de la figura; por defecto, el de la figura del modelo con las mismas piezas")
    a = ap.parse_args(argv[1:])

    ruta = Path(a.modelo)
    if not ruta.is_file():
        print(f"ERROR: no existe {ruta}", file=sys.stderr)
        return 2
    try:
        m = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON inválido: {e}. Pasar antes por validar_modelo.py.", file=sys.stderr)
        return 2
    tipo = m.get("tipo") if m.get("tipo") in EJE_POR_TIPO else "fisico"
    try:
        mk = cargar_marca(a.marca)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    piezas = {p["id"]: p for p in m.get("piezas", []) if isinstance(p, dict) and "id" in p}
    if a.subconjunto and a.subconjunto not in piezas:
        print(f"ERROR: --subconjunto «{a.subconjunto}» no existe en piezas", file=sys.stderr)
        return 2
    if a.destacar and a.destacar not in piezas:
        print(f"ERROR: --destacar «{a.destacar}» no existe en piezas", file=sys.stderr)
        return 2
    padre = a.subconjunto
    grupo = [p for p in piezas.values() if p.get("padre") == padre]
    if not grupo:
        print(f"ERROR: «{padre}» no tiene hijos que explotar", file=sys.stderr)
        return 2
    # Orden ascendente: la 1 abajo. Sin «orden» en todas, el del flujo; si tampoco, el de escritura.
    flujo = [f for f in m.get("flujo") or [] if isinstance(f, str)]
    criterio = None
    if all(orden_de(p) is not None for p in grupo):
        grupo.sort(key=orden_de)
        criterio = "orden"
    elif all(p["id"] in flujo for p in grupo):
        grupo.sort(key=lambda p: flujo.index(p["id"]))
        criterio = "flujo"
    n = len(grupo)
    formas = [forma_de(p, tipo) for p in grupo]

    # Alturas: la escena se construye de abajo arriba; cada pieza a SEP de la anterior más su propio alto.
    # Una fila de chips iguales va centrada en el eje: su mitad izquierda sube en pantalla y hay que dejarle
    # sitio a la pieza de arriba; si es la última, solo al margen superior.
    # «cima»: cuánto sube la escena sobre el origen, con la esquina trasera de cada pieza proyectada; así el
    # margen superior es el que pide la pieza más alta, no el de una placa grande.
    # «alcance»: cuánto baja en pantalla la esquina delantera de una pieza bajo su base. Si la de arriba baja
    # más que la de abajo (una carcasa sobre un cable), se separa esa diferencia de más: así la de abajo
    # queda tan a la vista como bajo una pieza igual a ella.
    # Sobre una carcasa (bandeja abierta) o entre las aletas de un disipador, la pieza de arriba se vería metida
    # dentro, y estar dentro es «padre», el otro eje: se sube hasta que su punto más bajo libra el borde trasero.
    zs: list[float] = []
    z = 0.0
    cima = 0.0
    alcance_prev = None
    for k, (p, f) in enumerate(zip(grupo, formas)):
        sube = 0.0
        if f == "chip" and isinstance(p.get("cantidad"), int) and p["cantidad"] > 1:
            sube = (min(p["cantidad"], 6) - 1) * (FORMAS["chip"]["w"] + 26) * SIN / 2
        fo = FORMAS[f]
        alcance = ((fo["w"] + fo["d"]) / 2 + fo.get("dy", 0)) * SIN + sube
        if alcance_prev is not None:
            z += max(0.0, alcance - alcance_prev)
            if formas[k - 1] in ("carcasa", "disipador"):
                fc = FORMAS[formas[k - 1]]
                borde = zs[-1] + fc["h"] + min(fc["w"], fc["d"]) * SIN  # borde trasero, sobre el eje
                z = max(z, borde + alcance + 12)
        alcance_prev = alcance
        zs.append(z)
        cima = max(cima, z + fo["h"] + sube + ((fo["w"] + fo["d"]) / 2 - fo.get("dy", 0)) * SIN)
        z += fo["h"] + SEP + sube
    pie_h = 56 if mk["pie"] else 24
    oy = TOP + 12 + cima
    H = int(oy + 130 + pie_h)
    iso = Iso(ESCENA_CX, oy)  # origen (0,0,0) en pantalla: la base de la pieza 1

    ids_grupo = {p["id"] for p in grupo}
    titulo = a.titulo
    if not titulo:
        for f in m.get("figuras", []):
            if isinstance(f, dict) and set(f.get("piezas") or []) == ids_grupo and f.get("titulo"):
                titulo = f["titulo"]
                break
    if not titulo:
        titulo = f"Dentro de {piezas[padre]['nombre']}" if padre else (m.get("nivel0", {}).get("titulo") or m.get("objeto", "Vista explotada"))
    # El subtítulo dice qué ordena la pila, y nada más: el «eje» de la pieza abierta (o del modelo, en las
    # raíces) si se ordenó por «orden» o por el flujo; si no hay «eje», uno genérico; y si la pila va en el
    # orden de escritura, no se afirma ningún orden.
    duenno = piezas[padre] if padre else m
    eje = duenno.get("eje") if isinstance(duenno.get("eje"), str) and duenno["eje"].strip() else None
    if criterio == "orden":
        subt = f"Vista explotada · de abajo arriba, {recortar(eje or EJE_POR_TIPO[tipo], 90)}"
    elif criterio == "flujo":
        subt = f"Vista explotada · de abajo arriba, {recortar(eje or 'el orden del flujo', 90)}"
    else:
        subt = f"Vista explotada · las partes de {recortar(piezas[padre]['nombre'], 60)}" if padre else "Vista explotada"

    s: list[str] = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
             f'role="img" aria-label="{escape(recortar(titulo, 120))}" font-family="{escape(mk["fuente"])}">')
    s.append(f'<rect width="{W}" height="{H}" fill="{PAPEL}"/>')
    s.append(f'<text x="64" y="52" font-size="26" font-weight="700" fill="{mk["primario"]}">{escape(recortar(titulo, 78))}</text>')
    s.append(f'<text x="64" y="80" font-size="15" fill="{GRIS}">{escape(subt)}</text>')

    # Sombra suave bajo la pieza base y eje de montaje.
    sx, sy = iso.p(0, 0, -6)
    s.append(f'<ellipse cx="{sx:.1f}" cy="{sy + 14:.1f}" rx="190" ry="34" fill="#000000" fill-opacity="0.05"/>')
    ex0 = iso.p(0, 0, zs[0] - 24)
    ex1 = iso.p(0, 0, zs[-1] + FORMAS[formas[-1]]["h"] + 40)
    s.append(f'<line x1="{ex0[0]:.1f}" y1="{ex0[1]:.1f}" x2="{ex1[0]:.1f}" y2="{ex1[1]:.1f}" stroke="{LINEA}" stroke-width="1.6" stroke-dasharray="7,6"/>')

    # Primera pasada: dibujar las piezas y recoger los anclajes; después repartir la lista sin solapes.
    dibujos: list[tuple[dict, str, str, tuple[float, float], float, bool, bool, dict]] = []
    for i, (p, forma) in enumerate(zip(grupo, formas)):
        destacada = a.destacar == p["id"]
        apagada = bool(a.destacar) and not destacada
        col, sw = paleta(mk, destacada, apagada)
        cuerpo, ancla, h = dibujar_pieza(iso, p, forma, zs[i], col, sw)
        dibujos.append((p, forma, cuerpo, ancla, h, destacada, apagada, col))
    FILA = 66  # alto mínimo de una entrada de la lista (nombre + dos líneas)
    ys_lista: list[float] = []
    tope = H - pie_h - 30
    for _, _, _, ancla, *_ in dibujos:  # la pieza 1 es la de abajo: se reparte de abajo arriba
        y = min(ancla[1], tope)
        ys_lista.append(y)
        tope = y - FILA
    # Si la primera se salió por arriba, empujar todo hacia abajo lo justo.
    desplazar = max(0.0, (TOP - 10) - ys_lista[0])
    ys_lista = [y + desplazar for y in ys_lista]

    s.append('<g id="fv-escena">')
    llamadas: list[str] = []
    lista: list[str] = []
    for i, (p, forma, cuerpo, ancla, h, destacada, apagada, col) in enumerate(dibujos):
        num = i + 1
        hijos = [q for q in piezas.values() if q.get("padre") == p["id"]]
        tinta = GRIS if apagada else TINTA
        s.append(f'<g class="fv-punto" data-id="{escape(p["id"])}" data-forma="{forma}">')
        if i > 0:
            # Sombra proyectada (huella tenue) sobre la cima de la pieza de abajo: vende la separación.
            f0 = FORMAS[forma]
            zb = zs[i - 1] + FORMAS[formas[i - 1]]["h"] + 0.3
            fw, fd, fcy = f0["w"], f0["d"], f0.get("dy", 0)
            if forma == "chip" and isinstance(p.get("cantidad"), int) and p["cantidad"] > 1:
                fw = (min(p["cantidad"], 6) - 1) * (FORMAS["chip"]["w"] + 26) + FORMAS["chip"]["w"]
            s.append(f'<polygon points="{iso.pts((-fw/2 + 6, fcy - fd/2 + 6, zb), (fw/2 + 6, fcy - fd/2 + 6, zb), (fw/2 + 6, fcy + fd/2 + 6, zb), (-fw/2 + 6, fcy + fd/2 + 6, zb))}" fill="#1f2933" fill-opacity="0.045"/>')
        s.append(cuerpo)
        if hijos and not destacada:
            # Pieza cerrada que se abre en otra figura: un pequeño «+» sobre ella.
            cx_mas = 0.0
            if forma == "chip" and isinstance(p.get("cantidad"), int) and p["cantidad"] > 1:
                cx_mas = -(min(p["cantidad"], 6) - 1) * (FORMAS["chip"]["w"] + 26) / 2  # sobre el primer chip de la fila
            px, py = iso.p(cx_mas, FORMAS[forma].get("dy", 0), zs[i] + h + 26)  # sobre la pieza, no sobre el eje
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="1.2"/>')
            s.append(f'<text x="{px:.1f}" y="{py + 4:.1f}" font-size="13" font-weight="700" fill="{col["borde"]}" text-anchor="middle">+</text>')
        s.append("</g>")
        # Llamada: guía desde el borde derecho de la pieza, con un codo, hasta el círculo numerado.
        yc = ys_lista[i]
        xq = X_LLAMADA - 48
        color_num = mk["secundario"] if destacada else (mezclar(mk["primario"], 0.45) if apagada else mk["primario"])
        # Guía: horizontal desde la pieza, codo a 45° hasta la altura de su entrada en la lista.
        dy = yc - ancla[1]
        xk = xq - abs(dy)
        if xk < ancla[0] + 12:
            xk = ancla[0] + 12
        llamadas.append(f'<polyline points="{ancla[0]:.1f},{ancla[1]:.1f} {xk:.1f},{ancla[1]:.1f} {xq:.1f},{yc:.1f} {X_LLAMADA - 16:.1f},{yc:.1f}" fill="none" stroke="{LINEA}" stroke-width="1.3" stroke-linejoin="round"/>')
        llamadas.append(f'<circle cx="{ancla[0]:.1f}" cy="{ancla[1]:.1f}" r="3" fill="{color_num}"/>')
        llamadas.append(f'<circle cx="{X_LLAMADA}" cy="{yc:.1f}" r="15" fill="{color_num}"/>')
        llamadas.append(f'<text x="{X_LLAMADA}" y="{yc + 5:.1f}" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">{num}</text>')
        # Lista a la derecha, alineada con la llamada.
        detalle = []
        if p.get("cantidad") and p["cantidad"] != 1:
            detalle.append(f"×{p['cantidad']}")
        if hijos:
            detalle.append(f"contiene {len(hijos)} piezas → figura aparte")
        fuente = p.get("fuente") if isinstance(p.get("fuente"), str) and p.get("fuente").strip() else None
        if not fuente:
            detalle.append("▲ supuesto")
        lista.append(f'<text x="{X_LISTA}" y="{yc - 8:.1f}" font-size="16" font-weight="600" fill="{tinta}">{escape(recortar(p.get("nombre", p["id"]), 40))}'
                     + (f'<tspan font-weight="400" fill="{GRIS}" font-size="13"> · {escape(" · ".join(detalle))}</tspan>' if detalle else "") + "</text>")
        for k, linea in enumerate(envolver(p.get("funcion", ""), 64)):
            lista.append(f'<text x="{X_LISTA}" y="{yc + 12 + 18 * k:.1f}" font-size="14" fill="{GRIS}">{escape(linea)}</text>')
    s.append("</g>")
    s.append('<g id="fv-llamadas">' + "\n".join(llamadas) + "</g>")
    s.append('<g id="fv-lista">' + "\n".join(lista) + "</g>")
    if mk["pie"]:
        yp = H - 22
        s.append(f'<line x1="64" y1="{yp - 22}" x2="{W - 64}" y2="{yp - 22}" stroke="{LINEA}" stroke-width="1"/>')
        s.append(f'<text x="64" y="{yp}" font-size="13" fill="{GRIS}">{escape(mk["pie"])}</text>')
        s.append(f'<text x="{W - 64}" y="{yp}" font-size="12" fill="{mk["secundario"]}" text-anchor="end" letter-spacing="1.5">{escape(mk["lema"])}</text>')
    s.append("</svg>")
    svg = "\n".join(s)

    try:
        ET.fromstring(svg)
    except ET.ParseError as e:
        print(f"ERROR: SVG mal formado, no se escribe nada: {e}", file=sys.stderr)
        return 1
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(svg, encoding="utf-8")
    print(json.dumps({"salida": str(salida), "piezas": [p["id"] for p in grupo], "viewBox": f"0 0 {W} {H}",
                      "destacada": a.destacar, "subconjunto": padre, "formas": dict(zip([p["id"] for p in grupo], formas))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
