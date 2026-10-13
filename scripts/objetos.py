# -*- coding: utf-8 -*-
"""Saca los objetos magicos de los cinco SRD 5.2.1 con su estructura.

Mismo lector que los conjuros (titulo GillSans-SemiBold 12 y linea en cursiva debajo, cuerpo en bloques). Cada
objeto sale con: nombre, pagina, cabecera (categoria, rareza y sintonizacion, tal cual) y bloques.

Uso: py -3.14 objetos.py   (deja datos\\_objetos_crudo.json; lo empareja emparejar_objetos.py)
"""
import json
import re
import os
import sys

from conjuros import cortar, cuerpo
from srd import LANGS, limpia, une

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def objetos(lang):
    res = []
    for e in cortar(lang, "objetos"):
        fs = [dict(r) for r in e["filas"]]
        k, cab = 0, []
        while k < len(fs) and fs[k]["font"] == "Cambria-Italic":
            t = limpia(fs[k]["t"])
            hasta = une(cab)
            abierto = hasta.count("(") > hasta.count(")") or hasta.endswith(",") or \
                re.search(r"\b(Very|or|and|o|y|muy|oder|sehr|ou|très|molto|e)$", hasta) is not None
            if cab and not abierto and t[:1].isupper():
                # la primera linea del texto en cursiva por error de maqueta (la cota de escamas de dragon
                # espanola): es texto normal, no cabecera
                fs[k]["font"] = "Cambria"
                fs[k]["spans"] = [[s[0], s[1].replace("-Italic", "")] + list(s[2:]) for s in fs[k]["spans"]]
                break
            cab.append(fs[k]["t"]); k += 1
        res.append({"nombre": e["nombre"], "p": e["p"], "cabecera": une(cab), "bloques": cuerpo(lang, fs[k:])})
    return res


# Tablas que la maqueta coloco dentro de otro objeto: (idioma, objeto donde sale, titulo de la tabla, objeto al que
# pertenece). La tabla de palancas del aparato aleman sale en mitad del amuleto de los planos, dos objetos antes.
MOVER = [("de", "Amulett der Ebenen", "Hebel des Apparats der Krabbe", "Apparat der Krabbe")]


def mover_tablas(lang, lista, avisos):
    por = {o["nombre"]: o for o in lista}
    for l, desde, titulo, hacia in MOVER:
        if l != lang:
            continue
        a, b = por.get(desde), por.get(hacia)
        t = next((x for x in (a or {}).get("bloques", []) if x["t"] == "tabla" and x.get("titulo") == titulo), None)
        if a is None or b is None or t is None:
            avisos.append(f"{lang}: no se pudo mover la tabla '{titulo}' de {desde} a {hacia}")
            continue
        a["bloques"].remove(t)
        b["bloques"].append(t)


def unir_frases_partidas(o):
    """Un parrafo que empieza en minuscula detras de una tabla sigue la frase de antes de la tabla (la maqueta
    metio la tabla en mitad del parrafo): se une a ese parrafo y la tabla queda detras."""
    bl = o["bloques"]
    k = 2
    while k < len(bl):
        a, t, b = bl[k - 2], bl[k - 1], bl[k]
        if a["t"] == "p" and t["t"] == "tabla" and b["t"] == "p" and b["txt"][:1].islower() \
                and not re.sub(r"<[^>]+>", "", a["txt"]).rstrip().endswith((".", ":", "!", "?")):
            a["txt"] = a["txt"].rstrip() + " " + b["txt"].lstrip()
            del bl[k]
            continue
        k += 1
    # y dos parrafos seguidos en los que el segundo sigue la frase del primero (la tabla de en medio era de
    # otro objeto y ya se ha llevado a su sitio)
    k = 1
    while k < len(bl):
        a, b = bl[k - 1], bl[k]
        if a["t"] == "p" and b["t"] == "p" and b["txt"][:1].islower() \
                and not re.sub(r"<[^>]+>", "", a["txt"]).rstrip().endswith((".", ":", "!", "?")):
            a["txt"] = a["txt"].rstrip() + " " + b["txt"].lstrip()
            del bl[k]
            continue
        k += 1


def main():
    salida = {}
    for l in LANGS:
        o = objetos(l)
        avisos = []
        mover_tablas(l, o, avisos)
        for x in o:
            unir_frases_partidas(x)
        for a in avisos:
            print("  ", a)
        otros = [(x["nombre"], b["txt"][:40]) for x in o for b in x["bloques"] if b["t"] == "otro"]
        vacios = [x["nombre"] for x in o if not x["bloques"]]
        print(f"{l}: {len(o)} objetos; sin texto {len(vacios)} {vacios[:4]}; bloques sin clasificar {len(otros)} "
              f"{otros[:3]}")
        salida[l] = o
    with open(os.path.join(DATOS, "_objetos_crudo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
