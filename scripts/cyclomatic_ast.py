"""Cyclomatic complexity per function, counted like SonarQube's Python rules:
+1 per function/lambda, +1 per if/elif, for, while, except, with-less constructs,
+1 per boolean operator (and/or) operand beyond the first, +1 per comprehension 'if'/'for',
+1 per ternary, +1 per match case."""
import ast, sys

def score(node):
    c = 0
    for n in ast.walk(node):
        if n is node: continue
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)): c += 1
        elif isinstance(n, (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)): c += 1
        elif isinstance(n, ast.BoolOp): c += len(n.values) - 1
        elif isinstance(n, ast.comprehension): c += 1 + len(n.ifs)
        elif isinstance(n, ast.match_case): c += 1
    return c

path = sys.argv[1]
tree = ast.parse(open(path, encoding="utf-8").read())
total = 0
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        s = 1 + score(n); 
        if len(sys.argv) > 2 and n.name == sys.argv[2]: print(f"{n.name}: V(G)={s}")
# file total: functions counted once each, with nested decisions counted inside their own function
file_total = sum(1 for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)))
file_total += sum(1 for n in ast.walk(tree) if isinstance(n,(ast.If,ast.IfExp,ast.For,ast.AsyncFor,ast.While,ast.ExceptHandler)))
file_total += sum(len(n.values)-1 for n in ast.walk(tree) if isinstance(n,ast.BoolOp))
file_total += sum(1+len(n.ifs) for n in ast.walk(tree) if isinstance(n,ast.comprehension))
print(f"file total (Sonar-style): {file_total}")
