import streamlit as st
from pathlib import Path

from config import PASTA_BACKUP, PASTA_PLANOS_PROFESSORES, PLANOS_FINALIZADOS_DIR, BASE_DIR
from core.database import obter_professores_db
from ui.shared import (
    _diagnosticar_modelos_professores_cache,
    _carregar_professores_dos_planos_cache,
)

def _renderizar_diagnostico_modelos() -> None:
    st.markdown('<div class="section-title">Diagnóstico dos modelos</div>', unsafe_allow_html=True)
    st.caption("Confira se os modelos dos professores estão prontos para preenchimento automático.")

    col_atualizar, _ = st.columns([1, 4])
    with col_atualizar:
        if st.button("Atualizar diagnóstico"):
            _diagnosticar_modelos_professores_cache.clear()
            _carregar_professores_dos_planos_cache.clear()
            st.rerun()

    diagnostico = _diagnosticar_modelos_professores_cache()
    if diagnostico.get("erro_base"):
        st.error(str(diagnostico["erro_base"]))
        return

    professores_banco = obter_professores_db()
    professores_pasta = _carregar_professores_dos_planos_cache()

    col_total, col_ok, col_sem_hora, col_dup, col_banco = st.columns(5)
    col_total.metric("Modelos DOCX", int(diagnostico.get("total_docx", 0)))
    col_ok.metric("Lidos sem erro", int(diagnostico.get("lidos_ok", 0)))
    col_sem_hora.metric("Sem data/horário", len(diagnostico.get("sem_datas_horarios", [])))
    col_dup.metric("Duplicidades", len(diagnostico.get("duplicidades", [])))
    col_banco.metric("Banco / pastas", f"{len(professores_banco)} / {len(professores_pasta)}")

    erros = diagnostico.get("erros_leitura", [])
    sem_disciplina_turma = diagnostico.get("sem_disciplina_turma", [])
    sem_datas_horarios = diagnostico.get("sem_datas_horarios", [])
    duplicidades = diagnostico.get("duplicidades", [])

    if not erros and not sem_disciplina_turma and not duplicidades:
        st.success("Estrutura principal dos modelos lida sem erros.")

    with st.expander("Modelos sem data/horário detectável", expanded=bool(sem_datas_horarios)):
        if sem_datas_horarios:
            st.dataframe(sem_datas_horarios, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum modelo sem data/horário foi encontrado.")

    with st.expander("Duplicidades por professor, disciplina e turma", expanded=bool(duplicidades)):
        if duplicidades:
            linhas_dup = [
                {
                    "professor": item.get("professor", ""),
                    "disciplina": item.get("disciplina", ""),
                    "turma": item.get("turma", ""),
                    "arquivos": "\n".join(item.get("arquivos", [])),
                }
                for item in duplicidades
            ]
            st.dataframe(linhas_dup, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma duplicidade foi encontrada.")

    with st.expander("Arquivos sem disciplina/turma ou com erro de leitura", expanded=bool(erros or sem_disciplina_turma)):
        if sem_disciplina_turma:
            st.markdown("**Sem disciplina ou turma**")
            st.dataframe(sem_disciplina_turma, use_container_width=True, hide_index=True)
        if erros:
            st.markdown("**Erro de leitura**")
            st.dataframe(erros, use_container_width=True, hide_index=True)
        if not erros and not sem_disciplina_turma:
            st.info("Nenhum problema de leitura foi encontrado.")

    with st.expander("Backup e restauração"):
        st.caption("Use estes comandos quando quiser fazer uma cópia completa fora do sistema.")
        st.code(
            "\n".join(
                [
                    "$Data = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'",
                    f"$Backup = \"{PASTA_BACKUP}\\BACKUP_$Data\"",
                    f"Copy-Item -LiteralPath \"{BASE_DIR}\" -Destination \"$Backup\\PLANOS_LUAN\" -Recurse -Force",
                    f"Copy-Item -LiteralPath \"{PASTA_PLANOS_PROFESSORES}\" -Destination \"$Backup\\{PASTA_PLANOS_PROFESSORES.name}\" -Recurse -Force",
                    f"Copy-Item -LiteralPath \"{PLANOS_FINALIZADOS_DIR}\" -Destination \"$Backup\\PLANOS-FINALIZADOS\" -Recurse -Force",
                    "Compress-Archive -Path \"$Backup\\*\" -DestinationPath \"$Backup.zip\" -Force",
                ]
            ),
            language="powershell",
        )
