import ast


def analyze_performance(code):
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return create_result(issues)

    # Warn about nested loops only once per outer loop, and don't flag print() by default:
    # printing can be intentional, so it is not sufficient evidence of a performance bug.
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            nested = [
                child for child in ast.walk(node)
                if child is not node and isinstance(child, (ast.For, ast.While))
            ]
            if nested:
                issues.append({
                    "title": "Nested Loop",
                    "severity": "Moderate",
                    "line": nested[0].lineno,
                    "description": "A loop is nested inside another loop; runtime may grow quickly for large inputs.",
                    "suggestion": "Check the algorithm's time complexity and consider a more efficient data structure."
                })
    return create_result(issues)


def create_result(issues):
    critical = sum(1 for issue in issues if issue["severity"] == "Critical")
    moderate = sum(1 for issue in issues if issue["severity"] == "Moderate")
    minor = sum(1 for issue in issues if issue["severity"] == "Minor")
    return {"issues": issues, "critical": critical, "moderate": moderate,
            "minor": minor, "total": len(issues)}
