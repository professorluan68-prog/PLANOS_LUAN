import sqlite3

conn = sqlite3.connect("planos_luan.db")
cursor = conn.cursor()

# Search for any disciplines containing 'geografia' or 'biologia'
cursor.execute("SELECT DISTINCT disciplina FROM professor_turmas WHERE disciplina LIKE ? OR disciplina LIKE ?", ("%geografia%", "%biologia%"))
disciplines = cursor.fetchall()
print("Disciplinas found in database containing 'geografia' or 'biologia':", disciplines)

cursor.execute("SELECT DISTINCT disciplina FROM professor_turmas")
all_discs = cursor.fetchall()
print("\nAll unique disciplines in database:")
for d in all_discs:
    print(d)

conn.close()
