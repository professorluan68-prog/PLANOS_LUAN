from core.database import connection_scope
import pandas as pd

with connection_scope() as conn:
    df = pd.read_sql("SELECT DISTINCT bimestre FROM historico_planos", conn)
    print(df)
