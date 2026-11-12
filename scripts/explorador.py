"""Explorador del despiece: lo escribe ensamblar.py --explorador, no se ejecuta solo.

Dibuja en Python la lámina de cada nivel que se puede abrir (las raíces y cada pieza con hijos) con la
misma geometría que explosionado.py, y rellena assets/plantilla-explorador.html: una sola página, sin
dependencias, para los cuatro tipos. Se navega con zoom semántico: acercar sobre una pieza con «+» la
abre en su propia lámina y alejar vuelve al nivel de arriba (rueda, pellizco, botones o teclado). Un panel
lateral lleva las migas, la lista de piezas del nivel y la ficha de la elegida (función y fuente), y el
historial del navegador acompaña: «atrás» sube un nivel y #/<id> abre ese nivel directamente.

Las láminas se precalculan en vez de portar la geometría a JavaScript: así hay una sola implementación
del dibujo y el explorador enseña exactamente las mismas figuras que la página estática.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import explosionado as ex
from interactiva import e, json_en_html, mezclar, tokens_marca

PLANTILLA = Path(__file__).resolve().parent.parent / "assets" / "plantilla-explorador.html"
PREFIJO = "Vista explotada · "


def niveles_de(piezas: list[dict]) -> list[str | None]:
    """None (las raíces) y cada pieza con hijos, en recorrido en profundidad por «orden»."""
    hijos: dict[str | None, list[dict]] = {}
    for p in piezas:
        hijos.setdefault(p.get("padre"), []).append(p)
    clave = lambda p: (ex.orden_de(p) is None, ex.orden_de(p) or 0)  # noqa: E731
    salida: list[str | None] = []

    def recorrer(padre: str | None) -> None:
        salida.append(padre)
        for p in sorted(hijos.get(padre, []), key=clave):
            if p["id"] in hijos:
                recorrer(p["id"])
    recorrer(None)
    return salida


def con_aspecto(svg: str, vb: str) -> str:
    """El CSS encaja la lámina en su caja con el aspecto del viewBox: --ar como número para calc()."""
    _, _, w, h = (float(x) for x in vb.split())
    return svg.replace("<svg ", f'<svg style="--ar:{w / h:.4f};aspect-ratio:{w:g}/{h:g}" ', 1)


def pagina(m: dict, mk: dict) -> tuple[str, dict]:
    """HTML completo y un resumen {niveles, piezas}. Lanza ValueError si un nivel no se puede dibujar y
    ET.ParseError si una lámina no es XML válido: ensamblar.py los convierte en errores accionables."""
    piezas = [p for p in m.get("piezas", []) if isinstance(p, dict) and "id" in p]
    fuentes = {f["id"]: f for f in m.get("fuentes", []) if isinstance(f, dict) and "id" in f}
    hijos: dict[str, int] = {}
    for p in piezas:
        if p.get("padre"):
            hijos[p["padre"]] = hijos.get(p["padre"], 0) + 1
    objeto = m.get("objeto", "Despiece")
    n0 = m.get("nivel0") or {}

    vista: dict = {"objeto": objeto, "niveles": {}, "piezas": {}}
    for p in piezas:
        f = fuentes.get(p.get("fuente") or "")
        fuente = None if (p.get("supuesto") is True or not f) else {"texto": f.get("descripcion", f["id"]), "url": f.get("url")}
        cantidad = p.get("cantidad") if isinstance(p.get("cantidad"), int) and p.get("cantidad") != 1 else None
        vista["piezas"][p["id"]] = {"nombre": p.get("nombre", p["id"]), "funcion": p.get("funcion", ""),
                                    "padre": p.get("padre") or "", "cantidad": cantidad, "fuente": fuente,
                                    "hijos": hijos.get(p["id"], 0)}

    plantillas: list[str] = []
    svg_inicial = ""
    for nivel in niveles_de(piezas):
        svg, inf = ex.figura(m, nivel, None, mk, None, explorador=True)
        ET.fromstring(svg)
        svg = con_aspecto(svg, inf["viewBox"])
        clave = nivel or ""
        if nivel is None:
            svg_inicial = svg
        plantillas.append(f'<template data-nivel="{e(clave)}">{svg}</template>')
        sub = inf["subtitulo"]
        sub = sub[len(PREFIJO):] if sub.startswith(PREFIJO) else ""
        prof, q = 1, nivel
        while q:
            prof += 1
            q = vista["piezas"][q]["padre"]
        vista["niveles"][clave] = {"titulo": inf["titulo"], "subtitulo": sub[:1].upper() + sub[1:], "piezas": inf["piezas"],
                                   "prof": prof}
        for k, pid in enumerate(inf["piezas"], 1):
            vista["piezas"][pid]["num"] = k

    pred = m.get("prediccion") or {}
    vista["comprension"] = {"feynman": [str(x) for x in m.get("feynman") or []],
                            "pregunta": pred.get("pregunta"), "respuesta": pred.get("respuesta")}
    vista["raiz"] = {"titulo": n0.get("titulo"), "frontera": n0.get("frontera"),
                     "fuera": [str(x) for x in n0.get("fuera") or []], "foco": m.get("pregunta_foco"),
                     "lector": m.get("lector")}

    c = mk["secundario"]
    destacada, _ = ex.paleta(mk, True, False)
    apagada, _ = ex.paleta(mk, False, True)
    nombre_marca = mk.get("nombre", "")
    pie_izq = e(mk["pie"]) if mk.get("pie") else e(objeto)
    valores = {
        "TITULO_PAGINA": e(f"{objeto} · explorador"),
        **tokens_marca(mk),
        "HL_S": destacada["sup"], "HL_I": destacada["izq"], "HL_D": destacada["der"], "HL_B": destacada["borde"], "HL_N": c,
        "VER_S": mezclar(c, "#ffffff", .88), "VER_I": mezclar(c, "#ffffff", .74), "VER_D": mezclar(c, "#ffffff", .62),
        "AP_S": apagada["sup"], "AP_I": apagada["izq"], "AP_D": apagada["der"], "AP_B": apagada["borde"],
        "MARCA_BARRA": (f"{e(nombre_marca)} <span>· despiece</span>" if nombre_marca else "despiece <span>· explorador</span>"),
        "OBJETO": e(objeto), "TITULO_RAIZ": e(vista["niveles"][""]["titulo"]),
        "SVG_INICIAL": svg_inicial, "PLANTILLAS": "\n".join(plantillas),
        "PIE": f"<span>{pie_izq}</span>" + (f'<span class="lema">{e(mk["lema"])}</span>' if mk.get("lema") else ""),
        "VISTA_JSON": json_en_html(vista),
    }
    texto = PLANTILLA.read_text(encoding="utf-8")
    for k, v in valores.items():
        texto = texto.replace("{{" + k + "}}", str(v))
    sobrantes = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", texto)))
    if sobrantes:
        raise ValueError(f"la plantilla tiene huecos sin rellenar: {sobrantes}")
    return texto, {"niveles": [n or "" for n in niveles_de(piezas)], "piezas": len(piezas)}
