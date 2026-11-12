"""Ensambla la página HTML del despiece a partir del modelo y de las figuras ya dibujadas.

Usage: python -I ensamblar.py MODELO.json --salida PAGINA.html [--figuras CARPETA] [--marca RUTA.json|ninguna] [--interactivo]

La plantilla es fija y el modelo solo aporta el contenido: cabecera con la pregunta foco y el lector;
nivel 0 (el todo y su frontera); nivel 1 con su figura y la lista de piezas, cada una con su fuente;
un apartado por subconjunto en los niveles siguientes; «Lo que suele malentenderse»; «En tres frases»
(Feynman); «Ponete a prueba» (predicción con la respuesta plegada); y la lista de fuentes. Las figuras
SVG se incrustan inline (sin width/height, para que escalen); las PNG van como <img>; si el fichero
de una figura no existe, se deja un hueco visible «Figura pendiente» y se avisa en stderr.

--interactivo, solo en tipo físico con bloque «geometria» en el modelo, escribe en su lugar la página
interactiva (assets/plantilla-interactiva.html, detalle en references/interactivo.md): vista isométrica
que se explota con un deslizador, desmontaje pieza a pieza con el scroll, flujo paso a paso, nivel 2 que
se abre en su propia lámina y predicción con opciones. Las figuras se dibujan desde la geometría, así que
--figuras no se usa. Sin geometría o en otro tipo, escribe la página estática y lo dice («interactivo»:
false y «motivo» en la salida).

--marca acepta la ruta de un fichero JSON con la marca del proyecto (assets/marca-ejemplo.json enseña
los campos: nombre, primario, secundario, fuente, pie, lema) o «ninguna», el valor por defecto: la skill
no trae la marca de ninguna organización. Tema claro y oscuro respetando los colores de marca.
Salida en stdout: JSON {"salida", "interactivo", "figuras_incrustadas", "figuras_pendientes", "secciones"};
con --interactivo, además «oclusiones» (piezas que otra tapa en algún paso del desmontaje) y «alzas».
Códigos de salida: 0 OK · 1 hay figuras pendientes u oclusiones (la página se escribe igual) · 2
argumentos, fichero del modelo, fichero de marca o geometría inválidos.
Ejemplo:
  python -I ensamblar.py despiece/modelo.json --salida despiece/index.html --figuras despiece/figuras --marca marca.json
  python -I ensamblar.py despiece/modelo.json --salida despiece/interactivo.html --interactivo
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

MARCA_NINGUNA = {"nombre": "", "primario": "#1f2933", "secundario": "#3e7cb1", "fuente": "system-ui, sans-serif", "pie": "", "lema": ""}
CAMPOS_MARCA = {"nombre", "primario", "secundario", "fuente", "pie", "lema"}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

CSS = """
:root{--p:%(primario)s;--s:%(secundario)s;--pt:%(primario)s;--st:%(secundario)s;--papel:#ffffff;--tinta:#1f2933;--gris:#5c6b7a;--linea:#dde3ea;--suave:#f3f6f9}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--pt:%(primario_oscuro)s;--st:%(secundario_oscuro)s;--papel:#121a22;--tinta:#e6edf3;--gris:#9fb0c0;--linea:#2a3744;--suave:#1a2530}}
:root[data-theme="dark"]{--pt:%(primario_oscuro)s;--st:%(secundario_oscuro)s;--papel:#121a22;--tinta:#e6edf3;--gris:#9fb0c0;--linea:#2a3744;--suave:#1a2530}
*{box-sizing:border-box}body{margin:0;background:var(--papel);color:var(--tinta);font-family:%(fuente)s;line-height:1.5}
a{color:var(--st);text-decoration-thickness:1px;text-underline-offset:2px}
main{max-width:1040px;margin:0 auto;padding:32px 16px 48px}
header.cab{border-bottom:3px solid var(--p);padding-bottom:16px;margin-bottom:28px}
header.cab h1{margin:0 0 6px;font-size:1.9rem;color:var(--pt)}header.cab .foco{font-size:1.15rem;margin:6px 0}
.meta{color:var(--gris);font-size:.95rem}.lema{color:var(--st);letter-spacing:.14em;font-size:.72rem;font-weight:600}
section{margin:36px 0}section>h2{font-size:1.35rem;margin:0 0 4px;color:var(--pt)}
.nivel{color:var(--st);font-weight:700;font-size:.8rem;letter-spacing:.08em;text-transform:uppercase}
.frontera{background:var(--suave);border-left:4px solid var(--s);padding:10px 14px;border-radius:6px;margin:12px 0}
figure{margin:18px 0;background:#fff;border:1px solid var(--linea);border-radius:10px;padding:12px}
figure svg,figure img{width:100%%;height:auto;display:block}figcaption{color:#5c6b7a;font-size:.9rem;margin-top:8px}
.pendiente{border:2px dashed #dde3ea;color:#5c6b7a;padding:28px;text-align:center;border-radius:10px}
ol.piezas{padding-left:0;list-style:none;counter-reset:pz}ol.piezas li{counter-increment:pz;display:grid;grid-template-columns:34px 1fr;gap:10px;padding:10px 0;border-bottom:1px solid var(--linea)}
ol.piezas li::before{content:counter(pz);display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%%;background:var(--p);color:#fff;font-weight:700;font-size:.85rem}
ol.piezas b{display:block}ol.piezas .fuente{color:var(--gris);font-size:.85rem}.supuesto{color:#b4541a;font-weight:600}
ul.mal li{margin:6px 0}details{background:var(--suave);border-radius:10px;padding:12px 16px}summary{cursor:pointer;font-weight:600;color:var(--pt)}
.feynman{display:grid;gap:10px}.feynman p{margin:0;padding:12px 14px;background:var(--suave);border-radius:8px;border-left:4px solid var(--p)}
footer.pie{margin-top:48px;padding-top:14px;border-top:1px solid var(--linea);display:flex;justify-content:space-between;color:var(--gris);font-size:.85rem;flex-wrap:wrap;gap:8px}
@media (max-width:640px){header.cab h1{font-size:1.45rem}}
"""


def cargar_marca(valor: str) -> dict:
    """«ninguna» → página neutra; una ruta → JSON con los campos de assets/marca-ejemplo.json (los que
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


def aclarar(hexcolor: str, t: float = 0.55) -> str:
    """Mezcla un color #rrggbb con blanco (t = cuánto blanco). Para que el primario y el secundario,
    pensados para fondo claro, sigan leyéndose como texto sobre el fondo oscuro de la página."""
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    mezcla = lambda c: round(c + (255 - c) * t)  # noqa: E731
    return "#%02x%02x%02x" % (mezcla(r), mezcla(g), mezcla(b))


def _utf8_stdout() -> None:
    # La consola de Windows es cp1252: sin esto, «» y acentos salen rotos en stdout y stderr.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass


def e(t: object) -> str:
    return html.escape(str(t if t is not None else ""), quote=True)


def svg_inline(ruta: Path) -> str:
    svg = ruta.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.IGNORECASE).strip()
    # Sin width/height fijos el contenedor manda; el viewBox queda.
    svg = re.sub(r'(<svg\b[^>]*?)\s(width|height)="[^"]*"', r"\1", svg, count=2)
    return svg


def bloque_figura(f: dict, carpeta: Path | None, pendientes: list[str], incrustadas: list[str]) -> str:
    titulo = e(f.get("titulo", "Figura"))
    fichero = f.get("fichero")
    cuerpo = None
    if fichero:
        ruta = (carpeta / fichero) if carpeta and not Path(fichero).is_absolute() else Path(fichero)
        if ruta.is_file():
            if ruta.suffix.lower() == ".svg":
                cuerpo = svg_inline(ruta)
            else:
                cuerpo = f'<img src="{e(ruta.as_posix())}" alt="{titulo}">'
            incrustadas.append(str(ruta))
    if cuerpo is None:
        pendientes.append(f.get("titulo", fichero or "sin título"))
        skill = f.get("skill", "una skill de dibujo")
        cuerpo = f'<div class="pendiente">Figura pendiente · {titulo}<br><small>se dibuja con {e(skill)} ({e(f.get("tipo_visual", ""))})</small></div>'
    return f"<figure>{cuerpo}<figcaption>{titulo}</figcaption></figure>"


def lista_piezas(piezas: list[dict], fuentes: dict[str, dict]) -> str:
    items = []
    for p in piezas:
        f = p.get("fuente")
        if p.get("supuesto") is True and not f:
            fuente_html = '<span class="supuesto">▲ supuesto, sin fuente</span>'
        else:
            ref = fuentes.get(f, {})
            texto = ref.get("descripcion", f)
            url = ref.get("url")
            fuente_html = f'Fuente: <a href="{e(url)}">{e(texto)}</a>' if url else f"Fuente: {e(texto)}"
        extra = f" ×{p['cantidad']}" if p.get("cantidad") and p["cantidad"] != 1 else ""
        items.append(f"<li><div><b>{e(p.get('nombre'))}{e(extra)}</b>{e(p.get('funcion'))}<div class=\"fuente\">{fuente_html}</div></div></li>")
    return f'<ol class="piezas">{"".join(items)}</ol>'


def main(argv: list[str]) -> int:
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modelo")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--figuras", default=None, help="carpeta donde están los ficheros de las figuras")
    ap.add_argument("--marca", default="ninguna", help="ruta de un JSON de marca (ver assets/marca-ejemplo.json) o «ninguna»")
    ap.add_argument("--interactivo", action="store_true",
                    help="página interactiva (tipo físico con «geometria»); si no se puede, la estática")
    a = ap.parse_args(argv[1:])

    ruta = Path(a.modelo)
    if not ruta.is_file():
        print(f"ERROR: no existe {ruta}", file=sys.stderr)
        return 2
    try:
        m = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        print(f"ERROR: JSON inválido: {ex}. Pasar antes por validar_modelo.py.", file=sys.stderr)
        return 2
    try:
        mk = cargar_marca(a.marca)
    except ValueError as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2
    mk["primario_oscuro"] = aclarar(mk["primario"])
    mk["secundario_oscuro"] = aclarar(mk["secundario"])
    motivo = None
    if a.interactivo:
        if m.get("tipo") != "fisico":
            motivo = f"la página interactiva es solo para tipo físico y este modelo es «{m.get('tipo')}»"
        elif not isinstance(m.get("geometria"), dict):
            motivo = "el modelo no tiene bloque «geometria» (references/interactivo.md)"
        else:
            return interactiva(m, mk, Path(a.salida))
        print(f"AVISO: se escribe la página estática: {motivo}", file=sys.stderr)
    carpeta = Path(a.figuras) if a.figuras else ruta.parent
    piezas = [p for p in m.get("piezas", []) if isinstance(p, dict)]
    por_id = {p["id"]: p for p in piezas if "id" in p}
    fuentes = {f["id"]: f for f in m.get("fuentes", []) if isinstance(f, dict) and "id" in f}
    figuras = [f for f in m.get("figuras", []) if isinstance(f, dict)]
    pendientes: list[str] = []
    incrustadas: list[str] = []
    secciones: list[str] = []

    n0 = m.get("nivel0", {})
    raices = [p for p in piezas if p.get("padre") is None]
    flujo = [por_id[i] for i in m.get("flujo", []) if i in por_id]
    # Orden del nivel 1: en lo físico, el de montaje (coincide con la numeración de la vista explotada);
    # en lo demás, el del flujo si lo hay (se sigue la petición); si no, el escrito.
    if m.get("tipo") == "fisico":
        orden = sorted(raices, key=lambda p: p.get("orden_montaje", 0))
    elif flujo and all(p.get("padre") is None for p in flujo):
        orden = flujo + [p for p in raices if p not in flujo]
    else:
        orden = raices

    partes = [f"<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
              f"<title>{e(m.get('objeto', 'Despiece'))}</title><style>{CSS % mk}</style></head><body><main>"]
    lema_html = f'<div class="lema">{e(mk["lema"])}</div>' if mk["lema"] else ""
    partes.append(f"<header class=\"cab\">{lema_html}"
                  f"<h1>{e(m.get('objeto'))}</h1><p class=\"foco\"><b>La pregunta:</b> {e(m.get('pregunta_foco'))}</p>"
                  f"<p class=\"meta\">Para {e(m.get('lector'))} · despiece de tipo {e(m.get('tipo'))} · {len(piezas)} piezas en {m.get('profundidad', 2)} niveles</p></header>")

    # Nivel 0
    partes.append(f"<section><div class=\"nivel\">Nivel 0 · el todo</div><h2>{e(n0.get('titulo'))}</h2>"
                  f"<div class=\"frontera\"><b>Frontera:</b> {e(n0.get('frontera'))}"
                  + (f"<br><b>Queda fuera:</b> {e('; '.join(n0.get('fuera', [])))}" if n0.get("fuera") else "") + "</div>"
                  + "".join(bloque_figura(f, carpeta, pendientes, incrustadas) for f in figuras if f.get("nivel") == 0) + "</section>")
    secciones.append("nivel0")

    # Nivel 1
    fig1 = [f for f in figuras if f.get("nivel") == 1]
    titulo1 = fig1[0].get("titulo") if fig1 else f"Las {len(raices)} piezas de {m.get('objeto')}"
    partes.append(f"<section><div class=\"nivel\">Nivel 1 · las piezas</div><h2>{e(titulo1)}</h2>"
                  + "".join(bloque_figura(f, carpeta, pendientes, incrustadas) for f in fig1)
                  + lista_piezas(orden, fuentes) + "</section>")
    secciones.append("nivel1")

    # Niveles 2+ : un apartado por padre con hijos
    for nivel in (2, 3):
        padres = [p for p in orden if any(q.get("padre") == p["id"] for q in piezas)] if nivel == 2 else \
                 [p for p in piezas if p.get("padre") in {x["id"] for x in piezas if x.get("padre") is not None} and any(q.get("padre") == p["id"] for q in piezas)]
        for padre in padres:
            hijos = [q for q in piezas if q.get("padre") == padre["id"]]
            figs = [f for f in figuras if f.get("nivel") == nivel and any(h["id"] in (f.get("piezas") or []) for h in hijos)]
            titulo = figs[0].get("titulo") if figs else f"Dentro de {padre.get('nombre')}"
            partes.append(f"<section><div class=\"nivel\">Nivel {nivel} · zoom</div><h2>{e(titulo)}</h2>"
                          + "".join(bloque_figura(f, carpeta, pendientes, incrustadas) for f in figs)
                          + lista_piezas(hijos, fuentes) + "</section>")
            secciones.append(f"nivel{nivel}:{padre['id']}")

    if m.get("malentendidos"):
        partes.append("<section><h2>Lo que suele malentenderse</h2><ul class=\"mal\">"
                      + "".join(f"<li>{e(x)}</li>" for x in m["malentendidos"]) + "</ul></section>")
        secciones.append("malentendidos")
    if isinstance(m.get("feynman"), list):
        partes.append("<section><h2>En tres frases</h2><div class=\"feynman\">"
                      + "".join(f"<p>{e(x)}</p>" for x in m["feynman"]) + "</div></section>")
        secciones.append("feynman")
    pred = m.get("prediccion") or {}
    if pred.get("pregunta"):
        partes.append(f"<section><h2>Ponete a prueba</h2><p>{e(pred['pregunta'])}</p>"
                      f"<details><summary>Ver la respuesta</summary><p>{e(pred.get('respuesta'))}</p></details></section>")
        secciones.append("prediccion")
    if fuentes:
        items_f = []
        for f in fuentes.values():
            texto = e(f.get("descripcion", f["id"]))
            items_f.append(f'<li><a href="{e(f["url"])}">{texto}</a></li>' if f.get("url") else f"<li>{texto}</li>")
        partes.append("<section><h2>Fuentes</h2><ul>" + "".join(items_f) + "</ul></section>")
        secciones.append("fuentes")
    pie_izq = e(mk["pie"]) if mk["pie"] else e(m.get("objeto"))
    partes.append(f"<footer class=\"pie\"><span>{pie_izq}</span><span class=\"lema\">{e(mk['lema'])}</span></footer></main></body></html>")

    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(partes), encoding="utf-8")
    for p in pendientes:
        print(f"AVISO: figura pendiente «{p}»: dibujarla y volver a ensamblar", file=sys.stderr)
    resultado = {"salida": str(salida), "interactivo": False, "figuras_incrustadas": incrustadas,
                 "figuras_pendientes": pendientes, "secciones": secciones}
    if motivo:
        resultado["motivo"] = motivo
    print(json.dumps(resultado, ensure_ascii=False))
    return 1 if pendientes else 0


def interactiva(m: dict, mk: dict, salida: Path) -> int:
    # python -I no pone la carpeta del script en sys.path: sin esto no se encuentran los módulos hermanos
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import interactiva as pag  # noqa: E402
    try:
        texto, info = pag.pagina(m, mk)
    except (KeyError, StopIteration, TypeError, ValueError, IndexError) as ex:
        print(f"ERROR: geometría incompleta ({type(ex).__name__}: {ex}). validar_modelo.py dice qué falta.", file=sys.stderr)
        return 2
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(texto, encoding="utf-8")
    for o in info["oclusiones"]:
        print(f"AVISO: «{o['tapada']}» queda tapada por {o['por']} en el paso {o['estado']} del desmontaje: "
              "mover piezas en «geometria» o agruparlas", file=sys.stderr)
    print(json.dumps({"salida": str(salida), "interactivo": True, "figuras_incrustadas": [], "figuras_pendientes": [],
                      "secciones": info["secciones"], "oclusiones": info["oclusiones"], "alzas": info["alzas"]},
                     ensure_ascii=False))
    return 1 if info["oclusiones"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
