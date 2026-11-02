"""Dibuja una vista explotada 2D (SVG) de un modelo de despiece de tipo fisico.

Usage: python -I explosionado.py MODELO.json --salida FIGURA.svg
                                  [--subconjunto ID] [--destacar ID] [--marca RUTA.json|ninguna] [--titulo TEXTO]

Reglas que aplica (Agrawala 2003/2008, Biesty): las piezas se separan sobre un solo eje y lo mínimo
para verse; el orden de arriba abajo es el inverso del montaje (la última pieza montada queda arriba);
una pieza con hijos se dibuja cerrada con la etiqueta «contiene N piezas» y se abre en otra figura con
--subconjunto; con --destacar una sola pieza va en color y el resto en gris. Llamadas numeradas con
línea guía hasta la lista de piezas, alineada a la derecha para que las guías no se crucen.

--marca acepta la ruta de un JSON con la marca del proyecto (assets/marca-ejemplo.json enseña los campos)
o «ninguna», el valor por defecto: la skill no trae la marca de ninguna organización.
Entrada: un modelo validado con validar_modelo.py (tipo fisico, raíces con orden_montaje).
Salida: el SVG (sin width/height fijos: viewBox y preserveAspectRatio, para que el contenedor mande)
y en stdout JSON {"salida", "piezas", "viewBox", "destacada", "subconjunto"}.
Códigos de salida: 0 OK · 1 el SVG generado no es XML válido (no se escribe nada) · 2 argumentos,
fichero, marca o tipo inválidos.
Ejemplo:
  python -I explosionado.py assets/ejemplo-fisico.json --salida figuras/n1-explosion.svg --destacar controladora
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

MARCA_NINGUNA = {"primario": "#1f2933", "secundario": "#3e7cb1", "fuente": "system-ui, sans-serif", "pie": "", "lema": ""}
CAMPOS_MARCA = {"nombre", "primario", "secundario", "fuente", "pie", "lema"}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
TINTA, GRIS, LINEA, PAPEL = "#1f2933", "#7b8794", "#cbd2d9", "#ffffff"
W, BOX_W, BOX_H, GAP, X_BOX, X_LISTA, TOP = 1240, 420, 76, 44, 90, 640, 120


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
    """Parte el texto por palabras en hasta `lineas` líneas de `n` caracteres; la última se recorta con «…»
    si aún sobra. Para la función de cada pieza en la lista: una sola línea se quedaba a medias."""
    palabras = " ".join(str(texto).split()).split(" ")
    salida: list[str] = []
    actual = ""
    for i, w in enumerate(palabras):
        candidata = (actual + " " + w).strip()
        if len(candidata) <= n or not actual:
            actual = recortar(candidata, n)  # una sola palabra más larga que la línea también se recorta
            continue
        salida.append(actual)
        actual = recortar(w, n)
        if len(salida) == lineas - 1:
            resto = " ".join(palabras[i:])
            return salida + [recortar(resto, n)]
    if actual:
        salida.append(actual)
    return salida[:lineas]


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
    # Sin orden_montaje en un subconjunto, se respeta el orden de escritura.
    grupo.sort(key=lambda p: p.get("orden_montaje", 0) if isinstance(p.get("orden_montaje"), int) else 0, reverse=True)
    for i, p in enumerate(grupo):
        if not isinstance(p.get("orden_montaje"), int):
            grupo = list(reversed([q for q in piezas.values() if q.get("padre") == padre]))
            break

    n = len(grupo)
    pie_h = 56 if mk["pie"] else 24
    H = TOP + n * (BOX_H + GAP) - GAP + 40 + pie_h
    cx = X_BOX + BOX_W / 2
    # Título: el que se pase; si no, el de la figura del modelo que muestra estas mismas piezas (así la figura
    # afirma lo suyo y no repite el título del nivel 0); si no, un rótulo genérico.
    ids_grupo = {p["id"] for p in grupo}
    titulo = a.titulo
    if not titulo:
        for f in m.get("figuras", []):
            if isinstance(f, dict) and set(f.get("piezas") or []) == ids_grupo and f.get("titulo"):
                titulo = f["titulo"]
                break
    if not titulo:
        titulo = f"Dentro de {piezas[padre]['nombre']}" if padre else (m.get("nivel0", {}).get("titulo") or m.get("objeto", "Vista explotada"))
    subt = "Vista explotada · de abajo arriba, el orden de montaje; de arriba abajo, el de desmontaje"

    s: list[str] = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
             f'role="img" aria-label="{escape(recortar(titulo, 120))}" font-family="{escape(mk["fuente"])}">')
    s.append(f'<rect width="{W}" height="{H}" fill="{PAPEL}"/>')
    s.append(f'<text x="{X_BOX}" y="52" font-size="26" font-weight="700" fill="{mk["primario"]}">{escape(recortar(titulo, 78))}</text>')
    s.append(f'<text x="{X_BOX}" y="80" font-size="15" fill="{GRIS}">{escape(subt)}</text>')
    y_ini, y_fin = TOP - 16, TOP + n * (BOX_H + GAP) - GAP + 16
    s.append(f'<line x1="{cx}" y1="{y_ini}" x2="{cx}" y2="{y_fin}" stroke="{LINEA}" stroke-width="2" stroke-dasharray="8,6"/>')
    s.append(f'<g id="fv-escena">')
    for i, p in enumerate(grupo):
        y = TOP + i * (BOX_H + GAP)
        num = n - i  # numeración en orden de montaje: la de abajo es la 1
        hijos = [q for q in piezas.values() if q.get("padre") == p["id"]]
        destacada = a.destacar == p["id"]
        apagada = bool(a.destacar) and not destacada
        fill = "#e6f4f3" if destacada else PAPEL
        stroke = mk["secundario"] if destacada else (LINEA if apagada else TINTA)
        tinta = GRIS if apagada else TINTA
        s.append(f'<g class="fv-punto" data-id="{escape(p["id"])}">')
        s.append(f'<rect x="{X_BOX}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{3 if destacada else 1.6}"/>')
        s.append(f'<text x="{X_BOX + 18}" y="{y + 31}" font-size="18" font-weight="600" fill="{tinta}">{escape(recortar(p.get("nombre", p["id"]), 34))}</text>')
        detalle = f"paso de montaje {p['orden_montaje']}" if isinstance(p.get("orden_montaje"), int) else ""
        if p.get("cantidad") and p["cantidad"] != 1:
            detalle = (detalle + " · " if detalle else "") + f"×{p['cantidad']}"
        if hijos:
            detalle = (detalle + " · " if detalle else "") + f"contiene {len(hijos)} piezas → figura aparte"
        if detalle:
            s.append(f'<text x="{X_BOX + 18}" y="{y + 56}" font-size="13" fill="{GRIS}">{escape(detalle)}</text>')
        # Llamada numerada y guía hasta la lista.
        xc, yc = X_BOX + BOX_W + 34, y + BOX_H / 2
        s.append(f'<line x1="{X_BOX + BOX_W}" y1="{yc}" x2="{X_LISTA - 24}" y2="{yc}" stroke="{LINEA}" stroke-width="1.4"/>')
        s.append(f'<circle cx="{xc}" cy="{yc}" r="15" fill="{mk["secundario"] if destacada else mk["primario"]}"/>')
        s.append(f'<text x="{xc}" y="{yc + 5}" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">{num}</text>')
        # Lista de piezas, alineada con su caja.
        fuente = p.get("fuente") if isinstance(p.get("fuente"), str) and p.get("fuente").strip() else None
        marca_f = "" if fuente else " ▲ supuesto"
        s.append(f'<text x="{X_LISTA}" y="{yc - 6}" font-size="16" font-weight="600" fill="{tinta}">{num}. {escape(recortar(p.get("nombre", p["id"]), 40))}'
                 f'<tspan font-weight="400" fill="{GRIS}" font-size="13">{escape(marca_f)}</tspan></text>')
        for k, linea in enumerate(envolver(p.get("funcion", ""), 72)):
            s.append(f'<text x="{X_LISTA}" y="{yc + 14 + 18 * k}" font-size="14" fill="{GRIS}">{escape(linea)}</text>')
        s.append("</g>")
    s.append("</g>")
    if mk["pie"]:
        yp = H - 22
        s.append(f'<line x1="{X_BOX}" y1="{yp - 22}" x2="{W - X_BOX}" y2="{yp - 22}" stroke="{LINEA}" stroke-width="1"/>')
        s.append(f'<text x="{X_BOX}" y="{yp}" font-size="13" fill="{GRIS}">{escape(mk["pie"])}</text>')
        s.append(f'<text x="{W - X_BOX}" y="{yp}" font-size="12" fill="{mk["secundario"]}" text-anchor="end" letter-spacing="1.5">{escape(mk["lema"])}</text>')
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
                      "destacada": a.destacar, "subconjunto": padre}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
