from common import END, START, Node, is_nonterminal, productions

def augment_grammar(grammar):
    """Devuelve (prods aumentadas, índice aumentado)."""
    prods = [(head, list(body)) for head, body in productions(grammar)]
    augmented_index = len(prods)
    prods.append((START + "'", [START]))
    return prods, augmented_index


def closure(items, grammar, prods):
    """Devuelve el cierre como frozenset."""
    result = set(items)
    while True:
        additions = set()
        for production_index, dot in result:
            _, body = prods[production_index]
            if dot < len(body) and is_nonterminal(body[dot]):
                nonterminal = body[dot]
                for index, (head, _) in enumerate(prods):
                    if head == nonterminal:
                        additions.add((index, 0))
        if additions <= result:
            return frozenset(result)
        # Actualizar al terminar la ronda evita mutar el conjunto recorrido.
        result.update(additions)


def goto(items, X, grammar, prods):
    """Devuelve GOTO(items, X) como frozenset."""
    advanced = set()
    for production_index, dot in items:
        _, body = prods[production_index]
        if dot < len(body) and body[dot] == X:
            advanced.add((production_index, dot + 1))
    return closure(advanced, grammar, prods)


def canonical_collection(grammar, prods):
    """Devuelve (tupla de estados, transiciones) para prods ya aumentada."""
    original_prods = productions(grammar)
    augmented_index = len(original_prods)
    if prods != original_prods + [(START + "'", [START])]:
        raise ValueError(
            "prods debe contener las originales y una sola aumentada al final"
        )

    initial = closure({(augmented_index, 0)}, grammar, prods)
    states = [initial]
    state_ids = {initial: 0}
    transitions = {}
    cursor = 0
    while cursor < len(states):
        state = states[cursor]
        symbols = set()
        for production_index, dot in state:
            _, body = prods[production_index]
            if dot < len(body):
                symbols.add(body[dot])

        # El orden del frozenset no debe determinar los números de estado.
        for symbol in sorted(symbols):
            target = goto(state, symbol, grammar, prods)
            if not target:
                continue
            if target not in state_ids:
                state_ids[target] = len(states)
                states.append(target)
            transitions[(cursor, symbol)] = state_ids[target]
        cursor += 1
    return tuple(states), transitions


def build_slr_tables(prods, states, transitions, follow):
    """Devuelve (ACTION, GOTO, conflictos) con FOLLOW de la gramática original."""
    action = {}
    goto_table = {
        (i, X): j for (i, X), j in sorted(transitions.items()) if is_nonterminal(X)
    }
    conflicts = []
    augmented_index = len(prods) - 1
    for i, state in enumerate(states):
        for idx, dot in sorted(state):
            A, body = prods[idx]
            if dot < len(body):
                a = body[dot]
                if is_nonterminal(a):
                    continue
                proposed = ('shift', transitions[(i, a)])
                symbols = [a]
            elif idx == augmented_index:
                proposed = ('accept',)
                symbols = [END]
            else:
                proposed = ('reduce', idx)
                symbols = sorted(follow[A])

            for a in symbols:
                existing = action.get((i, a))
                if existing is None:
                    action[(i, a)] = proposed
                elif existing != proposed:
                    kind = '/'.join(sorted((existing[0], proposed[0]), reverse=True))
                    conflicts.append({
                        'state': i, 'symbol': a, 'existing': existing,
                        'proposed': proposed, 'type': kind,
                    })
    return action, goto_table, conflicts


def slr_parse(grammar, tables, string):
    """Devuelve (ok, árbol) al analizar string con las tablas SLR(1)."""
    prods = productions(grammar)
    action, goto_table = tables
    tokens = list(string) + [END]
    stack = [(0, None)]
    pos = 0
    while True:
        state, a = stack[-1][0], tokens[pos]
        act = action.get((state, a))
        if act is None:
            return False, None
        if act[0] == 'shift':
            node = Node(a, None, [], {'lexval': a})
            stack.append((act[1], node))
            pos += 1
        elif act[0] == 'reduce':
            idx = act[1]
            head, body = prods[idx]
            n = len(body)
            children = [node for _, node in stack[len(stack) - n:]]
            del stack[len(stack) - n:]
            node = Node(head, idx, children, {})
            state = goto_table[(stack[-1][0], head)]
            stack.append((state, node))
        elif act[0] == 'accept':
            return True, stack[-1][1]
