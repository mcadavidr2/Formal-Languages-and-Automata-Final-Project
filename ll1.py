"""Ítem 2 (parte LL(1)): condición LL(1), tabla (Alg. 4.31) y parser con pila (Alg. 4.34)."""
from common import EPS, END, START, Node, is_terminal, productions
from first_follow import first_of_string


def is_ll1_condition(grammar, first, follow):
    """Condición del inicio de 4.4.3: para cada par de alternativas distintas
    A -> a | b:
      1) FIRST(a) y FIRST(b) son disjuntos (ninguno de los dos deriva cadenas
         que empiecen con el mismo terminal);
      2) a lo sumo uno de los dos deriva ε;
      3) si b =>* ε, entonces FIRST(a) y FOLLOW(A) son disjuntos (y simétrico).
    """
    for A, alts in grammar.items():
        firsts = [first_of_string(body, first) for body in alts]
        for i in range(len(alts)):
            for j in range(i + 1, len(alts)):
                fi, fj = firsts[i] - {EPS}, firsts[j] - {EPS}
                if fi & fj:
                    return False
                if EPS in firsts[i] and EPS in firsts[j]:
                    return False
                if EPS in firsts[j] and fi & follow[A]:
                    return False
                if EPS in firsts[i] and fj & follow[A]:
                    return False
    return True


def build_ll1_table(grammar, first, follow):
    """Algoritmo 4.31. Devuelve table[(A, a)] = [índices de producción].
    Si alguna celda tiene más de una producción, la gramática no es LL(1)."""
    table = {}
    for idx, (A, body) in enumerate(productions(grammar)):
        f = first_of_string(body, first)
        for a in f - {EPS}:
            table.setdefault((A, a), []).append(idx)
        if EPS in f:
            for b in follow[A]:          # incluye $ si está en FOLLOW(A)
                table.setdefault((A, b), []).append(idx)
    return table


def table_has_conflicts(table):
    return any(len(v) > 1 for v in table.values())


def ll1_parse(grammar, table, string, start=START):
    """Algoritmo 4.34 (parser predictivo no recursivo, con pila).
    `string` es la cadena SIN $ (la cadena vacía es ''). Devuelve (ok, árbol)."""
    prods = productions(grammar)
    tokens = list(string) + [END]
    root = Node(start)
    stack = [Node(END), root]            # el tope es stack[-1]
    pos = 0
    while True:
        top = stack[-1]
        X, a = top.symbol, tokens[pos]
        if X == END:                     # pila vacía: aceptar si la entrada también terminó
            return (True, root) if a == END else (False, None)
        if is_terminal(X):
            if X != a:
                return False, None
            top.attrs['lexval'] = X      # el lexval de un terminal es el propio carácter
            stack.pop()
            pos += 1
        else:
            entry = table.get((X, a))
            if not entry:
                return False, None       # celda vacía: error de sintaxis
            idx = entry[0]
            _, body = prods[idx]
            stack.pop()
            top.production = idx
            top.children = [Node(s) for s in body]   # ε => sin hijos
            for child in reversed(top.children):
                stack.append(child)
