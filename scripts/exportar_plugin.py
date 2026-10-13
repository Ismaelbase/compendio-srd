# -*- coding: utf-8 -*-
"""Empaqueta los datos para el plugin: un fichero comprimido comun y uno por idioma, en datos\\plugin\\.

    comun.json.gz   {"version", "entradas": [{"k": clase, "id", "c": datos comunes del ingles}, ...]}
    <idioma>.json.gz {"entradas": {"<clase>/<id>": {...}}, "correcciones": [...]}

En cada idioma, la entrada es la de los datos sin "p" (pagina) ni "lead", y su version en pies va como cambios sobre
el texto en metros ("pies": {ruta: [[desde, hasta, texto nuevo], ...]}), que pesan mucho menos que el texto entero.
Los gzip se escriben sin fecha para que no cambien si los datos no cambian.

Uso: py -3.14 exportar_plugin.py
"""
import difflib
import gzip
import io
import json
import os
import sys

from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
SALIDA = os.path.join(DATOS, "plugin")
VERSION_DATOS = 1

# fichero -> clase de cada registro (los de reglas, personajes y equipo la llevan en "tipo")
FICHEROS = {"criaturas": "criatura", "conjuros": "conjuro", "objetos": "objeto", "estados": "estado",
            "reglas": None, "personajes": None, "equipo": None}
FUERA = {"p", "lead", "grupo_es"}


def limpiar(o):
    if isinstance(o, dict):
        return {k: limpiar(v) for k, v in o.items() if k not in FUERA}
    if isinstance(o, list):
        return [limpiar(v) for v in o]
    return o


def resolver(x, ruta):
    o = x
    for p in ruta.split("."):
        o = o[int(p)] if isinstance(o, list) else o[p]
    return o


def cambios(a, b):
    """[[desde, hasta, texto]] que convierten a en b (por palabras, para que los cambios sean legibles)."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if out and out[-1][1] == i1:
            out[-1][1] = i2
            out[-1][2] += b[j1:j2]
        else:
            out.append([i1, i2, b[j1:j2]])
    # comprobacion: aplicar los cambios da b
    r = a
    for i1, i2, t in reversed(out):
        r = r[:i1] + t + r[i2:]
    assert r == b, (a, b)
    return out


def gz(obj, ruta):
    crudo = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, compresslevel=9) as f:
        f.write(crudo)
    with open(ruta, "wb") as f:
        f.write(buf.getvalue())
    return len(crudo), len(buf.getvalue())


def main():
    os.makedirs(SALIDA, exist_ok=True)
    comun = {"version": VERSION_DATOS, "entradas": []}
    por_idioma = {l: {"entradas": {}, "correcciones": []} for l in LANGS}
    claves = set()
    for f, clase_fija in FICHEROS.items():
        for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8")):
            clase = clase_fija or r["tipo"]
            clave = f"{clase}/{r['id']}"
            assert clave not in claves, clave
            claves.add(clave)
            e = {"k": clase, "id": r["id"]}
            if r.get("comun"):
                e["c"] = r["comun"]
            if r.get("cap"):
                e["cap"] = r["cap"]
            comun["entradas"].append(e)
            for l in LANGS:
                x = r.get(l)
                if x is None:
                    continue
                y = limpiar({k: v for k, v in x.items() if k != "pies"})
                pies = {}
                for ruta, texto in (x.get("pies") or {}).items():
                    pies[ruta] = cambios(resolver(x, ruta), texto)
                if pies:
                    y["pies"] = pies
                por_idioma[l]["entradas"][clave] = y
            for c in r.get("correcciones", []):
                por_idioma[c["idioma"]]["correcciones"].append(
                    {"clave": clave, "antes": c.get("antes", ""), "despues": c.get("despues", ""),
                     "por_que": c.get("por_que", "")})
    total_c, total_z = gz(comun, os.path.join(SALIDA, "comun.json.gz"))
    print(f"comun: {len(comun['entradas'])} entradas, {total_c / 1e6:.2f} MB -> {total_z / 1e6:.2f} MB")
    for l, d in por_idioma.items():
        c, z = gz(d, os.path.join(SALIDA, f"{l}.json.gz"))
        total_c += c
        total_z += z
        print(f"{l}: {len(d['entradas'])} entradas, {len(d['correcciones'])} erratas, {c / 1e6:.2f} MB -> {z / 1e6:.2f} MB")
    print(f"total {total_c / 1e6:.2f} MB -> {total_z / 1e6:.2f} MB comprimido, {total_z * 4 / 3 / 1e6:.2f} MB en base64")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
