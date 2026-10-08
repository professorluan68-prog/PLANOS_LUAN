import os
import glob
import re
from pathlib import Path
import sys
import logging
import pdfplumber

logging.basicConfig(level=logging.ERROR)

sys.path.append(r"C:\Users\LuanDias\PLANOS_LUAN")

from core.ae_priorizado import carregar_base_habilidades_planilha
from core.lote import _tema_por_texto

def normalizar_para_comparacao(texto):
    return re.sub(r'[^A-Z0-9]', '', str(texto).upper())

def extrair_texto_primeira_pagina(caminho_pdf):
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            if pdf.pages:
                return pdf.pages[0].extract_text() or ""
    except:
        return ""
    return ""

def verificar_planilhas(raiz):
    print(f"===========================================================")
    print(f"Iniciando varredura rapida em: {raiz}")
    print(f"===========================================================\n")
    
    planilhas = []
    for root, dirs, files in os.walk(raiz):
        for file in files:
            if file.endswith(".xlsx") and "GUIA" not in file.upper() and not file.startswith("~$"):
                planilhas.append(os.path.join(root, file))
                
    if not planilhas:
        print("Nenhuma planilha valida (excluindo GUIA) encontrada.")
        return

    total_divergencias = 0
    
    for caminho_planilha in planilhas:
        pasta = os.path.dirname(caminho_planilha)
        nome_planilha = os.path.basename(caminho_planilha)
        partes = pasta.split(os.sep)
        pasta_curta = os.sep.join(partes[-2:]) if len(partes) >= 2 else pasta
        
        print(f"--- Turma/Pasta: {pasta_curta} | Planilha: {nome_planilha} ---")
        
        try:
            base = carregar_base_habilidades_planilha(caminho_planilha)
            itens = base.get("mapa_por_aula", [])
            
            if not itens:
                print("  [!] Planilha nao contem dados validos de 'mapa_por_aula'.\n")
                continue
                
            mapa_planilha = {str(item.get("aula_numero")): item.get("titulo") for item in itens if item.get("aula_numero")}
            
            pdfs = glob.glob(os.path.join(pasta, "*.pdf"))
            if not pdfs:
                print("  [!] Nenhum PDF encontrado nesta pasta.\n")
                continue
                
            inconsistencias = 0
            for pdf in pdfs:
                nome_pdf = os.path.basename(pdf)
                match_aula = re.search(r'AULA[_\s]*(\d+)', nome_pdf.upper())
                if not match_aula:
                    continue
                
                numero_aula = match_aula.group(1)
                titulo_planilha = mapa_planilha.get(numero_aula)
                
                if not titulo_planilha:
                    # Nao relatar avisos para nao poluir, so focar nos erros
                    continue
                
                try:
                    texto_pdf = extrair_texto_primeira_pagina(pdf)
                    disciplina = "Lingua Portuguesa"
                    titulo_pdf = _tema_por_texto(texto_pdf, pdf, disciplina)
                    
                    if not titulo_pdf:
                        titulo_pdf = ""
                        
                    titulo_planilha_clean = str(titulo_planilha).strip()
                    titulo_pdf_clean = str(titulo_pdf).strip()
                    
                    norm_planilha = normalizar_para_comparacao(titulo_planilha_clean)
                    norm_pdf = normalizar_para_comparacao(titulo_pdf_clean)
                    
                    if not norm_pdf:
                        continue
                        
                    if norm_planilha not in norm_pdf and norm_pdf not in norm_planilha:
                        print(f"  -> [DIVERGENCIA] AULA {numero_aula}")
                        print(f"     - Na Planilha : {titulo_planilha_clean}")
                        print(f"     - No PDF      : {titulo_pdf_clean}")
                        inconsistencias += 1
                        
                except Exception as e:
                    pass
                    
            if inconsistencias == 0:
                print("  -> OK! Titulos batem com os PDFs (ou PDFs nao extraiveis).\n")
            else:
                print(f"  -> {inconsistencias} problema(s) encontrado(s).\n")
                total_divergencias += inconsistencias
                
        except Exception as e:
            pass
            
    print(f"===========================================================")
    print(f"Total de divergencias encontradas: {total_divergencias}")
    print(f"===========================================================")

if __name__ == '__main__':
    verificar_planilhas(r"C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS\LINGUA_PORTUGUESA")
