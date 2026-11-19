import importlib
import io
import sys
from collections import deque

from common import START, is_nonterminal, normalize_input, productions, read_grammar
from first_follow import compute_first, compute_follow
from ll1 import build_ll1_table, is_ll1_condition, ll1_parse
from slr import augment_grammar, build_slr_tables, canonical_collection, slr_parse


class CircularSDD(Exception):
    """El grafo de dependencias del árbol tiene un ciclo: no hay orden topológico."""


def has_attr(symbol, attr, attr_kinds):
    """Devuelve si el símbolo admite el atributo."""
    if is_nonterminal(symbol):
        return attr in attr_kinds.get(symbol, {})
    return attr == 'lexval'


def validate_sdd(grammar, sdd, attr_kinds):
    """Devuelve los problemas encontrados en las reglas semánticas."""
    problems = []
    prods = productions(grammar)
    if any(kind == 'inh' for kind in attr_kinds.get(START, {}).values()):
        problems.append(f'{START} must not have inherited attributes')
    for idx in sdd:
        if not 0 <= idx < len(prods):
            problems.append(f'production {idx} does not exist')
    for idx, (head, body) in enumerate(prods):
        symbols = [head] + list(body)
        where = f'production {idx} ({head} -> {"".join(body) or "e"})'
        defined = []
        for rule in sdd.get(idx, []):
            for pos, attr in [rule['defines']] + list(rule['uses']):
                if not 0 <= pos < len(symbols):
                    problems.append(f'{where}: position {pos} does not exist')
                elif not has_attr(symbols[pos], attr, attr_kinds):
                    problems.append(f'{where}: {symbols[pos]} has no attribute {attr}')
            pos, attr = rule['defines']
            kind = attr_kinds.get(symbols[pos], {}).get(attr) if 0 <= pos < len(symbols) else None
            if pos == 0 and kind != 'syn':
                problems.append(f'{where}: the head can only get synthesized attributes ({attr})')
            if pos > 0 and kind != 'inh':
                problems.append(f'{where}: the body can only get inherited attributes ({attr})')
            defined.append((pos, attr))
        needed = [(0, a) for a, k in attr_kinds.get(head, {}).items() if k == 'syn']
        for pos, sym in enumerate(body, start=1):
            if is_nonterminal(sym):
                needed += [(pos, a) for a, k in attr_kinds.get(sym, {}).items() if k == 'inh']
        for pos, attr in needed:
            count = defined.count((pos, attr))
            if count != 1:
                problems.append(f'{where}: {symbols[pos]}.{attr} is defined {count} times (must be 1)')
    return problems


def child_at(node, pos):
    """Devuelve el nodo en la posición indicada de una producción."""
    return node if pos == 0 else node.children[pos - 1]


def preorder(tree):
    """Devuelve los nodos del árbol en preorden."""
    nodes, stack = [], [tree]
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(reversed(node.children))
    return nodes


def label(nodes, vertex):
    """Devuelve la etiqueta de un atributo del árbol."""
    k, attr = vertex
    return f'{nodes[k].symbol}#{k}.{attr}'


def check_productions(grammar, nodes):
    """Devuelve None si los nodos corresponden a sus producciones."""
    prods = productions(grammar)
    for k, node in enumerate(nodes):
        if node.production is None:
            continue
        head, body = prods[node.production]
        if node.symbol != head or [c.symbol for c in node.children] != list(body):
            raise ValueError(f'node {node.symbol}#{k} does not match production {node.production}')


def build_graph(nodes, sdd):
    """Devuelve sucesores, grados de entrada y reglas por atributo."""
    number = {id(node): k for k, node in enumerate(nodes)}
    succ = {}
    indeg = {}
    rule_of = {}

    def add_vertex(v):
        if v not in succ:
            succ[v] = []
            indeg[v] = 0

    for k, node in enumerate(nodes):
        for attr in node.attrs:
            add_vertex((k, attr))

    for k, node in enumerate(nodes):
        if node.production is None:
            continue
        for rule in sdd.get(node.production, []):
            pos, attr = rule['defines']
            target = (number[id(child_at(node, pos))], attr)
            if target in rule_of:
                raise ValueError(f'{label(nodes, target)} is defined twice')
            add_vertex(target)
            used = []
            for upos, uattr in rule['uses']:
                source = (number[id(child_at(node, upos))], uattr)
                add_vertex(source)
                succ[source].append(target)
                indeg[target] += 1
                used.append(source)
            rule_of[target] = (rule['fn'], used)
    return succ, indeg, rule_of


def topological_order(succ, indeg):
    """Devuelve el orden topológico y los vértices pendientes."""
    indeg = dict(indeg)
    ready = deque(v for v in succ if indeg[v] == 0)
    order = []
    while ready:
        v = ready.popleft()
        order.append(v)
        for w in succ[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                ready.append(w)
    stuck = [v for v in succ if indeg[v] > 0]
    return order, stuck


def find_cycle(stuck, rule_of):
    """Devuelve un ciclo en la dirección de las dependencias."""
    stuck_set = set(stuck)
    path, position = [], {}
    v = stuck[0]
    while v not in position:
        position[v] = len(path)
        path.append(v)
        v = next(u for u in rule_of[v][1] if u in stuck_set)
    cycle = path[position[v]:] + [v]
    return cycle[::-1]


def evaluate(grammar, tree, sdd):
    """Devuelve los nodos anotados y el orden de evaluación."""
    nodes = preorder(tree)
    check_productions(grammar, nodes)
    for node in nodes:
        if node.production is not None:
            node.attrs = {}
    succ, indeg, rule_of = build_graph(nodes, sdd)
    order, stuck = topological_order(succ, indeg)
    if stuck:
        cycle = find_cycle(stuck, rule_of)
        raise CircularSDD(' -> '.join(label(nodes, v) for v in cycle))
    evaluated = []
    for k, attr in order:
        if (k, attr) not in rule_of:
            if attr not in nodes[k].attrs:
                raise ValueError(f'{label(nodes, (k, attr))} has no rule that defines it')
            continue
        fn, used = rule_of[(k, attr)]
        nodes[k].attrs[attr] = fn(*[nodes[uk].attrs[ua] for uk, ua in used])
        evaluated.append((k, attr))
    return nodes, evaluated


def fmt(value):
    """Devuelve el valor como texto con conjuntos ordenados."""
    if isinstance(value, (set, frozenset)):
        return '{' + ', '.join(sorted(map(str, value))) + '}'
    return str(value)


def tree_lines(nodes, attr_kinds=None):
    """Devuelve las líneas del árbol anotado."""
    attr_kinds = attr_kinds or {}
    depth = {id(nodes[0]): 0}
    lines = []
    for k, node in enumerate(nodes):
        d = depth[id(node)]
        names = [a for a in attr_kinds.get(node.symbol, {}) if a in node.attrs]
        names += [a for a in node.attrs if a not in names]
        text = '  '.join(f'{a}={fmt(node.attrs[a])}' for a in names)
        lines.append(f'{"  " * d}{node.symbol}#{k}  {text}'.rstrip())
        for child in node.children:
            depth[id(child)] = d + 1
        if node.production is not None and not node.children:
            lines.append('  ' * (d + 1) + 'e')
    return lines


def make_parser(grammar, use_slr=False):
    """Devuelve el parser elegido o None si la gramática no lo admite."""
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)
    if use_slr:
        prods, _ = augment_grammar(grammar)
        states, transitions = canonical_collection(grammar, prods)
        action, goto_table, conflicts = build_slr_tables(prods, states, transitions, follow)
        if conflicts:
            return None
        return lambda string: slr_parse(grammar, (action, goto_table), string)
    table = build_ll1_table(grammar, first, follow)
    if not is_ll1_condition(grammar, first, follow):
        return None
    return lambda string: ll1_parse(grammar, table, string)


def run(sdd_module, use_slr=False, circular=False, stream=sys.stdin):
    """Imprime la evaluación de las cadenas y devuelve None."""
    grammar = read_grammar(io.StringIO(sdd_module.GRAMMAR_TEXT))
    sdd = sdd_module.SDD_CIRCULAR if circular else sdd_module.SDD
    problems = validate_sdd(grammar, sdd, sdd_module.ATTR_KINDS)
    if problems:
        print('\n'.join('SDD error: ' + p for p in problems))
        return
    parse = make_parser(grammar, use_slr)
    if parse is None:
        print(f'The SDD grammar is not {"SLR(1)" if use_slr else "LL(1)"}.')
        return
    main_attr = sdd_module.MAIN_ATTR
    for line in stream:
        if not line.strip():
            break
        ok, tree = parse(normalize_input(line))
        if not ok:
            print('no')
        else:
            try:
                nodes, order = evaluate(grammar, tree, sdd)
            except CircularSDD as cycle:
                print(f'SDD is circular: {cycle}')
            else:
                print('\n'.join(tree_lines(nodes, sdd_module.ATTR_KINDS)))
                print('Evaluation order: ' + ', '.join(label(nodes, v) for v in order))
                print(f'{START}.{main_attr} = {fmt(tree.attrs[main_attr])}')
        print()


if __name__ == '__main__':
    args = sys.argv[1:]
    name = next((a.split('=', 1)[1] for a in args if a.startswith('--sdd=')), 'my_sdd')
    run(importlib.import_module(name), use_slr='--slr' in args, circular='--circular' in args)
