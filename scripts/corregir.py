# -*- coding: utf-8 -*-
"""Aplica las erratas de traduccion revisadas a mano (datos\\correcciones_*.json).

Cada correccion dice id, idioma, antes, despues y por que. 'antes' tiene que salir una sola vez entre todos los
textos de esa entrada en ese idioma; si no sale o sale mas de una vez, es un error y no se toca nada.
La entrada guarda la lista de lo cambiado en "correcciones", para el credito de cambios que pide la CC-BY.
"""
import json
import os

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
        sitios = [(o, k) for o, k in _textos(r[c["idioma"]]) if c["antes"] in o[k]]
        veces = sum(o[k].count(c["antes"]) for o, k in sitios)
        if veces != 1:
            errores.append(f"{c['id']} ({c['idioma']}): '{c['antes']}' sale {veces} veces")
            continue
        o, k = sitios[0]
        o[k] = o[k].replace(c["antes"], c["despues"])
        r.setdefault("correcciones", []).append({k2: c[k2] for k2 in ("idioma", "antes", "despues", "por_que")})
    return errores
