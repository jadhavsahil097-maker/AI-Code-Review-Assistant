import ast
import re


SECRET_PATTERN = re.compile(
    r"""(?i)\b(password|passwd|api_key|apikey|secret|token)\b\s*=\s*(['"])[^'"]+\2"""
)


def analyze_security(code):
    issues = []
    lines = code.splitlines()

    # AST-based checks are preferred when syntax is valid; regex catches straightforward assignments.
    for number, line in enumerate(lines, start=1):
        if SECRET_PATTERN.search(line):
            issues.append({
                "title": "Hard-coded Password or Secret",
                "severity": "Critical",
                "line": number,
                "description": "Sensitive information is directly written in the source code.",
                "suggestion": "Use an environment variable or secret manager instead."
            })

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return create_result(_deduplicate(issues))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            issues.append({
                "title": "Unsafe Function Usage",
                "severity": "Critical",
                "line": node.lineno,
                "description": f"{node.func.id}() can execute dynamically supplied code.",
                "suggestion": "Avoid eval() and exec(); use explicit logic or a safe parser."
            })
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "system":
            issues.append({
                "title": "os.system() Usage",
                "severity": "Moderate",
                "line": node.lineno,
                "description": "Shell commands can be dangerous when arguments contain untrusted input.",
                "suggestion": "Prefer subprocess.run with a list of arguments and shell=False."
            })
    return create_result(_deduplicate(issues))


def _deduplicate(issues):
    seen, output = set(), []
    for issue in issues:
        key = (issue["title"], issue.get("line"))
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def create_result(issues):
    counts = {level.lower(): sum(1 for i in issues if i.get("severity", "").lower() == level.lower())
              for level in ("Critical", "Moderate", "Minor")}
    return {"issues": issues, "critical": counts["critical"], "moderate": counts["moderate"],
            "minor": counts["minor"], "total": len(issues)}
import ast
import re


SECRET_PATTERN = re.compile(
    r"""(?i)\b(password|passwd|api_key|apikey|secret|token)\b\s*=\s*(['"])[^'"]+\2"""
)


def analyze_security(code):
    issues = []
    lines = code.splitlines()

    # AST-based checks are preferred when syntax is valid; regex catches straightforward assignments.
    for number, line in enumerate(lines, start=1):
        if SECRET_PATTERN.search(line):
            issues.append({
                "title": "Hard-coded Password or Secret",
                "severity": "Critical",
                "line": number,
                "description": "Sensitive information is directly written in the source code.",
                "suggestion": "Use an environment variable or secret manager instead."
            })

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return create_result(_deduplicate(issues))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            issues.append({
                "title": "Unsafe Function Usage",
                "severity": "Critical",
                "line": node.lineno,
                "description": f"{node.func.id}() can execute dynamically supplied code.",
                "suggestion": "Avoid eval() and exec(); use explicit logic or a safe parser."
            })
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "system":
            issues.append({
                "title": "os.system() Usage",
                "severity": "Moderate",
                "line": node.lineno,
                "description": "Shell commands can be dangerous when arguments contain untrusted input.",
                "suggestion": "Prefer subprocess.run with a list of arguments and shell=False."
            })
    return create_result(_deduplicate(issues))


def _deduplicate(issues):
    seen, output = set(), []
    for issue in issues:
        key = (issue["title"], issue.get("line"))
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def create_result(issues):
    counts = {level.lower(): sum(1 for i in issues if i.get("severity", "").lower() == level.lower())
              for level in ("Critical", "Moderate", "Minor")}
    return {"issues": issues, "critical": counts["critical"], "moderate": counts["moderate"],
            "minor": counts["minor"], "total": len(issues)}

