# -*- coding: utf-8 -*-
"""Trae las erratas de traduccion de los conjuros que ya se encontraron para las cartas de hechizos (T-0108).

Las cartas compararon los 339 conjuros del SRD en espanol, ingles y aleman con revisores y verificadores aparte
(29/09/2026). De sus listas se traen solo las que corrigen el SRD: mecanica, errata, unidad, falta, area,
salvacion, termino, coherencia y formato. No se traen las de redaccion propia de las cartas ("redaccion",
"propio"), que adaptan el texto a la carta.

Dos ajustes: las cartas llevan el espanol en pies (aqui va en metros, como el SRD) y usan los nombres de 5etools
como id (aqui, el nombre del SRD ingles). Cada errata se comprueba contra el texto de este proyecto: tiene que
salir una sola vez; las que no casan se listan para mirarlas a mano.

Uso: py -3.14 importar_erratas_cartas.py   (escribe datos\\correcciones_conjuros.json)
"""
import json
import os
import re
import sys

from corregir import sitios_de
from emparejar import slug

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
CARTAS = os.environ.get("CARTAS_DIR", r"G:\General\The Obsidian Die\Cartas\Cartas Hechizos Tarot\datos")
TIPOS = {"mecanica", "errata", "unidad", "falta", "area", "salvacion", "termino", "coherencia", "formato"}

# pies -> metros del SRD espanol (la tabla de las cartas, al reves; sale de emparejar las medidas con el ingles)
PIES = {"5 pies": "1,5 m", "10 pies": "3 m", "15 pies": "4,5 m", "20 pies": "6 m", "25 pies": "7,5 m",
        "30 pies": "9 m", "40 pies": "12 m", "45 pies": "13,5 m", "50 pies": "15 m", "60 pies": "18 m",
        "90 pies": "27 m", "100 pies": "30 m", "120 pies": "36 m", "150 pies": "45 m", "200 pies": "60 m",
        "300 pies": "90 m", "500 pies": "150 m", "1000 pies": "300 m", "1 milla": "1,5 km"}


def a_metros(t):
    for a, b in sorted(PIES.items(), key=lambda x: -len(x[0])):
        t = re.sub(r"(?<![\d,])" + re.escape(a) + r"\b", b, t)
    return t


def main():
    import emparejar_conjuros
    nuestros = {r["id"]: r for r in emparejar_conjuros.construir()[0]}  # texto sin erratas
    base = json.load(open(os.path.join(CARTAS, "conjuros.json"), encoding="utf-8"))
    id_cartas = {}
    for c in base:
        if c.get("srd"):
            id_cartas[c["id"]] = slug(c.get("nombre_srd_en") or c["en"]["nombre"])
    lista = []
    for f in ("correcciones_2_mecanica.json", "correcciones_3_final.json"):
        lista += [dict(x, _fichero=f) for x in json.load(open(os.path.join(CARTAS, f), encoding="utf-8"))]
    salida, fuera, no_casan, repetidas = [], 0, [], 0
    for x in lista:
        if x.get("tipo") not in TIPOS:
            continue
        nid = id_cartas.get(x["id"])
        if nid is None:
            fuera += 1  # conjuro que no esta en el SRD (de los 52 propios de las cartas)
            continue
        antes, despues = x["actual"], x["propuesta"]
        if x["idioma"] == "es":
            antes, despues = a_metros(antes), a_metros(despues)
        r = nuestros.get(nid)
        if r is None:
            no_casan.append((x, "id sin conjuro"))
            continue
        # se comprueba sobre el texto con las erratas anteriores ya puestas (algunas van encadenadas); si sale mas
        # de una vez, se mira solo en el bloque que dicen las cartas
        donde = None
        sitios, veces = sitios_de(r[x["idioma"]], antes)
        if veces > 1 and x.get("donde"):
            donde = x["donde"]
            sitios, veces = sitios_de(r[x["idioma"]], antes, donde)
        if veces == 0 and despues and sitios_de(r[x["idioma"]], despues)[1]:
            repetidas += 1  # la misma errata dos veces en las listas de las cartas: ya esta puesta
            continue
        if veces != 1:
            no_casan.append((x, f"sale {veces} veces", antes))
            continue
        o, k = sitios[0]
        o[k] = o[k].replace(antes, despues)
        salida.append({"id": nid, "idioma": x["idioma"], "antes": antes, "despues": despues, **({"donde": donde} if donde else {}),
                       "por_que": (x.get("que_cambia_en_mesa") or x.get("por_que") or "").strip(),
                       "tipo": x["tipo"], "origen": f"T-0108 {x['_fichero']}"})
    with open(os.path.join(DATOS, "correcciones_conjuros.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_que_es": "Erratas de traduccion de los conjuros, traidas de las cartas de hechizos (T-0108) "
                              "por importar_erratas_cartas.py. Manda el ingles (decision 34 de T-0111).",
                   "correcciones": salida}, f, ensure_ascii=False, indent=1)
    print(f"{len(salida)} erratas traidas; {fuera} de conjuros fuera del SRD; {repetidas} repetidas; "
          f"{len(no_casan)} no casan:")
    for n in no_casan:
        x = n[0]
        print(f"   {x['idioma']} {x['id']} [{x['tipo']}] {n[1]}: {n[-1] if len(n) > 2 else x['actual']!r}"[:220])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
