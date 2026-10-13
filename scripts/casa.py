# -*- coding: utf-8 -*-
"""Normas de casa sobre el texto del SRD (manual de estilo de T-0111), solo en espanol e ingles.

- DM y nunca GM, aunque el SRD diga GM (decision del 16/09/2026).
- Espanol: los estados con mayuscula (decision del 12/09/2026), con la misma regla que revisar_estilo.py: tras
  "estado (de)", "quedar", "estar" y "seguir", y en la lista de inmunidades a estados de la cabecera.
- Sin raya (decision C del 23/09/2026): las del SRD ingles pasan a coma, dos puntos o parentesis.
- Signo menos en las formulas de dados del ingles ("1d4 – 1" -> "1d4 − 1").

El aleman, el frances y el italiano se quedan como su SRD (no hay manual ni comprobador para francés e italiano;
el aleman pasa el comprobador sin errores).
"""
import importlib.util
import os
import re

ESTILO_DIR = os.environ.get("ESTILO_DIR", r"G:\General\Tareas\material\T-0111-estilo-rol-es-en")

_mod = None


def _estilo():
    global _mod
    if _mod is None:
        spec = importlib.util.spec_from_file_location("revisar_estilo", os.path.join(ESTILO_DIR, "revisar_estilo.py"))
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
    return _mod


# Rayas del SRD ingles: texto exacto -> texto sin raya (el mismo sentido; el espanol usa coma o punto y coma).
RAYAS_EN = {
    "<i>Response—Wisdom Saving Throw:</i>": "<i>Response; Wisdom Saving Throw:</i>",
    "Piercing damage—or 12 (2d8 + 3) Piercing damage if the target is Grappled by the mimic—plus":
        "Piercing damage, or 12 (2d8 + 3) Piercing damage if the target is Grappled by the mimic, plus",
    "one nonmagical metal object—armor or a weapon—worn or carried":
        "one nonmagical metal object (armor or a weapon) worn or carried",
    "Piercing damage—or 6 (1d4 + 4) Piercing damage if the swarm is Bloodied—plus":
        "Piercing damage, or 6 (1d4 + 4) Piercing damage if the swarm is Bloodied, plus",
}


def _textos(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str):
                yield o, k
            else:
                yield from _textos(v)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, str):
                yield o, i
            else:
                yield from _textos(v)


def _gm(t):
    return re.sub(r"(?<![\w-])GM(?![\w-])", "DM", t)


def _estados_es(t):
    m = _estilo()
    rx = re.compile(r"\b(estado(?: de)?|qued(?:ar|a|as|an|e|es|en|ará|arán|ó|aron|ando|aría|ado|ada)|"
                    r"est(?:ar|á|ás|án|é|és|én|ará|arán|aba|aban)|sigue|siguen|seguir)(\s+(?:<[^>]+>)?)(" +
                    m.RX_ESTADO_ES + r")\b")

    def sub(mm):
        antes = t[max(0, mm.start() - 30):mm.start()]
        if re.search(r"\b(arma|armas|hoja|flecha|flechas|munici[oó]n|proyectil|filo|daga|espada|objeto|comida|"
                     r"bebida|agua|vino)\b", antes, re.I):
            return mm.group(0)  # «el arma queda envenenada»: un objeto no tiene estados
        e = mm.group(3)
        return mm.group(1) + mm.group(2) + e[0].upper() + e[1:]
    return rx.sub(sub, t)


def _inmunidades_es(v):
    """'veneno; agarrado, apresado' -> 'veneno; Agarrado, Apresado' (tras el punto y coma van los estados)."""
    m = _estilo()
    if ";" not in v and not re.match(r"\s*(" + m.RX_ESTADO_ES + r")\b", v):
        return v
    dano, sep, estados = v.rpartition(";") if ";" in v else ("", "", v)
    estados = re.sub(r"\b(" + m.RX_ESTADO_ES + r")\b", lambda mm: mm.group(1)[0].upper() + mm.group(1)[1:], estados)
    return dano + sep + estados


def aplicar_casa(registros, contar=None):
    """Aplica las normas de casa a las entradas (en su sitio). Devuelve el recuento de cambios por norma."""
    cuenta = {"GM a DM": 0, "estados con mayuscula": 0, "raya": 0, "signo menos": 0}
    for r in registros:
        for l in ("es", "en"):
            x = r.get(l)
            if x is None:
                continue
            for o, k in list(_textos(x)):
                t = o[k]
                n = _gm(t)
                cuenta["GM a DM"] += n != t
                if l == "es":
                    n2 = _estados_es(n)
                    if k == "inm" and isinstance(o, dict):
                        n2 = _inmunidades_es(n2)
                    cuenta["estados con mayuscula"] += n2 != n
                    n = n2
                else:
                    n2 = n
                    for a, b in RAYAS_EN.items():
                        n2 = n2.replace(a, b)
                    cuenta["raya"] += n2 != n
                    n3 = re.sub(r"(\dd\d+) – (\d)", "\\1 \u2212 \\2", n2)
                    cuenta["signo menos"] += n3 != n2
                    n = n3
                o[k] = n
    return cuenta
