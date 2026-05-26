from __future__ import annotations

from io import BytesIO
import re

from docx import Document

from core.lote import (
    _acessibilidade_cdp_contextual,
    _acompanhamento_cdp_contextual,
    _formatar_material_cdp_contextual,
    _limpar_tema_cdp_contextual,
    _metodologia_cdp_contextual,
)
from docx_generator.preencher import (
    _eh_tabela_aulas,
    _indices_linha_aula,
    _preencher_celula_lista,
    _preencher_celula_metodologia,
    _preencher_celula_tema_material,
)


def _extrair_tema_material(texto: str) -> str:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto:
        return "Conteúdo da aula"

    linhas = [linha.strip(" -:–—") for linha in str(texto or "").splitlines() if linha.strip()]
    candidatas: list[str] = []
    for linha in linhas:
        linha_limpa = re.sub(r"^\s*TEMA\s*:\s*", "", linha, flags=re.I).strip(" -:–—")
        linha_limpa = re.sub(r"^\s*AULA\s*\d+\s*[-:–—]?\s*", "", linha_limpa, flags=re.I).strip(" -:–—")
        linha_limpa = re.sub(r"^\s*MATEMÁTICA\s*[-:–—]?\s*", "", linha_limpa, flags=re.I).strip(" -:–—")
        if linha_limpa and linha_limpa.upper() not in {"TEMA", "MATEMÁTICA"}:
            candidatas.append(linha_limpa)

    if not candidatas:
        if " - " in bruto:
            return bruto.split(" - ", 1)[-1].strip()
        return bruto

    return max(candidatas, key=len)


def reescrever_docx_cdp_contextual_matematica(docx_bytes: bytes) -> tuple[bytes, dict[str, object]]:
    doc = Document(BytesIO(docx_bytes))
    linhas_reescritas = 0
    temas: list[str] = []

    for tabela in doc.tables:
        if not _eh_tabela_aulas(tabela):
            continue
        cabecalho = tabela.rows[0] if tabela.rows else None
        for linha in tabela.rows[1:]:
            indices = _indices_linha_aula(linha, cabecalho)
            if not indices:
                continue

            texto_material = linha.cells[indices["material"]].text
            texto_aprendizagem = linha.cells[indices["aprendizagem"]].text
            tema = _limpar_tema_cdp_contextual(_extrair_tema_material(texto_material), "Matemática")
            if not tema:
                continue

            metodologia = _metodologia_cdp_contextual("matematica", "", tema, texto_aprendizagem, linhas_reescritas)
            acompanhamento = _acompanhamento_cdp_contextual("matematica", tema, texto_aprendizagem, linhas_reescritas)
            acessibilidade = _acessibilidade_cdp_contextual("matematica", tema, texto_aprendizagem, linhas_reescritas)

            _preencher_celula_tema_material(
                linha.cells[indices["material"]],
                _formatar_material_cdp_contextual(tema, "Matemática"),
            )
            _preencher_celula_metodologia(linha.cells[indices["desenvolvimento"]], metodologia)
            _preencher_celula_lista(linha.cells[indices["acompanhamento"]], acompanhamento)
            _preencher_celula_lista(linha.cells[indices["acessibilidade"]], acessibilidade)

            linhas_reescritas += 1
            temas.append(tema)

    saida = BytesIO()
    doc.save(saida)
    saida.seek(0)
    return saida.getvalue(), {
        "linhas_reescritas": linhas_reescritas,
        "temas": temas,
    }


def reescrever_docx_cdp_ensino_medio(docx_bytes: bytes) -> tuple[bytes, dict[str, object]]:
    return reescrever_docx_cdp_contextual_matematica(docx_bytes)
