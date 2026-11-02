"""Pruebas del validador: cada mutación de assets/ejemplo-fisico.json tiene que disparar su regla.

Usage: python -I evals/probar_validador.py

Sirve al tocar validar_modelo.py: una regla que deja de saltar, o un aviso que salta donde no debe, se
ve aquí antes que en un modelo real. No escribe nada (tampoco __pycache__).
Salida: una línea OK/MAL por caso y el total. Códigos: 0 todas pasan · 1 alguna falla.
"""
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, str(RAIZ / "scripts"))
import validar_modelo as v  # noqa: E402

if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
    print(__doc__.strip())
    sys.exit(0)
base = json.loads((RAIZ / "assets" / "ejemplo-fisico.json").read_text(encoding="utf-8"))
E0, A0, _ = v.validar(base)
if E0 or A0:
    print(f"MAL el ejemplo de partida no está limpio: E={E0} A={A0}")
    sys.exit(1)


def caso(nombre, mutar, clase, fragmento):
    m = copy.deepcopy(base)
    mutar(m)
    E, A, _ = v.validar(m)
    lista = E if clase == "E" else A
    ok = any(fragmento in x for x in lista)
    print(("OK  " if ok else "MAL ") + f"{clase} {nombre}" + ("" if ok else f"\n     E={E}\n     A={A}"))
    return ok


def sin(nombre, mutar, fragmento):
    m = copy.deepcopy(base)
    mutar(m)
    E, A, _ = v.validar(m)
    ok = not any(fragmento in x for x in E + A)
    print(("OK  " if ok else "MAL ") + f"- {nombre}" + ("" if ok else f" E={E} A={A}"))
    return ok


def poner(ruta, valor):
    def f(m):
        d = m
        for k in ruta[:-1]:
            d = d[k]
        d[ruta[-1]] = valor
    return f


def quitar(ruta):
    def f(m):
        d = m
        for k in ruta[:-1]:
            d = d[k]
        del d[ruta[-1]]
    return f


G = ["geometria"]
P = G + ["piezas"]
S = G + ["subconjuntos", "nand"]
r = [
    caso("destacada fuera de la figura", poner(["figuras", 0, "destacada"], "nand-slc"), "E", "destacada «nand-slc»"),
    caso("opciones: una sola", poner(["prediccion", "opciones"], ["solo una"]), "E", "entre 2 y 4"),
    caso("opciones: correcta fuera de rango", poner(["prediccion", "correcta"], 2), "E", "de 0 a 1"),
    caso("opciones: correcta booleana", poner(["prediccion", "correcta"], True), "E", "de 0 a 1"),
    caso("correcta sin opciones", quitar(["prediccion", "opciones"]), "A", "sin opciones"),
    caso("flujo_entrada fuera de nivel0.fuera", poner(["flujo_entrada"], "la fuente de alimentación"), "A", "nivel0.fuera"),
    caso("flujo_entrada vacío", poner(["flujo_entrada"], ""), "E", "flujo_entrada debe ser"),
    caso("paso del flujo sin relación", poner(["relaciones"], [x for x in base["relaciones"] if x["a"] != "dram"]), "A", "a «dram» (paso 3)"),
    caso("geometría en tipo sistema", lambda m: (m.update(tipo="sistema")), "A", "tipo sistema"),
    caso("placa sin ancho", quitar(G + ["placa", "ancho"]), "E", "largo y ancho"),
    caso("raíz sin geometría", quitar(P + ["dram"]), "E", "faltan las raíces ['dram']"),
    caso("geometría de una hija en piezas", poner(P + ["nand-slc"], {"forma": "chip", "x": [1, 2], "y": [1, 2], "alto": 1}), "E", "no es raíz"),
    caso("id inexistente", poner(P + ["disipador"], {"forma": "caja", "x": [1, 2], "y": [1, 2], "alto": 1}), "E", "«disipador» no existe"),
    caso("forma desconocida", poner(P + ["dram", "forma"], "esfera"), "E", "forma «esfera»"),
    caso("dos placas", poner(P + ["dram"], {"forma": "placa"}), "E", "exactamente una"),
    caso("placa no es la primera", lambda m: [p.update(orden_montaje=9) for p in m["piezas"] if p["id"] == "pcb"], "E", "primera en orden_montaje"),
    caso("rango al revés", poner(P + ["dram", "x"], [36, 28]), "E", "x debe ser"),
    caso("alto cero", poner(P + ["dram", "alto"], 0), "E", "alto debe ser > 0"),
    caso("z negativa", poner(P + ["dram", "z"], -1), "E", "z (altura"),
    caso("unidades ≠ cantidad", poner(P + ["nand", "unidades"], [[40, 48.5], [50, 58.5]]), "E", "2 unidades y cantidad = 4"),
    caso("cantidad sin unidades", lambda m: (m["geometria"]["piezas"]["nand"].pop("unidades"), m["geometria"]["piezas"]["nand"].update(x=[40, 78])), "A", "sin unidades"),
    caso("se sale de la placa", poner(P + ["dram", "x"], [76, 84]), "A", "se sale de la placa"),
    caso("solape en volumen", poner(P + ["dram", "x"], [20, 30]), "E", "ocupan el mismo volumen"),
    sin("apilado con z no solapa", lambda m: m["geometria"]["piezas"]["dram"].update(x=[14, 22], z=1.3), "mismo volumen"),
    caso("lift a mano", poner(P + ["dram", "lift"], 40), "A", "«lift» se ignora"),
    caso("rótulo de placa con hueco inexistente", poner(G + ["placa", "rotulo"], "Placa {modelo}"), "E", "{modelo}"),
    caso("rótulo de subconjunto con llave sin cerrar", poner(S + ["rotulo"], "Chip de {ancho"), "E", "llaves sin cerrar"),
    caso("muesca mal", poner(P + ["conector", "muesca"], [16, 14]), "E", "muesca"),
    caso("subconjunto de una raíz sin hijos", poner(G + ["subconjuntos", "dram"], {"huella": {"x": [0, 1], "y": [0, 1]}, "piezas": {}}), "E", "«dram» no es una raíz con hijos"),
    caso("huella sin y", quitar(S + ["huella", "y"]), "E", "huella necesita"),
    caso("capa que no es hija", poner(S + ["piezas", "dram"], {"z": [3, 4]}), "E", "no es hija"),
    caso("capa sin z", quitar(S + ["piezas", "nand-slc", "z"]), "E", "z debe ser [desde, hasta]"),
    caso("patrón desconocido", poner(S + ["piezas", "nand-celdas", "patron"], "rayas"), "E", "patron «rayas»"),
    caso("hija sin geometría", quitar(S + ["piezas", "nand-slc"]), "A", "['nand-slc'] no tienen geometría"),
    caso("raíz con hijos sin subconjunto", quitar(G + ["subconjuntos"]), "A", "no la abre en el nivel 2"),
    caso("paso del flujo que no es raíz", lambda m: m["flujo"].append("nand-slc"), "A", "no son raíces"),
    caso("nivel 3", lambda m: (m.update(profundidad=3), m["piezas"].extend([
        {"id": "c1", "nombre": "Celda 1", "padre": "nand-celdas", "funcion": "x", "supuesto": True},
        {"id": "c2", "nombre": "Celda 2", "padre": "nand-celdas", "funcion": "x", "supuesto": True}])), "A", "nivel 3"),
]
print(f"{sum(bool(x) for x in r)}/{len(r)}")
sys.exit(0 if all(r) else 1)
