import streamlit as st
from pathlib import Path

from core.cdp_em_docx import reescrever_docx_cdp_contextual_matematica

def _renderizar_reescrita_cdp_em() -> None:
    st.markdown('<div class="section-title">Reescrita de Plano CDP Contextual</div>', unsafe_allow_html=True)
    st.caption(
        "Envie um plano em DOCX do CDP contextual de Matemática para reescrever o título do material, "
        "o desenvolvimento, o acompanhamento e a acessibilidade no padrão EJA/CDP."
    )

    arquivo = st.file_uploader(
        "Plano em DOCX",
        type=["docx"],
        key="arquivo_reescrita_cdp_em",
    )

    if arquivo is not None:
        st.info(f"Arquivo carregado: {arquivo.name}")

    if st.button("Reescrever plano CDP E.M.", type="primary", disabled=arquivo is None, key="btn_reescrever_cdp_em"):
        try:
            corrigido_bytes, relatorio = reescrever_docx_cdp_contextual_matematica(arquivo.getvalue())
            nome_base = Path(arquivo.name).stem
            nome_saida = f"{nome_base}_metodologia_reescrita.docx"
            st.success(f"Plano reescrito com sucesso. Linhas ajustadas: {relatorio.get('linhas_reescritas', 0)}")
            temas = relatorio.get("temas") or []
            if temas:
                st.caption("Temas identificados: " + " | ".join(str(t) for t in temas[:8]))
            st.download_button(
                "Baixar DOCX reescrito",
                data=corrigido_bytes,
                file_name=nome_saida,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_reescrita_cdp_em",
            )
        except Exception as exc:
            st.error(f"Não foi possível reescrever o plano: {exc}")
