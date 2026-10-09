import streamlit as st
import pandas as pd
from core.leitor_lista_pei import ler_lista_alunos_pei
from core.gerador_pei import gerar_docx_pei
from core.database import (
    connection_scope,
    obter_disciplinas_historico_por_professor,
    obter_turmas_historico_por_professor_disciplina_bimestre,
    obter_caminho_plano_historico_exato
)
import config
from pathlib import Path
import re

def encontrar_md_adaptado(disciplina, segmento, ano_str):
    base = Path(config.PLANOS_LUAN_DADOS_DIR) / "PASTA MESTRE - PLANOS PEI" / disciplina
    if not base.exists():
        return None
    
    ano_match = re.search(r'\d+', ano_str)
    ano_num = ano_match.group() if ano_match else "1"
    
    for md_file in base.rglob("Textos_Adaptados.md"):
        if ano_num in md_file.parent.name:
            if "Fundamental" in segmento and ("EM" not in md_file.parent.name and "EM" not in str(md_file.parent.parent)):
                return md_file
            if "Médio" in segmento and ("AF" not in md_file.parent.name and "AF" not in str(md_file.parent.parent)):
                return md_file
    return None

def _renderizar_pei(professores_db):
    st.markdown("<h2 class='section-header' style='margin-bottom: 24px;'>Gerador de PEI em Lote (Inclusão)</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    professores = sorted(professores_db.keys())
    professor = col1.selectbox("Professor", professores, index=None, placeholder="Selecione o professor")
    
    opcoes_disciplinas = []
    if professor:
        opcoes_disciplinas = obter_disciplinas_historico_por_professor(professor)
            
        # Merge with registered ones
        dados_prof = professores_db.get(professor, {})
        reg_disc = [d.get("disciplina", "") for d in dados_prof.get("disciplinas", [])]
        opcoes_disciplinas = sorted(list(dict.fromkeys(opcoes_disciplinas + reg_disc)))
    
    if not opcoes_disciplinas:
        opcoes_disciplinas = ["Língua Portuguesa", "Matemática", "História", "Geografia", "Ciências", "Biologia", "Arte"]
        
    disciplina = col2.selectbox("Disciplina", opcoes_disciplinas, index=None)
    
    bimestre = col3.selectbox("Bimestre", ["1", "2", "3", "4"], index=None, placeholder="Selecione o bimestre")
    
    # Buscar as turmas que esse professor gerou plano
    opcoes_turmas = []
    if professor and disciplina and bimestre:
        opcoes_turmas = obter_turmas_historico_por_professor_disciplina_bimestre(professor, disciplina, bimestre)
            
    turma_selecionada = st.selectbox("Turma/Sala", opcoes_turmas, index=None, placeholder="Selecione a Turma (apenas turmas com plano pronto)")
    
    st.markdown("---")
    arquivo_lista = st.file_uploader("📥 Envie a Lista Geral de Alunos da Escola (DOCX)", type=["docx"])
    
    if not professor or not disciplina or not bimestre or not turma_selecionada or not arquivo_lista:
        st.info("Preencha todos os filtros acima e envie o documento com a lista de alunos para prosseguir.")
        return
        
    with st.spinner("Lendo lista de alunos e filtrando pela turma..."):
        import tempfile
        import uuid
        temp_path = Path(tempfile.gettempdir()) / f"temp_lista_{uuid.uuid4().hex}.docx"
        with open(temp_path, "wb") as f:
            f.write(arquivo_lista.read())
        try:
            alunos_escola = ler_lista_alunos_pei(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        
    if not alunos_escola:
        st.error("Não foi possível extrair a lista de alunos. Verifique o formato do documento.")
        return

    from core.turma_matcher import limpar_turma_nome

    # FILTRO MÁGICO: Mostrar apenas alunos da turma selecionada
    t_selecionada_norm = limpar_turma_nome(turma_selecionada)
    
    alunos_filtrados = []
    for a in alunos_escola:
        t_doc_norm = limpar_turma_nome(a['turma_doc'])
        if t_doc_norm == t_selecionada_norm:
            alunos_filtrados.append(a)
            
    if not alunos_filtrados:
        st.warning(f"Não encontramos nenhum aluno de inclusão na lista para a turma '{turma_selecionada}'.")
        return
        
    caminho_plano_regular = obter_caminho_plano_historico_exato(professor, disciplina, bimestre, turma_selecionada)
        
    resultados = []
    for aluno in alunos_filtrados:
        if caminho_plano_regular:
            md_path = encontrar_md_adaptado(disciplina, aluno['segmento'], aluno['turma_doc'])
            if md_path:
                status = "✅ Pronto (Plano e Textos OK)"

                pode_gerar = True
            else:
                status = "⚠️ Faltam Textos_Adaptados.md"
                pode_gerar = False
                md_path = None
        else:
            status = "❌ Plano Regular Ausente"
            pode_gerar = False
            md_path = None
            
        resultados.append({
            "Aluno": aluno['nome'],
            "Turma": aluno['turma_doc'],
            "Segmento": aluno['segmento'],
            "Status": status,
            "_caminho_plano": caminho_plano_regular,
            "_md_path": md_path,
            "_pode_gerar": pode_gerar
        })
        
    df_result = pd.DataFrame(resultados)
    
    st.write(f"### Raio-X da Turma {turma_selecionada} ({len(alunos_filtrados)} alunos de inclusão)")
    st.dataframe(df_result[["Aluno", "Turma", "Segmento", "Status"]], use_container_width=True)
    
    alunos_aptos = [r for r in resultados if r["_pode_gerar"]]
    
    if alunos_aptos:
        if st.button("🚀 Gerar PEIs da Turma", type="primary"):
            import traceback
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            Path("lock_processamento.txt").touch()
            try:
                pasta_lote = Path(config.PLANOS_LUAN_DADOS_DIR) / "Planos feitos" / professor / f"PEI_{disciplina}" / f"{bimestre}_Bimestre"
                pasta_lote.mkdir(parents=True, exist_ok=True)
                
                sucessos = 0
                for i, aluno in enumerate(alunos_aptos):
                    status_text.text(f"Gerando PEI para {aluno['Aluno']}...")
                    aluno_seguro = re.sub(r'[^a-zA-Z0-9_\- ]', '', aluno['Aluno'])
                    turma_segura = re.sub(r'[^a-zA-Z0-9_\- ]', '', aluno['Turma'])
                    saida = pasta_lote / f"PEI_{aluno_seguro}_{turma_segura}.docx".replace(" ", "_")
                    
                    try:
                        gerar_docx_pei(
                            aluno=aluno['Aluno'],
                            prof=professor,
                            componente=disciplina,
                            bimestre=bimestre,
                            caminho_md=aluno['_md_path'],
                            caminho_plano=aluno['_caminho_plano'],
                            saida_path=saida
                        )
                        sucessos += 1
                    except Exception as e:
                        st.error(f"Erro ao gerar para {aluno['Aluno']}: {e}")
                        
                    progress_bar.progress((i + 1) / len(alunos_aptos))
                    
                status_text.text("Concluído!")
                st.success(f"Geração concluída! {sucessos} PEIs foram salvos em: {pasta_lote}")
            finally:
                Path("lock_processamento.txt").unlink(missing_ok=True)
