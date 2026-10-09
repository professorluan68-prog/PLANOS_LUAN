# ui/tela_inicial_moderna.py
"""
Tela inicial modernizada — Design System v2.0
Mantém compatibilidade com as importações existentes em planos_luan_app.py.
"""
import streamlit as st
from ui.components_html import (
    hero_section, card_secao, kpi_row, divider,
    alerta_customizado, sidebar_logo, sidebar_section,
    progress_steps, badge,
)

# ── Constantes de compatibilidade (mantidas para não quebrar importações) ──
HERO_CSS = ""  # CSS agora está em assets/style.css

HERO_HTML = hero_section(
    titulo="Planos de Aula",
    subtitulo=(
        "Geração automatizada de planejamento escolar com integração IA, "
        "processamento de guias pedagógicos e formatação Word padronizada pela SEDUC."
    ),
    stats=[
        {"valor": "23",  "label": "Disciplinas"},
        {"valor": "3",   "label": "Modelos DOCX"},
        {"valor": "2",   "label": "Motores IA"},
        {"valor": "5",   "label": "Modos de Uso"},
        {"valor": "+3K", "label": "Aulas Mapeadas"},
    ],
    features=[
        "📘 Leitura automática de PDFs",
        "📎 Processamento em lote",
        "✏️ Revisão e convalidação",
        "📄 Saída DOCX padronizada",
        "🤖 IA Integrada",
    ],
)

STATS_HTML = ""  # Incorporado ao HERO_HTML

SECTION_HEADER_HTML = """
<div style="display:flex; align-items:center; gap:10px; margin:24px 0 12px;">
    <div style="width:4px; height:24px; background:linear-gradient(180deg,#2563EB,#7C3AED);
                border-radius:2px;"></div>
    <span style="font-size:1rem; font-weight:700; color:#FFFFFF;">{titulo}</span>
</div>
"""

OPTION_MENU_STYLES = {
    "container": {
        "padding": "8px 12px",
        "background-color": "#0D1F3C",
        "border-bottom": "1px solid #1A3A6B",
    },
    "icon": {"color": "#93C5FD", "font-size": "16px"},
    "nav-link": {
        "font-size": "0.8rem",
        "font-weight": "500",
        "color": "#9CA3AF",
        "border-radius": "8px",
        "padding": "8px 16px",
        "margin": "0 2px",
        "--hover-color": "#112952",
    },
    "nav-link-selected": {
        "background": "linear-gradient(135deg, #1E4D8C, #2563EB)",
        "color": "#FFFFFF",
        "font-weight": "600",
        "box-shadow": "0 4px 12px rgba(37,99,235,0.3)",
    },
}


def renderizar_tela_inicial(stats_sistema: dict | None = None) -> None:
    """
    Renderiza a tela inicial completa com hero, KPIs e cards de funcionalidades.
    stats_sistema: {"professores": 12, "planos_mes": 45, "ultima_geracao": "hoje"}
    """
    stats_sistema = stats_sistema or {}

    # Hero principal
    st.markdown(HERO_HTML, unsafe_allow_html=True)

    # KPIs dinâmicos (se disponíveis)
    if stats_sistema:
        st.markdown(kpi_row([
            {"valor": str(stats_sistema.get("professores", "—")),
             "label": "Professores", "cor": "#3B82F6", "icone": "👨‍🏫"},
            {"valor": str(stats_sistema.get("planos_mes", "—")),
             "label": "Planos este mês", "cor": "#10B981", "icone": "📄"},
            {"valor": str(stats_sistema.get("turmas", "—")),
             "label": "Turmas ativas", "cor": "#8B5CF6", "icone": "🏫"},
            {"valor": stats_sistema.get("ultima_geracao", "—"),
             "label": "Última geração", "cor": "#F59E0B", "icone": "⏱️"},
        ]), unsafe_allow_html=True)

    st.markdown(divider("Como funciona"), unsafe_allow_html=True)

    # Cards de funcionalidades em colunas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(card_secao(
            titulo="Planos Gerais",
            subtitulo="Ensino Regular e EJA",
            icone="📘",
            cor="blue",
            conteudo_html="""
            <p style="font-size:0.82rem; color:#9CA3AF; line-height:1.6;">
                Gere planos mensais completos a partir de PDFs pedagógicos,
                com extração automática de habilidades BNCC e metodologia ativa.
            </p>
            """,
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(card_secao(
            titulo="Motor de IA",
            subtitulo="Gemini · OpenAI · Local",
            icone="🤖",
            cor="purple",
            status="ai",
            conteudo_html="""
            <p style="font-size:0.82rem; color:#9CA3AF; line-height:1.6;">
                Integração com Google Gemini e OpenAI para elaboração
                metodológica inteligente, com fallback heurístico automático.
            </p>
            """,
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(card_secao(
            titulo="PEI Inclusão",
            subtitulo="Planos Educacionais Individualizados",
            icone="♿",
            cor="green",
            status="success",
            conteudo_html="""
            <p style="font-size:0.82rem; color:#9CA3AF; line-height:1.6;">
                Geração automática de PEIs a partir da lista de alunos
                e dos planos regulares já aprovados.
            </p>
            """,
        ), unsafe_allow_html=True)