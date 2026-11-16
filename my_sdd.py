"""SDD propio del Ítem 3: verificación de alcance de variables.

Lenguaje: bloques [ ... ] donde dx declara la variable x y ux la usa (igual con y).
Atributo principal: S.err = número de usos de variables no declaradas.

Este archivo es solo DATOS. El evaluador general (sdd_eval.py) no sabe nada de
este SDD: cambiar de SDD solo exige cambiar este archivo.
"""

GRAMMAR_TEXT = """5
S -> B
B -> [L]
L -> IL e
I -> dV uV B
V -> x y
"""

# Numeración de productions(grammar), en orden de lectura (contrato del equipo):
#   0: S -> B        1: B -> [ L ]     2: L -> I L      3: L -> e
#   4: I -> d V      5: I -> u V       6: I -> B        7: V -> x      8: V -> y
# Posiciones en cada regla: 0 = la cabeza; k = el k-ésimo símbolo del cuerpo.

# Clase de cada atributo: 'syn' = sintetizado, 'inh' = heredado.
# Los terminales solo tienen lexval, que lo pone el parser.
ATTR_KINDS = {
    'S': {'err': 'syn'},
    'B': {'env': 'inh', 'err': 'syn'},
    'L': {'env': 'inh', 'err': 'syn'},
    'I': {'env': 'inh', 'decl': 'syn', 'err': 'syn'},
    'V': {'name': 'syn'},
}

MAIN_ATTR = 'err'

EMPTY = frozenset()   # conjunto vacío inmutable: ningún nodo puede modificar el de otro

SDD = {
    # 0: S -> B          B.env = {} ; S.err = B.err
    0: [
        {'defines': (1, 'env'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(1, 'err')], 'fn': lambda err: err},
    ],
    # 1: B -> [ L ]      L.env = B.env ; B.err = L.err      (L está en la posición 2)
    1: [
        {'defines': (2, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (0, 'err'), 'uses': [(2, 'err')], 'fn': lambda err: err},
    ],
    # 2: L -> I L1       I.env = L.env ; L1.env = L.env U I.decl ; L.err = I.err + L1.err
    2: [
        {'defines': (1, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (2, 'env'), 'uses': [(0, 'env'), (1, 'decl')],
         'fn': lambda env, decl: env | decl},
        {'defines': (0, 'err'), 'uses': [(1, 'err'), (2, 'err')],
         'fn': lambda err1, err2: err1 + err2},
    ],
    # 3: L -> e          L.err = 0
    3: [
        {'defines': (0, 'err'), 'uses': [], 'fn': lambda: 0},
    ],
    # 4: I -> d V        I.decl = {V.name} ; I.err = 0
    4: [
        {'defines': (0, 'decl'), 'uses': [(2, 'name')], 'fn': lambda name: frozenset([name])},
        {'defines': (0, 'err'), 'uses': [], 'fn': lambda: 0},
    ],
    # 5: I -> u V        I.decl = {} ; I.err = 0 si V.name está en I.env, si no 1
    5: [
        {'defines': (0, 'decl'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(0, 'env'), (2, 'name')],
         'fn': lambda env, name: 0 if name in env else 1},
    ],
    # 6: I -> B          B.env = I.env ; I.decl = {} ; I.err = B.err
    6: [
        {'defines': (1, 'env'), 'uses': [(0, 'env')], 'fn': lambda env: env},
        {'defines': (0, 'decl'), 'uses': [], 'fn': lambda: EMPTY},
        {'defines': (0, 'err'), 'uses': [(1, 'err')], 'fn': lambda err: err},
    ],
    # 7: V -> x          V.name = x.lexval
    7: [
        {'defines': (0, 'name'), 'uses': [(1, 'lexval')], 'fn': lambda c: c},
    ],
    # 8: V -> y          V.name = y.lexval
    8: [
        {'defines': (0, 'name'), 'uses': [(1, 'lexval')], 'fn': lambda c: c},
    ],
}

# Variante CIRCULAR, solo para la demostración del Paso 6:  python sdd_eval.py --circular
# En la producción 2 (L -> I L1), I.env pasa a usar también I.err. Como en I -> u V
# el err depende del env, queda el ciclo I.env -> I.err -> I.env. Aparece en cualquier
# cadena con u; con [dx] no hay ciclo y la evaluación funciona normal.
SDD_CIRCULAR = dict(SDD)
SDD_CIRCULAR[2] = [
    {'defines': (1, 'env'), 'uses': [(0, 'env'), (1, 'err')],
     'fn': lambda env, err: env if err == 0 else EMPTY},
] + SDD[2][1:]
