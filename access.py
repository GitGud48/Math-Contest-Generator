import sqlite3

conn = sqlite3.connect("putnam.sqlite")
cursor = conn.cursor()

cursor.execute("SELECT label, statement FROM problems LIMIT 5")
rows = cursor.fetchall()

for label, statement in rows:
    print(f"{label}:\n{statement}\n{'-'*40}")

conn.close()