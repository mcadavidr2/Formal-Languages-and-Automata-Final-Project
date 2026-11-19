# Formal Languages and Compilers — Final Project (2026-2)

Implementation of FIRST/FOLLOW sets, table-driven LL(1) and SLR(1) parsers,
and a syntax-directed definition (SDD) evaluator based on dependency graphs.
The algorithms follow Aho et al., *Compilers: Principles, Techniques, and Tools*,
2nd edition, sections 4.4, 4.5, 4.6, 5.1 and 5.2.

## Group members

- Mateo Cadavid Ramírez
- Daniel Alejandro Cruz Jaimes
- Juan Sebastián Rave Martínez

## Requirements and verified environment

Only the Python standard library is required. There is no build step, package
installation or parser generator. Run the commands from the repository root.

The commands and examples below were verified in this environment:

| Component | Version |
|---|---|
| Operating system | Microsoft Windows, OS version 10.0.26300, 64-bit |
| Python | CPython 3.11.4, 64-bit |
| Git | 2.56.0.windows.2 |
| Windows PowerShell | 5.1.26100.9818 |

Commands use `python` to mean a working Python 3 interpreter. Check it with:

```text
python --version
```

If your interpreter is available as `python3` or `py -3`, use that command instead.
In PowerShell, a full executable path is invoked with
`& "C:\path\to\python.exe"`.
The shell-specific file-input forms are shown below; the verified environment
listed above is Windows.

## Files

| File | Purpose |
|---|---|
| [common.py](common.py) | Grammar reader, constants, production numbering and shared parse-tree nodes |
| [first_follow.py](first_follow.py) | FIRST/FOLLOW computation and formatted `--sets` output |
| [ll1.py](ll1.py) | Explicit LL(1) condition, predictive table and non-recursive parser |
| [slr.py](slr.py) | Augmentation, LR(0) items, CLOSURE/GOTO, canonical collection, SLR tables, conflicts and parser |
| [main.py](main.py) | Entry point for Items 1 and 2 and the four classification cases |
| [my_sdd.py](my_sdd.py) | Scope-checking grammar, attributes and semantic rules stored as data |
| [sdd_eval.py](sdd_eval.py) | Item 3 evaluator: dependency graph, topological order and cycle detection |
| [ll1_cli.py](ll1_cli.py) | Auxiliary LL(1)-only command-line program |
| [test_a.py](test_a.py), [test_c.py](test_c.py) | Included automated tests |
| [entrada.txt](entrada.txt) | Input for the auxiliary LL(1) program |
| [cadenas_sdd.txt](cadenas_sdd.txt) | Sample strings for the SDD evaluator |

## Items 1 and 2: grammar analysis and parsing

Start the main program interactively:

```text
python -B main.py
```

To print FIRST and FOLLOW before the normal parser output:

```text
python -B main.py --sets
```

### Input conventions

1. Enter the number of nonterminals, followed by one production line per

   nonterminal. Each head appears exactly once.
2. Nonterminals are single uppercase letters. The start symbol is always

   `S`; its line need not be first. All nonterminals must derive a terminal string.
3. Alternatives are separated by spaces, without a `|` separator.

   For example, `B -> bBc e` means two alternatives.
4. Terminals are single characters other than uppercase letters, whitespace,

   `e` or `$`. Write `e` for an epsilon production.
5. Enter strings one per line, without `$`; the parser appends it internally.

   A line containing only `e` represents the empty string.
6. An empty line ends the current parsing session. End-of-file also ends input.

The input grammar is classified without removing left recursion or otherwise
rewriting its productions. LL(1) classification uses the explicit condition
of section 4.4.3. SLR(1) classification requires an ACTION table without conflicts.

### Classification and output

| Classification | Exact initial message | Behavior |
|---|---|---|
| Both LL(1) and SLR(1) | `Select a parser (T: for LL(1), B: for SLR(1), Q: quit):` | Choose `T` or `B`; an empty line returns to the menu; `Q` quits |
| LL(1) only | `Grammar is LL(1).` | Parse with LL(1) until an empty line or EOF |
| SLR(1) only | `Grammar is SLR(1).` | Parse with SLR(1) until an empty line or EOF |
| Neither | `Grammar is neither LL(1) nor SLR(1).` | Exit |

Menu selections are case-insensitive. An invalid selection repeats the menu.
Each parsed string produces exactly `yes` or `no`, on its own line.

### Complete example: both parsers

After starting `main.py`, enter the following. Keep the empty lines before
`B` and `Q`: they end the two parsing sessions.

```text
3
S -> AB
A -> aA d
B -> bBc e
T
d
adbc
a

B
d
adbc
a

Q
```

Expected standard output, excluding the input echoed by an interactive terminal:

```text
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
yes
yes
no
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
yes
yes
no
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
```

With `--sets`, these lines precede that output:

```text
First(A) = {a, d}
First(B) = {b, e}
First(S) = {a, d}
Follow(A) = {b, $}
Follow(B) = {c, $}
Follow(S) = {$}
```

All FIRST lines appear before all FOLLOW lines, with nonterminals in alphabetical
order. Inside each set, terminals are in ASCII order, followed by `e` and then
`$` when present.

### Reading from a file

Save the complete example above as `parser_input.txt`, including its menu choices.
That file is an example you can create; it is not a bundled input file.

In a POSIX shell or Windows Command Prompt:

```text
python -B main.py < parser_input.txt
python -B main.py --sets < parser_input.txt
```

In Windows PowerShell:

```powershell
Get-Content -LiteralPath parser_input.txt | python -B main.py --sets
```

The bundled `entrada.txt` has no menu selection. Use it with the auxiliary
LL(1) program:

```powershell
Get-Content -LiteralPath entrada.txt | python -B ll1_cli.py --sets
```

To adapt that file for `main.py`, insert `T` or `B` after the grammar lines,
as in the complete example.

## Item 3: syntax-directed evaluation

The selected language contains blocks with declarations and uses of variables:

```text
5
S -> B
B -> [L]
L -> IL e
I -> dV uV B
V -> x y
```

`dx` declares variable `x`, and `ux` uses it; the same applies to `y`.
Declarations are visible after their declaration, in the current block and its
nested blocks. Declarations inside a nested block do not escape that block.
The main synthesized attribute, `S.err`, counts uses of undeclared variables.

The grammar has five nonterminals, nine productions and recursion, and is both
LL(1) and SLR(1). Its SDD has inherited environments and synthesized results.
It is L-attributed and is not S-attributed. Evaluation still uses the general
dependency-graph method: edges go from used attributes to defined attributes,
and Kahn's algorithm determines the evaluation order.

### Running the evaluator

For interactive input, run:

```text
python -B sdd_eval.py
```

Enter one string per line and finish with an empty line or EOF.
Use `--slr` to build the tree with SLR(1); LL(1) is the default.

In a POSIX shell or Windows Command Prompt:

```text
python -B sdd_eval.py < cadenas_sdd.txt
python -B sdd_eval.py --slr < cadenas_sdd.txt
```

In Windows PowerShell:

```powershell
Get-Content -LiteralPath cadenas_sdd.txt | python -B sdd_eval.py
Get-Content -LiteralPath cadenas_sdd.txt | python -B sdd_eval.py --slr
```

For a syntactically invalid string, the program prints `no`. Otherwise, it prints
the annotated parse tree, one node per line with indentation, the evaluation order,
and the value of `S.err`. A valid string can have `S.err > 0`; such a string
still produces a tree and an error count.

| Input line | Result |
|---|---|
| `[]` | `S.err = 0`; shortest string in the language |
| `[dxux]` | `S.err = 0` |
| `[uxdx]` | `S.err = 1`; use before declaration |
| `[[dx]ux]` | `S.err = 1`; inner declaration is not visible outside |
| `[dx[[[[ux]]]]uy]` | `S.err = 1`; nested use of `x` is valid, `y` is undeclared |
| `[dx` | `no`; missing closing bracket |
| `[dxuy]` | `S.err = 1` |
| `e` | `no`; the empty string is outside this language |

The first seven inputs are bundled in `cadenas_sdd.txt`.

### Circularity demonstration

Run:

```text
python -B sdd_eval.py --circular
```

Enter `[ux]` and then an empty line. Expected output:

```text
SDD is circular: I#4.err -> I#4.env -> I#4.err
```

This option selects `SDD_CIRCULAR`, a variant where `I.env` also depends on
`I.err`. The dependency cycle prevents evaluation of that tree and is reported
before any semantic result is produced.

### SDD data interface

The evaluator accepts `--sdd=module_name` to load another importable data module.
It must expose `GRAMMAR_TEXT`, `ATTR_KINDS`, `SDD` and `MAIN_ATTR`;
`SDD_CIRCULAR` is also needed when `--circular` is used.
Each rule records `defines`, `uses` and its computing function `fn`.
Position 0 denotes the production head; position k denotes the k-th body symbol.
Changing the SDD requires changing this data, not the evaluator.

## Shared parsing contracts

- Production indices start at zero and follow grammar input order. The augmented
production is appended after the original productions, preserving their indices.
- An epsilon body is an empty list. Its parse-tree node has no children.
- Both parsers return `(True, tree)` on acceptance and `(False, None)` on rejection.
- Tree nodes share `Node(symbol, production, children, attrs)`. Children keep
production order; terminal nodes have `production=None` and
`attrs['lexval']` equal to the character.
- Parsers receive normalized strings without `$` and append the end marker internally.
SLR reductions use original production indices and FOLLOW of the original grammar.

## Tests

Run the included tests from the repository root:

```text
python -B test_a.py
python -B test_c.py
```

Successful runs print `todas las pruebas de A pasan` and
`todas las pruebas de C pasan`, respectively.
They check FIRST/FOLLOW, parsing results, epsilon, SDD validation, agreement between
both parsers' trees and semantic results, circularity, and 2,000 nested blocks.

## Use of generative AI

### Claude (Anthropic)

Claude was used to summarize the assignment, propose the work distribution,
schedule and shared interfaces, and draft the
internal instruction documents. It generated initial versions of `common.py`,
`first_follow.py`, `ll1.py`, `ll1_cli.py` and `test_a.py`.
It also provided PowerShell execution guidance and drafts of project documentation.

For the SDD work, Claude was used to propose the grammar and SDD, generate
`my_sdd.py`, `sdd_eval.py` and `test_c.py`, explain book sections 5.1 and 5.2,
and draft the README and the corresponding report section.
**The final decision on the grammar and SDD was made by the team.**

### Codex / ChatGPT (OpenAI)

Codex was used to inspect the reference documents and integration contracts,  
design and propose the LR(0)/SLR(1) implementation in `slr.py`.

It also executed validation checks, compared parse trees with the book's examples, and assisted in developing the final report using LaTeX.

**The team remains responsible for the submitted code and text, for understanding
and defending every component, and for the book reading and hand-worked examples
required by the assignment. Program-generated traces do not replace those examples.**

## References

Aho, A. V., Lam, M. S., Sethi, R., and Ullman, J. D.
*Compilers: Principles, Techniques, and Tools*, 2nd edition.
Addison-Wesley, 2006.

| Component | Book reference |
|---|---|
| FIRST/FOLLOW | Section 4.4.2 |
| LL(1) condition and table | Section 4.4.3, Algorithm 4.31 |
| Predictive parser | Section 4.4.4, Algorithm 4.34 |
| Shift-reduce parsing and conflicts | Section 4.5, especially 4.5.4 |
| LR(0) items, CLOSURE/GOTO and collection | Section 4.6.2, Figures 4.32–4.33 |
| LR parser | Section 4.6.3, Algorithm 4.44 |
| SLR table construction | Section 4.6.4, Algorithm 4.46 |
| SDD attributes and annotated trees | Sections 5.1.1–5.1.2 |
| Dependency graphs and evaluation order | Sections 5.2.1–5.2.2 |
| S-attributed and L-attributed definitions | Sections 5.2.3–5.2.4 |
