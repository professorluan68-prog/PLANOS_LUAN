import streamlit as st
import re
import os
import unicodedata
from pathlib import Path
from datetime import date, timedelta

from config import MODELO_OPENAI_PADRAO, MODELO_GEMINI_PADRAO, TEMPLATES_DOCX_DIR, BASE_DIR
from core.database import (
    listar_vinculos_professores,
    obter_ultima_aula_gerada_sistema,
    salvar_historico_plano,
)
from core.disciplinas import (
    BIMESTRES,
    TURMAS_CDP_MULTISSERIADA,
    eh_cdp,
    eh_cdp_contextual,
    eh_cdp_multisseriada,
)
from core.modelos_docx import (
    resolver_template_id_geracao,
    caminho_template_central,
)
from core.constantes import MESES, HORARIOS_AULA
from ui.shared import (
    _mes_numero_app,
    _datas_horarios_do_mes,
    nome_arquivo_plano,
)
from core.helpers import LocalFileWrapper, ordenar_pdfs_por_numero


def _limpar_nome_pasta(nome: str) -> str:
    nome_norm = unicodedata.normalize("NFKD", str(nome or ""))
    nome_norm = "".join(ch for ch in nome_norm if not unicodedata.combining(ch))
    nome_norm = re.sub(r'[\\/:*?"<>|]', " ", nome_norm)
    return nome_norm.strip()


def _slug_lote(texto: str) -> str:
    texto_norm = unicodedata.normalize("NFKD", str(texto or ""))
    texto_norm = "".join(ch for ch in texto_norm if not unicodedata.combining(ch))
    texto_norm = re.sub(r"[^A-Za-z0-9_-]+", "_", texto_norm)
    return texto_norm.strip("_") or "item"


def _quantidade_aulas_lote_regular(total_datas: int, total_pdfs: int, reutilizar_pdf_unico: bool = False) -> int:
    total_datas = max(int(total_datas or 0), 0)
    total_pdfs = max(int(total_pdfs or 0), 0)
    if reutilizar_pdf_unico:
        return total_datas or total_pdfs
    if total_datas and total_pdfs:
        return min(total_datas, total_pdfs)
    return total_pdfs or total_datas


def _proxima_aula_cdp_lote(ultima_aula: int) -> int:
    return max(1, int(ultima_aula or 0) + 1)


def _nome_arquivo_plano_lote(professor: str, turma: str, disciplina: str, mes: str, ia_usada: bool = False) -> str:
    nome_base = nome_arquivo_plano(turma, disciplina, ia_usada=ia_usada)
    stem = Path(nome_base).stem
    suffix = Path(nome_base).suffix or ".docx"
    return f"{_slug_lote(professor)}_{_slug_lote(mes)}_{stem}{suffix}"

def _renderizar_geracao_lote(
    _gerar_docx_cdp_final_fn,
    _extrair_aulas_dos_pdfs_fn,
    _gerar_docx_final_fn,
) -> None:
    st.markdown('<div class="section-title">📦 Geração Automática em Lote</div>', unsafe_allow_html=True)
    st.caption("Gere os planos de todos os professores e turmas de uma só vez a partir da estrutura de pastas de arquivos PDFs.")

    # 1. Select Mes and Bimestre
    col_mes, col_bim, col_ia = st.columns([1, 1, 1])
    with col_mes:
        mes = st.selectbox("Mês de Referência", MESES, index=MESES.index("JUNHO") if "JUNHO" in MESES else 0, key="lote_mes")
    with col_bim:
        bimestre = st.selectbox("Bimestre", BIMESTRES, key="lote_bimestre")
    with col_ia:
        modo_ia = st.radio("Motor de Processamento", ["Sem IA", "OpenAI", "Gemini"], index=0, key="lote_modo_ia", horizontal=True)

    # 2. Paths
    _D_DRIVE_EXISTS = Path(r"D:\\").exists()
    default_raiz = f"D:\\PLANOS DE {mes}" if _D_DRIVE_EXISTS else str(BASE_DIR / f"planos_de_{mes.lower()}")
    raiz_dir = st.text_input("Diretório Raiz dos Professores", value=default_raiz, key="lote_raiz_dir")
    default_out = r"D:\PLANOS-FINALIZADOS" if _D_DRIVE_EXISTS else str(BASE_DIR / "planos_finalizados")
    out_dir = st.text_input("Diretório de Saída (Planos Word)", value=default_out, key="lote_out_dir")

    # 3. Actions
    col_btn1, col_btn2, _ = st.columns([2, 2, 4])
    with col_btn1:
        btn_criar = st.button("Criar Estrutura de Pastas", type="secondary", use_container_width=True)
    with col_btn2:
        btn_atualizar = st.button("Atualizar Status de PDFs", type="secondary", use_container_width=True)

    vinculos = listar_vinculos_professores()

    if btn_criar:
        criadas = 0
        for v in vinculos:
            prof_folder = _limpar_nome_pasta(v["professor"])
            disc_turma_folder = _limpar_nome_pasta(f"{v['disciplina']} - {v['turma']}")
            caminho_completo = Path(raiz_dir) / prof_folder / disc_turma_folder
            caminho_completo.mkdir(parents=True, exist_ok=True)
            criadas += 1
        st.success(f"Estrutura de pastas criada/atualizada com sucesso! Total de {criadas} pastas criadas em '{raiz_dir}'.")

    # 4. Scan paths
    status_rows = []
    for v in vinculos:
        prof_folder = _limpar_nome_pasta(v["professor"])
        disc_turma_folder = _limpar_nome_pasta(f"{v['disciplina']} - {v['turma']}")
        caminho_completo = Path(raiz_dir) / prof_folder / disc_turma_folder
        
        disciplina = v["disciplina"]
        comp_curricular = v["componente_curricular"] or disciplina
        is_cdp_mode = eh_cdp(disciplina) or eh_cdp_contextual(disciplina) or "CDP" in (disciplina + " " + comp_curricular).upper()
        
        pdf_count = 0
        if caminho_completo.exists():
            pdf_count = len(list(caminho_completo.glob("*.pdf")))
            
        if is_cdp_mode:
            status = "✅ Pronto (Modo CDP - Geração Direta)"
        elif pdf_count > 0:
            status = f"✅ Pronto ({pdf_count} PDF(s) encontrado(s))"
        else:
            status = "⚠️ Aguardando PDFs"
            
        status_rows.append({
            "Professor": v["professor"],
            "Disciplina": v["disciplina"],
            "Turma": v["turma"],
            "Tipo": "CDP" if is_cdp_mode else "Regular",
            "PDFs na Pasta": pdf_count if not is_cdp_mode else "N/A",
            "Status": status,
            "is_cdp": is_cdp_mode,
            "caminho_folder": caminho_completo,
            "vinculo": v
        })

    st.markdown("### 🔍 Status dos Arquivos dos Professores")
    df_show = []
    for row in status_rows:
        df_show.append({
            "Professor": row["Professor"],
            "Disciplina": row["Disciplina"],
            "Turma": row["Turma"],
            "Tipo": row["Tipo"],
            "PDFs": row["PDFs na Pasta"],
            "Status": row["Status"]
        })
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # 5. GERAR PLANOS
    a_gerar = [r for r in status_rows if r["is_cdp"] or (not r["is_cdp"] and isinstance(r["PDFs na Pasta"], int) and r["PDFs na Pasta"] > 0)]
    
    st.markdown("---")
    st.markdown(f"**Total de turmas prontas para geração**: {len(a_gerar)} / {len(status_rows)}")
    
    btn_gerar = st.button("GERAR TODOS OS PLANOS EM LOTE", type="primary", use_container_width=True)
    
    if btn_gerar:
        if not a_gerar:
            st.warning("Nenhuma turma pronta para geração. Coloque arquivos PDFs nas pastas das turmas Regulares.")
            return
            
        progress_bar = st.progress(0, text="Iniciando processamento em lote...")
        logs = []
        sucessos = 0
        erros_list = 0
        
        modelo_openai = os.environ.get("OPENAI_MODEL", MODELO_OPENAI_PADRAO) if modo_ia == "OpenAI" else ""
        modelo_gemini = os.environ.get("GEMINI_MODEL", MODELO_GEMINI_PADRAO) if modo_ia == "Gemini" else ""
        
        os.makedirs(out_dir, exist_ok=True)
        
        for idx, r in enumerate(a_gerar):
            pct = int((idx / len(a_gerar)) * 100)
            progress_bar.progress(pct, text=f"Gerando plano ({idx+1}/{len(a_gerar)}): {r['Professor']} - {r['Disciplina']} ({r['Turma']})")
            
            v = r["vinculo"]
            try:
                # Resolve templates
                comp_curricular = v["componente_curricular"] or v["disciplina"]
                template_id_central = resolver_template_id_geracao(
                    template_id=v["template_id"] or "",
                    disciplina=v["disciplina"],
                    componente_curricular=comp_curricular,
                    arquivo_modelo=v["arquivo"] or "",
                )
                caminho_template = caminho_template_central(template_id_central)
                if not caminho_template.exists():
                    if r["is_cdp"]:
                        caminho_template = Path(TEMPLATES_DOCX_DIR) / "MODELOCDP.docx"
                    else:
                        caminho_template = Path(TEMPLATES_DOCX_DIR) / "MODELOPADRE.docx"
                        if not caminho_template.exists():
                            caminho_template = Path(TEMPLATES_DOCX_DIR) / "MODELOEGLE.docx"
                            
                if not caminho_template.exists():
                    raise FileNotFoundError(f"Template Word não encontrado.")
                    
                modelo_bytes = caminho_template.read_bytes()
                
                # Escola final
                escola_final = "EE PROFª. EGLE LUPORINI COSTA"
                if "padre" in str(v["template_id"]).lower() or "padre" in str(v["arquivo"]).lower():
                    escola_final = "PADRE GERALDO LOURENÇO"
                elif "egle" in str(v["template_id"]).lower() or "egle" in str(v["arquivo"]).lower():
                    escola_final = "EE PROFª. EGLE LUPORINI COSTA"
                
                # Dates / horarios
                config_agenda_mes = {**v, "repetir_modelo_semanal": True}
                datas_horarios_mes = _datas_horarios_do_mes(config_agenda_mes, mes, v["turma"], extensao=0)
                
                # Filter holidays
                from core.calendario import datas_do_periodo, datas_feriado_padrao, datas_sem_aula_padrao, filtrar_datas_sem_aula, fim_periodo_mes_com_extensao
                inicio_periodo = date(date.today().year, _mes_numero_app(mes), 1)
                fim_periodo = fim_periodo_mes_com_extensao(date.today().year, _mes_numero_app(mes), 0)
                datas_opcoes_sem_aula = datas_do_periodo(inicio_periodo, fim_periodo)
                datas_sem_aula_default = datas_feriado_padrao(datas_opcoes_sem_aula) or datas_sem_aula_padrao(datas_horarios_mes)
                datas_horarios_mes = filtrar_datas_sem_aula(datas_horarios_mes, datas_sem_aula_default)
                
                if r["is_cdp"]:
                    # CDP Mode
                    ultima_aula = obter_ultima_aula_gerada_sistema(
                        v["professor"],
                        v["disciplina"],
                        v["turma"],
                        bimestre,
                    )
                    cdp_aula_inicial = _proxima_aula_cdp_lote(ultima_aula)
                    turma_cdp_val = ""
                    if eh_cdp_multisseriada(v["disciplina"]):
                        turma_cdp_val = TURMAS_CDP_MULTISSERIADA[0] if TURMAS_CDP_MULTISSERIADA else ""
                        
                    res_docx = _gerar_docx_cdp_final_fn(
                        modelo_bytes=modelo_bytes,
                        escola=escola_final,
                        professor=v["professor"],
                        disciplina=v["disciplina"],
                        turma_atual=v["turma"],
                        mes=mes,
                        bimestre=bimestre,
                        semana="",
                        observacao="",
                        cdp_aula_inicial=cdp_aula_inicial,
                        turma_cdp=turma_cdp_val,
                        modo_ia=modo_ia,
                        modelo_openai=modelo_openai,
                        modelo_gemini=modelo_gemini,
                        datas_horarios=datas_horarios_mes,
                        aulas_previstas_manual=str(v["aulas_semana"] or len(datas_horarios_mes))
                    )
                else:
                    # Regular Mode
                    pdf_files = ordenar_pdfs_por_numero(r["caminho_folder"].glob("*.pdf"))
                    local_pdfs = [LocalFileWrapper(p) for p in pdf_files]

                    orientacao_estudos_lote = "orienta" in str(v["disciplina"]).lower() and "estudo" in str(v["disciplina"]).lower()
                    reutilizar_pdf_unico = orientacao_estudos_lote and len(local_pdfs) == 1
                    num_rows = _quantidade_aulas_lote_regular(
                        len(datas_horarios_mes),
                        len(local_pdfs),
                        reutilizar_pdf_unico=reutilizar_pdf_unico,
                    )
                    if num_rows <= 0:
                        raise ValueError("Nenhum PDF válido foi encontrado para esta turma.")

                    if not datas_horarios_mes:
                        datas_horarios_mes = [{"data": date.today() + timedelta(days=i), "horario": HORARIOS_AULA[0]} for i in range(num_rows)]
                    elif not reutilizar_pdf_unico and len(local_pdfs) < len(datas_horarios_mes):
                        logs.append(
                            f"⚠️ **{v['professor']} - {v['disciplina']} ({v['turma']})**: pasta parcial detectada; "
                            f"o lote usou {len(local_pdfs)} PDF(s) para {len(datas_horarios_mes)} aula(s) previstas."
                        )

                    aulas_envio_lote = []
                    for j in range(num_rows):
                        item_dh = datas_horarios_mes[j] if j < len(datas_horarios_mes) else datas_horarios_mes[-1]
                        pdf_file = local_pdfs[0] if reutilizar_pdf_unico else local_pdfs[j]
                        aulas_envio_lote.append({
                            "data": item_dh["data"],
                            "horario": item_dh["horario"],
                            "pdf": pdf_file,
                            "dividir_pdf": False
                        })

                    res_extraction = _extrair_aulas_dos_pdfs_fn(
                        aulas_envio=aulas_envio_lote,
                        disciplina=v["disciplina"],
                        turma_atual=v["turma"],
                        bimestre=bimestre,
                        modo_ia=modo_ia,
                        modelo_openai=modelo_openai,
                        modelo_gemini=modelo_gemini,
                        dividir_metodologia=False,
                        modalidade_eja=False,
                        usar_ae_priorizado=False
                    )
                    
                    res_docx = _gerar_docx_final_fn(
                        modelo_bytes=modelo_bytes,
                        aulas=res_extraction["aulas"],
                        escola=escola_final,
                        professor=v["professor"],
                        disciplina=v["disciplina"],
                        componente_curricular=comp_curricular,
                        turma_atual=v["turma"],
                        mes=mes,
                        bimestre=bimestre,
                        semana="",
                        observacao="",
                        aulas_previstas_manual=str(v["aulas_semana"] or len(res_extraction["aulas"]))
                    )
                
                docx_data = res_docx["docx_bytes"].getvalue()
                ia_used = res_docx.get("ia_usada", False)
                filename = _nome_arquivo_plano_lote(v["professor"], v["turma"], v["disciplina"], mes, ia_usada=ia_used)
                filepath = Path(out_dir) / filename
                filepath.write_bytes(docx_data)
                
                salvar_historico_plano(v["professor"], v["disciplina"], v["turma"], filename, docx_data)
                
                sucessos += 1
                logs.append(f"✅ **{v['professor']} - {v['disciplina']} ({v['turma']})**: Gerado com sucesso -> `{filename}`")
                
            except Exception as exc:
                erros_list += 1
                logs.append(f"❌ **{v['professor']} - {v['disciplina']} ({v['turma']})**: Falha ao gerar -> {str(exc)}")
                
        progress_bar.progress(100, text="Processamento em lote concluído!")
        
        st.subheader("📊 Relatório de Geração em Lote")
        st.write(f"**Sucessos**: {sucessos} | **Falhas**: {erros_list}")
        for log in logs:
            st.write(log)
