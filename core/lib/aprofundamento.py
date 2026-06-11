"""
Utilitário para leitura e integração com planilhas de Aprofundamento.

Responsável por carregar, cachear e buscar metadados estruturados (habilidades,
objetivos, conteúdos) das planilhas de Aprofundamento em Biologia e Aprofundamento em Geografia.
"""

import os
import re
from functools import lru_cache
from pathlib import Path
import openpyxl
from core.normalizacao import normalizar as normalizar_texto

# Determinar BASE_DIR do projeto a partir do local deste arquivo (core/lib/aprofundamento.py -> core -> projeto)
BASE_DIR = Path(__file__).resolve().parents[2]


def eh_aprofundamento_biologia(disciplina: str) -> bool:
    """Verifica de forma robusta se a disciplina é Aprofundamento em Biologia."""
    norm = normalizar_texto(disciplina or "").lower()
    return "aprofundamento" in norm and "biologia" in norm


def eh_aprofundamento_geografia(disciplina: str) -> bool:
    """Verifica de forma robusta se a disciplina é Aprofundamento em Geografia."""
    norm = normalizar_texto(disciplina or "").lower()
    return "aprofundamento" in norm and "geografia" in norm


def obter_caminho_planilha(nome_arquivo: str) -> Path:
    """Retorna o caminho existente da planilha de aprofundamento com fallbacks de desenvolvimento."""
    caminhos = [
        Path("D:/planilhas") / nome_arquivo,
        BASE_DIR / "planilhas" / nome_arquivo,
        BASE_DIR / "Planos feitos" / nome_arquivo,
        Path(os.getcwd()) / "planilhas" / nome_arquivo,
    ]
    for c in caminhos:
        if c.exists():
            return c
    # Retorna o padrão se nenhum existir (erro tratado no carregamento)
    return caminhos[0]


@lru_cache(maxsize=4)
def carregar_linhas_planilha(caminho_str: str) -> list[tuple]:
    """Carrega todas as linhas de uma planilha Excel e armazena em cache na memória."""
    caminho = Path(caminho_str)
    if not caminho.exists():
        return []
    try:
        wb = openpyxl.load_workbook(str(caminho), data_only=True, read_only=True)
        sheet = wb.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(row)
        wb.close()
        return rows
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao carregar planilha {caminho_str}: {e}")
        return []


def comparar_aula(val_planilha, val_pdf) -> bool:
    """Compara robustamente o número da aula da planilha com o extraído do PDF."""
    if val_planilha is None or val_pdf is None:
        return False
    # Tenta comparação numérica direta
    try:
        if int(val_planilha) == int(val_pdf):
            return True
    except (ValueError, TypeError):
        pass
    # Fallback para string normalizada
    s_plan = str(val_planilha).strip().lstrip("0")
    s_pdf = str(val_pdf).strip().lstrip("0")
    return s_plan == s_pdf and s_plan != ""


def quebrar_e_limpar_itens(texto: str) -> list[str]:
    """Quebra uma string multilinha em itens individuais de lista, removendo marcadores."""
    if not texto:
        return []
    itens = []
    for linha in str(texto).split("\n"):
        linha = re.sub(r"^[•●*\-\t\s]+", "", linha).strip()
        if linha:
            itens.append(linha)
    return itens


def eh_educacao_financeira_ef(disciplina: str, turma: str = "") -> bool:
    """Verifica se a disciplina é Educação Financeira no Ensino Fundamental."""
    from core.lib.classificador import perfil_disciplina
    perfil = perfil_disciplina(disciplina)
    if perfil != "educacao_financeira":
        return False
    norm_turma = normalizar_texto(turma or "").lower()
    if not norm_turma:
        return True
    return "ano" in norm_turma or "ef" in norm_turma or any(str(i) in norm_turma for i in range(6, 10))


def eh_projeto_vida_ef(disciplina: str, turma: str = "") -> bool:
    """Verifica se a disciplina é Projeto de Vida no Ensino Fundamental."""
    from core.lib.classificador import perfil_disciplina
    perfil = perfil_disciplina(disciplina)
    if perfil != "projeto_de_vida":
        return False
    norm_turma = normalizar_texto(turma or "").lower()
    if not norm_turma:
        return True
    return "ano" in norm_turma or "ef" in norm_turma or any(str(i) in norm_turma for i in range(6, 10))


def eh_redacao_leitura_ef(disciplina: str, turma: str = "") -> bool:
    """Verifica se a disciplina é Redação e Leitura no Ensino Fundamental."""
    from core.lib.classificador import perfil_disciplina
    perfil = perfil_disciplina(disciplina)
    if perfil != "leitura_redacao":
        return False
    norm_turma = normalizar_texto(turma or "").lower()
    if not norm_turma:
        return True
    return "ano" in norm_turma or "ef" in norm_turma or any(str(i) in norm_turma for i in range(6, 10))


def obter_dados_aprofundamento(disciplina: str, numero_aula: str, turma: str = "") -> dict | None:
    """
    Busca os metadados estruturados da planilha para a disciplina, aula e turma (se aplicável).

    Retorna um dicionário com:
    - habilidade: str
    - objetos_conhecimento: str
    - titulo: str
    - conteudo: str
    - objetivos: str
    - bloco_exercicios: str
    """
    if not numero_aula:
        return None

    caminho = None
    modo = None

    if eh_aprofundamento_biologia(disciplina):
        caminho = obter_caminho_planilha("aprofundamentoembiologia.xlsx")
        modo = "biologia"
    elif eh_aprofundamento_geografia(disciplina):
        caminho = obter_caminho_planilha("aprofundamentoemgeografia.xlsx")
        modo = "geografia"
    elif eh_educacao_financeira_ef(disciplina, turma):
        caminho = obter_caminho_planilha("Educaçãofinanceiraensinofundamental.xlsx")
        modo = "educacao_financeira"
    elif eh_projeto_vida_ef(disciplina, turma):
        caminho = obter_caminho_planilha("projetodevidaensinofundamental.xlsx")
        modo = "projeto_vida"
    elif eh_redacao_leitura_ef(disciplina, turma):
        caminho = obter_caminho_planilha("redacaoeleituraensinofundamental.xlsx")
        modo = "redacao_leitura"

    if not caminho or not caminho.exists():
        return None

    rows = carregar_linhas_planilha(str(caminho))
    if not rows:
        return None

    if modo in ("biologia", "geografia"):
        # 0: AULA COMPLEMENTAR, 1: CICLO, 2: SÉRIE, 3: BIMESTRE, 4: AULA, 5: EIXO,
        # 6: UNIDADE TEMÁTICA, 7: HABILIDADE, 8: OBJETOS DO CONHECIMENTO, 9: TÍTULO,
        # 10: CONTEÚDO, 11: OBJETIVOS, 12: BLOCO DE EXERCÍCIOS
        for row in rows[1:]:
            if len(row) < 13:
                continue
            val_aula_planilha = row[4]
            if comparar_aula(val_aula_planilha, numero_aula):
                return {
                    "habilidade": str(row[7]).strip() if row[7] is not None else "",
                    "objetos_conhecimento": str(row[8]).strip() if row[8] is not None else "",
                    "titulo": str(row[9]).strip() if row[9] is not None else "",
                    "conteudo": str(row[10]).strip() if row[10] is not None else "",
                    "objetivos": str(row[11]).strip() if row[11] is not None else "",
                    "bloco_exercicios": str(row[12]).strip() if row[12] is not None else "",
                }

    elif modo == "educacao_financeira":
        # 0: AULA COMPLEMENTAR, 1: CICLO, 2: ANO, 3: BIMESTRE, 4: AULA,
        # 5: HABILIDADE - CÓDIGO, 6: HABILIDADE - TEXTO, 7: UNIDADE TEMÁTICA,
        # 8: OBJETO DE CONHECIMENTO, 9: TÍTULO DA AULA, 10: CONTEÚDO, 11: OBJETIVOS
        digits_turma = set(re.findall(r"\d", str(turma))) if turma else set()
        for row in rows[1:]:
            if len(row) < 12:
                continue
            val_ano = str(row[2])
            digits_ano = set(re.findall(r"\d", val_ano))
            if digits_turma and digits_ano and not (digits_turma & digits_ano):
                continue
            val_aula_planilha = row[4]
            if comparar_aula(val_aula_planilha, numero_aula):
                hab_cod = str(row[5]).strip("- ").strip() if row[5] is not None else ""
                hab_txt = str(row[6]).strip("- ").strip() if row[6] is not None else ""
                habilidade = f"{hab_cod}: {hab_txt}" if hab_cod else hab_txt
                return {
                    "habilidade": habilidade,
                    "objetos_conhecimento": str(row[8]).strip("- ").strip() if row[8] is not None else "",
                    "titulo": str(row[9]).strip() if row[9] is not None else "",
                    "conteudo": str(row[10]).strip() if row[10] is not None else "",
                    "objetivos": str(row[11]).strip() if row[11] is not None else "",
                    "bloco_exercicios": "",
                }

    elif modo == "projeto_vida":
        # 0: AULA COMPLEMENTAR, 1: CICLO, 2: ANO, 3: BIMESTRE, 4: TEMA, 5: AULA,
        # 6: DIMENSÃO EM FOCO, 7: COMPREENSÃO, 8: CONTEXTO DA AULA, 9: QUESTÃO ESSENCIAL,
        # 10: ATITUDE, 11: PRÁTICA, 12: HABILIDADE
        digits_turma = set(re.findall(r"\d", str(turma))) if turma else set()
        last_tema = ""
        for row in rows[1:]:
            if len(row) < 13:
                continue
            if row[4]:
                last_tema = str(row[4]).strip()
            val_ano = str(row[2])
            digits_ano = set(re.findall(r"\d", val_ano))
            if digits_turma and digits_ano and not (digits_turma & digits_ano):
                continue
            val_aula_planilha = row[5]
            if comparar_aula(val_aula_planilha, numero_aula):
                return {
                    "habilidade": str(row[12]).strip() if row[12] is not None else "",
                    "objetos_conhecimento": str(row[6]).strip() if row[6] is not None else "",
                    "titulo": last_tema,
                    "conteudo": str(row[8]).strip() if row[8] is not None else "",
                    "objetivos": str(row[7]).strip() if row[7] is not None else "",
                    "bloco_exercicios": "",
                }

    elif modo == "redacao_leitura":
        # 0: Ano/Série, 1: Bimestre, 2: Semana, 3: Título GPS Semanal, 4: Aula,
        # 5: Prática de linguagem, 6: Proposta, 7: Gênero textual, 8: Eixo Temático,
        # 9: Sugestão 1, 10: Sugestão 2, 11: Sugestão 3, 12: Práticas pedagógicas,
        # 13: Plataforma, 14: Objetivos de aprendizagem, 15: Objetos de conhecimento,
        # 16: Habilidade - Código, 17: Habilidade - Texto
        digits_turma = set(re.findall(r"\d", str(turma))) if turma else set()
        for row in rows[1:]:
            if len(row) < 18:
                continue
            val_ano = str(row[0])
            digits_ano = set(re.findall(r"\d", val_ano))
            if digits_turma and digits_ano and not (digits_turma & digits_ano):
                continue
            val_aula_planilha = row[4]
            if comparar_aula(val_aula_planilha, numero_aula):
                hab_cod = str(row[16]).strip("- ").strip() if row[16] is not None else ""
                hab_txt = str(row[17]).strip("- ").strip() if row[17] is not None else ""
                habilidade = f"{hab_cod}: {hab_txt}" if hab_cod else hab_txt
                return {
                    "habilidade": habilidade,
                    "objetos_conhecimento": str(row[15]).strip() if row[15] is not None else "",
                    "titulo": str(row[3]).strip() if row[3] is not None else "",
                    "conteudo": str(row[7]).strip() if row[7] is not None else "",
                    "objetivos": str(row[14]).strip() if row[14] is not None else "",
                    "bloco_exercicios": "",
                }

    return None
