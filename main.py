import sys

from common import normalize_input, read_grammar
from first_follow import compute_first, compute_follow, sets_lines
from ll1 import build_ll1_table, is_ll1_condition, ll1_parse
from slr import augment_grammar, build_slr_tables, canonical_collection, slr_parse


MENU = 'Select a parser (T: for LL(1), B: for SLR(1), Q: quit):'


def _parse_session(grammar, table, parse):
    """Devuelve True al recibir una línea vacía y False al llegar a EOF."""
    for line in sys.stdin:
        if not line.strip():
            return True
        ok, _ = parse(grammar, table, normalize_input(line))
        print('yes' if ok else 'no')
    return False


if __name__ == '__main__':
    grammar = read_grammar(sys.stdin)
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)
    if '--sets' in sys.argv:
        print('\n'.join(sets_lines(grammar, first, follow)))

    ll1_table = build_ll1_table(grammar, first, follow)
    is_ll1 = is_ll1_condition(grammar, first, follow)
    prods, _ = augment_grammar(grammar)
    states, transitions = canonical_collection(grammar, prods)
    action, goto_table, conflicts = build_slr_tables(prods, states, transitions, follow)
    slr_tables = action, goto_table

    if is_ll1 and not conflicts:
        parsers = {'T': (ll1_parse, ll1_table), 'B': (slr_parse, slr_tables)}
        while True:
            print(MENU)
            choice = sys.stdin.readline()
            if not choice:
                break
            choice = choice.strip().upper()
            if choice == 'Q':
                break
            if choice in parsers:
                parse, table = parsers[choice]
                if not _parse_session(grammar, table, parse):
                    break
    elif is_ll1:
        print('Grammar is LL(1).')
        _parse_session(grammar, ll1_table, ll1_parse)
    elif not conflicts:
        print('Grammar is SLR(1).')
        _parse_session(grammar, slr_tables, slr_parse)
    else:
        print('Grammar is neither LL(1) nor SLR(1).')
