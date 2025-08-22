import sqlite3

conn = sqlite3.connect("putnam.sqlite") #create a connection object
cursor = conn.cursor() #create a cursor object

cursor.execute("SELECT label, statement FROM problems LIMIT 1") #set prompt and pull data
rows = cursor.fetchall() #store data in rows table

for label, statement in rows:
    print(f"{label}:\n{statement}\n{'-'*40}") #display problem

conn.close() #close connection object