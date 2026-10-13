# -*- coding: utf-8 -*-
"""Comprueba datos\\conjuros.json entre idiomas.

1. Recuento: 339 conjuros en cada idioma, los del glosario de T-0107 (ES, EN, DE).
2. Cabecera: tiempo, alcance, componentes y duracion en todos; el mismo nivel que el ingles.
3. Estructura: los mismos bloques (parrafos, puntos, tablas, fichas, nivel superior) que el ingles.
4. Cifras: en cada bloque y en la cabecera, las cifras del ingles (medidas pasadas a metros).

Uso: py -3.14 comprobar_conjuros.py [--json F]. Las diferencias de cifras salen como AVISO; las revisadas a mano
que no son errata estan en datos\\revisados_conjuros.json.
"""
import collections
import json
import os
import sys

from cifras import cifras, cifras_en
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def texto_bloque(b):
    if b["t"] in ("p", "li"):
        return b["txt"]
    if b["t"] == "tabla":
        return " ".join(x for fila in b["filas"] for x in fila)
    if b["t"] == "ficha":
        partes = [b.get("ca", ""), b.get("pg", ""), b.get("vel", "")] + [v for _, v in b.get("rasgos", [])]
        for s in b.get("secciones", []):
            partes += [t for _, t in s["items"]]
        return " ".join(partes)
    return ""


def orden_listas(be, bx, lang):
    """Indice de bx para cada bloque de be. Los puntos de una lista seguidos se emparejan por cifras y largo,
    porque el frances y el italiano ordenan algunas listas por su alfabeto (las opciones de Alarma, de Mano
    arcana, de Simbolo...)."""
    from scipy.optimize import linear_sum_assignment
    from marcas import sin_marcas
    orden = list(range(len(be)))
    k = 0
    def de_lista(b):  # punto de lista o parrafo con rotulo ("Audible Alarm.", "Mental Alarm.")
        return b["t"] == "li" or (b["t"] == "p" and b.get("lead") and not b.get("sup"))

    while k < len(be):
        if not de_lista(be[k]):
            k += 1
            continue
        j = k
        while j < len(be) and de_lista(be[j]) and de_lista(bx[j]):
            j += 1
        if j == k:
            k += 1
            continue
        if j - k > 1:
            ce = [cifras_en(texto_bloque(b)) for b in be[k:j]]
            cx = [cifras(texto_bloque(b), lang) for b in bx[k:j]]
            le = [len(sin_marcas(texto_bloque(b))) for b in be[k:j]]
            lx = [len(sin_marcas(texto_bloque(b))) for b in bx[k:j]]
            coste = []
            for a in range(j - k):
                fila = []
                for b in range(j - k):
                    u = sum((ce[a] | cx[b]).values())
                    jac = sum((ce[a] & cx[b]).values()) / u if u else 1.0
                    fila.append(-(0.7 * jac + 0.3 * min(le[a], lx[b]) / max(le[a], lx[b], 1)))
                coste.append(fila)
            _, cols = linear_sum_assignment(coste)
            for a, b in enumerate(cols):
                orden[k + a] = k + b
        k = j
    return orden


def main():
    salida_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    datos = json.load(open(os.path.join(DATOS, "conjuros.json"), encoding="utf-8"))
    errores, avisos = [], []
    for l in LANGS:
        n = sum(1 for r in datos if l in r)
        if n != 339:
            errores.append(f"{l}: {n} conjuros (tienen que ser 339)")
    for r in datos:
        e = r["en"]
        for l in LANGS:
            x = r.get(l)
            if x is None:
                errores.append(f"{r['id']}: falta {l}")
                continue
            for c in ("tiempo", "alcance", "comp", "dur"):
                if not x.get(c):
                    errores.append(f"{l}: {x['nombre']}: falta {c}")
            if [b["t"] for b in x["bloques"]] != [b["t"] for b in e["bloques"]]:
                errores.append(f"{l}: {x['nombre']}: bloques distintos del ingles")
                continue
            if l == "en":
                continue
            for c in ("tiempo", "alcance", "comp", "dur"):
                ce, cx = cifras_en(e.get(c, "")), cifras(x.get(c, ""), l)
                otras = [cifras(r[o].get(c, ""), o) for o in LANGS if o not in ("en", l) and o in r]
                if ce != cx and sum(1 for k in otras if k == cx) < 2:
                    avisos.append({"id": r["id"], "idioma": l, "conjuro": x["nombre"], "donde": c,
                                   "solo_en_ingles": dict(ce - cx), "solo_en_este": dict(cx - ce),
                                   "texto": x.get(c, ""), "texto_en": e.get(c, "")})
            orden = orden_listas(e["bloques"], x["bloques"], l)
            for k, (be, kx) in enumerate(zip(e["bloques"], orden)):
                bx = x["bloques"][kx]
                te, tx = texto_bloque(be), texto_bloque(bx)
                ce, cx = cifras_en(te), cifras(tx, l)
                if ce != cx:
                    # si las otras traducciones dan las mismas cifras que esta, es la conversion de unidades que
                    # usan todas (10 galones = 40 l), no una errata de esta traduccion
                    otras = [cifras(texto_bloque(r[o]["bloques"][k]), o) for o in LANGS
                             if o not in ("en", l) and o in r and len(r[o]["bloques"]) > k]
                    if sum(1 for c in otras if c == cx) >= 2:
                        continue
                    avisos.append({"id": r["id"], "idioma": l, "conjuro": x["nombre"], "donde": f"bloques[{k}]",
                                   "solo_en_ingles": dict(ce - cx), "solo_en_este": dict(cx - ce),
                                   "texto": tx, "texto_en": te})
    ruta_rev = os.path.join(DATOS, "revisados_conjuros.json")
    rev = json.load(open(ruta_rev, encoding="utf-8"))["revisados"] if os.path.exists(ruta_rev) else []
    claves = {(x["id"], x["idioma"], x["donde"]) for x in rev}
    usados = {(a["id"], a["idioma"], a["donde"]) for a in avisos} & claves
    for x in sorted(claves - usados):
        errores.append(f"revisado que ya no sale: {x}")
    revisados = [a for a in avisos if (a["id"], a["idioma"], a["donde"]) in claves]
    avisos = [a for a in avisos if (a["id"], a["idioma"], a["donde"]) not in claves]
    print(f"{len(errores)} errores; {len(avisos)} avisos de cifras sin revisar "
          f"{dict(collections.Counter(a['idioma'] for a in avisos))}; {len(revisados)} revisados sin errata")
    for x in errores[:40]:
        print("  ERROR", x)
    if salida_json:
        with open(salida_json, "w", encoding="utf-8") as f:
            json.dump({"errores": errores, "avisos": avisos}, f, ensure_ascii=False, indent=1)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
