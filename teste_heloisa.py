from core.database import connection_scope
import pandas as pd

with connection_scope() as conn:
    df = pd.read_sql("SELECT DISTINCT professor_nome, disciplina, bimestre, turma FROM historico_planos WHERE professor_nome LIKE '%HELOÍSA%'", conn)
    print(df.head(10))
