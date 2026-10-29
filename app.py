from flask import Flask, render_template, request
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

from dotenv import load_dotenv
from database import create_database, save_review
from services.ai_reviewer import review_code_with_ai
from services.security_analyzer import analyze_security
from services.performance_analyzer import analyze_performance
from services.code_smell_analyzer import analyze_code_smells

load_dotenv()
app = Flask(__name__)
create_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/history")
def history():
    connection = sqlite3.connect("code_review.db")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
        reviews = cursor.fetchall()
    finally:
        connection.close()
    return render_template("history.html", reviews=reviews)


def calculate_quality_score(pylint_output):
    """Score Pylint errors more heavily than style/convention warnings."""
    score = 100
    for line in pylint_output.splitlines():
        match = re.search(r":\d+:\d+:\s*([A-Z])(\d+):", line)
        if not match:
            continue
        category, code = match.groups()
        # Fatal/error messages matter more than convention/refactor messages.
        if category == "F":
            score -= 25
        elif category == "E":
            score -= 20
        elif category == "W":
            score -= 8
        elif category == "R":
            score -= 5
        elif category == "C":
            score -= 2
    return max(0, min(100, score))


@app.route("/review", methods=["POST"])
def review():
    code = request.form.get("code", "")
    if not code.strip():
        return render_template("index.html", error="Please enter Python code.")

    normalized_code = code.replace("\r\n", "\n").replace("\r", "\n")
    file_path = None
    pylint_output = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8", newline="\n"
        ) as temp_file:
            file_path = temp_file.name
            temp_file.write(normalized_code.rstrip("\n") + "\n")

        result = subprocess.run(
            [sys.executable, "-m", "pylint", file_path, "--reports=no", "--score=no"],
            capture_output=True, text=True, timeout=30
        )
        pylint_output = result.stdout
        if result.stderr:
            pylint_output += "\n" + result.stderr
    except subprocess.TimeoutExpired:
        pylint_output = "Pylint analysis timed out."
    except Exception as error:
        pylint_output = f"Pylint Error: {error}"
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    issue_pattern = r":\d+:\d+:\s+[A-Z]\d+:"
    issue_count = len(re.findall(issue_pattern, pylint_output))
    quality_score = calculate_quality_score(pylint_output)
    if quality_score >= 90:
        quality_status = "Excellent"
    elif quality_score >= 75:
        quality_status = "Good"
    elif quality_score >= 50:
        quality_status = "Needs Improvement"
    else:
        quality_status = "Poor"

    security_result = analyze_security(normalized_code)
    performance_result = analyze_performance(normalized_code)
    code_smell_result = analyze_code_smells(normalized_code)
    ai_result = review_code_with_ai(normalized_code)

    ai_score = 0
    ai_summary = ""
    corrected_code = normalized_code
    if ai_result.get("status") == "success":
        ai_data = ai_result.get("result", {})
        ai_score = ai_data.get("score", 0)
        ai_summary = ai_data.get("summary", "")
        corrected_code = ai_data.get("corrected_code", normalized_code)
    else:
        ai_summary = ai_result.get("message", "AI review could not be completed.")

    save_review(
        code=normalized_code, quality_score=quality_score, issue_count=issue_count,
        security_issues=security_result["total"],
        performance_issues=performance_result["total"],
        code_smells=code_smell_result["total"], ai_score=ai_score,
        ai_summary=ai_summary, corrected_code=corrected_code
    )

    return render_template(
        "result.html", code=normalized_code, output=pylint_output,
        quality_score=quality_score, quality_status=quality_status,
        issue_count=issue_count, security_result=security_result,
        performance_result=performance_result, code_smell_result=code_smell_result,
        ai_result=ai_result
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
