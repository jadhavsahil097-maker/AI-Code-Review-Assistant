import ast


def analyze_code_smells(code):
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return create_result(issues)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            issues.append({
                "title": "Wildcard Import", "severity": "Minor", "line": node.lineno,
                "description": "Wildcard imports can make it unclear where names come from.",
                "suggestion": "Import only the names that are required."
            })
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({
                "title": "Bare Except", "severity": "Moderate", "line": node.lineno,
                "description": "A bare except catches almost every exception, including interrupts.",
                "suggestion": "Catch the specific exception types you expect."
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if getattr(node, "end_lineno", node.lineno) - node.lineno + 1 > 40:
                issues.append({
                    "title": "Long Function", "severity": "Moderate", "line": node.lineno,
                    "description": f"Function '{node.name}' is long and may be difficult to maintain.",
                    "suggestion": "Consider splitting it into smaller functions with clear responsibilities."
                })
            positional = len(node.args.posonlyargs) + len(node.args.args)
            if positional > 5:
                issues.append({
                    "title": "Too Many Parameters", "severity": "Minor", "line": node.lineno,
                    "description": f"Function '{node.name}' has more than five positional parameters.",
                    "suggestion": "Consider grouping related parameters into a data class or configuration object."
                })
    return create_result(issues)


def create_result(issues):
    critical = sum(1 for issue in issues if issue["severity"] == "Critical")
    moderate = sum(1 for issue in issues if issue["severity"] == "Moderate")
    minor = sum(1 for issue in issues if issue["severity"] == "Minor")
    return {"issues": issues, "critical": critical, "moderate": moderate,
            "minor": minor, "total": len(issues)}
