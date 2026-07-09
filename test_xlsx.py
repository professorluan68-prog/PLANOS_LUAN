import pandas as pd
import json

path = r'C:\Users\Luan Dias\Documents\PDF_AULAS\QUIMICA\EM\3_BIMESTRE\2_ANO\GUIA_2_ANO_3_BIMESTRE.xlsx'
df = pd.read_excel(path)

data = []
for idx, row in df.iterrows():
    data.append(row.to_dict())

with open('quimica_ae_columns.json', 'w', encoding='utf-8') as f:
    json.dump({'columns': list(df.columns), 'data': data[:5]}, f, indent=2, ensure_ascii=False)
