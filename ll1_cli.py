"""LL(1): condición §4.4.3 y parser predictivo §4.4.4."""
import sys
from common import read_grammar, normalize_input
from first_follow import compute_first, compute_follow, sets_lines
from ll1 import is_ll1_condition, build_ll1_table, ll1_parse

grammar = read_grammar(sys.stdin)
first = compute_first(grammar)
follow = compute_follow(grammar, first)
if '--sets' in sys.argv:
    print("\n".join(sets_lines(grammar, first, follow)))

table = build_ll1_table(grammar, first, follow)
if not is_ll1_condition(grammar, first, follow):
    print("Grammar is NOT LL(1).")
    sys.exit()
print("Grammar is LL(1).")
for line in sys.stdin:
    if line.strip() == '':
        break
    ok, _ = ll1_parse(grammar, table, normalize_input(line))
    print("yes" if ok else "no")
