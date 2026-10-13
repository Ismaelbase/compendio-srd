# -*- coding: utf-8 -*-
"""Comprueba datos\\reglas.json, personajes.json y equipo.json entre idiomas.

1. Recuento: las notas de cada tipo en cada idioma (el italiano no trae la entrada "Save" del glosario).
2. Estructura: los mismos titulos dentro de cada nota que el ingles.
3. Cifras: cada apartado de la nota (lo que va entre dos titulos) frente al mismo apartado ingles, con las
   medidas inglesas pasadas a metros. Los apartados se casan por cifras y largo cuando cada idioma los ordena por
   su alfabeto (las propiedades de las armas, los efectos ambientales). Si las otras traducciones dan las mismas
   cifras que esta, es la conversion de unidades que usan todas y no se avisa.

Uso: py -3.14 comprobar_reglas.py [--json F]. Las diferencias revisadas a mano que no son errata, en
datos\\revisados_reglas.json.
"""
import collections
import json
import os
import re
import sys
import unicodedata

from cifras_reglas import cifras_r as cifras, cifras_r_en as cifras_en
from emparejar_reglas import FALTAN, texto_bloques
from marcas import sin_marcas
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
FICHEROS = ("reglas", "personajes", "equipo")
CUANTAS = {"regla": 53, "glosario": 140, "veneno": 14, "trampa": 8, "clase": 12, "subclase": 12, "especie": 9,
           "trasfondo": 4, "dote": 17, "herramienta": 25, "equipo": 81, "arma": 38, "armadura": 13}


def apartados(x):
    """[(titulo, texto, nivel)] de una nota: lo de antes del primer titulo y lo de debajo de cada titulo."""
    out = [["", [], 0]]
    for b in x["bloques"]:
        if b["t"] == "h":
            out.append([b["txt"], [], b["n"]])
        else:
            out[-1][1].append(b)
    return [(t, texto_bloques([b for b in bl if b["t"] != "tabla"]), n) for t, bl, n in out if bl or t]


def tablas(x):
    return [(b.get("titulo") or "", texto_bloques([dict(b, titulo=None)])) for b in x["bloques"] if b["t"] == "tabla"]


def casar_tablas(te, tx, lang):
    """Indice de tx para cada tabla de te (las tablas flotan y cada maqueta las deja en un apartado distinto): por
    cifras, largo y orden. None donde no hay pareja."""
    from scipy.optimize import linear_sum_assignment
    if not te or not tx:
        return [None] * len(te)
    ce = [cifras_en(t + " " + s) for t, s in te]
    cx = [cifras(t + " " + s, lang) for t, s in tx]
    coste = []
    for a in range(len(te)):
        fila = []
        for b in range(len(tx)):
            u = sum((ce[a] | cx[b]).values())
            jac = sum((ce[a] & cx[b]).values()) / u if u else 1.0
            la, lb = len(te[a][1]) + 1, len(tx[b][1]) + 1
            fila.append(-(0.7 * jac + 0.2 * min(la, lb) / max(la, lb) + 0.1 * (a == b)))
        coste.append(fila)
    filas, cols = linear_sum_assignment(coste)
    out = [None] * len(te)
    for f, c in zip(filas, cols):
        out[f] = c
    return out


def unidades_de(e, x, lang, errores):
    """{clave: (titulo, texto)}: los apartados (sin tablas) casados con los del ingles y las tablas casadas aparte."""
    ae, ax = apartados(e), apartados(x)
    out = {}
    if x is e:
        for k, (t, s_, _) in enumerate(ae):
            out[("s", k)] = (t, s_)
        for k, (t, s_) in enumerate(tablas(e)):
            out[("t", k)] = (t, s_)
        return out
    idx = casar(ae, ax, lang)
    if idx is None:
        out[("s", 0)] = ("", " ".join(t + " " + s_ for t, s_, _ in ax))
        out["entero"] = True
    else:
        for k in range(len(ae)):
            out[("s", k)] = ax[idx[k]][:2]
    te, tx = tablas(e), tablas(x)
    if len(te) != len(tx):
        errores.append(f"{lang}: {x['nombre']}: {len(tx)} tablas frente a {len(te)} en ingles")
    for k, j in enumerate(casar_tablas(te, tx, lang)):
        if j is not None:
            out[("t", k)] = tx[j]
    return out


def _alfa(t):
    t = unicodedata.normalize("NFKD", sin_marcas(t).lower())
    return "".join(c for c in t if not unicodedata.combining(c)).replace("’", "'")


def _numero(t):
    m = re.match(r"\D*?(\d+)\s*[:.]", t)
    return m.group(1) if m else None


def casar(ae, ax, lang):
    """Indice de ax para cada apartado de ae, o None si no tienen el mismo numero de apartados.

    Van en el mismo orden salvo donde cada idioma ordena por su alfabeto: los apartados hermanos (mismo nivel, uno
    detras de otro) en orden alfabetico en los dos idiomas (propiedades de las armas, efectos ambientales), y los
    rasgos del mismo nivel de una clase ("Nivel 3: Conocimiento primigenio" y "Nivel 3: Subclase de barbaro" van al
    reves en ingles). Ahi se casan por cifras y largo."""
    if len(ae) != len(ax):
        return None
    n = len(ae)
    idx = list(range(n))
    k = 0
    while k < n:
        j = k
        while j + 1 < n and ae[j + 1][2] == ae[k][2] and ax[j + 1][2] == ae[k][2] and ae[k][0]:
            j += 1
        tramo = list(range(k, j + 1))
        if len(tramo) >= 3 and (all(_alfa(ae[a][0]) <= _alfa(ae[a + 1][0]) for a in tramo[:-1]) or
                                all(_alfa(ax[a][0]) <= _alfa(ax[a + 1][0]) for a in tramo[:-1])):
            _asignar(ae, ax, lang, tramo, idx)
        else:
            a = k
            while a <= j:
                b = a
                while b + 1 <= j and _numero(ae[a][0]) and _numero(ae[b + 1][0]) == _numero(ae[a][0]):
                    b += 1
                if b > a:
                    _asignar(ae, ax, lang, list(range(a, b + 1)), idx)
                a = b + 1
        k = j + 1
    return idx


def _asignar(ae, ax, lang, tramo, idx):
    from scipy.optimize import linear_sum_assignment
    ce = [cifras_en(ae[a][0] + " " + ae[a][1]) for a in tramo]
    cx = [cifras(ax[a][0] + " " + ax[a][1], lang) for a in tramo]
    le = [len(sin_marcas(ae[a][1])) + 1 for a in tramo]
    lx = [len(sin_marcas(ax[a][1])) + 1 for a in tramo]
    coste = []
    for p in range(len(tramo)):
        fila = []
        for q in range(len(tramo)):
            u = sum((ce[p] | cx[q]).values())
            jac = sum((ce[p] & cx[q]).values()) / u if u else 1.0
            fila.append(-(0.6 * jac + 0.4 * min(le[p], lx[q]) / max(le[p], lx[q])))
        coste.append(fila)
    _, cols = linear_sum_assignment(coste)
    for p, q in enumerate(cols):
        idx[tramo[p]] = tramo[q]


def main():
    salida_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    datos = [r for f in FICHEROS for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8"))]
    errores, avisos, info = [], [], []
    for l in LANGS:
        cuenta = collections.Counter(r["tipo"] for r in datos if l in r)
        for t, n in CUANTAS.items():
            falta = sum(1 for r in datos if r["tipo"] == t and (l, r["en"]["nombre"]) in FALTAN)
            if cuenta.get(t, 0) + falta != n:
                errores.append(f"{l}: {cuenta.get(t, 0)} notas de tipo {t} (tienen que ser {n})")
    for r in datos:
        e = r["en"]
        unidades = {}
        for l in LANGS:
            x = r.get(l)
            if x is None:
                if (l, e["nombre"]) not in FALTAN:
                    errores.append(f"{r['id']}: falta {l}")
                continue
            if not x["bloques"] and e["bloques"]:
                errores.append(f"{l}: {x['nombre']}: sin texto")
            he = [b["n"] for b in e["bloques"] if b["t"] == "h"]
            hx = [b["n"] for b in x["bloques"] if b["t"] == "h"]
            if he != hx:
                errores.append(f"{l}: {x['nombre']}: titulos {len(hx)} frente a {len(he)} en ingles")
            unidades[l] = unidades_de(e, x, l, errores)
        ue = unidades["en"]
        for l, ux in unidades.items():
            if l == "en":
                continue
            x = r[l]
            ue_l = ue
            if ux.get("entero"):
                # distinto numero de apartados que el ingles: se compara la nota entera (sin las tablas)
                ue_l = {c: v for c, v in ue.items() if c[0] == "t"}
                ue_l[("s", 0)] = ("", " ".join(t + " " + s_ for c, (t, s_) in ue.items() if c[0] == "s"))
            for clave, (te, se) in ue_l.items():
                tx, sx = ux.get(clave, ("", ""))
                ce, cx = cifras_en(te + " " + se), cifras(tx + " " + sx, l)
                if ce == cx:
                    continue
                otras = [cifras(" ".join(uo.get(clave, ("", ""))), o) for o, uo in unidades.items()
                         if o not in ("en", l) and bool(uo.get("entero")) == bool(ux.get("entero"))]
                if sum(1 for c in otras if c == cx) >= 2:
                    continue
                solo_e, solo_x = ce - cx, cx - ce
                if not (solo_e and solo_x) and all(float(n) <= 3 for n in (solo_e or solo_x)):
                    # una cifra pequena de mas en un idioma: "1 Hit Point" frente a "un point de vie", "level 1"
                    # frente a "ersten Stufe"; no es una errata de cifras
                    info.append(f"{l}: {x['nombre']} ({te or 'inicio'}): {dict(solo_e)} / {dict(solo_x)}")
                    continue
                avisos.append({"id": r["id"], "idioma": l, "nota": x["nombre"],
                               "apartado": ("tabla " if clave[0] == "t" else "") + (te[:80] if te else "(inicio)"),
                               "solo_en_ingles": dict(solo_e), "solo_en_este": dict(solo_x),
                               "texto": (tx + " " + sx).strip(), "texto_en": (te + " " + se).strip()})
    ruta_rev = os.path.join(DATOS, "revisados_reglas.json")
    rev = json.load(open(ruta_rev, encoding="utf-8"))["revisados"] if os.path.exists(ruta_rev) else []
    claves = {(x["id"], x["idioma"], x["apartado"]) for x in rev}
    usados = {(a["id"], a["idioma"], a["apartado"]) for a in avisos} & claves
    for x in sorted(claves - usados):
        errores.append(f"revisado que ya no sale: {x}")
    revisados = [a for a in avisos if (a["id"], a["idioma"], a["apartado"]) in claves]
    avisos = [a for a in avisos if (a["id"], a["idioma"], a["apartado"]) not in claves]
    print(f"{len(errores)} errores; {len(avisos)} avisos de cifras sin revisar "
          f"{dict(collections.Counter(a['idioma'] for a in avisos))}; {len(revisados)} revisados sin errata")
    for x in errores[:40]:
        print("  ERROR", x)
    if salida_json:
        with open(salida_json, "w", encoding="utf-8") as f:
            json.dump({"errores": errores, "avisos": avisos, "info": info}, f, ensure_ascii=False, indent=1)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
