import re
import json
from io import BytesIO
from pathlib import Path
from docx import Document

from config import REGISTRO_PROXIMA_GERACAO_PATH
from core.disciplinas import BIMESTRES

def detectar_ultima_aula_de_docx_bytes(docx_bytes: bytes, bimestre: str = "") -> int:
    """
    Analisa os bytes de um arquivo .docx para extrair o número máximo de aula gerado.
    """
    if not docx_bytes:
        return 0

    # 1. Se um bimestre foi informado, verificar se o plano do histórico pertence a esse mesmo bimestre
    if bimestre:
        try:
            doc_temp = Document(BytesIO(docx_bytes))
            outro_bimestre_detectado = False
            for table in doc_temp.tables:
                contem_palavra_bimestre = False
                textos_celulas = []
                for row in table.rows:
                    for cell in row.cells:
                        txt = cell.text.strip()
                        textos_celulas.append(txt)
                        if "BIMESTRE" in txt.upper():
                            contem_palavra_bimestre = True
                
                if contem_palavra_bimestre:
                    for b in BIMESTRES:
                        if b.lower() != bimestre.lower():
                            if any(b.lower() in tc.lower() for tc in textos_celulas):
                                outro_bimestre_detectado = True
                                break
                    if outro_bimestre_detectado:
                        break
            
            if outro_bimestre_detectado:
                # O último plano gerado pertence a outro bimestre, então zeramos a contagem para o bimestre atual
                return 0
        except Exception:
            pass

    # 2. Fazer o parsing das tabelas para encontrar "Aula X"
    try:
        doc = Document(BytesIO(docx_bytes))
        total_linhas = 0
        aulas_detectadas = []
        for t in doc.tables:
            if len(t.rows) > 0:
                textos_cab = [c.text.upper() for c in t.rows[0].cells]
                if any('AULA' in tc for tc in textos_cab) and any('APRENDIZAGEM' in tc for tc in textos_cab):
                    for row in t.rows[1:]:
                        total_linhas += 1
                        if len(row.cells) >= 2:
                            txt_col2 = row.cells[1].text
                            match = re.search(r'(?i)Aula\s*(\d+)', txt_col2)
                            if match:
                                aulas_detectadas.append(int(match.group(1)))
        if aulas_detectadas:
            return max(aulas_detectadas)
        if total_linhas > 0:
            return total_linhas
    except Exception:
        pass

    return 0

def obter_aula_parada_do_json(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    """
    Tenta obter o número da aula de parada a partir do arquivo JSON de mapeamento.
    """
    prof_upper = str(professor or "").strip().upper()
    disc_upper = str(disciplina or "").strip().upper()
    turma_upper = str(turma or "").strip().upper()

    try:
        json_path = Path(REGISTRO_PROXIMA_GERACAO_PATH)
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as fj:
                dados = json.load(fj)
                for item in dados:
                    if (str(item.get("professor") or "").strip().upper() == prof_upper and
                        str(item.get("disciplina") or "").strip().upper() == disc_upper and
                        str(item.get("turma") or "").strip().upper() == turma_upper):
                        if bimestre and item.get("bimestre"):
                            if str(item.get("bimestre")).strip().lower() != bimestre.strip().lower():
                                continue
                        return int(item.get("aula_parada") or 0)
    except Exception:
        pass

    return 0

def obter_ultima_aula_gerada_sistema_impl(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    """
    Regra atual do projeto: novos planos sempre começam pela Aula 1.

    O histórico continua salvo para consulta e download, mas não deve mais
    interferir na aula inicial sugerida para novas gerações.
    """
    return 0
