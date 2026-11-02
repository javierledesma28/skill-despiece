"""Valida un modelo de despiece (modelo.json) antes de dibujar o ensamblar.

Usage: python -I validar_modelo.py MODELO.json

Comprueba lo que el método exige y que, sin guía, se salta (E = error, A = aviso):
  E  JSON válido con objeto, tipo (fisico|proceso|sistema|idea), pregunta_foco (termina en «?»), lector
  E  nivel0.titulo y nivel0.frontera presentes; el título afirma algo (no «Qué es…», no termina en «:»)
  E  piezas con id único, nombre, funcion y fuente (o supuesto: true); padre existente y sin ciclos
  E  raíces: 2–7 (A si son 2); hijos por padre: 2–7 (una pieza con un solo hijo no se despieza)
  E  tipo fisico: orden_montaje entero en las raíces; proceso/sistema: flujo con ≥ 3 ids existentes
  E  relaciones con de/a existentes y tipo conocido
  E  feynman con exactamente 3 frases; prediccion con pregunta (termina en «?») y respuesta
  A  figuras: > 6 piezas nuevas (E si > 9), título no afirmativo, skill desconocida, nivel > profundidad
  A  funcion > 160 caracteres (es un párrafo, no una función); nombre > 40
  A  sin malentendidos; sin figuras; piezas sin ninguna figura que las muestre

Salida (stdout, JSON): {"ok", "errores": [...], "avisos": [...], "metricas": {...}}
Códigos de salida: 0 sin errores · 1 hay errores · 2 argumentos o fichero inválidos.
Ejemplo:
  python -I validar_modelo.py despiece/modelo.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TIPOS = {"fisico", "proceso", "sistema", "idea"}
TIPOS_RELACION = {"flujo", "contiene", "depende", "controla", "dato", "energia", "causa"}
SKILLS_DIBUJO = {"diagram-design", "diagrama-microsoft-learn", "grafico-interactivo", "explosionado", "propio", "ninguna"}
NO_AFIRMATIVO = re.compile(
    r"^\s*(qu[eé] es|definici[oó]n|introducci[oó]n|visi[oó]n general|resumen|overview|descripci[oó]n)\b",
    re.IGNORECASE,
)


def _utf8_stdout() -> None:
    # La consola de Windows es cp1252: sin esto, «» y acentos salen rotos en stdout y stderr.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - consolas antiguas
            pass


def titulo_afirmativo(t: str) -> str | None:
    """Devuelve el motivo si el título no afirma nada; None si pasa."""
    if not isinstance(t, str) or not t.strip():
        return "vacío"
    if t.strip().endswith(":"):
        return "termina en «:»"
    if NO_AFIRMATIVO.search(t):
        return "empieza como una definición o un índice («Qué es…», «Introducción…»)"
    if len(t.split()) < 4:
        return "menos de 4 palabras: un rótulo, no una afirmación"
    return None


def validar(m: dict) -> tuple[list[str], list[str], dict]:
    E: list[str] = []
    A: list[str] = []

    for campo in ("objeto", "tipo", "pregunta_foco", "lector"):
        if not isinstance(m.get(campo), str) or not m[campo].strip():
            E.append(f"falta «{campo}» o está vacío")
    tipo = m.get("tipo")
    if tipo not in TIPOS:
        E.append(f"tipo «{tipo}» desconocido; usar uno de {sorted(TIPOS)}")
    pf = m.get("pregunta_foco", "")
    if isinstance(pf, str) and pf.strip() and not pf.strip().endswith("?"):
        E.append("pregunta_foco no termina en «?»: tiene que ser la pregunta que el lector quiere responder")

    profundidad = m.get("profundidad", 2)
    if not isinstance(profundidad, int) or not 1 <= profundidad <= 3:
        E.append("profundidad debe ser un entero entre 1 y 3")
        profundidad = 2

    n0 = m.get("nivel0") or {}
    if not isinstance(n0, dict):
        E.append("nivel0 debe ser un objeto con titulo y frontera")
        n0 = {}
    motivo = titulo_afirmativo(n0.get("titulo", ""))
    if motivo:
        E.append(f"nivel0.titulo no afirma nada ({motivo})")
    if not isinstance(n0.get("frontera"), str) or not n0["frontera"].strip():
        E.append("nivel0.frontera vacía: hay que decir dónde empieza y termina el objeto")

    piezas = m.get("piezas")
    if not isinstance(piezas, list) or not piezas:
        E.append("piezas debe ser una lista no vacía")
        piezas = []
    ids: dict[str, dict] = {}
    for i, p in enumerate(piezas):
        if not isinstance(p, dict):
            E.append(f"piezas[{i}] no es un objeto")
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not pid.strip():
            E.append(f"piezas[{i}] sin id")
            continue
        if pid in ids:
            E.append(f"id de pieza repetido: «{pid}»")
            continue
        ids[pid] = p
        for campo in ("nombre", "funcion"):
            if not isinstance(p.get(campo), str) or not p[campo].strip():
                E.append(f"pieza «{pid}» sin «{campo}»")
        fuente = p.get("fuente")
        if not (isinstance(fuente, str) and fuente.strip()) and p.get("supuesto") is not True:
            E.append(f"pieza «{pid}» sin fuente y sin «supuesto: true»: no se explica de memoria")
        if isinstance(p.get("funcion"), str) and len(p["funcion"]) > 160:
            A.append(f"pieza «{pid}»: funcion de {len(p['funcion'])} caracteres; una función se dice en una línea")
        if isinstance(p.get("nombre"), str) and len(p["nombre"]) > 40:
            A.append(f"pieza «{pid}»: nombre de {len(p['nombre'])} caracteres; acortarlo para que quepa en la figura")

    # Jerarquía: padres existentes, sin ciclos, conteos por nivel.
    hijos: dict[str | None, list[str]] = {}
    for pid, p in ids.items():
        padre = p.get("padre")
        if padre is not None and padre not in ids:
            E.append(f"pieza «{pid}»: padre «{padre}» no existe")
            padre = None
        hijos.setdefault(padre, []).append(pid)
    for pid in ids:
        visto = set()
        cur: str | None = pid
        while cur is not None:
            if cur in visto:
                E.append(f"ciclo en la jerarquía de piezas pasando por «{pid}»")
                break
            visto.add(cur)
            cur = ids[cur].get("padre") if cur in ids else None
    raices = hijos.get(None, [])
    if len(raices) > 7:
        E.append(f"{len(raices)} piezas en el nivel 1: más de 7 no se retienen; agrupar en subconjuntos")
    elif len(raices) < 2 and ids:
        E.append("una sola pieza en el nivel 1: eso no es un despiece")
    elif len(raices) == 2:
        A.append("solo 2 piezas en el nivel 1: comprobar que la partición no esconde una tercera")
    for padre, hs in hijos.items():
        if padre is None:
            continue
        if len(hs) == 1:
            E.append(f"«{padre}» tiene un solo hijo («{hs[0]}»): o se funden o falta alguna pieza")
        elif len(hs) > 7:
            E.append(f"«{padre}» tiene {len(hs)} hijos: más de 7 no se retienen; agrupar")

    def nivel_de(pid: str) -> int:
        n, cur = 1, ids[pid].get("padre")
        while cur in ids:
            n += 1
            cur = ids[cur].get("padre")
        return n

    niveles = {pid: nivel_de(pid) for pid in ids}
    max_nivel = max(niveles.values(), default=0)
    if max_nivel > profundidad:
        A.append(f"hay piezas en el nivel {max_nivel} y profundidad={profundidad}: o se sube la profundidad o sobran niveles")

    if tipo == "fisico":
        for pid in raices:
            if not isinstance(ids[pid].get("orden_montaje"), int):
                E.append(f"tipo fisico: la pieza «{pid}» necesita orden_montaje (entero); el desmontaje es el montaje al revés")
        ordenes = [ids[p].get("orden_montaje") for p in raices if isinstance(ids[p].get("orden_montaje"), int)]
        if len(ordenes) != len(set(ordenes)):
            E.append("tipo fisico: hay orden_montaje repetidos entre las raíces")

    flujo = m.get("flujo") or []
    if not isinstance(flujo, list):
        E.append("flujo debe ser una lista de ids")
        flujo = []
    for fid in flujo:
        if fid not in ids:
            E.append(f"flujo: id «{fid}» no existe en piezas")
    if tipo in {"proceso", "sistema"} and len(flujo) < 3:
        E.append(f"tipo {tipo}: flujo necesita al menos 3 pasos; sin flujo no se puede «seguir la petición»")

    for i, r in enumerate(m.get("relaciones") or []):
        if not isinstance(r, dict):
            E.append(f"relaciones[{i}] no es un objeto")
            continue
        for extremo in ("de", "a"):
            if r.get(extremo) not in ids:
                E.append(f"relaciones[{i}]: «{extremo}» = «{r.get(extremo)}» no existe")
        if r.get("tipo") not in TIPOS_RELACION:
            E.append(f"relaciones[{i}]: tipo «{r.get('tipo')}» desconocido; usar uno de {sorted(TIPOS_RELACION)}")

    if not m.get("malentendidos"):
        A.append("sin malentendidos: ¿qué suele creer el lector que es falso? Es lo que más ayuda a entender")

    figuras = m.get("figuras") or []
    if not isinstance(figuras, list):
        E.append("figuras debe ser una lista")
        figuras = []
    if not figuras:
        A.append("sin figuras: el despiece es visual; al menos una por nivel mostrado")
    mostradas: set[str] = set()
    for i, f in enumerate(figuras):
        if not isinstance(f, dict):
            E.append(f"figuras[{i}] no es un objeto")
            continue
        motivo = titulo_afirmativo(f.get("titulo", ""))
        if motivo:
            A.append(f"figuras[{i}]: el título no afirma nada ({motivo}); el título dice lo que la figura demuestra")
        if f.get("skill") not in SKILLS_DIBUJO:
            A.append(f"figuras[{i}]: skill «{f.get('skill')}» desconocida; usar una de {sorted(SKILLS_DIBUJO)}")
        nivel = f.get("nivel")
        if not isinstance(nivel, int) or nivel < 0:
            E.append(f"figuras[{i}]: nivel debe ser un entero ≥ 0")
        elif nivel > profundidad:
            A.append(f"figuras[{i}]: nivel {nivel} por encima de profundidad={profundidad}")
        pz = f.get("piezas") or []
        desconocidas = [p for p in pz if p not in ids]
        if desconocidas:
            E.append(f"figuras[{i}]: piezas inexistentes {desconocidas}")
        nuevas = [p for p in pz if p not in mostradas]
        if len(nuevas) > 9:
            E.append(f"figuras[{i}]: {len(nuevas)} piezas nuevas; nadie retiene más de 9 en una figura")
        elif len(nuevas) > 6:
            A.append(f"figuras[{i}]: {len(nuevas)} piezas nuevas; el tope cómodo son 6")
        mostradas.update(pz)
    sin_figura = [p for p in ids if p not in mostradas]
    if figuras and sin_figura:
        A.append(f"piezas que ninguna figura muestra: {sin_figura}")

    fey = m.get("feynman")
    if not isinstance(fey, list) or len(fey) != 3 or not all(isinstance(s, str) and s.strip() for s in fey):
        E.append("feynman debe ser una lista de exactamente 3 frases no vacías")
    else:
        for s in fey:
            if len(s) > 220:
                A.append(f"feynman: frase de {len(s)} caracteres; si no cabe en una línea y media, no está entendido")

    pred = m.get("prediccion") or {}
    if not isinstance(pred, dict) or not isinstance(pred.get("pregunta"), str) or not pred["pregunta"].strip():
        E.append("prediccion.pregunta vacía: hay que hacer predecir al lector antes de darle la respuesta")
    elif not pred["pregunta"].strip().endswith("?"):
        E.append("prediccion.pregunta no termina en «?»")
    if not isinstance(pred, dict) or not isinstance(pred.get("respuesta"), str) or not pred["respuesta"].strip():
        E.append("prediccion.respuesta vacía")

    metricas = {
        "tipo": tipo,
        "piezas": len(ids),
        "raices": len(raices),
        "niveles": max_nivel,
        "profundidad": profundidad,
        "figuras": len(figuras),
        "supuestos": sum(1 for p in ids.values() if p.get("supuesto") is True),
        "pasos_flujo": len(flujo),
    }
    return E, A, metricas


def main(argv: list[str]) -> int:
    _utf8_stdout()
    if len(argv) != 2 or argv[1] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stderr if len(argv) == 2 else sys.stdout)
        return 0 if len(argv) == 2 and argv[1] in {"-h", "--help"} else 2
    ruta = Path(argv[1])
    if not ruta.is_file():
        print(f"ERROR: no existe {ruta}. Escribir primero el modelo (ver references/modelo.md).", file=sys.stderr)
        return 2
    try:
        modelo = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {ruta} no es JSON válido: {e}. Revisar comas finales y comillas.", file=sys.stderr)
        return 2
    if not isinstance(modelo, dict):
        print("ERROR: el modelo debe ser un objeto JSON", file=sys.stderr)
        return 2
    E, A, metricas = validar(modelo)
    print(json.dumps({"ok": not E, "errores": E, "avisos": A, "metricas": metricas}, ensure_ascii=False, indent=2))
    return 1 if E else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
