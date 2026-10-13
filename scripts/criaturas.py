# -*- coding: utf-8 -*-
"""Saca las fichas de criatura de los cinco SRD 5.2.1 (capitulos "Monstruos de la A a la Z" y "Animales").

Cada ficha sale con su estructura completa:
    nombre, pagina, grupo (titulo de 18 pt que la agrupa), tipo (linea en cursiva),
    campos: ca, ini, pg, vel, hab, res, vul, inm, equipo, sen, idi, vd (texto con marcas),
    car: [[abreviatura, puntuacion, modificador, salvacion]] x 6,
    secciones: [{clave, titulo, intro, items: [{nombre, bloques: [{t: p|li, txt}]}]}]

Uso: py -3.14 criaturas.py   (deja datos\\_criaturas_crudo.json; lo empareja y comprueba emparejar.py)
"""
import json
import os
import re
import sys

from marcas import a_html, unir_html
from srd import LANGS, en_paginas, es, limpia, rango, une

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

ETIQ = {
    "es": dict(CA="ca", Iniciativa="ini", PG="pg", Velocidad="vel", Habilidades="hab", Resistencias="res",
               Vulnerabilidades="vul", Inmunidades="inm", Equipo="equipo", Sentidos="sen", Idiomas="idi", VD="vd"),
    "en": dict(AC="ca", Initiative="ini", HP="pg", Speed="vel", Skills="hab", Resistances="res",
               Vulnerabilities="vul", Immunities="inm", Gear="equipo", Senses="sen", Languages="idi", CR="vd"),
    "de": dict(RK="ca", Initiative="ini", TP="pg", Bewegungsrate="vel", Fertigkeiten="hab", Resistenzen="res",
               Anfälligkeiten="vul", Immunitäten="inm", Ausrüstung="equipo", Sinne="sen", Sprachen="idi", HG="vd"),
    "fr": dict(CA="ca", Initiative="ini", Pv="pg", Vitesse="vel", Compétences="hab", Résistances="res",
               Vulnérabilités="vul", Immunités="inm", Équipement="equipo", Sens="sen", Langues="idi", FP="vd"),
    "it": dict(CA="ca", Iniziativa="ini", PF="pg", Velocità="vel", Abilità="hab", Resistenze="res",
               Vulnerabilità="vul", Immunità="inm", Attrezzatura="equipo", Sensi="sen", Lingue="idi", GS="vd"),
}
OBLIGATORIOS = ("ca", "ini", "pg", "vel", "sen", "idi", "vd")
SECC = {
    "es": {"Atributos": "rasgos", "Acciones": "acciones", "Acciones adicionales": "adicionales",
           "Reacciones": "reacciones", "Acciones legendarias": "legendarias"},
    "en": {"Traits": "rasgos", "Actions": "acciones", "Bonus Actions": "adicionales",
           "Reactions": "reacciones", "Legendary Actions": "legendarias"},
    "de": {"Merkmale": "rasgos", "Aktionen": "acciones", "Bonusaktionen": "adicionales",
           "Reaktionen": "reacciones", "Legendäre Aktionen": "legendarias"},
    "fr": {"Traits": "rasgos", "Actions": "acciones", "Actions Bonus": "adicionales",
           "Réactions": "reacciones", "Actions Légendaires": "legendarias"},
    "it": {"Tratti": "rasgos", "Azioni": "acciones", "Azioni bonus": "adicionales",
           "Reazioni": "reacciones", "Azioni leggendarie": "legendarias"},
}
CAR = {"es": ["Fue", "Des", "Con", "Int", "Sab", "Car"], "en": ["Str", "Dex", "Con", "Int", "Wis", "Cha"],
       "de": ["Stä", "Ges", "Kon", "Int", "Wei", "Cha"], "fr": ["For", "Dex", "Con", "Int", "Sag", "Cha"],
       "it": ["For", "Des", "Cos", "Int", "Sag", "Car"]}
BASE_X = {0: 63.0, 1: 313.5}  # margen izquierdo de cada columna (igual en los cinco SRD)

# Fallos de maquetacion del PDF: (idioma, pagina, texto exacto de la linea) -> tramos corregidos.
# Cada uno comprobado contra la misma ficha en los otros cuatro idiomas.
PARCHES = {
    # la primera linea de Multiattacco y su final van enteros en negrita cursiva
    ("it", 405, "Multiattacco. Il triceratopo effettua due attacchi "):
        [["Multiattacco.", "Optima-BoldItalic"], [" Il triceratopo effettua due attacchi ", "Optima-Regular"]],
    ("it", 405, "Trafiggere."): [["Trafiggere.", "Optima-Regular"]],
}


def parchear(lang, r):
    clave = (lang, r["p"], r["t"])
    if clave not in PARCHES:
        return r
    r = dict(r)
    r["spans"] = [[t, f, r["size"], 0, r["x"]] for t, f in PARCHES[clave]]
    r["font"] = r["spans"][0][1]
    return r


def dx(r):
    return r["x"] - BASE_X[r["col"]]


def es_titulo(r):
    return r["font"] == "GillSans-SemiBold" and r["size"] >= 14.0


def marca_span(font):
    """Negrita cursiva: rotulo. Negrita sola: otra ficha citada ("se convierte en una **sombra**"), salvo
    al principio de un punto de lista (ver html_spans). Cursiva: conjuro citado, "Acierto:"."""
    if "Optima" not in font:
        return ""
    if "BoldItalic" in font:
        return "b"
    if "Bold" in font:
        return "strong"
    if "Italic" in font:
        return "i"
    return ""


def html_spans(spans, li=False):
    marcas = [(marca_span(s[1]), s[0]) for s in spans]
    if li and marcas:
        marcas[0] = ("b", marcas[0][1])
    return a_html(marcas)


def es_rotulo_lista(sp):
    """Punto de lista: la linea empieza por negrita sin cursiva acabada en punto o dos puntos ("A voluntad:",
    "Luz solar.", "1-4."). Una negrita sin ese final es una ficha citada partida entre lineas."""
    return "Bold" in sp[0][1] and "Italic" not in sp[0][1] and limpia(sp[0][0]).endswith((".", ":"))


# Fichas en las que la maqueta ordeno por el alfabeto los puntos de una lista junto con los rasgos (el vampiro
# italiano: sus debilidades salen mezcladas con Fuga nebbiosa y Movimenti del ragno). Se recolocan en el rasgo
# que abre la lista.
RECOLOCAR = {("it", "Vampiro"), ("it", "Progenie vampirica")}


def cortar(lang):
    """Fichas de criatura: titulo GillSans-SemiBold 14.8 seguido de la linea de tipo en Optima-Italic 9."""
    filas_cap = []
    for cap in ("monstruos_az", "animales"):
        p0, p1 = rango(lang, cap)
        filas_cap.extend(dict(r, _cap=cap) for r in en_paginas(lang, p0, p1))
    res, sueltas = [], []
    grupo, cap_actual = None, None
    i = 0
    while i < len(filas_cap):
        r = filas_cap[i]
        if r["_cap"] != cap_actual:
            grupo, cap_actual = None, r["_cap"]  # los animales no tienen titulos de grupo
        if es(r, "GillSans-SemiBold", 18.0):
            g = [r["t"]]
            j = i + 1
            while j < len(filas_cap) and es(filas_cap[j], "GillSans-SemiBold", 18.0):
                g.append(filas_cap[j]["t"]); j += 1
            grupo = une(g)
            i = j
            continue
        if es(r, "GillSans-SemiBold", 14.8):
            nombre = [r["t"]]
            j = i + 1
            while j < len(filas_cap) and es(filas_cap[j], "GillSans-SemiBold", 14.8):
                nombre.append(filas_cap[j]["t"]); j += 1
            tipo = []
            while j < len(filas_cap) and es(filas_cap[j], "Optima-Italic", 9.0):
                tipo.append(filas_cap[j]["t"]); j += 1
            if not tipo:
                sueltas.append(r); i += 1
                continue
            cuerpo = []
            while j < len(filas_cap) and not es_titulo(filas_cap[j]) and not (filas_cap[j]["font"].startswith("GillSans-SemiBold") and filas_cap[j]["size"] >= 25):
                cuerpo.append(filas_cap[j]); j += 1
            res.append({"nombre": une(nombre), "p": r["p"], "cap": r["_cap"], "grupo": grupo, "tipo": une(tipo),
                        "_filas": cuerpo})
            i = j
            continue
        if not (r["font"].startswith("GillSans-SemiBold") and r["size"] >= 25):
            sueltas.append(r)
        i += 1
    return res, sueltas


def caracteristicas(lang, rows):
    """Tokens de la tabla de caracteristicas en orden de lectura: etiqueta, puntuacion, mod, salvacion."""
    toks = []
    prev_label = False
    for r in rows:
        for s in r["spans"]:
            if "SC700" in s[1] or ("GillSans" in s[1] and "Bold" in s[1]):
                t = limpia(s[0])
                if prev_label and toks:
                    toks[-1] = ("L", toks[-1][1] + t)
                else:
                    toks.append(("L", t))
                prev_label = True
            else:
                prev_label = False
                for n in limpia(s[0]).split():
                    toks.append(("N", n))
    car, k = [], 0
    while k < len(toks):
        tipo, t = toks[k]
        if tipo == "L":
            vals = []
            k += 1
            while k < len(toks) and toks[k][0] == "N" and len(vals) < 3:
                vals.append(toks[k][1]); k += 1
            car.append([t] + vals)
        else:
            car.append(["?", t]); k += 1
    out = []
    for c in car:
        if len(c) == 4 and re.fullmatch(r"\d{1,2}", c[1]):
            out.append([c[0], int(c[1]), c[2].replace("-", "−"), c[3].replace("-", "−")])
        else:
            out.append(c)
    return out


def tipografia_campo(clave, v):
    """Espacios que el PDF se come en la cabecera: "veneno;asustado" (28 fichas en los cinco idiomas),
    "13,000in lair" y "XP 450;PB" (ingles)."""
    v = re.sub(r";(?=[^\s<])", "; ", v)
    if clave == "vd":
        v = re.sub(r"(\d)(?=[^\W\d_])", r"\1 ", v)
    return v


def fin_de_frase(linea):
    t = re.sub(r"<[^>]+>", "", linea).rstrip().rstrip("­")
    return t.endswith((".", ":", "!", "?", ")", "»", "”", '"'))


# Parrafos o puntos de lista que la maqueta coloco en otro rasgo: (idioma, ficha) -> [(principio del texto, rasgo
# destino, posicion; None = al final)]. Comprobado contra la misma ficha en los otros cuatro idiomas.
MOVER = {
    # "Primo ruggito" cae, por el alfabeto, dentro de Incantesimi
    ("it", "Sfinge del valore"): [("Primo ruggito", "Ruggito (3/giorno)", 1)],
    # el segundo parrafo de Nube di muco sale detras de Sonda telepatica
    ("it", "Aboleth"): [("Finché la creatura maledetta", "Nube di muco", None)],
}


def mover_puntos(lang, nombre, secciones, errores):
    for prefijo, destino, pos in MOVER.get((lang, nombre), []):
        hecho = False
        for s in secciones:
            dest = next((i for i in s["items"] if limpia(une(i["_nombre"])).rstrip(".:") == destino), None)
            if dest is None:
                continue
            for it in s["items"]:
                for b in list(it["bloques"]):
                    if b["lineas"] and limpia(re.sub(r"<[^>]+>", "", b["lineas"][0])).startswith(prefijo):
                        it["bloques"].remove(b)
                        if pos is None:
                            dest["bloques"].append(b)
                        else:
                            dest["bloques"].insert(pos, b)
                        hecho = True
        if not hecho:
            errores.append(f"no se pudo mover '{prefijo}' a '{destino}'")


def recolocar_listas(sec, errores):
    """Un punto de lista va siempre detras de un parrafo que acaba en dos puntos o de otro punto. Si aparece
    detras de un parrafo cualquiera (o antes del primer rasgo), es un rotulo que la maqueta ordeno con los
    rasgos: se lleva al rasgo que abre la lista."""
    def acaba_en_dos_puntos(b):
        return b["t"] == "p" and b["lineas"] and re.sub(r"<[^>]+>", "", b["lineas"][-1]).rstrip().endswith(":")

    items = sec["items"]
    destino = None
    for it in items:
        if not it.get("_huerfano") and any(acaba_en_dos_puntos(b) for b in it["bloques"]):
            destino = it
            break
    sueltos = []
    for it in items:
        nuevos, previo_ok = [], False
        for b in it["bloques"]:
            if b["t"] == "li":
                # bien colocado si sigue a un parrafo que acaba en dos puntos o a otro punto bien colocado
                (nuevos if previo_ok else sueltos).append(b)
                continue
            nuevos.append(b)
            previo_ok = acaba_en_dos_puntos(b)
        it["bloques"] = nuevos
    if not sueltos:
        sec["items"] = [i for i in items if not i.get("_huerfano")]
        return
    if destino is None:
        errores.append(f"puntos de lista sin parrafo que los abra en {sec['titulo']}")
        return
    destino["bloques"].extend(sueltos)
    errores_txt = ", ".join(limpia(re.sub(r"<[^>]+>", "", b["lineas"][0]))[:25] for b in sueltos)
    destino.setdefault("_recolocados", []).append(errores_txt)
    sec["items"] = [i for i in items if not i.get("_huerfano")]


def estructurar(lang, e):
    et = ETIQ[lang]
    campos, ultimo = {}, None
    car_rows, secciones = [], []
    errores = []
    nombre_sigue = False
    usados = set()
    for r in e["_filas"]:
        if (lang, r["p"], r["t"]) in PARCHES:
            usados.add((lang, r["p"], r["t"]))
            r = parchear(lang, r)
        f, sz = r["font"], r["size"]
        if f.startswith("GillSans") and abs(sz - 6.0) < 0.05:
            continue  # MOD. SALV.
        if not secciones and (any("SC700" in s[1] for s in r["spans"]) or (f.startswith("GillSans") and abs(sz - 9.8) < 0.1)):
            car_rows.append(r)
            continue
        if es(r, "GillSans", 12.0):
            t = limpia(r["t"])
            secciones.append({"clave": SECC[lang].get(t), "titulo": t, "intro": [], "items": []})
            if t not in SECC[lang]:
                errores.append(f"seccion desconocida: {t}")
            continue
        if not secciones:
            if f.startswith("Optima") and abs(sz - 9.0) < 0.05:
                sp0 = r["spans"][0]
                if "Bold" in sp0[1] and "Italic" not in sp0[1]:
                    lab = limpia(sp0[0]).rstrip(":").strip()
                    clave = et.get(lab)
                    if clave is None:
                        errores.append(f"campo desconocido: {lab}")
                        clave = lab
                    campos[clave] = [html_spans(r["spans"][1:]).replace("\t", " ")]
                    ultimo = clave
                elif ultimo:
                    campos[ultimo].append(html_spans(r["spans"]).replace("\t", " "))
                else:
                    errores.append(f"linea de cabecera sin campo: {limpia(r['t'])}")
                continue
            errores.append(f"linea suelta antes de las secciones: {f} {sz} {limpia(r['t'])}")
            continue
        sec = secciones[-1]
        if not f.startswith("Optima"):
            errores.append(f"linea no Optima en seccion: {f} {sz} {limpia(r['t'])}")
            continue
        sp = r["spans"]
        if not sec["items"] and es(r, "Optima-Italic", 9.0) and "BoldItalic" not in sp[0][1]:
            sec["intro"].append(html_spans(sp))
            continue
        if "BoldItalic" in sp[0][1] and not (sec["items"] and nombre_sigue):
            k = 0
            nm = []
            while k < len(sp) and "BoldItalic" in sp[k][1]:
                nm.append(sp[k][0]); k += 1
            resto = sp[k:]
            sec["items"].append({"_nombre": ["".join(nm)], "bloques": [{"t": "p", "lineas": []}]})
            if resto:
                sec["items"][-1]["bloques"][-1]["lineas"].append(html_spans(resto))
            nombre_sigue = not resto and not limpia("".join(nm)).endswith((".", ":"))
            continue
        if nombre_sigue and "BoldItalic" in sp[0][1]:
            k = 0
            nm = []
            while k < len(sp) and "BoldItalic" in sp[k][1]:
                nm.append(sp[k][0]); k += 1
            it = sec["items"][-1]
            it["_nombre"].append("".join(nm))
            resto = sp[k:]
            if resto:
                it["bloques"][-1]["lineas"].append(html_spans(resto))
            nombre_sigue = not resto and not limpia("".join(nm)).endswith((".", ":"))
            continue
        nombre_sigue = False
        es_li = es_rotulo_lista(sp)
        if not sec["items"]:
            # un punto de lista antes del primer rasgo: el PDF italiano ordena por el alfabeto los rotulos de las
            # debilidades del vampiro junto con los rasgos; se recoloca despues
            sec["items"].append({"_nombre": [""], "_huerfano": True, "bloques": [{"t": "p", "lineas": []}]})
            if not es_li:
                errores.append(f"texto sin nombre en {sec['titulo']}: {limpia(r['t'])[:60]}")
        it = sec["items"][-1]
        bl = it["bloques"][-1]
        if es_li:
            it["bloques"].append({"t": "li", "lineas": [html_spans(sp, li=True)]})
        elif dx(r) > 5 and bl["t"] == "p" and bl["lineas"] and fin_de_frase(bl["lineas"][-1]):
            # sangria de primera linea: parrafo nuevo (si la linea anterior no acaba la frase, es un salto de
            # linea mal sangrado, como en "Nimble Escape" del tigre ingles)
            it["bloques"].append({"t": "p", "lineas": [html_spans(sp)]})
        else:
            bl["lineas"].append(html_spans(sp))
    if (lang, e["nombre"]) in RECOLOCAR:
        for s in secciones:
            recolocar_listas(s, errores)
    mover_puntos(lang, e["nombre"], secciones, errores)
    for s in secciones:
        if any(i.get("_huerfano") for i in s["items"]):
            errores.append(f"puntos de lista antes del primer rasgo en {s['titulo']}")
    out = {k: v for k, v in e.items() if not k.startswith("_")}
    out["campos"] = {k: tipografia_campo(k, unir_html(v)) for k, v in campos.items()}
    out["car"] = caracteristicas(lang, car_rows)
    out["secciones"] = []
    for s in secciones:
        items = []
        for it in s["items"]:
            nm = limpia(une(it["_nombre"]))
            nm = re.sub(r"[.:]\s*$", "", nm).strip()
            bloques = [{"t": b["t"], "txt": unir_html(b["lineas"])} for b in it["bloques"] if b["lineas"]]
            if bloques:
                # el punto que cierra el nombre a veces va en letra normal (". Whenever the golem...")
                bloques[0]["txt"] = re.sub(r"^[.:]\s*", "", bloques[0]["txt"])
            items.append({"nombre": nm, "bloques": bloques})
        out["secciones"].append({"clave": s["clave"], "titulo": s["titulo"],
                                 "intro": unir_html(s["intro"]) if s["intro"] else None, "items": items})
    # comprobaciones de la propia ficha
    for c in OBLIGATORIOS:
        if c not in out["campos"]:
            errores.append(f"falta el campo {c}")
    abrevs = [c[0] for c in out["car"]]
    if abrevs != CAR[lang] or any(len(c) != 4 for c in out["car"]):
        errores.append(f"caracteristicas raras: {out['car']}")
    for s in out["secciones"]:
        for it in s["items"]:
            if not it["nombre"]:
                errores.append(f"elemento sin nombre en {s['titulo']}")
            if not it["bloques"]:
                errores.append(f"elemento sin texto: {it['nombre']}")
    out["errores"] = errores
    out["_parches"] = sorted(usados)
    return out


def main():
    salida = {}
    for lang in LANGS:
        ents, sueltas = cortar(lang)
        fichas = [estructurar(lang, e) for e in ents]
        n_err = sum(1 for f in fichas if f["errores"])
        print(f"{lang}: {len(fichas)} fichas, {n_err} con avisos, {len(sueltas)} lineas fuera de fichas")
        for f in fichas:
            for er in f["errores"][:3]:
                print(f"   {f['nombre']} (p. {f['p']}): {er}")
        for r in sueltas[:8]:
            print(f"   suelta p. {r['p']}: {r['font']} {r['size']} {limpia(r['t'])[:80]}")
        for f in fichas:
            f.pop("_parches", None)
        salida[lang] = fichas
    os.makedirs(DATOS, exist_ok=True)
    with open(os.path.join(DATOS, "_criaturas_crudo.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
