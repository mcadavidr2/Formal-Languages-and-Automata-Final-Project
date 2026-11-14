"""Pruebas de la Persona A.  Ejecutar:  python3 test_a.py"""
import io
from common import read_grammar, normalize_input
from first_follow import compute_first, compute_follow, sets_lines
from ll1 import is_ll1_condition, build_ll1_table, table_has_conflicts, ll1_parse


def load(text):
    g = read_grammar(io.StringIO(text))
    f = compute_first(g)
    fo = compute_follow(g, f)
    return g, f, fo


def check_sets(text, expected):
    g, f, fo = load(text)
    got = sets_lines(g, f, fo)
    assert got == expected, "\n".join(got)


# Ejemplo 2 del PDF (a mano: First(B)={b,e}, Follow(B)={c,$}, ...)
EX2 = "3\nS -> AB\nA -> aA d\nB -> bBc e\n"
check_sets(EX2, ["First(A) = {a, d}", "First(B) = {b, e}", "First(S) = {a, d}",
                 "Follow(A) = {b, $}", "Follow(B) = {c, $}", "Follow(S) = {$}"])

# Muchas producciones ε (a mano): First(S)={a,b,e}, Follow(A)={b,$}, Follow(B)={$}
check_sets("3\nS -> AB\nA -> e a\nB -> e b\n",
           ["First(A) = {a, e}", "First(B) = {b, e}", "First(S) = {a, b, e}",
            "Follow(A) = {b, $}", "Follow(B) = {$}", "Follow(S) = {$}"])

# Gramática de expresiones del libro (Ej. 4.28): S=E, R=E', T=T, Y=T', F=F
EXPR = "5\nS -> TR\nR -> +TR e\nT -> FY\nY -> *FY e\nF -> (S) i\n"
check_sets(EXPR, ["First(F) = {(, i}", "First(R) = {+, e}", "First(S) = {(, i}",
                  "First(T) = {(, i}", "First(Y) = {*, e}",
                  "Follow(F) = {), *, +, $}", "Follow(R) = {), $}", "Follow(S) = {), $}",
                  "Follow(T) = {), +, $}", "Follow(Y) = {), +, $}"])


def ll1_run(text, strings):
    g, f, fo = load(text)
    t = build_ll1_table(g, f, fo)
    assert is_ll1_condition(g, f, fo) == (not table_has_conflicts(t))
    return not table_has_conflicts(t), [ll1_parse(g, t, normalize_input(s))[0] for s in strings]


# Ejemplo 2: LL(1); d yes, adbc yes, a no
ok, res = ll1_run(EX2, ["d", "adbc", "a"])
assert ok and res == [True, True, False], (ok, res)

# Expresiones LL(1)
ok, res = ll1_run(EXPR, ["i+i*i", "(i)", "(i+i)*i", "i+", "(i", "", "e"])
assert ok and res == [True, True, True, False, False, False, False], res

# Ejemplo 1 (recursiva por la izquierda) y 3: NO LL(1)
assert not ll1_run("3\nS -> S+T T\nT -> T*F F\nF -> (S) i\n", [])[0]
assert not ll1_run("1\nS -> SS a\n", [])[0]

# Cadena vacía con ε-producciones: S -> aS e acepta 'e' (cadena vacía)
ok, res = ll1_run("1\nS -> aS e\n", ["e", "a", "aaa", "ab"])
assert ok and res == [True, True, True, False], res

print("todas las pruebas de A pasan")
