import streamlit as st

# Importamos as funções do banco de dados que a sidebar precisa usar
# (Se o caminho para o teu database.py for diferente, avisa-me para ajustarmos)
from core.database import listar_historico_planos, obter_arquivo_historico

def render_sidebar(professores: list[str], modo_tela: str = "") -> None:
    """Sidebar modernizada com identidade visual SEDUC."""
    from ui.components_html import sidebar_logo, sidebar_section, badge, status_bar

    # Logo e identidade
    st.sidebar.markdown(sidebar_logo(), unsafe_allow_html=True)

    # Status do sistema
    st.sidebar.markdown(
        f"""
        <div style="margin:0 12px 16px; padding:10px 14px;
                    background:rgba(5,150,105,0.1); border:1px solid rgba(16,185,129,0.3);
                    border-radius:10px; display:flex; align-items:center; gap:8px;">
            <span class="status-dot green"></span>
            <span style="font-size:0.75rem; color:#34D399; font-weight:600;">
                Sistema Ativo — SEDUC
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Seção: Configuração de IA ──────────────────────────────────────────
    st.sidebar.markdown(sidebar_section("⚙️ Motor de Processamento"), unsafe_allow_html=True)

    modo_ia = st.sidebar.radio(
        "Motor de IA",
        options=["Sem IA", "OpenAI", "Gêmeos"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # Badge de status da IA
    if modo_ia != "Sem IA":
        st.sidebar.markdown(
            badge(f"🤖 {modo_ia} ativo", cor="purple"),
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Seção: Dados do Cabeçalho ──────────────────────────────────────────
    st.sidebar.markdown(sidebar_section("📝 Dados do Plano"), unsafe_allow_html=True)

    # Professor
    professor = st.sidebar.selectbox(
        "Professor",
        options=["(selecione o professor)"] + sorted(professores) + ["Outro (digitar)"],
        key="sidebar_professor_select",
    )

    if professor == "Outro (digitar)":
        professor = st.sidebar.text_input("Nome do professor", key="sidebar_professor")

    # Disciplina, Turma, Bimestre em layout compacto
    col_disc, col_turma = st.sidebar.columns(2)
    with col_disc:
        disciplina = st.sidebar.selectbox("Disciplina", options=["Arte", "Biologia", "Ciências", "Educação Física", "Filosofia", "Física", "Geografia", "História", "Língua Inglesa", "Língua Portuguesa", "Matemática", "Projeto de Vida", "Química", "Sociologia"], key="sidebar_disciplina_opcao")
    with col_turma:
        turma = st.sidebar.selectbox("Turma", options=["(selecione)"], key="sidebar_turma_select")

    col_bim, col_mes = st.sidebar.columns(2)
    with col_bim:
        bimestre = st.sidebar.selectbox("Bimestre", ["1º", "2º", "3º", "4º"], key="sidebar_bimestre")
    with col_mes:
        mes = st.sidebar.selectbox("Mês", ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"], key="sidebar_mes_select")

    # Escola e componente
    escola = st.sidebar.selectbox("Escola", options=["EE PROF. EGLE..."], key="sidebar_escola")
    componente = st.sidebar.text_input("Componente curricular", key="sidebar_componente_curricular")

    st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Seção: Ações Rápidas ───────────────────────────────────────────────
    st.sidebar.markdown(sidebar_section("⚡ Ações Rápidas"), unsafe_allow_html=True)

    if st.sidebar.button("🗑️ Limpar dados da tela", use_container_width=True, key="sidebar_limpar_dados"):
        # chamar limpar_dados_tela()
        pass

    # Informações do sistema no rodapé da sidebar
    st.sidebar.markdown(
        """
        <div style="position:fixed; bottom:0; left:0; width:var(--sidebar-width,280px);
                    padding:12px 20px; background:#0A1628;
                    border-top:1px solid #1A3A6B; font-size:0.7rem; color:#4B5563;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>Planos Luan v1.2.14</span>
                <span style="color:#2563EB;">● Online</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    """
    Desenha a barra lateral do sistema, incluindo o Histórico de Planos.
    """
    with st.sidebar:
        st.markdown("### Histórico de Planos")
        historico = listar_historico_planos()
        
        if not historico:
            st.info("Nenhum plano gerado ainda.")
        else:
            # Pega apenas os 5 mais recentes para não poluir
            for plano_id, prof, disc, t, data_gen, arq_nome in historico[:5]:
                with st.expander(f"{t} - {data_gen[:10]}"):
                    st.caption(f"Prof: {prof}")
                    st.caption(f"Arquivo: {arq_nome}")
                    
                    # Quando o usuário clicar, carrega o blob
                    if st.button("Preparar Download", key=f"prep_{plano_id}"):
                        arq_info = obter_arquivo_historico(plano_id)
                        if arq_info:
                            st.session_state[f"download_bytes_{plano_id}"] = arq_info[1]
                            
                    if f"download_bytes_{plano_id}" in st.session_state:
                        st.download_button(
                            label="📥 Baixar DOCX",
                            data=st.session_state[f"download_bytes_{plano_id}"],
                            file_name=arq_nome,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_hist_{plano_id}"
                        )
