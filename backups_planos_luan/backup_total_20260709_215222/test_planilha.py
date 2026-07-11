from core.ae_priorizado import carregar_base_ae_planilha
import json
path = r'C:\Users\Luan Dias\Documents\PDF_AULAS\QUIMICA\EM\3_BIMESTRE\2_ANO\GUIA_2_ANO_3_BIMESTRE.xlsx'
base = carregar_base_ae_planilha(path)
with open('test_planilha.json', 'w', encoding='utf-8') as f:
    json.dump(base, f, indent=2, ensure_ascii=False)
