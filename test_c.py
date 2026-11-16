"""Pruebas de la Persona C (Ítem 3).  Ejecutar:  python3 test_c.py"""
import io

import my_sdd
from common import read_grammar
from sdd_eval import CircularSDD, evaluate, make_parser, validate_sdd

GRAMMAR = read_grammar(io.StringIO(my_sdd.GRAMMAR_TEXT))
LL1 = make_parser(GRAMMAR, use_slr=False)
SLR = make_parser(GRAMMAR, use_slr=True)

# (cadena, valor esperado de S.err; None = la cadena no pertenece al lenguaje)
CASES = [
    ('[]', 0),                  # la más corta del lenguaje
    ('[dxux]', 0),              # declarar antes de usar
    ('[uxdx]', 1),              # usar antes de declarar
    ('[[dx]ux]', 1),            # lo declarado en un bloque interno no se ve afuera
    ('[dx[[[[ux]]]]uy]', 1),    # anidamiento profundo
    ('[dxuy]', 1),              # ejemplo a mano del informe
    ('[dx', None),              # fuera del lenguaje: bloque sin cerrar
    ('', None),                 # cadena vacía (línea 'e'): fuera del lenguaje
]


def err_of(parse, string, sdd=my_sdd.SDD):
    ok, tree = parse(string)
    if not ok:
        return None
    evaluate(GRAMMAR, tree, sdd)
    return tree.attrs[my_sdd.MAIN_ATTR]


def shape(node):
    """Estructura del árbol sin atributos, para comparar los dos parsers."""
    return (node.symbol, node.production, [shape(c) for c in node.children])


# 1. El SDD cumple las condiciones de 5.1.1. La variante circular también: el ciclo
#    no se ve en una producción sola, solo en el grafo de un árbol concreto.
assert validate_sdd(GRAMMAR, my_sdd.SDD, my_sdd.ATTR_KINDS) == []
assert validate_sdd(GRAMMAR, my_sdd.SDD_CIRCULAR, my_sdd.ATTR_KINDS) == []

# 2. La gramática es LL(1) y SLR(1).
assert LL1 is not None and SLR is not None

# 3. Valores esperados con los dos parsers, y el mismo árbol con ambos.
for string, expected in CASES:
    for name, parse in (('LL(1)', LL1), ('SLR(1)', SLR)):
        got = err_of(parse, string)
        assert got == expected, f'{name} {string!r}: expected {expected}, got {got}'
    ok1, tree1 = LL1(string)
    ok2, tree2 = SLR(string)
    assert ok1 == ok2 and (not ok1 or shape(tree1) == shape(tree2)), f'different trees for {string!r}'

# 4. Circularidad: con u aparece el ciclo I.env -> I.err -> I.env; con [dx] no.
try:
    err_of(LL1, '[ux]', my_sdd.SDD_CIRCULAR)
    raise AssertionError('[ux] should be circular')
except CircularSDD:
    pass
assert err_of(LL1, '[dx]', my_sdd.SDD_CIRCULAR) == 0

# 5. Anidamiento muy profundo (2000 bloques): el evaluador no usa recursión.
deep = '[dx' + '[' * 2000 + 'ux' + ']' * 2000 + ']'
assert err_of(LL1, deep) == 0

print('todas las pruebas de C pasan')
