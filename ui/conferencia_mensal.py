import streamlit as st
from datetime import datetime

from core.database import (
    obter_arquivo_historico,
    obter_conferencia_mensal,
    obter_meses_conferencia,
    sincronizar_historico_planos_com_planos_feitos,
)
from ui.historico import _formatar_data, _formatar_mes_plano, _formatar_turma


def _opcoes_meses() -> list[str]:
    meses = set(obter_meses_conferencia())
    meses.add(datetime.now().strftime("%Y-%m"))
    return sorted((m for m in meses if _formatar_mes_plano(m)), reverse=True)


def _renderizar_conferencia_mensal(professores_db):
    st.markdown(
        "<h2 class='section-header' style='margin-bottom: 24px;'>Conferência Mensal de Planos</h2>",
        unsafe_allow_html=True,
    )

    if not st.session_state.get("conf_indexado"):
        with st.spinner("Verificando planos novos..."):
            sincronizar_historico_planos_com_planos_feitos()
        st.session_state["conf_indexado"] = True

    if st.button("Atualizar índice de arquivos", key="conf_sync"):
        inseridos = sincronizar_historico_planos_com_planos_feitos()
        if inseridos:
            st.success(f"{inseridos} arquivo(s) indexado(s).")
            st.rerun()
        else:
            st.info("Histórico já estava atualizado.")

    professores = sorted(professores_db.keys())
    meses = _opcoes_meses()
    col1, col2 = st.columns([2, 1])
    professor = col1.selectbox("Professor", professores, index=None, placeholder="Selecione o professor", key="conf_prof")
    mes = col2.selectbox("Mês do plano", meses, format_func=_formatar_mes_plano, key="conf_mes")

    if not professor or not mes:
        st.info("Selecione o professor e o mês para conferir os planos.")
        return

    itens = obter_conferencia_mensal(professor, mes)
    if not itens:
        st.warning("Este professor não possui turmas cadastradas.")
        return

    feitos = sum(1 for i in itens if i["feito"])
    st.progress(feitos / len(itens), text=f"{feitos} de {len(itens)} planos prontos em {_formatar_mes_plano(mes)}")
    somente_pendentes = st.checkbox("Mostrar somente pendentes", key="conf_pend")

    for n, item in enumerate(itens):
        if somente_pendentes and item["feito"]:
            continue
        c1, c2, c3 = st.columns([3, 2, 1.5])
        icone = "✅" if item["feito"] else "⬜"
        c1.markdown(f"{icone} **{item['disciplina']}**")
        c1.caption(f"Turma: {_formatar_turma(item['turma'])}")
        if item["feito"]:
            c2.caption(f"Gerado em {_formatar_data(item['data_geracao'])}")
            dados = obter_arquivo_historico(item["plano_id"])
            if dados and dados[1]:
                c3.download_button(
                    "Baixar",
                    data=dados[1],
                    file_name=dados[0] or "plano.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"conf_dl_{n}",
                )
        elif item["registro_sem_arquivo"]:
            c2.caption("⚠️ Registrado, mas o arquivo .docx não foi encontrado")
        else:
            c2.caption("Pendente")
