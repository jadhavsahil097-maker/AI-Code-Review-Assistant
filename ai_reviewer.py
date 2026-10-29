
import ast
import json
import re
import time
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:0.5b"

SECRET_NAMES = {
    "password", "passwd", "secret", "api_key", "apikey", "token"
}


def _make_issue(title, category, severity, line,
                description, impact, suggestion):
    return {
        "title": title,
        "category": category,
        "severity": severity,
        "line": line,
        "description": description,
        "impact": impact,
        "suggestion": suggestion
    }


def _find_secret_assignments(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    found = []

    for node in ast.walk(tree):
        name = None
        value = None

        if isinstance(node, ast.Assign):
            value = node.value
            if len(node.targets) == 1 and isinstance(
                node.targets[0], ast.Name
            ):
                name = node.targets[0].id

        elif isinstance(node, ast.AnnAssign):
            value = node.value
            if isinstance(node.target, ast.Name):
                name = node.target.id

        if (
            name
            and name.lower() in SECRET_NAMES
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and value.value
            and not value.value.startswith("${")
        ):
            found.append({
                "name": name,
                "line": node.lineno
            })

    return found


def _fix_missing_colon(code):
    """Fix only common, clearly recognizable missing-colon cases."""
    lines = code.splitlines()
    changed = False

    patterns = [
        r"^\s*(?:async\s+)?def\s+.+\)\s*(?:->\s*.+)?$",
        r"^\s*(?:if|elif|while|for|with|class|except)\b.+$",
        r"^\s*(?:else|try|finally)\s*$"
    ]

    for index, line in enumerate(lines):
        stripped = line.rstrip()

        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue

        if stripped.endswith(":"):
            continue

        for pattern in patterns:
            if re.match(pattern, stripped):
                # Avoid changing a line that already appears to
                # contain an inline suite or assignment.
                if re.search(r"\s=\s", stripped):
                    continue

                lines[index] = stripped + ":"
                changed = True
                break

    candidate = "\n".join(lines)

    if changed:
        try:
            ast.parse(candidate)
            return candidate
        except SyntaxError:
            pass

    return code


def _correct_code(code):
    corrected = _fix_missing_colon(code)

    try:
        tree = ast.parse(corrected)
    except SyntaxError:
        # Do not guess a correction for syntax we cannot safely fix.
        return corrected

    lines = corrected.splitlines()

    # Replace simple standalone hard-coded secret assignments.
    secrets = _find_secret_assignments(corrected)

    for item in sorted(
        secrets, key=lambda item: item["line"], reverse=True
    ):
        index = item["line"] - 1
        if not 0 <= index < len(lines):
            continue

        name = item["name"]
        env_name = (
            "APP_PASSWORD"
            if name.lower() in {"password", "passwd"}
            else name.upper()
        )

        match = re.match(
            r"""^(\s*)"""
            + re.escape(name)
            + r"""\s*=\s*(['"]).*?\2\s*;?\s*$""",
            lines[index]
        )

        if match:
            lines[index] = (
                match.group(1)
                + name
                + " = os.getenv("
                + repr(env_name)
                + ")"
            )

    corrected = "\n".join(lines)

    if secrets and not re.search(
        r"(?m)^\s*import\s+os\b", corrected
    ):
        corrected = "import os\n" + corrected

    try:
        tree = ast.parse(corrected)
    except SyntaxError:
        return corrected

    lines = corrected.splitlines()
    insertions = []

    for function in ast.walk(tree):
        if not isinstance(
            function, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        args = (
            function.args.posonlyargs
            + function.args.args
            + function.args.kwonlyargs
        )
        argument_names = {arg.arg for arg in args}

        # Handle average calculations that divide by len(list).
        for node in ast.walk(function):
            if not isinstance(node, ast.Return):
                continue

            value = node.value

            if not (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Div)
                and isinstance(value.right, ast.Call)
                and isinstance(value.right.func, ast.Name)
                and value.right.func.id == "len"
                and len(value.right.args) == 1
                and isinstance(value.right.args[0], ast.Name)
            ):
                continue

            list_name = value.right.args[0].id

            if list_name not in argument_names:
                continue

            index = node.lineno - 1
            indent = lines[index][:len(lines[index]) -
                                  len(lines[index].lstrip())]

            previous = lines[index - 1] if index > 0 else ""

            if re.match(
                r"^\s*if\s+not\s+" + re.escape(list_name) + r"\s*:",
                previous
            ):
                continue

            insertions.append((
                index,
                [
                    indent + f"if not {list_name}:",
                    indent + "    raise ValueError("
                    "'Cannot calculate average of an empty list')"
                ]
            ))

        # Guard a simple return expression such as return a / b.
        for node in ast.walk(function):
            if not isinstance(node, ast.Return):
                continue

            value = node.value

            if not (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Div)
                and isinstance(value.right, ast.Name)
                and value.right.id in argument_names
            ):
                continue

            divisor = value.right.id
            index = node.lineno - 1
            indent = lines[index][:len(lines[index]) -
                                  len(lines[index].lstrip())]

            previous = lines[index - 1] if index > 0 else ""

            if re.match(
                r"^\s*if\s+" + re.escape(divisor) + r"\s*==\s*0\s*:",
                previous
            ):
                continue

            insertions.append((
                index,
                [
                    indent + f"if {divisor} == 0:",
                    indent + "    raise ValueError("
                    "'Divisor cannot be zero')"
                ]
            ))

    # Insert from bottom to top.
    for index, new_lines in sorted(
        insertions, key=lambda item: item[0], reverse=True
    ):
        lines[index:index] = new_lines

    return "\n".join(lines)


def _deterministic_issues(code):
    issues = []

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        issues.append(_make_issue(
            "Python Syntax Error", "Bug", "High",
            error.lineno or "N/A",
            error.msg,
            "Python cannot parse this source code.",
            "Correct the syntax error and review the code again."
        ))
        return issues

    for item in _find_secret_assignments(code):
        issues.append(_make_issue(
            "Hard-coded Password or Secret", "Security", "Critical",
            item["line"],
            "A sensitive string is directly assigned in source code.",
            "The value may be exposed when the source is shared.",
            "Read the value from an environment variable."
        ))

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
        ):
            continue

        divisor = node.right

        if (
            isinstance(divisor, ast.Constant)
            and isinstance(divisor.value, (int, float))
            and not isinstance(divisor.value, bool)
            and divisor.value != 0
        ):
            continue

        issues.append(_make_issue(
            "Division by zero risk", "Bug", "High",
            node.lineno,
            "The divisor may be zero at runtime.",
            "A zero divisor causes ZeroDivisionError.",
            "Check the divisor before performing division."
        ))

    for function in ast.walk(tree):
        if not isinstance(
            function, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        for node in ast.walk(function):
            if not isinstance(node, ast.Return):
                continue

            value = node.value

            if not (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Div)
                and isinstance(value.right, ast.Call)
                and isinstance(value.right.func, ast.Name)
                and value.right.func.id == "len"
                and len(value.right.args) == 1
                and isinstance(value.right.args[0], ast.Name)
            ):
                continue

            issues.append(_make_issue(
                "Possible Empty List Error", "Bug", "High",
                node.lineno,
                "The average calculation divides by the list length.",
                "An empty list has length zero and causes division by zero.",
                "Check that the list is not empty before calculating."
            ))

    return issues


def _merge_issues(ai_issues, checked_issues):
    merged = []
    seen = set()

    for issue in list(ai_issues) + list(checked_issues):
        if not isinstance(issue, dict):
            continue

        normalized = {
            "title": str(issue.get("title", "Code issue")),
            "category": str(issue.get("category", "Code Quality")),
            "severity": str(issue.get("severity", "Medium")),
            "line": issue.get("line", "N/A"),
            "description": str(issue.get("description", "")),
            "impact": str(issue.get("impact", "Review the impact.")),
            "suggestion": str(issue.get("suggestion", "Review the code."))
        }

        key = (
            normalized["title"].lower(),
            normalized["category"].lower(),
            str(normalized["line"])
        )

        if key not in seen:
            merged.append(normalized)
            seen.add(key)

    return merged


def _score_for_issues(issues, ai_score):
    # Keep the AI score, but don't claim a high score when
    # deterministic checks find high-severity issues.
    if any(issue["severity"] == "Critical" for issue in issues):
        return min(ai_score, 60)

    if any(issue["severity"] == "High" for issue in issues):
        return min(ai_score, 75)

    return ai_score


def review_code_with_ai(code):
    start_time = time.time()

    if not isinstance(code, str):
        code = str(code or "")

    corrected_code = _correct_code(code)
    checked_issues = _deterministic_issues(code)

    prompt = f"""
You are reviewing Python code for a student project.
Do not execute the submitted code.
Return a valid JSON object only.
Report only genuine issues. Use source line numbers.
Do not replace the program with unrelated code.

Return this structure:
{{
  "score": 80,
  "summary": "Brief summary",
  "issues": [
    {{
      "title": "Issue title",
      "category": "Bug",
      "severity": "High",
      "line": 1,
      "description": "What is wrong",
      "impact": "Possible impact",
      "suggestion": "How to fix it"
    }}
  ]
}}

Submitted Python code:
<submitted_code>
{code}
</submitted_code>
"""

    ai_issues = []
    ai_score = 80
    ai_available = False

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "num_predict": 1600
                }
            },
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        ai_data = json.loads(data.get("response", ""))

        if isinstance(ai_data, dict):
            ai_available = True

            if isinstance(ai_data.get("issues"), list):
                ai_issues = ai_data["issues"]

            try:
                ai_score = max(
                    0, min(100, int(ai_data.get("score", 80)))
                )
            except (TypeError, ValueError):
                ai_score = 80

    except (
        requests.exceptions.RequestException,
        json.JSONDecodeError,
        ValueError
    ) as error:
        print("AI review unavailable; using built-in checks:", error)

    issues = _merge_issues(ai_issues, checked_issues)
    ai_score = _score_for_issues(issues, ai_score)

    if issues:
        summary = (
            f"Review found {len(issues)} issue(s). "
            "Review the findings and suggested fixes."
        )
    else:
        summary = (
            "No issues were detected by the AI and built-in checks. "
            "Review static analysis results as well."
        )

    result = {
        "score": ai_score,
        "summary": summary,
        "issues": issues,
        "corrected_code": corrected_code,
        "ai_available": ai_available
    }

    review_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "result": result,
        "review_time": review_time
    }
