import pandas as pd
df = pd.read_excel(r"D:\PDF novos\LINGUA_PORTUGUESA\AF\3_BIMESTRE\planilha.xlsx")
print(df.columns.tolist())
print(df.head(2))
