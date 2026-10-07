import ast
import re

class CodeEcoAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code):
        self.source_code = source_code
        self.issues = []
        self.current_loop_depth = 0
        self.loop_stack = []
        self.functions_defined = set()
        self.recursive_functions = set()
        self.memoized_functions = set()

    def analyze(self):
        self.issues = []
        self.current_loop_depth = 0
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
            self._post_analysis_checks()
        except SyntaxError as e:
            self.issues.append({
                "line": e.lineno or 1,
                "type": "SyntaxError",
                "severity": "High",
                "code": f"Syntax Error on line {e.lineno}",
                "message": f"Syntax error in submitted code: {e.msg}",
                "recommendation": "Fix syntax error to enable complete green energy analysis."
            })
        
        eco_score = self.calculate_eco_score()
        return {
            "eco_score": eco_score,
            "issues": self.issues,
            "issue_count": len(self.issues),
            "severity_summary": {
                "High": sum(1 for i in self.issues if i["severity"] == "High"),
                "Medium": sum(1 for i in self.issues if i["severity"] == "Medium"),
                "Low": sum(1 for i in self.issues if i["severity"] == "Low")
            }
        }

    def visit_FunctionDef(self, node):
        self.functions_defined.add(node.name)
        # Check if function has memoization decorator (@lru_cache or @cache)
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ('cache', 'lru_cache'):
                self.memoized_functions.add(node.name)
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id in ('cache', 'lru_cache'):
                self.memoized_functions.add(node.name)
            elif isinstance(decorator, ast.Attribute) and decorator.attr in ('cache', 'lru_cache'):
                self.memoized_functions.add(node.name)
                
        self.generic_visit(node)

    def visit_For(self, node):
        self._check_loop(node)

    def visit_While(self, node):
        self._check_loop(node)

    def _check_loop(self, node):
        self.current_loop_depth += 1
        line_no = getattr(node, 'lineno', 1)

        if self.current_loop_depth >= 2:
            severity = "High" if self.current_loop_depth >= 3 else "Medium"
            complexity = f"O(N^{self.current_loop_depth})"
            self.issues.append({
                "line": line_no,
                "type": "High Algorithmic Complexity",
                "severity": severity,
                "code": self._get_line_code(line_no),
                "message": f"Nested loop detected (Depth level {self.current_loop_depth}). Implies {complexity} time & power complexity.",
                "recommendation": f"Flatten nested loop using hash tables (dict/set), vectorization (NumPy), or list comprehension to achieve O(N) execution."
            })

        # Inspect statements inside loop body
        for stmt in node.body:
            self._inspect_loop_body(stmt, line_no)

        self.generic_visit(node)
        self.current_loop_depth -= 1

    def _inspect_loop_body(self, stmt, loop_line):
        # 1. String concatenation inside loop (str += val)
        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
            if isinstance(stmt.target, ast.Name):
                line_no = getattr(stmt, 'lineno', loop_line)
                self.issues.append({
                    "line": line_no,
                    "type": "Inefficient Memory Reallocation",
                    "severity": "Medium",
                    "code": self._get_line_code(line_no),
                    "message": "String dynamic concatenation inside loop (`+=`) allocates new memory buffer on every iteration.",
                    "recommendation": "Append string segments into a list and join them using `''.join(list)` after loop completion."
                })

        # 2. Linear search inside loop (`val in list_var`)
        for sub_node in ast.walk(stmt):
            if isinstance(sub_node, ast.Compare):
                for op in sub_node.ops:
                    if isinstance(op, ast.In) and self.current_loop_depth >= 1:
                        line_no = getattr(sub_node, 'lineno', loop_line)
                        self.issues.append({
                            "line": line_no,
                            "type": "Hidden O(N^2) Lookup",
                            "severity": "High",
                            "code": self._get_line_code(line_no),
                            "message": "Linear lookup (`in list`) inside loop creates hidden quadratic time & energy penalty.",
                            "recommendation": "Convert lookup container to `set` or `dict` before loop for O(1) instantaneous lookup."
                        })

            # 3. Recursive function call check
            if isinstance(sub_node, ast.Call):
                if isinstance(sub_node.func, ast.Name) and sub_node.func.id in self.functions_defined:
                    self.recursive_functions.add(sub_node.func.id)

    def visit_Call(self, node):
        # Check range(len(...)) pattern
        if isinstance(node.func, ast.Name) and node.func.id == 'range':
            if len(node.args) == 1 and isinstance(node.args[0], ast.Call):
                inner = node.args[0]
                if isinstance(inner.func, ast.Name) and inner.func.id == 'len':
                    line_no = getattr(node, 'lineno', 1)
                    self.issues.append({
                        "line": line_no,
                        "type": "Non-Pythonic Loop Indexing",
                        "severity": "Low",
                        "code": self._get_line_code(line_no),
                        "message": "Using `range(len(sequence))` causes extra subscript indexing energy overhead.",
                        "recommendation": "Use direct iteration `for item in sequence:` or `for idx, item in enumerate(sequence):`."
                    })
        self.generic_visit(node)

    def _post_analysis_checks(self):
        # Unmemoized recursion check
        for func_name in self.recursive_functions:
            if func_name not in self.memoized_functions:
                self.issues.append({
                    "line": 1,
                    "type": "Uncached Exponential Recursion",
                    "severity": "High",
                    "code": f"def {func_name}(...):",
                    "message": f"Recursive function `{func_name}` lacks caching decorator, risking O(2^N) exponential energy drain.",
                    "recommendation": f"Add `@functools.lru_cache(maxsize=None)` above `def {func_name}` to cache subproblem results."
                })

    def _get_line_code(self, lineno):
        lines = self.source_code.splitlines()
        if 0 <= lineno - 1 < len(lines):
            return lines[lineno - 1].strip()
        return ""

    def calculate_eco_score(self):
        score = 100
        for issue in self.issues:
            if issue["severity"] == "High":
                score -= 25
            elif issue["severity"] == "Medium":
                score -= 15
            elif issue["severity"] == "Low":
                score -= 5
        return max(0, score)

def analyze_code_sustainability(code_string):
    analyzer = CodeEcoAnalyzer(code_string)
    return analyzer.analyze()
