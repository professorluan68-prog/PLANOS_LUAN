import streamlit as st

# Importamos as funções do banco de dados que a sidebar precisa usar
# (Se o caminho para o teu database.py for diferente, avisa-me para ajustarmos)
from core.database import listar_historico_planos, obter_arquivo_historico

def render_sidebar():
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
