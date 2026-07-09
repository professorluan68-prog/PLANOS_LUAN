import streamlit as st
import pandas as pd
from core.database import obter_meses_historico_planos, buscar_historico_planos, obter_arquivo_historico

def _renderizar_historico(professores_db):
    st.markdown("<h2 class='section-header' style='margin-bottom: 24px;'>Histórico de Planos Gerados</h2>", unsafe_allow_html=True)
    st.write("Consulte e baixe os planos de aula que já foram gerados.")
    
    lista_professores = [""] + sorted(list(professores_db.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        prof_selecionado = st.selectbox("Selecione o Professor", lista_professores)
    
    meses_disponiveis = obter_meses_historico_planos()
    lista_meses = ["Todos"] + meses_disponiveis
    with col2:
        mes_selecionado = st.selectbox("Filtrar por Mês (Ano-Mês)", lista_meses)
        
    if prof_selecionado:
        filtro_mes = "" if mes_selecionado == "Todos" else mes_selecionado
        resultados = buscar_historico_planos(prof_selecionado, filtro_mes)
        
        if not resultados:
            st.info("Nenhum plano encontrado para este professor no período selecionado.")
        else:
            st.success(f"Foram encontrados {len(resultados)} planos.")
            
            for plano in resultados:
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.markdown(f"**{plano['disciplina']}**")
                    c2.markdown(f"**Turma:** {plano['turma']}")
                    
                    data_formatada = plano['data_geracao'][:10]
                    if len(data_formatada) == 10:
                        ano, mes, dia = data_formatada.split('-')
                        data_formatada = f"{dia}/{mes}/{ano}"
                    
                    c3.markdown(f"**Data:** {data_formatada}")
                    
                    with c4:
                        nome_arq, bytes_arq = obter_arquivo_historico(plano['id'])
                        if bytes_arq:
                            st.download_button(
                                label="📥 Baixar Plano",
                                data=bytes_arq,
                                file_name=nome_arq or f"plano_{plano['id']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_historico_{plano['id']}",
                                use_container_width=True
                            )
                        else:
                            st.button("Indisponível", disabled=True, key=f"dl_historico_nd_{plano['id']}", use_container_width=True)
                    st.divider()
    else:
        st.info("Selecione um professor acima para carregar o histórico de planos.")
