# -*- coding: utf-8 -*-
"""Empaqueta los datos para el plugin: un fichero comprimido comun y uno por idioma, en datos\\plugin\\.

    comun.json.gz   {"version", "entradas": [{"k": clase, "id", "c": datos comunes del ingles}, ...]}
    <idioma>.json.gz {"entradas": {"<clase>/<id>": {...}}, "correcciones": [...], "atribucion": "...",
                      "nombres": {"capitulos", "escuelas", "rarezas", "categorias"}}

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
import re
import sys

from srd import CAP, LANGS, en_paginas, une

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


def tabla(entrada, titulo_en, en):
    """La tabla de una nota que en ingles tiene ese titulo (las tablas van en el mismo orden en los cinco idiomas)."""
    tablas_en = [b for b in en["bloques"] if b["t"] == "tabla"]
    j = next(i for i, b in enumerate(tablas_en) if b.get("titulo") == titulo_en)
    return [b for b in entrada["bloques"] if b["t"] == "tabla"][j]


def sin_marcas(t):
    return re.sub(r"<[^>]+>", "", t).replace(" ", " ").strip()


def nombres(lang, entradas, entradas_en, comun):
    """Lo que el plugin escribe en las propiedades y en los indices, con las palabras del SRD de cada idioma:
    titulos de capitulo, escuelas de magia, rarezas y categorias de objeto (clave: el valor ingles de los datos
    comunes)."""
    out = {"capitulos": {}, "escuelas": {}, "rarezas": {}, "categorias": {}}
    # titulos de capitulo: la linea mas grande de su primera pagina (26 pt, 23 en los primeros del aleman)
    for cap, p in CAP[lang].items():
        if cap == "fin":
            continue
        ls = en_paginas(lang, p, p)
        mayor = max(r["size"] for r in ls)
        assert mayor >= 22.5, (lang, cap, mayor)
        out["capitulos"][cap] = une([r["t"] for r in ls if abs(r["size"] - mayor) < 0.1]).replace(" ", " ")
    # escuelas: la tabla "Schools of Magic", casada por el nombre que sale en la cabecera de cada conjuro
    t = tabla(entradas["regla/casting-spells"], "Schools of Magic", entradas_en["regla/casting-spells"])
    locales = [sin_marcas(f[0]) for f in t["filas"][1:]]
    por_escuela = {}
    for c in comun:
        if c["k"] == "conjuro":
            por_escuela.setdefault(c["c"]["escuela"], []).append(entradas[f"conjuro/{c['id']}"]["cabecera"].lower())
    for esc, cabs in por_escuela.items():
        casan = [n for n in locales if all(re.sub(r"s?magie$", "", n).lower() in cab for cab in cabs)]
        assert len(casan) == 1, (lang, esc, casan)
        out["escuelas"][esc] = casan[0]
    # rarezas: la tabla "Magic Item Rarities and Values", en el mismo orden en todos
    t = tabla(entradas["regla/magic-item-rarity"], "Magic Item Rarities and Values",
              entradas_en["regla/magic-item-rarity"])
    t_en = tabla(entradas_en["regla/magic-item-rarity"], "Magic Item Rarities and Values",
                 entradas_en["regla/magic-item-rarity"])
    for f_en, f in zip(t_en["filas"][1:], t["filas"][1:]):
        out["rarezas"][sin_marcas(f_en[0])] = sin_marcas(f[0])
    # categorias de objeto: el principio de la cabecera que mas se repite en esa categoria
    por_cat = {}
    for c in comun:
        if c["k"] == "objeto":
            cab = entradas[f"objeto/{c['id']}"]["cabecera"]
            por_cat.setdefault(c["c"]["categoria"], []).append(re.split(r" \(|,", cab)[0].strip())
    for cat, inicios in por_cat.items():
        nombre, veces = max(((n, inicios.count(n)) for n in set(inicios)), key=lambda x: x[1])
        assert veces * 2 > len(inicios), (lang, cat, inicios)
        out["categorias"][cat] = nombre
    return out


def solo_bmp(obj, donde):
    """El plugin aplica los cambios de los pies por posicion: JavaScript cuenta en UTF-16 y Python en caracteres,
    que solo coinciden si no hay nada fuera del plano basico."""
    texto = json.dumps(obj, ensure_ascii=False)
    fuera = sorted({c for c in texto if ord(c) > 0xFFFF})
    assert not fuera, (donde, fuera)


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
    atrib = json.load(open(os.path.join(DATOS, "atribucion.json"), encoding="utf-8"))
    for l in LANGS:
        por_idioma[l]["atribucion"] = atrib[l]
        por_idioma[l]["nombres"] = nombres(l, por_idioma[l]["entradas"], por_idioma["en"]["entradas"],
                                           comun["entradas"])
        solo_bmp(por_idioma[l], l)
        print(l, json.dumps(por_idioma[l]["nombres"], ensure_ascii=False))
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
