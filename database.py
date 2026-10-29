import sqlite3

DATABASE = "code_review.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def create_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            quality_score INTEGER,
            issue_count INTEGER,
            security_issues INTEGER,
            performance_issues INTEGER,
            code_smells INTEGER,
            ai_score INTEGER,
            ai_summary TEXT,
            corrected_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_review(
    code,
    quality_score,
    issue_count,
    security_issues,
    performance_issues,
    code_smells,
    ai_score,
    ai_summary,
    corrected_code
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO reviews (
            code,
            quality_score,
            issue_count,
            security_issues,
            performance_issues,
            code_smells,
            ai_score,
            ai_summary,
            corrected_code
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        quality_score,
        issue_count,
        security_issues,
        performance_issues,
        code_smells,
        ai_score,
        ai_summary,
        corrected_code
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":

    create_database()

    print("Database created successfully!")