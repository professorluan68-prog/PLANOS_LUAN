import streamlit as st
import re

from core.database import (
    buscar_historico_planos_avancado,
    obter_arquivo_historico,
    obter_bimestres_historico_planos,
    obter_meses_historico_planos,
    sincronizar_historico_planos_com_planos_feitos,
)


def _formatar_turma(turma: str) -> str:
    turma_display = re.sub(r"\s+", " ", str(turma or "").strip())
    turma_display = re.sub(
        r"\b(\d+)\s*[oOº°]\b",
        lambda match: f"{match.group(1)}\u00ba",
        turma_display,
    )
    turma_display = re.sub(r"\bE\s*\.?\s*F\.?\b", "E.F.", turma_display, flags=re.I)
    turma_display = re.sub(r"\bE\s*\.?\s*M\.?\b", "E.M.", turma_display, flags=re.I)

    match_multisseriada = re.fullmatch(r"((?:\d+\u00ba\s*){2,})(E\.[FM]\.)", turma_display)
    if match_multisseriada:
        anos = re.findall(r"\d+\u00ba", match_multisseriada.group(1))
        return f"{'/'.join(anos)} {match_multisseriada.group(2)}"

    return re.sub(
        r"(\d+)\u00ba\s+ANO",
        lambda match: f"{match.group(1)}\u00ba ANO",
        turma_display,
        flags=re.I,
    )


def _formatar_data(data_texto: str) -> str:
    data_formatada = str(data_texto or "")[:10]
    if len(data_formatada) == 10 and "-" in data_formatada:
        ano, mes, dia = data_formatada.split("-")
        return f"{dia}/{mes}/{ano}"
    return data_formatada


def _formatar_tamanho(tamanho: int | None) -> str:
    if tamanho is None:
        return ""
    if tamanho < 1024:
        return f"{tamanho} B"
    if tamanho < 1024 * 1024:
        return f"{tamanho / 1024:.1f} KB"
    return f"{tamanho / (1024 * 1024):.1f} MB"


def _formatar_resumo_aulas(ultima_aula: int | None, total_aulas: int | None) -> str:
    ultima = int(ultima_aula or 0)
    total = int(total_aulas or 0)
    if ultima <= 0 and total <= 0:
        return ""
    if total > 0 and ultima > 0:
        return f"Aulas: 1-{ultima} ({total})"
    if ultima > 0:
        return f"Última aula: {ultima}"
    return f"Aulas: {total}"


def _preparar_download_historico(plano_id: int) -> None:
    arquivo = obter_arquivo_historico(plano_id)
    if not arquivo:
        st.session_state.pop(f"historico_download_{plano_id}", None)
        return
    nome_arq, bytes_arq = arquivo
    if bytes_arq:
        st.session_state[f"historico_download_{plano_id}"] = {
            "nome": nome_arq,
            "bytes": bytes_arq,
        }
    else:
        st.session_state.pop(f"historico_download_{plano_id}", None)


def _renderizar_historico(professores_db):
    st.markdown(
        "<h2 class='section-header' style='margin-bottom: 24px;'>Historico de Planos Gerados</h2>",
        unsafe_allow_html=True,
    )

    col_sync, col_limite = st.columns([2, 1])
    with col_sync:
        if st.button("Atualizar indice de arquivos", use_container_width=True):
            inseridos = sincronizar_historico_planos_com_planos_feitos()
            if inseridos:
                st.success(f"{inseridos} arquivo(s) indexado(s).")
            else:
                st.info("Historico ja estava atualizado.")
    with col_limite:
        limite = st.selectbox("Limite", [50, 100, 200, 500], index=1)

    lista_professores = ["Todos"] + sorted(list(professores_db.keys()))
    meses_disponiveis = obter_meses_historico_planos()
    lista_meses = ["Todos"] + meses_disponiveis
    bimestres_disponiveis = obter_bimestres_historico_planos()
    lista_bimestres = ["Todos"] + bimestres_disponiveis

    col1, col2, col3 = st.columns(3)
    with col1:
        prof_selecionado = st.selectbox("Selecione o Professor", lista_professores)
    with col2:
        mes_selecionado = st.selectbox("Filtrar por Mes (Ano-Mes)", lista_meses)
    with col3:
        bimestre_selecionado = st.selectbox("Filtrar por Bimestre", lista_bimestres)

    col4, col5 = st.columns([2, 1])
    with col4:
        termo_busca = st.text_input("Buscar", placeholder="Professor, disciplina, turma ou arquivo")
    with col5:
        somente_disponiveis = st.checkbox("Somente disponiveis", value=True)

    filtro_professor = "" if prof_selecionado == "Todos" else prof_selecionado
    filtro_mes = "" if mes_selecionado == "Todos" else mes_selecionado
    filtro_bimestre = "" if bimestre_selecionado == "Todos" else bimestre_selecionado

    resultados = buscar_historico_planos_avancado(
        professor_nome=filtro_professor,
        mes=filtro_mes,
        bimestre=filtro_bimestre,
        termo_busca=termo_busca,
        somente_disponiveis=somente_disponiveis,
        limite=limite,
    )

    if not resultados:
        st.info("Nenhum plano encontrado para os filtros selecionados.")
    else:
        st.success(f"Foram encontrados {len(resultados)} plano(s).")

        for plano in resultados:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2.4, 1.7, 1.4, 1.4, 1.6])
                c1.markdown(f"**{plano['professor_nome']}**")
                c1.caption(plano["disciplina"])
                c2.markdown(f"**Turma:** {_formatar_turma(plano['turma'])}")
                c2.caption(plano.get("bimestre") or "Sem bimestre")
                c3.markdown(f"**Data:** {_formatar_data(plano['data_geracao'])}")
                detalhes = [
                    item
                    for item in [
                        _formatar_tamanho(plano.get("arquivo_tamanho")),
                        _formatar_resumo_aulas(
                            plano.get("ultima_aula"),
                            plano.get("total_aulas"),
                        ),
                    ]
                    if item
                ]
                c3.caption(" • ".join(detalhes))
                status = "Disponivel" if plano.get("arquivo_disponivel") else "Arquivo ausente"
                c4.markdown(f"**{status}**")
                c4.caption(plano.get("origem") or "sem origem")

                with c5:
                    chave_download = f"historico_download_{plano['id']}"
                    if plano.get("arquivo_disponivel"):
                        if st.button(
                            "Preparar",
                            key=f"prep_historico_{plano['id']}",
                            use_container_width=True,
                        ):
                            _preparar_download_historico(plano["id"])

                        download = st.session_state.get(chave_download)
                        if download:
                            st.download_button(
                                label="Baixar",
                                data=download["bytes"],
                                file_name=download["nome"] or f"plano_{plano['id']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_historico_{plano['id']}",
                                use_container_width=True,
                            )
                    else:
                        st.button("Indisponivel", key=f"ind_historico_{plano['id']}", disabled=True, use_container_width=True)
                st.caption(plano["arquivo_nome"])
                st.divider()
