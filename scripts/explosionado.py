"""Dibuja una vista explotada isométrica (SVG) de un modelo de despiece de tipo fisico.

Usage: python -I explosionado.py MODELO.json --salida FIGURA.svg
                                  [--subconjunto ID] [--destacar ID] [--marca RUTA.json|ninguna] [--titulo TEXTO]

Reglas que aplica (Agrawala 2003/2008, Biesty): las piezas se separan sobre un solo eje, el de montaje,
lo mínimo para verse; de abajo arriba va el orden de montaje (la pieza 1 queda abajo); cada pieza se
dibuja como un sólido isométrico con la forma de su papel (placa, chip, conector, módulo, carcasa,
disipador, cable); una pieza con hijos se dibuja cerrada y se abre en otra figura con --subconjunto;
con --destacar una sola pieza va en color y el resto queda en gris. Llamadas numeradas con línea guía
hasta la lista de piezas, a la derecha, para que las guías no se crucen.

Forma de cada pieza: campo opcional «forma» en la pieza (placa | chip | conector | modulo | carcasa |
disipador | cable). Sin él, se infiere del nombre; si no se reconoce, módulo.

--marca acepta la ruta de un JSON con la marca del proyecto (assets/marca-ejemplo.json enseña los campos)
o «ninguna», el valor por defecto: la skill no trae la marca de ninguna organización.
Entrada: un modelo validado con validar_modelo.py (tipo fisico, raíces con orden_montaje).
Salida: el SVG (sin width/height fijos: viewBox y preserveAspectRatio, para que el contenedor mande)
y en stdout JSON {"salida", "piezas", "viewBox", "destacada", "subconjunto", "formas"}.
Códigos de salida: 0 OK · 1 el SVG generado no es XML válido (no se escribe nada) · 2 argumentos,
fichero, marca o tipo inválidos.
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
W, X_LISTA, X_LLAMADA, TOP, SEP = 1240, 700, 612, 128, 96
COS, SIN = math.cos(math.radians(30)), math.sin(math.radians(30))
ESCENA_CX, ESCENA_W = 330, 560  # centro horizontal de la escena en pantalla

# Formas: (ancho x, fondo y, alto z) en unidades de escena, y cómo se colocan.
FORMAS = {
    "placa":     dict(w=300, d=170, h=8),
    "chip":      dict(w=78, d=78, h=12),
    "conector":  dict(w=240, d=26, h=16, dy=62),      # pegado al borde frontal
    "modulo":    dict(w=140, d=100, h=34),
    "carcasa":   dict(w=330, d=196, h=44, hueco=True),
    "disipador": dict(w=220, d=120, h=22, aletas=6),
    "cable":     dict(w=260, d=14, h=10, dy=-50),
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


def forma_de(p: dict) -> str:
    f = p.get("forma")
    if isinstance(f, str) and f in FORMAS:
        return f
    nombre = (p.get("nombre", "") + " " + p.get("id", "")).lower()
    for patron, forma in PISTAS:
        if re.search(patron, nombre):
            return forma
    return "modulo"


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


def dibujar_pieza(iso: Iso, p: dict, forma: str, z: float, col: dict, sw: float) -> tuple[str, tuple[float, float], float]:
    """Devuelve (svg, punto de anclaje derecho para la llamada, alto total de la pieza)."""
    f = FORMAS[forma]
    w, d, h = f["w"], f["d"], f["h"]
    cy = f.get("dy", 0)
    s: list[str] = []
    cantidad = p.get("cantidad") if isinstance(p.get("cantidad"), int) and p.get("cantidad", 1) > 1 else 1
    if forma == "chip" and cantidad > 1:
        # Varios chips iguales en una fila sobre el eje x, centrados.
        n = min(cantidad, 6)
        paso = w + 18
        x0 = -(n - 1) * paso / 2
        for k in range(n):
            s.append(iso.caja(x0 + k * paso, 0, z, w, d, h, col, sw))
            # Marca del encapsulado: punto del pin 1.
            px, py = iso.p(x0 + k * paso - w / 2 + 12, -d / 2 + 12, z + h + 0.1)
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.2" fill="{col["borde"]}"/>')
        ancho_total = (n - 1) * paso + w
        ancla = iso.p(ancho_total / 2, 0, z + h / 2)
        return "\n".join(s), ancla, h
    if forma == "carcasa":
        s.append(iso.caja(0, 0, z, w, d, h, col, sw, ' fill-opacity="0.55"'))
        # Hueco interior: la carcasa se ve como bandeja.
        s.append(f'<polygon points="{iso.pts((-w/2+14, -d/2+14, z+h), (w/2-14, -d/2+14, z+h), (w/2-14, d/2-14, z+h), (-w/2+14, d/2-14, z+h))}" fill="{PAPEL}" fill-opacity="0.9" stroke="{col["borde"]}" stroke-width="{sw*0.8}" stroke-dasharray="4,3"/>')
    elif forma == "placa":
        s.append(iso.caja(0, 0, z, w, d, h, col, sw))
        # Pistas sugeridas: tres líneas finas sobre la placa (sin pretender fidelidad).
        for k, yy in enumerate((-40, 0, 40)):
            a = iso.p(-w / 2 + 30, yy, z + h + 0.1)
            b = iso.p(w / 2 - 30, yy + (18 if k == 1 else 0), z + h + 0.1)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="0.8" stroke-opacity="0.45"/>')
        # Taladros de fijación en las esquinas.
        for xx, yy in ((-w / 2 + 16, -d / 2 + 16), (w / 2 - 16, -d / 2 + 16), (-w / 2 + 16, d / 2 - 16), (w / 2 - 16, d / 2 - 16)):
            px, py = iso.p(xx, yy, z + h + 0.1)
            s.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="4" ry="2.3" fill="{PAPEL}" stroke="{col["borde"]}" stroke-width="0.8"/>')
    elif forma == "conector":
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
        # Contactos: peine de líneas en la cara frontal.
        for k in range(14):
            xx = -w / 2 + 14 + k * (w - 28) / 13
            a = iso.p(xx, cy + d / 2, z + 2)
            b = iso.p(xx, cy + d / 2, z + h - 2)
            s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col["borde"]}" stroke-width="1" stroke-opacity="0.6"/>')
    elif forma == "disipador":
        base = 6
        s.append(iso.caja(0, 0, z, w, d, base, col, sw))
        n = f.get("aletas", 6)
        for k in range(n):
            xx = -w / 2 + 14 + k * (w - 28) / (n - 1)
            s.append(iso.caja(xx, 0, z + base, 8, d - 16, h - base, col, sw * 0.8))
    elif forma == "cable":
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
    else:  # modulo y chip simple
        s.append(iso.caja(0, cy, z, w, d, h, col, sw))
        if forma == "chip":
            px, py = iso.p(-w / 2 + 12, -d / 2 + 12, z + h + 0.1)
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.4" fill="{col["borde"]}"/>')
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
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], add_help=True)
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
    if m.get("tipo") != "fisico":
        print(f"ERROR: tipo «{m.get('tipo')}»; la vista explotada es solo para tipo fisico. Para procesos, sistemas e ideas, "
              "delegar la figura en una skill de dibujo (p. ej. diagram-design) o dibujarla con un script propio según "
              "references/guion-visual.md.", file=sys.stderr)
        return 2
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
    # Orden de montaje ascendente: la 1 abajo. Sin orden_montaje (subconjuntos), el de escritura.
    if all(isinstance(p.get("orden_montaje"), int) for p in grupo):
        grupo.sort(key=lambda p: p["orden_montaje"])
    n = len(grupo)
    formas = [forma_de(p) for p in grupo]

    # Alturas: la escena se construye de abajo arriba; cada pieza a SEP de la anterior más su propio alto.
    zs: list[float] = []
    z = 0.0
    for p, f in zip(grupo, formas):
        zs.append(z)
        extra = 0
        if f == "chip" and isinstance(p.get("cantidad"), int) and p["cantidad"] > 1:
            extra = (min(p["cantidad"], 6) - 1) * (FORMAS["chip"]["w"] + 18) * SIN  # la fila baja en pantalla
        z += FORMAS[f]["h"] + SEP + extra
    alto_pila = z - SEP  # de la base de la pieza 1 a la cima de la última
    pie_h = 56 if mk["pie"] else 24
    # Margen superior e inferior para la proyección de las caras (una placa de 300×170 sube/baja ~120 px).
    oy = TOP + 124 + alto_pila
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
    subt = "Vista explotada · de abajo arriba, el orden de montaje"

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
        s.append(cuerpo)
        if hijos and not destacada:
            # Pieza cerrada que se abre en otra figura: un pequeño «+» sobre ella.
            px, py = iso.p(0, 0, zs[i] + h + 22)
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
