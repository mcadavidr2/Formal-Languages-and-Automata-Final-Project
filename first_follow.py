"""Ítem 1: FIRST y FOLLOW (libro, sección 4.4.2) y la opción --sets."""
from common import EPS, END, START, is_terminal, is_nonterminal


def first_of_string(symbols, first):
    """FIRST de una cadena X1 X2 ... Xn (se usa para la tabla y para FOLLOW)."""
    result = set()
    for X in symbols:
        if is_terminal(X):
            result.add(X)
            return result
        result |= first[X] - {EPS}
        if EPS not in first[X]:
            return result
    result.add(EPS)          # todos los símbolos (o ninguno) derivan ε
    return result


def compute_first(grammar):
    """FIRST(A) para cada no terminal, por punto fijo (reglas 1-3 del libro)."""
    first = {A: set() for A in grammar}
    changed = True
    while changed:
        changed = False
        for A, alts in grammar.items():
            for body in alts:
                f = first_of_string(body, first)
                if not f <= first[A]:
                    first[A] |= f
                    changed = True
    return first


def compute_follow(grammar, first, start=START):
    """FOLLOW(A) para cada no terminal, por punto fijo (reglas 1-3 del libro)."""
    follow = {A: set() for A in grammar}
    follow[start].add(END)                                   # regla 1
    changed = True
    while changed:
        changed = False
        for A, alts in grammar.items():
            for body in alts:
                for i, X in enumerate(body):
                    if not is_nonterminal(X):
                        continue
                    beta = first_of_string(body[i + 1:], first)
                    new = beta - {EPS}                       # regla 2: A -> aXb
                    if EPS in beta:                          # regla 3: b => ε (o b vacío)
                        new = new | follow[A]
                    if not new <= follow[X]:
                        follow[X] |= new
                        changed = True
    return follow


def format_set(s):
    """Terminales en orden ASCII, luego e, luego $."""
    items = sorted(x for x in s if x not in (EPS, END))
    if EPS in s:
        items.append(EPS)
    if END in s:
        items.append(END)
    return "{" + ", ".join(items) + "}"


def sets_lines(grammar, first, follow):
    """Líneas de --sets: primero todos los First, luego todos los Follow."""
    lines = ["First(%s) = %s" % (A, format_set(first[A])) for A in sorted(grammar)]
    lines += ["Follow(%s) = %s" % (A, format_set(follow[A])) for A in sorted(grammar)]
    return lines
