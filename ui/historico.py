import streamlit as st

from core.database import (
    buscar_historico_planos,
    obter_arquivo_historico,
    obter_meses_historico_planos,
    sincronizar_historico_planos_com_planos_feitos,
)


def _renderizar_historico(professores_db):
    st.markdown(
        "<h2 class='section-header' style='margin-bottom: 24px;'>Historico de Planos Gerados</h2>",
        unsafe_allow_html=True,
    )
    st.write("Consulte e baixe os planos de aula que ja foram gerados.")

    sincronizar_historico_planos_com_planos_feitos()

    lista_professores = [""] + sorted(list(professores_db.keys()))

    col1, col2 = st.columns(2)
    with col1:
        prof_selecionado = st.selectbox("Selecione o Professor", lista_professores)

    meses_disponiveis = obter_meses_historico_planos()
    lista_meses = ["Todos"] + meses_disponiveis
    with col2:
        mes_selecionado = st.selectbox("Filtrar por Mes (Ano-Mes)", lista_meses)

    if prof_selecionado:
        filtro_mes = "" if mes_selecionado == "Todos" else mes_selecionado
        resultados = buscar_historico_planos(prof_selecionado, filtro_mes)

        if not resultados:
            st.info("Nenhum plano encontrado para este professor no periodo selecionado.")
        else:
            st.success(f"Foram encontrados {len(resultados)} planos.")

            for plano in resultados:
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.markdown(f"**{plano['disciplina']}**")
                    import re
                    turma_display = plano['turma'].replace("O ANO", "\u00ba ANO").replace("o ANO", "\u00ba ANO")
                    turma_display = re.sub(r'(\d+)\s+ANO', r'\1\u00ba ANO', turma_display)
                    c2.markdown(f"**Turma:** {turma_display}")

                    data_formatada = plano["data_geracao"][:10]
                    if len(data_formatada) == 10:
                        ano, mes, dia = data_formatada.split("-")
                        data_formatada = f"{dia}/{mes}/{ano}"

                    c3.markdown(f"**Data:** {data_formatada}")

                    with c4:
                        nome_arq, bytes_arq = obter_arquivo_historico(plano["id"])
                        if bytes_arq:
                            st.download_button(
                                label="Baixar Plano",
                                data=bytes_arq,
                                file_name=nome_arq or f"plano_{plano['id']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_historico_{plano['id']}",
                                use_container_width=True,
                            )
                        else:
                            st.button(
                                "Indisponivel",
                                disabled=True,
                                key=f"dl_historico_nd_{plano['id']}",
                                use_container_width=True,
                            )
                    st.divider()
    else:
        st.info("Selecione um professor acima para carregar o historico de planos.")
