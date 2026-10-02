"""
Módulo de geração de relatórios técnicos e de conferência de planos de aula.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
import streamlit as st

from config import BASE_DIR
from core.helpers import normalizar_para_pasta
from ui.shared import _texto_metodologia_app


def _texto_lista_conferencia(itens) -> str:
    linhas = []
    for item in itens or []:
        texto = str(item or "").strip()
        if texto:
            linhas.append(texto)
    return "\n".join(linhas)


def _texto_metodologia_conferencia(aula: dict) -> str:
    return _texto_metodologia_app(aula)


def _linhas_relatorio_tecnico_conferencia(aula: dict) -> list[str]:
    return [
        "Relatório Técnico da Geração",
        f"Provedor da IA: {aula.get('ia_provedor') or 'Sem IA'}",
        f"Cache Reutilizado: {'Sim' if aula.get('cache_reutilizado') else 'Não'}",
        f"Versão do Gerador: {aula.get('versao_gerador') or '1.2.9'}",
        f"Origem da Metodologia: {aula.get('origem_metodologia') or 'Desconhecida'}",
        f"Score de Confiança: {aula.get('confidence_score', 100)}%",
    ]


def _texto_diagnostico_conferencia(aula: dict) -> str:
    diag = aula.get("diagnostico_geracao") or {}
    if not diag:
        return "Sem diagnóstico técnico detalhado."

    secoes = [
        ("1. Rascunho Local Heurístico", diag.get("metodologia_local") or []),
        ("2. Resposta IA Crua", diag.get("metodologia_ia_crua") or []),
        ("3. Higienização/Polimento", diag.get("metodologia_higienizada") or []),
        ("4. Metodologia Final", diag.get("metodologia_final") or []),
    ]
    partes = []
    for titulo, valor in secoes:
        partes.append(titulo)
        if isinstance(valor, str):
            partes.append(valor.strip() or "Nenhum conteúdo registrado.")
        elif valor:
            partes.append(_texto_metodologia_app({"metodologia": valor}))
        else:
            partes.append("Nenhum conteúdo registrado.")
        partes.append("")
    return "\n".join(partes).strip()


def _montar_texto_conferencia_aula(aula: dict, numero_aula: int, frases_redundantes=None) -> str:
    frases_redundantes = [str(frase).strip() for frase in (frases_redundantes or []) if str(frase).strip()]
    avisos_val = [str(aviso).strip() for aviso in (aula.get("avisos_validacao") or []) if str(aviso).strip()]
    score = aula.get("confidence_score")
    linhas = [
        f"Aula {numero_aula} - {aula.get('tema', '')}",
        "",
    ]

    if score is not None and score < 70:
        linhas.extend(
            [
                f"Baixo Score de Confiança ({score}%): Este plano de aula pode necessitar de ajustes manuais significativos.",
                "",
            ]
        )

    if avisos_val:
        linhas.append("Alertas de Qualidade Pedagógica:")
        linhas.extend(f"- {aviso}" for aviso in avisos_val)
        linhas.append("")

    if frases_redundantes:
        linhas.append("Aviso de Redundância (frases repetidas em mais de 2 aulas do lote):")
        linhas.extend(f'- "{frase}"' for frase in frases_redundantes)
        linhas.append("")

    linhas.extend(
        [
            "Tema",
            str(aula.get("tema", "") or ""),
            "",
            "Aprendizagem",
            str(aula.get("aprendizagem", "") or ""),
            "",
            "Acompanhamento",
            _texto_lista_conferencia(aula.get("acompanhamento") or []),
            "",
            "Acessibilidade",
            _texto_lista_conferencia(aula.get("acessibilidade") or []),
            "",
            "Metodologia",
            _texto_metodologia_conferencia(aula),
            "",
        ]
    )
    linhas.extend(_linhas_relatorio_tecnico_conferencia(aula))
    linhas.extend(["", "Transformação da Metodologia (Pipeline)", _texto_diagnostico_conferencia(aula), ""])
    return "\n".join(linhas).strip() + "\n"


def _resolver_pasta_base_conferencia(pasta_pdfs_auto: str = "", pdfs_selecionados=None) -> Path:
    if pasta_pdfs_auto:
        pasta = Path(pasta_pdfs_auto)
        if pasta.exists():
            return pasta

    for arquivo in pdfs_selecionados or []:
        caminho = getattr(arquivo, "path", None)
        if caminho:
            caminho = Path(caminho)
            if caminho.exists():
                return caminho.parent

    return BASE_DIR


def _salvar_relatorios_conferencia(
    *,
    turmas_processadas,
    duplicadas_por_aula,
    professor: str,
    disciplina: str,
    turma: str,
    mes: str,
    bimestre: str,
    modo_ia: str,
    modo_upload_pdf: str,
    pasta_pdfs_auto: str = "",
    pdfs_selecionados=None,
):
    token = st.session_state.get("revisao_token", 0)
    resumo_chave = {
        "token": token,
        "professor": professor,
        "disciplina": disciplina,
        "turma": turma,
        "mes": mes,
        "bimestre": bimestre,
        "modo_ia": modo_ia,
        "modo_upload_pdf": modo_upload_pdf,
        "aulas": [
            [aula.get("tema", ""), aula.get("confidence_score"), aula.get("avisos_validacao") or []]
            for bloco in (turmas_processadas or [])
            for aula in (bloco.get("aulas") or [])
        ],
    }
    chave = hashlib.md5(json.dumps(resumo_chave, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if st.session_state.get("relatorio_conferencia_chave") == chave:
        paths_salvos = st.session_state.get("relatorio_conferencia_paths") or []
        if paths_salvos and all(Path(caminho).exists() for caminho in paths_salvos):
            return paths_salvos

    pasta_base = _resolver_pasta_base_conferencia(pasta_pdfs_auto, pdfs_selecionados)
    pasta_relatorios = pasta_base / "RELATORIOS_CONFERENCIA_PLANOS"
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_execucao = "_".join(
        parte
        for parte in [
            carimbo,
            normalizar_para_pasta(disciplina) or "DISCIPLINA",
            normalizar_para_pasta(turma) or "TURMA",
            normalizar_para_pasta(modo_ia) or "MODO",
        ]
        if parte
    )
    pasta_execucao = pasta_relatorios / nome_execucao
    pasta_execucao.mkdir(parents=True, exist_ok=True)

    cabecalho = [
        "RELATÓRIO DE CONFERÊNCIA DO PLANO",
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Professor: {professor}",
        f"Disciplina: {disciplina}",
        f"Turma selecionada: {turma}",
        f"Mês: {mes}",
        f"Bimestre: {bimestre}",
        f"Modo IA: {modo_ia}",
        f"Modo de envio dos PDFs: {modo_upload_pdf}",
        f"Pasta dos relatórios: {pasta_execucao}",
        "Observação: esta pasta é apenas para conferência e pode ser apagada depois sem afetar o sistema.",
        "",
    ]

    relatorio_lote = list(cabecalho)
    arquivos_salvos = []
    for t_idx, bloco in enumerate(turmas_processadas or []):
        turma_bloco = str(bloco.get("turma") or "").strip() or turma
        relatorio_lote.extend([f"TURMA: {turma_bloco}", ""])
        for a_idx, aula in enumerate(bloco.get("aulas") or [], start=1):
            texto_aula = _montar_texto_conferencia_aula(
                aula,
                a_idx,
                duplicadas_por_aula.get((t_idx, a_idx - 1), []),
            )
            relatorio_lote.append(texto_aula)
            nome_aula = f"aula_{a_idx:02d}_{normalizar_para_pasta(aula.get('tema') or 'sem_tema')[:60]}.txt"
            caminho_aula = pasta_execucao / nome_aula
            caminho_aula.write_text("\n".join(cabecalho) + f"TURMA: {turma_bloco}\n\n" + texto_aula, encoding="utf-8")
            arquivos_salvos.append(str(caminho_aula))

    caminho_lote = pasta_execucao / "relatorio_conferencia_lote.md"
    caminho_lote.write_text("\n".join(relatorio_lote), encoding="utf-8")
    paths = [str(caminho_lote)] + arquivos_salvos
    st.session_state["relatorio_conferencia_chave"] = chave
    st.session_state["relatorio_conferencia_paths"] = paths
    return paths
