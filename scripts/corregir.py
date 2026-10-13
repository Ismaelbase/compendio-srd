# -*- coding: utf-8 -*-
"""Aplica las erratas de traduccion revisadas a mano (datos\\correcciones_*.json).

Cada correccion dice id, idioma, antes, despues y por que. 'antes' tiene que salir una sola vez entre todos los
textos de esa entrada en ese idioma; si no sale o sale mas de una vez, es un error y no se toca nada.
La entrada guarda la lista de lo cambiado en "correcciones", para el credito de cambios que pide la CC-BY.
"""
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def _textos(x):
    """Rutas (contenedor, clave) de todos los textos de una entrada de un idioma."""
    out = []

    def rec(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str):
                    out.append((o, k))
                else:
                    rec(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str):
                    out.append((o, i))
                else:
                    rec(v)
    rec(x)
    return out


def resolver(x, donde):
    """'bloques[3].txt' -> (contenedor, clave) dentro de la entrada x, o None."""
    o = x
    partes = re.findall(r"([^.\[\]]+)|\[(\d+)\]", donde)
    pasos = [int(i) if i else n for n, i in partes]
    try:
        for p in pasos[:-1]:
            o = o[p]
        o[pasos[-1]]
    except (KeyError, IndexError, TypeError):
        return None
    return o, pasos[-1]


def sitios_de(x, antes, donde=None):
    """Sitios donde sale 'antes' (solo en 'donde' si se da) y cuantas veces en total."""
    if donde:
        r = resolver(x, donde)
        candidatos = [r] if r else []
    else:
        candidatos = list(_textos(x))
    sitios = [(o, k) for o, k in candidatos if isinstance(o[k], str) and antes in o[k]]
    return sitios, sum(o[k].count(antes) for o, k in sitios)


def aplicar(registros, fichero):
    ruta = os.path.join(DATOS, fichero)
    if not os.path.exists(ruta):
        return []
    lista = json.load(open(ruta, encoding="utf-8"))["correcciones"]
    por_id = {r["id"]: r for r in registros}
    errores = []
    for c in lista:
        r = por_id.get(c["id"])
        if r is None or c["idioma"] not in r:
            errores.append(f"{c['id']} ({c['idioma']}): no existe")
            continue
        if "insertar" in c:
            # parrafo que falta en una traduccion: va detras del bloque que empieza por 'tras'
            bl = r[c["idioma"]]["bloques"]
            k = next((i for i, b in enumerate(bl) if b.get("txt", "").startswith(c["tras"])), None)
            if k is None:
                errores.append(f"{c['id']} ({c['idioma']}): no esta el bloque '{c['tras'][:40]}'")
                continue
            bl.insert(k + 1, c["insertar"])
            r.setdefault("correcciones", []).append({"idioma": c["idioma"], "antes": "",
                                                     "despues": c["insertar"]["txt"], "por_que": c["por_que"]})
            continue
        sitios, veces = sitios_de(r[c["idioma"]], c["antes"], c.get("donde"))
        if veces != 1:
            errores.append(f"{c['id']} ({c['idioma']}): '{c['antes']}' sale {veces} veces")
            continue
        o, k = sitios[0]
        o[k] = o[k].replace(c["antes"], c["despues"])
        r.setdefault("correcciones", []).append({k2: c[k2] for k2 in ("idioma", "antes", "despues", "por_que")})
    return errores
