"""Programa de prueba de la Persona A (provisional: la B hará el programa principal
con los 4 casos y el parser SLR(1)).  Uso:  python3 ll1_cli.py [--sets] < entrada.txt"""
import sys
from common import read_grammar, normalize_input
from first_follow import compute_first, compute_follow, sets_lines
from ll1 import is_ll1_condition, build_ll1_table, table_has_conflicts, ll1_parse

grammar = read_grammar(sys.stdin)
first = compute_first(grammar)
follow = compute_follow(grammar, first)
if '--sets' in sys.argv:
    print("\n".join(sets_lines(grammar, first, follow)))

table = build_ll1_table(grammar, first, follow)
assert is_ll1_condition(grammar, first, follow) == (not table_has_conflicts(table))
if table_has_conflicts(table):
    print("Grammar is NOT LL(1) (aquí la B decidiría si es SLR(1)).")
    sys.exit()
print("Grammar is LL(1).")
for line in sys.stdin:
    if line.strip() == '':
        break
    ok, _ = ll1_parse(grammar, table, normalize_input(line))
    print("yes" if ok else "no")
