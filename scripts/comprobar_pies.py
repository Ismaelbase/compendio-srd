# -*- coding: utf-8 -*-
"""Prueba de punta a punta de la version en pies: las cifras de cada entrada en pies frente a las del ingles tal
cual, y las mismas en metros frente al ingles pasado a metros. Una entrada que en pies se aleja del ingles mas
que en metros tiene una medida mal pasada.

Uso: py -3.14 comprobar_pies.py   Sale con 1 si alguna entrada empeora.
"""
import collections
import re
import json
import os
import sys

from cifras import cifras, cifras_en
from pies import LANGS_M, recorrer

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def texto(x, pies=False):
    partes = []
    for donde, t in recorrer(x):
        partes.append(x["pies"].get(donde, t) if pies else t)
    return " ".join(partes)


# revisadas a mano el 13/10/2026: en pies dicen lo mismo que el ingles, con una cifra que el ingles pone con letra
# ("je 1 Gallone" por "every gallon", "per ogni piede" por "every 1 foot", "einem halben Zoll" por "1/2 inch")
ACEPTADAS = {("criaturas", "fire-elemental", "de"), ("conjuros", "forcecage", "de"), ("conjuros", "gust-of-wind", "it"),
             ("conjuros", "wall-of-thorns", "it")}


def distancia(a, b):
    return sum((a - b).values()) + sum((b - a).values())


def main():
    peores, total = [], collections.Counter()
    for tipo in ("criaturas", "conjuros", "objetos", "estados"):
        for r in json.load(open(os.path.join(DATOS, f"{tipo}.json"), encoding="utf-8")):
            en = texto(r["en"])
            # el ingles tal cual, con sus millares con coma ("XP 1,800") y "a foot" como 1
            en_crudo = re.sub(r"(\d),(\d{3})", r"\1\2", en)
            en_crudo = re.sub(r"\b(a|an|one) (cubic foot|square foot|foot|inch|mile|pound|gallon|pint)\b", r"1 \2", en_crudo)
            c_en_m, c_en_ft = cifras_en(en), cifras(en_crudo, "en")
            for l in LANGS_M:
                x = r.get(l)
                if not x or not x.get("pies"):
                    continue
                dm = distancia(cifras(texto(x), l), c_en_m)
                dp = distancia(cifras(texto(x, pies=True), l), c_en_ft)
                total[(tipo, l, "igual" if dp == dm else ("mejor" if dp < dm else "PEOR"))] += 1
                if dp > dm and (tipo, r["id"], l) not in ACEPTADAS:
                    peores.append((tipo, r["id"], l, dm, dp))
    for k, v in sorted(total.items()):
        print(k, v)
    for p in peores[:40]:
        print("  PEOR en pies:", p)
    return 1 if peores else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
