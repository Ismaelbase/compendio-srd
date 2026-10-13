# -*- coding: utf-8 -*-
"""Saca los 15 estados del glosario de reglas de los cinco SRD 5.2.1 y los empareja.

Cada estado es una entrada del glosario con su etiqueta ("Agarrado [estado]", "Grappled [Condition]",
"Gepackt (Zustand)", "Agrippé [État]", "Afferrato [condizione]"). El cuerpo se lee como el de un conjuro.
Espanol, ingles y aleman se emparejan por el glosario de T-0107; frances e italiano, por parecido del nombre
con el espanol y forma del texto (son 15 y se revisan a ojo en la salida).

Uso: py -3.14 estados.py   (deja datos\\estados.json)
"""
import csv
import json
import os
import re
import sys
from difflib import SequenceMatcher

from casa import aplicar_casa
from conjuros import cuerpo
from emparejar import GLOSARIO, slug
from emparejar_objetos import _norm
from srd import LANGS, en_paginas, limpia, rango

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
ETIQUETA = {"es": r"\s*\[estado\]$", "en": r"\s*\[Condition\]$", "de": r"\s*\(Zustand\)$", "fr": r"\s*\[État\]$",
            "it": r"\s*\[condizione\]$"}


def estados(lang):
    p0, p1 = rango(lang, "glosario")
    rows = en_paginas(lang, p0, p1)
    out, cur = [], None
    for r in rows:
        titulo = r["font"].startswith("GillSans-SemiBold") and r["size"] >= 12
        if titulo:
            if cur:
                out.append(cur)
                cur = None
            t = limpia(r["t"])
            if re.search(ETIQUETA[lang], t, re.I):
                cur = {"nombre": re.sub(ETIQUETA[lang], "", t, flags=re.I).strip(), "p": r["p"], "filas": []}
            continue
        if cur is not None:
            cur["filas"].append(r)
    if cur:
        out.append(cur)
    return [{"nombre": e["nombre"], "p": e["p"], "bloques": cuerpo(lang, e["filas"])} for e in out]


def main():
    datos = {l: estados(l) for l in LANGS}
    for l in LANGS:
        print(l, len(datos[l]), [e["nombre"] for e in datos[l]])
    g = [r for r in csv.DictReader(open(GLOSARIO, encoding="utf-8-sig"), delimiter=";") if r["categoria"] == "Estados"]
    idx = {l: {e["nombre"]: e for e in datos[l]} for l in LANGS}
    problemas, salida = [], []
    for row in g:
        rec = {"id": slug(row["ingles"])}
        for l, c in (("en", "ingles"), ("es", "espanol"), ("de", "aleman")):
            e = idx[l].get(row[c])
            if e is None:
                problemas.append(f"{l}: '{row[c]}' del glosario no esta en el SRD")
            rec[l] = e
        salida.append(rec)
    from scipy.optimize import linear_sum_assignment
    # frances e italiano: cada estado ingles va con el que aparece a la vez en las inmunidades de las mismas
    # criaturas (330 fichas ya emparejadas); el parecido del nombre con el espanol solo desempata
    criaturas = json.load(open(os.path.join(DATOS, "criaturas.json"), encoding="utf-8"))
    for l in ("fr", "it"):
        nombres_l = [e["nombre"] for e in datos[l]]
        cuenta = [[0] * len(nombres_l) for _ in salida]
        for c in criaturas:
            inm_en = c["en"]["campos"].get("inm", "").lower()
            inm_l = c[l]["campos"].get("inm", "").lower()
            for a, r in enumerate(salida):
                if re.search(r"\b" + re.escape(r["en"]["nombre"].lower()) + r"\b", inm_en):
                    for b, n in enumerate(nombres_l):
                        if re.search(r"(?<!\w)" + re.escape(n.lower()), inm_l):
                            cuenta[a][b] += 1
        coste = [[-(cuenta[a][b] / max(1, max(cuenta[a])) + 0.1 * SequenceMatcher(
            None, _norm(salida[a]["es"]["nombre"]), _norm(nombres_l[b])).ratio()) for b in range(len(nombres_l))]
            for a in range(len(salida))]
        filas, cols = linear_sum_assignment(coste)
        for f, c in zip(filas, cols):
            salida[f][l] = datos[l][c]
            mismo = SequenceMatcher(None, _norm(nombres_l[c]), _norm(salida[f]["en"]["nombre"])).ratio() > 0.8
            if cuenta[f][c] == 0 and not mismo:  # Invisible/Invisibile: el mismo nombre
                problemas.append(f"{l}: {nombres_l[c]} = {salida[f]['en']['nombre']} sin inmunidades que lo confirmen")
    for r in salida:
        print("  ", " | ".join(r[l]["nombre"] for l in LANGS))
    print("normas de casa:", aplicar_casa(salida))
    with open(os.path.join(DATOS, "estados.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print(f"{len(salida)} estados -> datos\\estados.json; {len(problemas)} problemas", problemas)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
