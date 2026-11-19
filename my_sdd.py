GRAMMAR_TEXT = """5
S -> B
B -> [L]
L -> IL e
I -> dV uV B
V -> x y
"""


ATTR_KINDS = {
    'S': {'err': 'syn'},
    'B': {'env': 'inh', 'err': 'syn'},
    'L': {'env': 'inh', 'err': 'syn'},
    'I': {'env': 'inh', 'decl': 'syn', 'err': 'syn'},
    'V': {'name': 'syn'},
}

MAIN_ATTR = 'err'

EMPTY = frozenset()

SDD = {
    0: [
        {'defines': (1, 'env'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(1, 'err')], 'fn': lambda err: err},
    ],
    1: [
        {'defines': (2, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (0, 'err'), 'uses': [(2, 'err')], 'fn': lambda err: err},
    ],
    2: [
        {'defines': (1, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (2, 'env'), 'uses': [(0, 'env'), (1, 'decl')],
         'fn': lambda env, decl: env | decl},
        {'defines': (0, 'err'), 'uses': [(1, 'err'), (2, 'err')],
         'fn': lambda err1, err2: err1 + err2},
    ],
    3: [
        {'defines': (0, 'err'), 'uses': [], 'fn': lambda: 0},
    ],
    4: [
        {'defines': (0, 'decl'), 'uses': [(2, 'name')], 'fn': lambda name: frozenset([name])},
        {'defines': (0, 'err'), 'uses': [], 'fn': lambda: 0},
    ],
    5: [
        {'defines': (0, 'decl'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(0, 'env'), (2, 'name')],
         'fn': lambda env, name: 0 if name in env else 1},
    ],
    6: [
        {'defines': (1, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (0, 'decl'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(1, 'err')], 'fn': lambda err: err},
    ],
    7: [
        {'defines': (0, 'name'), 'uses': [(1, 'lexval')], 'fn': lambda c: c},
    ],
    8: [
        {'defines': (0, 'name'), 'uses': [(1, 'lexval')], 'fn': lambda c: c},
    ],
}

SDD_CIRCULAR = dict(SDD)
SDD_CIRCULAR[2] = [
    {'defines': (1, 'env'), 'uses': [(0, 'env'), (1, 'err')],
     'fn': lambda env, err: env if err == 0 else EMPTY},
] + SDD[2][1:]
