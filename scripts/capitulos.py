# -*- coding: utf-8 -*-
"""Corta los capitulos de reglas del SRD 5.2.1 en notas, en los cinco idiomas.

Lee los bloques de documento.py y los parte por sus titulos. Las cinco ediciones tienen los mismos titulos en el
mismo sitio (comprobado capitulo a capitulo: mismo numero de titulos de 18, 14 y 12 pt bajo cada uno), asi que cada
nota lleva una clave de posicion que vale para todos los idiomas. Donde cada idioma ordena por su alfabeto (las
clases, las entradas del glosario, el equipo, las herramientas, las dotes de cada categoria, las especies, los
trasfondos, los venenos y las trampas) la clave es solo el grupo, y emparejar_reglas.py casa las notas del grupo
por su contenido.

Tipos de nota:
    regla       una seccion de 18 pt de un capitulo de reglas (como jugar, creacion de personajes, equipo, la
                introduccion de los conjuros, de los objetos magicos y de los monstruos, herramientas del juego)
    glosario    una entrada del glosario de reglas (sin los estados, que ya estan en estados.json)
    clase, subclase, especie, trasfondo, dote, herramienta, equipo, veneno, trampa

Cada nota: {"cap", "clave", "grupo", "tipo", "nombre", "p", "bloques", ...}. Los titulos de dentro de la nota van
como bloques {"t": "h", "n": 1, 2...} contados desde la nota (1 = el nivel de debajo del suyo).

Uso: py -3.14 capitulos.py   (deja datos\\_reglas_crudo.json)
"""
import json
import os
import re
import sys

from documento import capitulo, limpia
from srd import CAP, LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

# Etiqueta de los estados en el glosario: esas entradas no se repiten (estan en estados.json)
ESTADO = {"es": "estado", "en": "Condition", "de": "Zustand", "fr": "État", "it": "condizione"}
# Primera celda de la cabecera de la tabla de rasgos de cada clase
NIVEL = {"es": "Nivel", "en": "Level", "de": "Stufe", "fr": "Niveau", "it": "Livello"}


def arbol(bloques):
    """Arbol de titulos: {"h": bloque de titulo o None, "n", "bloques": contenido hasta el primer hijo, "hijos"}."""
    raiz = {"h": None, "n": -1, "bloques": [], "hijos": []}
    pila = [raiz]
    for b in bloques:
        if b["t"] == "h":
            while pila[-1]["n"] >= b["n"]:
                pila.pop()
            nodo = {"h": b, "n": b["n"], "bloques": [], "hijos": []}
            pila[-1]["hijos"].append(nodo)
            pila.append(nodo)
        else:
            pila[-1]["bloques"].append(b)
    return raiz


def aplanar(nodo, base, fuera=()):
    """Contenido de un nodo y sus hijos (salvo los de 'fuera'), con los titulos de los hijos contados desde base."""
    out = list(nodo["bloques"])
    for h in nodo["hijos"]:
        if any(h is f for f in fuera):
            continue
        out.append({"t": "h", "n": h["n"] - base, "txt": h["h"]["txt"], "p": h["h"]["p"]})
        out.extend(aplanar(h, base, fuera))
    return out


def nota(cap, clave, tipo, nodo, grupo=None, fuera=(), **extra):
    return dict({"cap": cap, "clave": clave, "grupo": grupo, "tipo": tipo, "nombre": nodo["h"]["txt"],
                 "p": nodo["h"]["p"], "bloques": aplanar(nodo, nodo["n"], fuera)}, **extra)


def h1s(lang, cap, p0=None, p1=None, hasta=None):
    """Nodos de 18 pt del capitulo (los 'hasta' primeros si se dice: la introduccion de los conjuros y de los
    objetos magicos acaba donde empiezan las entradas)."""
    bl = capitulo(lang, cap, p0, p1)
    if hasta is not None:
        k = [i for i, b in enumerate(bl) if b["t"] == "h" and b["n"] == 1]
        if len(k) <= hasta:
            raise SystemExit(f"{lang} {cap}: no hay {hasta + 1} titulos de 18 pt")
        bl = bl[:k[hasta]]
    raiz = arbol(bl)
    cap0 = raiz["hijos"][0] if raiz["hijos"] and raiz["hijos"][0]["n"] == 0 else raiz
    return [h for h in cap0["hijos"] if h["n"] == 1], cap0


def recolocar_tabla_de_clase(lang, bl):
    """La tabla de rasgos de una clase sale a veces antes del titulo de la clase (la maqueta la pone al pie de la
    pagina en que empieza la clase, debajo de la subclase anterior): se lleva detras del titulo y de la tabla de
    atributos basicos de su clase."""
    k = 0
    while k < len(bl):
        b = bl[k]
        if b["t"] == "h" and b["n"] == 1:
            j = k - 1
            while j >= 0 and bl[j]["t"] in ("tabla", "recuadro", "nota") and bl[j].get("p") == b["p"]:
                j -= 1
            movibles = [x for x in bl[j + 1:k] if x["t"] == "tabla" and x["filas"] and
                        limpia(x["filas"][0][0]) == NIVEL[lang]]
            if movibles:
                for x in movibles:
                    bl.remove(x)
                k = bl.index(b)
                destino = k + 1
                if destino < len(bl) and bl[destino]["t"] == "tabla" and bl[destino].get("vertical"):
                    destino += 1
                for x in reversed(movibles):
                    bl.insert(destino, x)
        k += 1
    return bl


def tablas_de_clase_arriba(lang, n):
    """La tabla de atributos basicos y la de rasgos de la clase van al principio de su nota (cada maqueta las deja
    caer en un apartado distinto)."""
    bl = n["bloques"]
    basicos = next((b for b in bl if b["t"] == "tabla" and b.get("vertical")), None)
    rasgos = next((b for b in bl if b["t"] == "tabla" and b["filas"] and limpia(b["filas"][0][0]) == NIVEL[lang]
                   and len(b["filas"]) >= 21), None)
    for b in (basicos, rasgos):
        if b is not None:
            bl.remove(b)
    n["bloques"] = [b for b in (basicos, rasgos) if b is not None] + bl
    return n


def clases(lang):
    bl = recolocar_tabla_de_clase(lang, capitulo(lang, "clases"))
    raiz = arbol(bl)
    cap0 = raiz["hijos"][0]
    out = []
    for c in cap0["hijos"]:
        sub = c["hijos"][-1]  # la subclase del SRD es siempre el ultimo apartado de 14 pt de la clase
        out.append(tablas_de_clase_arriba(lang, nota("clases", None, "clase", c, grupo="clases", fuera=[sub])))
        nombre = sub["h"]["txt"]
        out.append(nota("clases", None, "subclase", sub, grupo="subclases",
                        nombre_corto=limpia(nombre.split(":", 1)[1]) if ":" in nombre else nombre,
                        clase=c["h"]["txt"]))
    return out


def con_grupo(cap, clave, h1, k_h2, tipo, grupo):
    """Notas para cada titulo de 12 pt bajo el apartado de 14 pt k_h2 de h1 (lista que cada idioma ordena por
    su alfabeto)."""
    h2 = h1["hijos"][k_h2]
    return [nota(cap, None, tipo, h3, grupo=grupo, categoria=h2["h"]["txt"]) for h3 in h2["hijos"]]


def notas(lang):
    out = []
    # como jugar y creacion de personajes: cada seccion de 18 pt
    for cap in ("juego", "creacion"):
        for k, h in enumerate(h1s(lang, cap)[0]):
            out.append(nota(cap, f"{cap}.{k}", "regla", h))
    # introduccion de los conjuros (antes de "Descripciones de conjuros", la tercera seccion)
    p0 = CAP[lang]["conjuros"]
    for k, h in enumerate(h1s(lang, "conjuros", p0, p0 + 6, hasta=2)[0]):
        out.append(nota("conjuros", f"conjuros.{k}", "regla", h))
    out.extend(clases(lang))
    # origenes: trasfondos y especies (el segundo apartado de cada uno trae las descripciones)
    for k, h in enumerate(h1s(lang, "origenes")[0]):
        desc = h["hijos"][1]
        out.append(nota("origenes", f"origenes.{k}", "regla", h, fuera=desc["hijos"]))
        tipo = ("trasfondo", "especie")[k]
        out.extend(nota("origenes", None, tipo, h3, grupo=tipo) for h3 in desc["hijos"])
    # dotes: el primer apartado explica las partes de una dote y los otros cuatro son categorias
    h = h1s(lang, "dotes")[0][0]
    cats = h["hijos"][1:]
    out.append(nota("dotes", "dotes.0", "regla", h, fuera=[x for c in cats for x in c["hijos"]]))
    for k in range(1, len(h["hijos"])):
        out.extend(con_grupo("dotes", None, h, k, "dote", f"dotes.{k}"))
    # equipo
    hs = h1s(lang, "equipo")[0]
    for k, h in enumerate(hs):
        if k == 3:  # herramientas: de artesano y otras
            fuera = [x for h2 in h["hijos"][1:] for x in h2["hijos"]]
            out.append(nota("equipo", f"equipo.{k}", "regla", h, fuera=fuera))
            for j in (1, 2):
                out.extend(con_grupo("equipo", None, h, j, "herramienta", f"herramientas.{j}"))
        elif k == 4:  # equipo de aventureros
            out.append(nota("equipo", f"equipo.{k}", "regla", h, fuera=h["hijos"]))
            out.extend(nota("equipo", None, "equipo", h3, grupo="equipo") for h3 in h["hijos"])
        else:
            out.append(nota("equipo", f"equipo.{k}", "regla", h))
    # glosario: convenciones (regla) y una nota por entrada, sin los estados
    hs = h1s(lang, "glosario")[0]
    out.append(nota("glosario", "glosario.0", "regla", hs[0]))
    for h3 in hs[1]["hijos"]:
        nombre = h3["h"]["txt"]
        m = re.match(r"(.*?)\s*[\[(]([^\])]+)[\])]\s*$", nombre)
        etiqueta = limpia(m.group(2)) if m else None
        if etiqueta and etiqueta.lower() == ESTADO[lang].lower():
            continue
        out.append(nota("glosario", None, "glosario", h3, grupo="glosario", nombre_corto=limpia(m.group(1)) if m
                        else nombre, etiqueta=etiqueta))
    # herramientas del juego: venenos y trampas de ejemplo como notas aparte
    for k, h in enumerate(h1s(lang, "herramientas")[0]):
        if k == 5:
            out.append(nota("herramientas", f"herramientas.{k}", "regla", h, fuera=h["hijos"][2]["hijos"]))
            out.extend(con_grupo("herramientas", None, h, 2, "veneno", "venenos"))
        elif k == 6:
            out.append(nota("herramientas", f"herramientas.{k}", "regla", h, fuera=h["hijos"][1]["hijos"]))
            out.extend(con_grupo("herramientas", None, h, 1, "trampa", "trampas"))
        else:
            out.append(nota("herramientas", f"herramientas.{k}", "regla", h))
    # introduccion de los objetos magicos (antes de "Objetos magicos de la A a la Z", la novena seccion)
    p0 = CAP[lang]["objetos"]
    for k, h in enumerate(h1s(lang, "objetos", p0, p0 + 8, hasta=8)[0]):
        out.append(nota("objetos", f"objetos.{k}", "regla", h))
    # introduccion de los monstruos: como se lee un perfil
    for k, h in enumerate(h1s(lang, "monstruos")[0]):
        out.append(nota("monstruos", f"monstruos.{k}", "regla", h))
    return out


def _plano(t):
    t = re.sub(r"<[^>]+>", "", t or "").lower()
    return re.sub(r"[\s­]+", " ", t).strip()


def _texto(bl):
    partes = []
    for b in bl:
        if b["t"] in ("p", "li", "formula", "nota"):
            partes.append(b["txt"])
        elif b["t"] == "recuadro":
            partes.append(_texto(b["bloques"]))
        elif b["t"] == "campos":
            partes += [v for _, v in b["filas"]]
    return _plano(" ".join(partes))


def normalizar(ns):
    """Lo que un SRD compone de otra manera que los demas se lleva a la misma forma:
    - las lineas "Activador:" y "Duracion:" de las trampas, que el ingles pone como parrafos con rotulo, son campos;
    - las formulas que el ingles pone en el texto ("<strong>Miles per hour</strong> = Speed ÷ 10 <strong>Miles per
      day</strong> = ..."), una formula por rotulo."""
    for n in ns:
        bl = n["bloques"]
        if n["tipo"] == "trampa":
            k = 1 if bl and bl[0].get("sub") else 0
            filas = []
            while k < len(bl) and bl[k]["t"] == "p" and re.match(r"<b>[^<]+:</b>", bl[k]["txt"]):
                m = re.match(r"<b>([^<]+):</b>\s*(.*)", bl[k]["txt"])
                filas.append([m.group(1).strip(), m.group(2).strip()])
                del bl[k]
            if filas:
                bl.insert(1 if bl and bl[0].get("sub") else 0, {"t": "campos", "filas": filas})
        out = []
        for b in bl:
            partes = re.split(r"(?=<strong>[^<]+</strong>(?:\s*\([^)]*\))?\s*=)", b.get("txt", "")) if b["t"] == "p" else []
            partes = [x.strip() for x in partes if x.strip()]
            if len(partes) >= 2 and all(re.match(r"<strong>[^<]+</strong>", x) for x in partes):
                out.extend({"t": "formula", "txt": re.sub(r"</?strong>", lambda m: m.group(0).replace("strong", "b"), x)}
                           for x in partes)
            else:
                out.append(b)
        n["bloques"] = out


def recolocar_tablas(ns, avisos):
    """Las tablas flotan en la maqueta y pueden caer dentro de la nota de al lado (la tabla de equipo de
    aventureros en la nota de los abrojos; la de legados infernales en la del humano). Una tabla con titulo que su
    nota no cita y que cita una sola nota del mismo capitulo se lleva a esa nota, detras del bloque que la cita."""
    for n in ns:
        for b in list(n["bloques"]):
            if b["t"] != "tabla" or not b.get("titulo"):
                continue
            tit = _plano(b["titulo"])
            if len(tit) < 4 or tit in _texto(n["bloques"]) or tit == _plano(n["nombre"]):
                continue
            citan = [m for m in ns if m is not n and m["cap"] == n["cap"] and tit in _texto(m["bloques"])]
            if len(citan) != 1:
                continue
            m = citan[0]
            n["bloques"].remove(b)
            k = next(i for i, x in enumerate(m["bloques"]) if tit in _texto([x]))
            m["bloques"].insert(k + 1, b)
            avisos.append(f"tabla '{b['titulo']}' de '{n['nombre']}' a '{m['nombre']}'")


def main():
    salida = {}
    for l in LANGS:
        ns = notas(l)
        avisos = []
        recolocar_tablas(ns, avisos)
        normalizar(ns)
        for a in avisos:
            print(f"   {l}: {a}")
        cuenta = {}
        for n in ns:
            cuenta[n["tipo"]] = cuenta.get(n["tipo"], 0) + 1
        raros = sum(1 for n in ns for b in n["bloques"] if b["t"] == "otro")
        print(f"{l}: {len(ns)} notas {cuenta}; bloques sin clasificar {raros}")
        salida[l] = ns
    with open(os.path.join(DATOS, "_reglas_crudo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
