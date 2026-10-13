# -*- coding: utf-8 -*-
"""Empareja las notas de reglas de los cinco idiomas (salida de capitulos.py) y les pone su id.

- Las notas con clave de posicion (las secciones de los capitulos de reglas) se casan por esa clave: los cinco
  SRD tienen los mismos titulos en el mismo sitio.
- Las de un grupo que cada idioma ordena por su alfabeto (clases, subclases, especies, trasfondos, dotes de cada
  categoria, herramientas, equipo, entradas del glosario, venenos, trampas) se casan dentro del grupo:
    espanol y aleman, por el glosario ES-EN-DE de T-0107 (nombre a nombre);
    frances e italiano (y lo que el glosario no cubra), por huella con el ingles: cifras con las medidas inglesas en
    metros, forma de los bloques, largo, etiqueta del glosario y parecido del nombre con el espanol (lenguas
    hermanas), con asignacion optima. El metodo se prueba en espanol y aleman contra el glosario.
- Las armas y armaduras salen de las filas de sus tablas (una nota por fila) y se casan igual, dentro de cada
  categoria de la tabla.

El id es el nombre ingles sin tildes ni signos (sin el precio entre parentesis ni la etiqueta del glosario).

Uso: py -3.14 emparejar_reglas.py   (lee datos\\_reglas_crudo.json; deja datos\\reglas.json, personajes.json y
equipo.json)
"""
import collections
import csv
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

from casa import aplicar_casa
from cifras import cifras, cifras_en
from corregir import aplicar
from emparejar import GLOSARIO, slug
from marcas import sin_marcas
from srd import LANGS

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

FICHERO = {"regla": "reglas", "glosario": "reglas", "veneno": "reglas", "trampa": "reglas",
           "clase": "personajes", "subclase": "personajes", "especie": "personajes", "trasfondo": "personajes",
           "dote": "personajes", "herramienta": "equipo", "equipo": "equipo", "arma": "equipo", "armadura": "equipo"}

# Etiquetas del glosario de reglas, a la inglesa
ETIQUETAS = {
    "es": {"acción": "Action", "actitud": "Attitude", "área de efecto": "Area of Effect", "peligro": "Hazard"},
    "de": {"aktion": "Action", "einstellung": "Attitude", "wirkungsbereich": "Area of Effect", "gefahr": "Hazard"},
    "fr": {"action": "Action", "attitude": "Attitude", "zone d’effet": "Area of Effect", "zone d'effet": "Area of Effect",
           "danger": "Hazard"},
    "it": {"azione": "Action", "atteggiamento": "Attitude", "area di effetto": "Area of Effect", "pericolo": "Hazard"},
}


def texto_bloques(bl):
    partes = []
    for b in bl:
        t = b["t"]
        if t in ("p", "li", "formula", "nota", "h"):
            partes.append(b["txt"])
        elif t == "tabla":
            # las celdas con " | " para que dos cifras de celdas vecinas no se lean como millares ("12 100")
            partes += [b.get("titulo") or ""] + [" | ".join(f) for f in b["filas"]]
        elif t == "campos":
            partes += [" | ".join(f) for f in b["filas"]]
        elif t == "recuadro":
            partes += [b["titulo"], texto_bloques(b["bloques"])]
        elif t == "columnas":
            partes += b["items"]
    return " ".join(p for p in partes if p)


def texto_nota(n):
    return n["nombre"] + " " + texto_bloques(n["bloques"])


def nombre_base(n):
    """Nombre sin precio ("(1 po)"), sin etiqueta del glosario y, en las subclases, sin "Subclase de X:"."""
    t = n.get("nombre_corto") or n["nombre"]
    t = re.sub(r"\s*\((?:[^()]*\d[^()]*|variable|variabile|variabel|variable)\)\s*$", "", t, flags=re.I)
    return t.strip()


def norm(t):
    t = unicodedata.normalize("NFKD", sin_marcas(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c)).replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def glosario_t0107():
    """{lang: {nombre normalizado: nombre ingles}} del glosario ES-EN-DE."""
    out = {"es": {}, "de": {}}
    with open(GLOSARIO, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            for l, col in (("es", "espanol"), ("de", "aleman")):
                if row[col] and row["ingles"]:
                    out[l].setdefault(norm(row[col]), row["ingles"])
    return out


VACIAS = {"de", "del", "la", "las", "los", "el", "en", "y", "o", "un", "una", "the", "of", "and", "or", "a", "an",
          "der", "die", "das", "des", "und", "oder", "von", "ein", "eine", "le", "les", "du", "des", "et", "ou",
          "à", "au", "aux", "il", "lo", "gli", "di", "da", "e", "per", "con", "con", "sur", "par", "pour", "zu", "mit"}


def todo_texto(o):
    """Todo el texto de una entrada, venga en la forma que venga (fichas, conjuros, objetos)."""
    if isinstance(o, str):
        return o
    if isinstance(o, dict):
        return " ".join(todo_texto(v) for k, v in o.items() if k not in ("t", "pies", "lead", "sup"))
    if isinstance(o, list):
        return " ".join(todo_texto(v) for v in o)
    return ""


class Corpus:
    """Textos ya emparejados en los cinco idiomas (fichas, conjuros, objetos magicos, estados y las secciones de
    reglas con clave de posicion). Dos nombres se parecen si salen en los mismos textos: "Escalade" sale donde sale
    "Climbing" y "Sac a dos" donde "Backpack"."""

    def __init__(self, crudo):
        docs = []
        for f in ("criaturas", "conjuros", "objetos", "estados"):
            for r in json.load(open(os.path.join(DATOS, f + ".json"), encoding="utf-8")):
                docs.append({l: todo_texto(r[l]) for l in LANGS if l in r})
        claves = {}
        for l in LANGS:
            for n in crudo[l]:
                if n["clave"]:
                    claves.setdefault(n["clave"], {})[l] = texto_nota(n)
        docs.extend(claves.values())
        self.tokens = {l: [set(re.findall(r"\w+", norm(d.get(l, "")))) for d in docs] for l in LANGS}
        self.cache = {}

    @staticmethod
    def raices(nombre):
        ws = [w for w in re.findall(r"\w+", norm(nombre)) if w not in VACIAS and not w.isdigit()]
        return [w[:max(4, int(len(w) * 0.7))] if len(w) > 4 else w for w in ws]

    def docs(self, lang, nombre):
        clave = (lang, nombre)
        if clave not in self.cache:
            rs = self.raices(nombre)
            out = set()
            if rs:
                for k, toks in enumerate(self.tokens[lang]):
                    if all(any(t.startswith(r) if len(r) > 3 else t == r for t in toks) for r in rs):
                        out.add(k)
            self.cache[clave] = out
        return self.cache[clave]

    def parecido(self, lang_a, nombre_a, lang_b, nombre_b):
        a, b = self.docs(lang_a, nombre_a), self.docs(lang_b, nombre_b)
        if not a or not b:
            return None
        return len(a & b) / len(a | b)


MONEDAS = {
    "en": {"cp": 1, "sp": 10, "ep": 50, "gp": 100, "pp": 1000},
    "es": {"pc": 1, "pp": 10, "pe": 50, "po": 100, "ppt": 1000},
    "de": {"km": 1, "sm": 10, "em": 50, "gm": 100, "pm": 1000},
    "fr": {"pc": 1, "pa": 10, "pe": 50, "po": 100, "pp": 1000},
    "it": {"mr": 1, "ma": 10, "me": 50, "mo": 100, "mp": 1000},
}


def precio(nombre, lang):
    """Precios del titulo en piezas de cobre ("Cubo (5 pc)" -> {5}; el pergamino de conjuro trae dos)."""
    m = re.search(r"\(([^()]*\d[^()]*)\)\s*$", nombre)
    if not m:
        return None
    out = set()
    for n, u in re.findall(r"(\d[\d.,   ]*)\s*([A-Za-z]{2,3})\b", m.group(1)):
        v = MONEDAS[lang].get(u.lower())
        if v:
            out.add(int(re.sub(r"\D", "", n)) * v)
    return frozenset(out) or None


def forma(n):
    return collections.Counter(b["t"] for b in n["bloques"])


def parecido_forma(a, b):
    u = sum((a | b).values())
    return sum((a & b).values()) / u if u else 1.0


def emparejar_por_huella(en, otro, lang, fijos=None, nombres_es=None, corpus=None, extra=None, lang_a="en"):
    """Para cada nota inglesa del grupo, el indice de su pareja en 'otro' (o None). 'fijos': parejas ya sabidas
    {i_en: j}. 'extra': {(lang, nombre): texto} que se suma a la huella (el peso de la tabla de equipo).
    Devuelve (parejas, parecidos)."""
    from scipy.optimize import linear_sum_assignment
    fijos = dict(fijos or {})
    extra = extra or {}

    def txt(n, l):
        return texto_nota(n) + " " + extra.get((l, norm(nombre_base(n))), "")
    res = [fijos.get(i) for i in range(len(en))]
    libres_e = [i for i in range(len(en)) if i not in fijos]
    libres_o = [j for j in range(len(otro)) if j not in set(fijos.values())]
    par = {i: None for i in range(len(en))}
    if libres_e and libres_o:
        ce = {i: cifras_en(txt(en[i], "en")) if lang_a == "en" else cifras(txt(en[i], lang_a), lang_a)
              for i in libres_e}
        co = {j: cifras(txt(otro[j], lang), lang) for j in libres_o}
        le = {i: len(sin_marcas(texto_nota(en[i]))) for i in libres_e}
        lo = {j: len(sin_marcas(texto_nota(otro[j]))) for j in libres_o}
        fe = {i: forma(en[i]) for i in libres_e}
        fo = {j: forma(otro[j]) for j in libres_o}
        te = {i: en[i].get("etiqueta") if lang_a == "en" else
              ETIQUETAS[lang_a].get((en[i].get("etiqueta") or "").lower()) for i in libres_e}
        to = {j: ETIQUETAS.get(lang, {}).get((otro[j].get("etiqueta") or "").lower()) for j in libres_o}
        coste = []
        for i in libres_e:
            fila = []
            for j in libres_o:
                u = sum((ce[i] | co[j]).values())
                jac = sum((ce[i] & co[j]).values()) / u if u else 1.0
                s = 0.45 * jac + 0.15 * parecido_forma(fe[i], fo[j]) + 0.15 * min(le[i], lo[j]) / max(le[i], lo[j], 1)
                if lang_a == "es":
                    s += 0.25 * SequenceMatcher(None, norm(nombre_base(en[i])), norm(nombre_base(otro[j]))).ratio()
                elif nombres_es and nombres_es[i]:
                    s += 0.25 * SequenceMatcher(None, norm(nombres_es[i]), norm(nombre_base(otro[j]))).ratio()
                else:
                    s /= 0.75
                if (te[i] or to[j]) and te[i] != to[j]:
                    s -= 0.4
                if corpus is not None:
                    c = corpus.parecido(lang_a, nombre_base(en[i]), lang, nombre_base(otro[j]))
                    s += 0.6 * (c if c is not None else 0.15)
                pe, po = precio(en[i]["nombre"], lang_a), precio(otro[j]["nombre"], lang)
                if pe and po:
                    s += 0.35 if pe == po else -0.35
                fila.append(-s)
            coste.append(fila)
        filas, cols = linear_sum_assignment(coste)
        for f, c in zip(filas, cols):
            res[libres_e[f]] = libres_o[c]
            par[libres_e[f]] = -coste[f][c]
    return res, par


def grupos_de(notas):
    g = collections.OrderedDict()
    for k, n in enumerate(notas):
        if n["grupo"]:
            g.setdefault(n["grupo"], []).append(k)
    return g


def emparejar(crudo, problemas):
    """{lang: [indice en crudo[lang] para cada nota inglesa]}"""
    en = crudo["en"]
    gl = glosario_t0107()
    pareja = {"en": list(range(len(en)))}
    for l in LANGS:
        if l == "en":
            continue
        pareja[l] = [None] * len(en)
        por_clave = {n["clave"]: j for j, n in enumerate(crudo[l]) if n["clave"]}
        for i, n in enumerate(en):
            if n["clave"]:
                pareja[l][i] = por_clave.get(n["clave"])
                if pareja[l][i] is None:
                    problemas.append(f"{l}: falta la seccion {n['clave']} ({n['nombre']})")
    grupos_en = grupos_de(en)
    nombres_es = {}
    corpus = Corpus(crudo)
    # el peso de cada objeto de equipo esta en la tabla de equipo de aventureros, no en su descripcion
    extra = {}
    for l in LANGS:
        for n in crudo[l]:
            if n["clave"] == "equipo.4":
                for b in n["bloques"]:
                    if b["t"] == "tabla":
                        for f in b["filas"][1:]:
                            extra[(l, norm(re.sub(r"\s*\(.*?\)\s*$", "", sin_marcas(f[0]))))] = " ".join(f[1:])
    for l in ("es", "de", "fr", "it"):
        grupos_l = grupos_de(crudo[l])
        for g, ie in grupos_en.items():
            il = grupos_l.get(g, [])
            faltan = sum(1 for i in ie if (l, en[i]["nombre"]) in FALTAN)
            if len(il) + faltan != len(ie):
                problemas.append(f"{l}: grupo {g} con {len(il)} notas y {len(ie)} en ingles")
            gen = [en[i] for i in ie]
            gol = [crudo[l][j] for j in il]
            fijos = {}
            if l in ("es", "de"):
                por_nombre_en = {norm(nombre_base(n)): a for a, n in enumerate(gen)}
                for b, n in enumerate(gol):
                    nombre_en = gl[l].get(norm(nombre_base(n)))
                    a = por_nombre_en.get(norm(nombre_en)) if nombre_en else None
                    if a is not None and a not in fijos:
                        fijos[a] = b
                res, par = emparejar_por_huella(gen, gol, l, fijos, corpus=corpus, extra=extra)
                # prueba del metodo por huella contra el glosario (sin el glosario, sin nombres)
                prueba, _ = emparejar_por_huella(gen, gol, l, corpus=corpus, extra=extra)
                mal = [gen[a]["nombre"] for a in fijos if prueba[a] != fijos[a]]
                if mal:
                    print(f"   prueba de la huella en {l}, {g}: {len(fijos) - len(mal)} de {len(fijos)} como el "
                          f"glosario; distintas: {mal[:6]}")
                if l == "es":
                    nombres_es[g] = [nombre_base(gol[res[a]]) if res[a] is not None else "" for a in range(len(gen))]
            else:
                res, par = emparejar_por_huella(gen, gol, l, nombres_es=nombres_es.get(g), corpus=corpus, extra=extra)
                for (lr, gr, nom_l), nom_en in REVISADAS.items():
                    if (lr, gr) != (l, g):
                        continue
                    a = next(a for a, n in enumerate(gen) if n["nombre"] == nom_en)
                    b = next(b for b, n in enumerate(gol) if n["nombre"] == nom_l)
                    otra = next((x for x in range(len(gen)) if res[x] == b), None)
                    if otra is not None and otra != a:
                        res[otra] = res[a]
                    res[a] = b
                    par[a] = None
                # contraprueba por el espanol (ya casado por el glosario): frances e italiano se parecen mas al
                # espanol que al ingles en los nombres; donde las dos vias no coinciden, se mira a mano
                ges = [crudo["es"][pareja["es"][i]] for i in ie]
                pivote, _ = emparejar_por_huella(ges, gol, l, corpus=corpus, extra=extra, lang_a="es")
                for a in range(len(gen)):
                    if pivote[a] != res[a] and (l, g, gol[res[a]]["nombre"]) not in REVISADAS:
                        problemas.append(f"{l}, {g}: {gen[a]['nombre']} = {gol[res[a]]['nombre']} por el ingles, "
                                         f"pero {gol[pivote[a]]['nombre'] if pivote[a] is not None else '-'} "
                                         f"por el espanol ({ges[a]['nombre']})")
            sin_glos = [gen[a]["nombre"] for a in range(len(gen)) if l in ("es", "de") and a not in fijos]
            if sin_glos:
                print(f"   {l}, {g}: {len(sin_glos)} sin el glosario, por huella: {sin_glos[:8]}")
            for a, b in enumerate(res):
                pareja[l][ie[a]] = il[b] if b is not None else None
                if par.get(a) is not None and par[a] < 0.55 and (l, g, gol[b]["nombre"]) not in REVISADAS:
                    problemas.append(f"{l}: {gol[b]['nombre']} = {gen[a]['nombre']} con parecido {par[a]:.2f}")
    return pareja


# Parejas de frances e italiano miradas a mano (nombre en su SRD -> nombre ingles), donde la huella duda o el ingles y
# el espanol no coinciden. Comprobadas leyendo las dos entradas.
REVISADAS = {
    ("fr", "glosario", "Dés de vie"): "Hit Point Dice",
    ("fr", "glosario", "Métamorphes"): "Shape-Shifting",
    ("fr", "glosario", "Cat. de taille"): "Size",
    ("fr", "glosario", "Reptation"): "Crawling",
    ("it", "glosario", "Prepararsi [azione]"): "Ready [Action]",
    ("it", "glosario", "Nuotare"): "Swimming",
    ("fr", "arma.1", "Fléchette"): "Dart",
}
# Entradas que un SRD no trae: el italiano no tiene "Save" (en ingles solo dice que es otro nombre de "Saving Throw")
FALTAN = {("it", "Save")}


def ids_unicos(en, problemas):
    ids = []
    vistos = collections.Counter()
    for n in en:
        base = slug(nombre_base(n))
        if n["tipo"] == "subclase":
            base = slug(nombre_base(n))
        vistos[base] += 1
        ids.append(base)
    out = []
    for n, i in zip(en, ids):
        if vistos[i] > 1:
            i = f"{i}-{n['tipo']}" if n["tipo"] != "regla" else f"{i}-{n['cap']}"
        out.append(i)
    rep = [i for i, c in collections.Counter(out).items() if c > 1]
    if rep:
        problemas.append(f"ids repetidos: {rep}")
    return out


def construir():
    crudo = json.load(open(os.path.join(DATOS, "_reglas_crudo.json"), encoding="utf-8"))
    problemas = []
    pareja = emparejar(crudo, problemas)
    en = crudo["en"]
    ids = ids_unicos(en, problemas)
    salida = []
    for k, n in enumerate(en):
        rec = {"id": ids[k], "tipo": n["tipo"], "cap": n["cap"]}
        for l in LANGS:
            j = pareja[l][k]
            if j is None:
                if (l, n["nombre"]) not in FALTAN:
                    problemas.append(f"{n['nombre']}: sin pareja en {l}")
                continue
            x = dict(crudo[l][j])
            for c in ("cap", "clave", "grupo", "tipo"):
                x.pop(c, None)
            rec[l] = x
        salida.append(rec)
    salida += armas_y_armaduras(salida, problemas)
    alinear_recuadros(salida, problemas)
    return salida, problemas


def alinear_recuadros(salida, problemas):
    """Los recuadros flotan y, en la frontera entre dos secciones, cada maqueta los deja en una ("Lanzar conjuros con
    armadura" va al final de "Obtener conjuros" en aleman e italiano y al principio de "Lanzar conjuros" en los
    demas). Se ponen en la nota en que los pone el ingles, por orden dentro de cada capitulo."""
    por_cap = collections.defaultdict(list)
    for r in salida:
        por_cap[r["cap"]].append(r)
    for cap, recs in por_cap.items():
        sec_en = [(r, k) for r in recs for k, b in enumerate(r["en"]["bloques"]) if b["t"] == "recuadro"]
        for l in LANGS:
            if l == "en":
                continue
            sec_l = [(r, b) for r in recs if l in r for b in r[l]["bloques"] if b["t"] == "recuadro"]
            if len(sec_l) != len(sec_en):
                problemas.append(f"{l}, {cap}: {len(sec_l)} recuadros y {len(sec_en)} en ingles")
                continue
            for (re_, k), (rl, b) in zip(sec_en, sec_l):
                if re_ is rl:
                    continue
                rl[l]["bloques"].remove(b)
                destino = re_[l]["bloques"]
                destino.insert(0 if k == 0 else len(destino), b)


def armas_y_armaduras(salida, problemas):
    """Notas de arma y de armadura desde las filas de sus tablas, emparejadas como un grupo mas."""
    import armas
    por_id = {r["id"]: r for r in salida}
    out = []
    for tipo, sec, comun in (("arma", "weapons", armas.comun_arma), ("armadura", "armor", armas.comun_armadura)):
        rec = por_id[sec]
        pseudo = {l: [dict(n, cap="equipo", clave=None) for n in armas.notas_de_tabla(rec[l], tipo)]
                  for l in LANGS if l in rec}
        cats = {l: [n["categoria"] for n in v] for l, v in pseudo.items()}
        pareja = emparejar(pseudo, problemas)
        usados = {r["id"] for r in salida}
        for k, n in enumerate(pseudo["en"]):
            i = slug(n["nombre"])
            if i in usados:
                i = f"{i}-{tipo}"
            r = {"id": i, "tipo": tipo, "cap": "equipo", "comun": comun(n)}
            for l in LANGS:
                j = pareja[l][k] if l in pareja else None
                if j is None:
                    problemas.append(f"{tipo} {n['nombre']}: sin pareja en {l}")
                    continue
                x = dict(pseudo[l][j])
                for c in ("cap", "clave", "grupo", "tipo"):
                    x.pop(c, None)
                r[l] = x
            out.append(r)
        n_cats = {l: len(set(v)) for l, v in cats.items()}
        if len(set(n_cats.values())) != 1:
            problemas.append(f"{tipo}: categorias distintas por idioma {n_cats}")
    return out


def main():
    salida, problemas = construir()
    print("normas de casa:", aplicar_casa(salida))
    err = aplicar(salida, "correcciones_reglas.json")
    problemas += [f"correccion: {e}" for e in err]
    print(f"{sum(len(r.get('correcciones', [])) for r in salida)} erratas de traduccion corregidas")
    por_fichero = collections.defaultdict(list)
    for r in salida:
        por_fichero[FICHERO[r["tipo"]]].append(r)
    for f, lista in por_fichero.items():
        with open(os.path.join(DATOS, f + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(lista, fh, ensure_ascii=False, indent=1)
        print(f"{len(lista)} notas -> datos\\{f}.json", dict(collections.Counter(r["tipo"] for r in lista)))
    print(f"{len(problemas)} problemas")
    for p in problemas:
        print("  ", p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
