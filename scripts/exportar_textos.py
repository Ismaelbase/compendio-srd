# -*- coding: utf-8 -*-
"""Vuelca a texto plano todo lo que es texto del SRD, un fichero por idioma, para pasarle revisar_estilo.py.

Cada linea es un texto sin marcas; el fichero .mapa.json dice de que entrada y campo sale cada linea. Uso:
    py -3.14 exportar_textos.py <criaturas|conjuros|objetos> <carpeta de salida>
"""
import json
import os
import sys

from marcas import sin_marcas
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def lineas_criatura(r, l):
    x = r[l]
    yield "nombre", x["nombre"]
    yield "tipo", x["tipo"]
    for k, v in x["campos"].items():
        yield k, v
    for s in x["secciones"]:
        yield s["clave"], s["titulo"]
        if s["intro"]:
            yield s["clave"] + "/intro", s["intro"]
        for it in s["items"]:
            yield s["clave"] + "/" + it["nombre"], it["nombre"]
            for b in it["bloques"]:
                yield s["clave"] + "/" + it["nombre"], b["txt"]


def lineas_bloques(bloques, donde="bloques"):
    for k, b in enumerate(bloques):
        if b["t"] in ("p", "li", "nota"):
            yield f"{donde}[{k}]", b["txt"]
        elif b["t"] == "tabla":
            if b.get("titulo"):
                yield f"{donde}[{k}].titulo", b["titulo"]
            for fila in b["filas"]:
                for celda in fila:
                    yield f"{donde}[{k}].celda", celda
        elif b["t"] == "ficha":
            yield f"{donde}[{k}].nombre", b["nombre"]
            yield f"{donde}[{k}].tipo", b["tipo"]
            for c in ("ca", "pg", "vel"):
                if b.get(c):
                    yield f"{donde}[{k}].{c}", b[c]
            for rot, v in b.get("rasgos", []):
                yield f"{donde}[{k}].rasgo", f"{rot}: {v}"
            for s in b.get("secciones", []):
                yield f"{donde}[{k}].seccion", s["titulo"]
                for n, t in s["items"]:
                    yield f"{donde}[{k}].item", f"{n}. {t}"


def lineas_conjuro(r, l):
    x = r[l]
    for c in ("nombre", "cabecera", "tiempo", "alcance", "comp", "dur"):
        yield c, x[c]
    yield from lineas_bloques(x["bloques"])


def lineas_objeto(r, l):
    x = r[l]
    yield "nombre", x["nombre"]
    yield "cabecera", x["cabecera"]
    yield from lineas_bloques(x["bloques"])


def lineas_estado(r, l):
    yield "nombre", r[l]["nombre"]
    yield from lineas_bloques(r[l]["bloques"])


GENERADORES = {"criaturas": lineas_criatura, "conjuros": lineas_conjuro, "objetos": lineas_objeto,
               "estados": lineas_estado}


def main():
    tipo, salida = sys.argv[1], sys.argv[2]
    os.makedirs(salida, exist_ok=True)
    datos = json.load(open(os.path.join(DATOS, f"{tipo}.json"), encoding="utf-8"))
    gen = GENERADORES[tipo]
    for l in LANGS:
        ruta = os.path.join(salida, f"{tipo}_{l}.txt")
        mapa = []
        with open(ruta, "w", encoding="utf-8") as f:
            for r in datos:
                if l in r:
                    for donde, t in gen(r, l):
                        f.write(sin_marcas(t).replace("\n", " ") + "\n")
                        mapa.append([r["id"], donde])
        with open(ruta[:-4] + ".mapa.json", "w", encoding="utf-8") as f:
            json.dump(mapa, f, ensure_ascii=False)
        print(ruta)


if __name__ == "__main__":
    main()
