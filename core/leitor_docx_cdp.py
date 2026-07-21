"""Módulo para leitura de arquivos DOCX de disciplinas CDP."""

import re
from pathlib import Path
from typing import Dict, Any, List

def extrair_aulas_docx(caminho_docx: str | Path) -> Dict[int, Dict[str, Any]]:
    """Lê um arquivo DOCX e extrai as aulas formatadas."""
    try:
        import docx
    except ImportError:
        return {}

    if not Path(caminho_docx).exists():
        return {}

    doc = docx.Document(caminho_docx)
    aulas: Dict[int, Dict[str, Any]] = {}
    aula_atual = None
    
    estado = None # "HABILIDADE", "METODOLOGIA", "ACOMPANHAMENTO", "ACESSIBILIDADE"
    
    for para in doc.paragraphs:
        linhas = para.text.split('\n')
        for texto in linhas:
            texto = texto.strip()
            if not texto:
                continue
                
            m_aula = re.match(r"^AULA\s+(\d+)\s*[-–—]\s*(.*)$", texto, re.I)
            if m_aula:
                numero = int(m_aula.group(1))
                tema = m_aula.group(2).strip()
                aula_atual = {
                    "numero": numero,
                    "tema": tema,
                    "habilidade": "",
                    "metodologia": "",
                    "acompanhamento": [],
                    "acessibilidade": []
                }
                aulas[numero] = aula_atual
                estado = None
                continue
            
            if not aula_atual:
                continue
            
            texto_upper = texto.upper()
            if texto_upper.startswith("HABILIDADE:"):
                aula_atual["habilidade"] = texto.replace("HABILIDADE:", "").replace("HABILIDADE :", "").strip()
                estado = "HABILIDADE"
                continue
            elif texto_upper == "METODOLOGIA":
                estado = "METODOLOGIA"
                continue
            elif texto_upper in ["ACOMPANHAMENTO DA APRENDIZAGEM", "ACOMPANHAMENTO"]:
                estado = "ACOMPANHAMENTO"
                continue
            elif texto_upper == "ACESSIBILIDADE":
                estado = "ACESSIBILIDADE"
                continue
            
            # Collect data based on state
            if estado == "HABILIDADE":
                aula_atual["habilidade"] += " " + texto
            elif estado == "METODOLOGIA":
                if aula_atual["metodologia"]:
                    aula_atual["metodologia"] += "\n\n" + texto
                else:
                    aula_atual["metodologia"] = texto
            elif estado == "ACOMPANHAMENTO":
                aula_atual["acompanhamento"].append(texto)
            elif estado == "ACESSIBILIDADE":
                aula_atual["acessibilidade"].append(texto)
            
    return aulas
