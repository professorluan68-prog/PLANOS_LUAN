import sqlite3
import os

db_path = r"d:\PLANOS_LUAN\planos_luan.db"
base_dir = r"D:\PLANOS-FINALIZADOS\AGOSTO"

def create_folders():
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT DISTINCT p.nome, pt.disciplina 
    FROM professores p 
    JOIN professor_turmas pt ON p.id = pt.professor_id
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    for nome, disciplina in results:
        if nome and disciplina:
            # Just to be safe with windows folder names, remove invalid characters
            invalid_chars = '<>:"/\\|?*'
            safe_nome = nome
            safe_disciplina = disciplina
            for c in invalid_chars:
                safe_nome = safe_nome.replace(c, '')
                safe_disciplina = safe_disciplina.replace(c, '')
                
            safe_nome = safe_nome.strip()
            safe_disciplina = safe_disciplina.strip()
            
            prof_dir = os.path.join(base_dir, safe_nome)
            disc_dir = os.path.join(prof_dir, safe_disciplina)
            
            if not os.path.exists(disc_dir):
                os.makedirs(disc_dir)
                print(f"Created: {disc_dir}")
                
    conn.close()
    print("Folders created successfully.")

if __name__ == "__main__":
    create_folders()
