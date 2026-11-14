"""Piezas compartidas por todo el equipo: constantes, Node y lector de gramática.

Representación acordada de la gramática:
    grammar = {'S': [['A','B']], 'A': [['a','A'], ['d']], 'B': [['b','B','c'], []]}
  - cada alternativa es una lista de símbolos
  - ε (la letra 'e' en la entrada) es la lista vacía []
  - el orden del diccionario y de las alternativas es el orden de lectura;
    las producciones se numeran en ese orden (ver productions()).
"""

EPS = 'e'    # así se escribe ε en la entrada y en los conjuntos impresos
END = '$'    # marcador de fin de cadena
START = 'S'  # el símbolo inicial siempre es S


def is_nonterminal(sym):
    return sym.isupper()


def is_terminal(sym):
    return not sym.isupper()


class Node:
    """Nodo del árbol de parseo (lo usan los dos parsers y el evaluador del SDD)."""

    def __init__(self, symbol, production=None, children=None, attrs=None):
        self.symbol = symbol                       # 'S', 'a', ...
        self.production = production               # índice de producción (None si es terminal)
        self.children = children if children is not None else []
        self.attrs = attrs if attrs is not None else {}   # ej. {'lexval': 'a'}

    def __repr__(self):
        return "Node(%r, prod=%r)" % (self.symbol, self.production)


def tree_to_str(node, depth=0):
    """Árbol con un nodo por línea, indentado por profundidad (útil para depurar)."""
    line = "  " * depth + node.symbol
    if node.production is not None:
        line += "   [prod %d]" % node.production
    out = [line]
    for c in node.children:
        out.append(tree_to_str(c, depth + 1))
    return "\n".join(out)


def read_grammar(stream):
    """Lee la gramática del formato del PDF (sección 2.2.1).

    Primera línea: n. Luego n líneas 'A -> alt1 alt2 ...'.
    Devuelve el diccionario grammar descrito arriba.
    """
    n = int(stream.readline().strip())
    grammar = {}
    for _ in range(n):
        line = stream.readline().strip()
        head, _, rhs = line.partition('->')
        head = head.strip()
        alts = []
        for alt in rhs.split():            # alternativas separadas por espacios
            alts.append([] if alt == EPS else list(alt))
        grammar[head] = alts
    return grammar


def productions(grammar):
    """Lista numerada de producciones [(cabeza, cuerpo), ...] en orden de lectura."""
    return [(head, body) for head, alts in grammar.items() for body in alts]


def normalize_input(line):
    """Una línea 'e' representa la cadena vacía (sección 2.2.2 del PDF)."""
    line = line.strip()
    return '' if line == EPS else line
