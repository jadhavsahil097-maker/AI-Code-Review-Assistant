import sqlite3

connection = sqlite3.connect("code_review.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM reviews")

reviews = cursor.fetchall()

print("\n===== REVIEW HISTORY =====\n")

for review in reviews:
    print("ID:", review[0])
    print("Quality Score:", review[2])
    print("Issue Count:", review[3])
    print("Security Issues:", review[4])
    print("Performance Issues:", review[5])
    print("Code Smells:", review[6])
    print("AI Score:", review[7])
    print("AI Summary:", review[8])
    print("Created At:", review[10])
    print("-----------------------------")

connection.close()