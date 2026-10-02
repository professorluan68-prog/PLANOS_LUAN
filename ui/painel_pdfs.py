"""
Módulo de renderização do painel de PDFs e organização das aulas.
"""
from __future__ import annotations

import html
from pathlib import Path
import streamlit as st


def _nome_pdf_para_tela(arquivo) -> str:
    return html.escape(str(getattr(arquivo, "name", None) or Path(str(arquivo)).name))


def _render_painel_pdfs(
    *,
    modo: str,
    necessarios: int,
    carregados: int,
    total_aulas: int = 0,
    dividir_metodologia: bool = False,
    encontrados: int = 0,
    pasta: str = "",
    selecionados=None,
    faltantes_ae=None,
) -> None:
    selecionados = list(selecionados or [])
    faltantes_ae = list(faltantes_ae or [])
    necessarios = max(0, int(necessarios or 0))
    carregados = max(0, int(carregados or 0))
    total_aulas = max(0, int(total_aulas or 0))
    encontrados = max(0, int(encontrados or 0))
    modo_texto = str(modo or "-").strip()
    if modo_texto != "Automatico":
        pasta = ""
        encontrados = 0
        faltantes_ae = []
    faltam = max(necessarios - carregados, 0)
    excedentes = max(carregados - necessarios, 0)
    progresso = 0 if necessarios <= 0 else min(100, int(round((carregados / necessarios) * 100)))

    if necessarios <= 0:
        status_texto = "Aguardando modelo"
        status_classe = "neutral"
        orientacao = "Selecione professor, turma e modelo para o sistema calcular quantos PDFs serao usados."
    elif faltam > 0:
        status_texto = f"Faltam {faltam}"
        status_classe = "warning"
        orientacao = f"Adicione mais {faltam} PDF(s) para completar o plano."
    elif excedentes > 0:
        status_texto = f"{excedentes} a mais"
        status_classe = "warning"
        orientacao = "Revise a selecao: ha mais PDFs do que a organizacao atual exige."
    else:
        status_texto = "Completo"
        status_classe = "success"
        orientacao = "Tudo certo: a quantidade de PDFs bate com a organizacao escolhida."

    criterio_pdfs = "1 PDF para cada par de aulas marcado" if dividir_metodologia else "1 PDF por aula"
    aulas_rotulo = total_aulas or necessarios

    html_code = (
        f'<div class="pdf-dashboard">'
        f'<div class="pdf-dashboard__header">'
        f'<div>'
        f'<span class="pdf-dashboard__eyebrow">Painel dos PDFs</span>'
        f'<div class="pdf-dashboard__title">Organização das aulas</div>'
        f'<div class="pdf-dashboard__subtitle">{orientacao}</div>'
        f'</div>'
        f'<div class="pdf-dashboard__status pdf-dashboard__status--{status_classe}">{status_texto}</div>'
        f'</div>'
        f'<div class="pdf-dashboard__stats">'
        f'<div class="pdf-stat"><span>Modo</span><strong>{modo_texto}</strong></div>'
        f'<div class="pdf-stat"><span>Necessários</span><strong>{necessarios}</strong></div>'
        f'<div class="pdf-stat"><span>Agendados</span><strong>{carregados}</strong></div>'
        f'<div class="pdf-stat"><span>Encontrados</span><strong>{encontrados}</strong></div>'
        f'</div>'
        f'<div class="pdf-progress"><div class="pdf-progress__bar" style="width: {progresso}%;"></div></div>'
        f'</div>'
    )
    st.markdown(html_code, unsafe_allow_html=True)

    st.caption(f"{carregados}/{necessarios or 0} PDF(s) prontos para processamento | {criterio_pdfs}")

    if pasta:
        st.caption(f"Pasta automatica: {pasta}")

    if faltantes_ae:
        faltantes_txt = ", ".join(f"AULA {int(numero)}" for numero in faltantes_ae)
        st.warning(f"PDFs AE nao encontrados: {faltantes_txt}")

    st.markdown("**Ordem que sera processada**")
    if selecionados:
        for indice, item in enumerate(selecionados, start=1):
            st.write(f"{indice}. {_nome_pdf_para_tela(item)}")
    else:
        st.caption("Nenhum PDF selecionado ainda.")
