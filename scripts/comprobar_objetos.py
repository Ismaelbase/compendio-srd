# -*- coding: utf-8 -*-
"""Comprueba datos\\objetos.json entre idiomas.

1. Recuento: 258 objetos en cada idioma, los del glosario de T-0107 (ES, EN, DE).
2. Cabecera: la misma rareza y la misma sintonizacion que el ingles.
3. Cifras: las de cada objeto entero frente al ingles (medidas pasadas a metros). Se compara el objeto entero y
   no bloque a bloque porque cada SRD parte las tablas y ordena las listas a su manera (las cartas de las
   barajas, las figuritas). Si las otras traducciones dan las mismas cifras, es la conversion de unidades que
   usan todas y no se avisa.

Uso: py -3.14 comprobar_objetos.py [--json F]. Las revisadas a mano que no son errata, en
datos\\revisados_objetos.json.
"""
import collections
import json
import os
import sys

from cifras import cifras, cifras_en
from emparejar_objetos import SINTONIA, rarezas, texto_objeto
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def main():
    salida_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    datos = json.load(open(os.path.join(DATOS, "objetos.json"), encoding="utf-8"))
    errores, avisos, info = [], [], []
    for l in LANGS:
        n = sum(1 for r in datos if l in r)
        if n != 258:
            errores.append(f"{l}: {n} objetos (tienen que ser 258)")
    for r in datos:
        e = r["en"]
        for l in LANGS:
            x = r.get(l)
            if x is None:
                errores.append(f"{r['id']}: falta {l}")
                continue
            if not x["bloques"]:
                errores.append(f"{l}: {x['nombre']}: sin texto")
            if rarezas(x["cabecera"], l) != rarezas(e["cabecera"], "en"):
                errores.append(f"{l}: {x['nombre']}: rareza distinta del ingles: {x['cabecera']}")
            if (SINTONIA[l] in x["cabecera"].lower()) != (SINTONIA["en"] in e["cabecera"].lower()):
                errores.append(f"{l}: {x['nombre']}: sintonizacion distinta del ingles: {x['cabecera']}")
            if l == "en":
                continue
            if collections.Counter(b["t"] for b in x["bloques"]) != collections.Counter(b["t"] for b in e["bloques"]):
                info.append(f"{l}: {x['nombre']}: bloques {[b['t'] for b in x['bloques']]} frente a "
                            f"{[b['t'] for b in e['bloques']]}")
            te = e["cabecera"] + " " + texto_objeto(e)
            tx = x["cabecera"] + " " + texto_objeto(x)
            ce, cx = cifras_en(te), cifras(tx, l)
            if ce == cx:
                continue
            otras = [cifras(r[o]["cabecera"] + " " + texto_objeto(r[o]), o) for o in LANGS if o not in ("en", l)]
            if sum(1 for c in otras if c == cx) >= 2:
                continue
            avisos.append({"id": r["id"], "idioma": l, "objeto": x["nombre"], "donde": "objeto",
                           "solo_en_ingles": dict(ce - cx), "solo_en_este": dict(cx - ce),
                           "texto": tx, "texto_en": te})
    ruta_rev = os.path.join(DATOS, "revisados_objetos.json")
    rev = json.load(open(ruta_rev, encoding="utf-8"))["revisados"] if os.path.exists(ruta_rev) else []
    claves = {(x["id"], x["idioma"]) for x in rev}
    usados = {(a["id"], a["idioma"]) for a in avisos} & claves
    for x in sorted(claves - usados):
        errores.append(f"revisado que ya no sale: {x}")
    revisados = [a for a in avisos if (a["id"], a["idioma"]) in claves]
    avisos = [a for a in avisos if (a["id"], a["idioma"]) not in claves]
    print(f"{len(errores)} errores; {len(avisos)} avisos de cifras sin revisar "
          f"{dict(collections.Counter(a['idioma'] for a in avisos))}; {len(revisados)} revisados sin errata; "
          f"{len(info)} objetos con los bloques en otro orden o partidos de otra manera (informativo)")
    for x in errores[:40]:
        print("  ERROR", x)
    if salida_json:
        with open(salida_json, "w", encoding="utf-8") as f:
            json.dump({"errores": errores, "avisos": avisos, "info": info}, f, ensure_ascii=False, indent=1)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
