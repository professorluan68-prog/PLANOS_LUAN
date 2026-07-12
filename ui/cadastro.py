import streamlit as st
import re
import unicodedata
from datetime import date
from pathlib import Path

from core.database import (
    listar_vinculos_professores,
    atualizar_vinculo_professor,
    salvar_professor_turma,
    duplicar_vinculo_professor,
    excluir_vinculo_professor,
)
from core.modelos_docx import (
    resolver_template_id_geracao,
    caminho_template_central,
)
from core.disciplinas import nomes_disciplinas
from ui.shared import (
    _chave_cadastro,
    _eh_cadastro_cdp_eja,
    _arquivo_existe,
    _diagnosticar_modelos_professores_cache,
    _carregar_professores_dos_planos_cache,
    _ler_bytes_arquivo_cache,
    _rotulo_cadastro,
    _slug_key,
    _selecionar_turma,
    _selecionar_aulas_semana,
    _rotulo_horario,
    _serializar_horarios_padronizados,
    _turno_e_aulas_de_horario,
    _montar_horario_flexivel,
    DIAS_SEMANA_CADASTRO,
    TURNOS_HORARIOS,
    _defaults_grade_horarios,
)

def _cadastros_para_gestao() -> list[dict]:
    cadastros = []
    chaves_banco = {}

    for item in listar_vinculos_professores():
        cadastro = dict(item)
        cadastro["id_cadastro"] = f"banco:{cadastro.get('id')}"
        cadastro["origem"] = "Banco"
        cadastro["editavel_banco"] = True
        template_path = caminho_template_central(
            resolver_template_id_geracao(
                template_id=cadastro.get("template_id") or "",
                disciplina=cadastro.get("disciplina", ""),
                componente_curricular=cadastro.get("componente_curricular", ""),
                arquivo_modelo=cadastro.get("arquivo") or "",
            )
        )
        cadastro["template_central"] = str(template_path)
        cadastro["sem_modelo"] = not template_path.exists()
        chave = _chave_cadastro(
            cadastro.get("professor", ""),
            cadastro.get("disciplina", ""),
            cadastro.get("turma", ""),
            cadastro.get("componente_curricular", ""),
        )
        chaves_banco.setdefault(chave, cadastro)
        cadastros.append(cadastro)

    # Nota: A pasta dos professores não está sendo iterada aqui (conforme estrutura original simplificada)
    for professor, dados in _carregar_professores_dos_planos_cache().items():
        for indice, item in enumerate(dados.get("disciplinas", [])):
            chave = _chave_cadastro(
                professor,
                item.get("disciplina", ""),
                item.get("turma", ""),
                item.get("componente_curricular", ""),
            )
            modelo = {
                "id": None,
                "professor": professor,
                "disciplina": item.get("disciplina", ""),
                "turma": item.get("turma", ""),
                "dia_semana": item.get("dia_semana", ""),
                "horario": item.get("horario", ""),
                "aulas_semana": item.get("aulas_semana", ""),
                "arquivo": item.get("arquivo", ""),
                "arquivo_modelo": item.get("arquivo", ""),
                "componente_curricular": item.get("componente_curricular", ""),
                "datas_horarios": item.get("datas_horarios") or [],
                "origem": "Pasta DOCX",
                "editavel_banco": False,
                "sem_modelo": not _arquivo_existe(item.get("arquivo", "")),
            }

            existente = chaves_banco.get(chave)
            if existente:
                for campo in ["arquivo", "arquivo_modelo", "componente_curricular", "dia_semana", "horario", "aulas_semana", "datas_horarios"]:
                    if not existente.get(campo) and modelo.get(campo):
                        existente[campo] = modelo[campo]
                if modelo.get("arquivo"):
                    existente["origem"] = "Banco + DOCX"
                    existente["sem_modelo"] = False
                continue

            modelo["id_cadastro"] = f"modelo:{indice}:{modelo['arquivo']}"
            cadastros.append(modelo)

    return sorted(
        cadastros,
        key=lambda item: (
            item.get("professor", ""),
            item.get("disciplina", ""),
            item.get("turma", ""),
            item.get("componente_curricular", ""),
            item.get("id") or 0,
        ),
    )

def _limpar_cache_cadastro() -> None:
    _carregar_professores_dos_planos_cache.clear()
    _diagnosticar_modelos_professores_cache.clear()
    _ler_bytes_arquivo_cache.clear()

def _preparar_modelo_cadastro(
    professor: str,
    disciplina: str,
    turma: str,
    aulas_semana: str,
    arquivo_modelo: str = "",
    componente_curricular: str = "",
) -> tuple[str, str]:
    template_id = resolver_template_id_geracao(
        disciplina=disciplina,
        componente_curricular=componente_curricular,
        arquivo_modelo=arquivo_modelo,
    )
    template_path = caminho_template_central(template_id)
    if template_path.exists():
        return arquivo_modelo or "", ""
    return (
        arquivo_modelo or "",
        f"Cadastro salvado, mas o modelo central {template_path.name} nao foi encontrado em templates.",
    )

def _salvar_cadastro_gerenciado(
    cadastro_id,
    professor: str,
    disciplina: str,
    turma: str,
    dia_semana: str,
    horario: str,
    aulas_semana: str,
    arquivo_modelo: str,
    componente_curricular: str,
) -> tuple[str, str]:
    arquivo_corrigido, aviso = _preparar_modelo_cadastro(
        professor,
        disciplina,
        turma,
        aulas_semana,
        arquivo_modelo,
        componente_curricular,
    )
    template_id = resolver_template_id_geracao(
        disciplina=disciplina,
        componente_curricular=componente_curricular,
        arquivo_modelo=arquivo_corrigido or arquivo_modelo,
    )
    if cadastro_id:
        atualizar_vinculo_professor(
            cadastro_id,
            professor,
            disciplina,
            turma,
            dia_semana,
            horario,
            aulas_semana,
            arquivo_corrigido,
            componente_curricular,
            template_id,
        )
    else:
        salvar_professor_turma(
            professor,
            disciplina,
            turma,
            dia_semana,
            horario,
            aulas_semana,
            arquivo_corrigido,
            componente_curricular,
            template_id,
        )
    return arquivo_corrigido, aviso

def _renderizar_grade_horarios(prefixo: str, dia_texto: str = "", horario_texto: str = "", contexto: str = "") -> tuple[str, str, int]:
    st.markdown("**Grade semanal de horários**")
    st.caption("Selecione o turno e as aulas de cada dia. Deixe vazio o dia em que não há aula.")
    defaults = _defaults_grade_horarios(dia_texto, horario_texto, contexto)
    selecionados = []
    turnos = list(TURNOS_HORARIOS.keys())

    for indice, dia in enumerate(DIAS_SEMANA_CADASTRO):
        default_dia = defaults.get(dia, {})
        turno_default = str(default_dia.get("turno") or "Manhã")
        aulas_opcoes_default = [f"{numero}ª" for numero in range(1, len(TURNOS_HORARIOS.get(turno_default, TURNOS_HORARIOS["Manhã"])))]
        aulas_default = [aula for aula in default_dia.get("aulas", []) if aula in aulas_opcoes_default]

        col_dia, col_turno, col_aulas, col_previa = st.columns([1.1, 1.1, 2.2, 2.1])
        with col_dia:
            st.markdown(f"**{dia}**")
        with col_turno:
            turno = st.selectbox(
                "Turno",
                turnos,
                index=turnos.index(turno_default) if turno_default in turnos else 0,
                key=f"{prefixo}_turno_{indice}",
                label_visibility="collapsed",
            )
        aulas_opcoes = [f"{numero}ª" for numero in range(1, len(TURNOS_HORARIOS[turno]))]
        aulas_default = [aula for aula in aulas_default if aula in aulas_opcoes]
        with col_aulas:
            aulas = st.multiselect(
                "Aulas",
                aulas_opcoes,
                default=aulas_default,
                key=f"{prefixo}_aulas_{indice}",
                label_visibility="collapsed",
            )
        horario = _montar_horario_flexivel(turno, aulas)
        with col_previa:
            st.caption(_rotulo_horario(horario) if horario else "Sem aula neste dia")
        if horario:
            selecionados.append({"dia": dia, "horario": horario, "aulas": aulas})

    dia_serializado = " - ".join(item["dia"] for item in selecionados)
    horario_serializado = _serializar_horarios_padronizados([item["horario"] for item in selecionados])
    total_aulas = sum(len(item["aulas"]) for item in selecionados)
    if total_aulas:
        st.caption(f"Total selecionado na semana: {total_aulas} aula(s).")
    return dia_serializado, horario_serializado, total_aulas

def _renderizar_metricas_cadastro(cadastros: list[dict], diagnostico: dict) -> None:
    professores = {cad.get("professor") for cad in cadastros if cad.get("professor")}
    sem_modelo = [cad for cad in cadastros if cad.get("sem_modelo")]
    duplicidades = diagnostico.get("duplicidades", []) if diagnostico else []
    col_prof, col_vinc, col_sem_modelo, col_dup = st.columns(4)
    col_prof.metric("Professores", len(professores))
    col_vinc.metric("Cadastros", len(cadastros))
    col_sem_modelo.metric("Sem DOCX", len(sem_modelo))
    col_dup.metric("Duplicidades", len(duplicidades))

def _filtrar_cadastros(cadastros: list[dict]) -> list[dict]:
    professores = ["Todos"] + sorted({cad.get("professor", "") for cad in cadastros if cad.get("professor")})
    disciplinas = ["Todas"] + sorted({cad.get("disciplina", "") for cad in cadastros if cad.get("disciplina")})
    turmas = ["Todas"] + sorted({cad.get("turma", "") for cad in cadastros if cad.get("turma")})
    origens = ["Todas"] + sorted({cad.get("origem", "") for cad in cadastros if cad.get("origem")})
    if st.session_state.get("cadastro_filtro_professor") not in professores:
        st.session_state["cadastro_filtro_professor"] = "Todos"
    if st.session_state.get("cadastro_filtro_disciplina") not in disciplinas:
        st.session_state["cadastro_filtro_disciplina"] = "Todas"
    if st.session_state.get("cadastro_filtro_turma") not in turmas:
        st.session_state["cadastro_filtro_turma"] = "Todas"
    if st.session_state.get("cadastro_filtro_origem") not in origens:
        st.session_state["cadastro_filtro_origem"] = "Todas"

    col_prof, col_disc, col_turma, col_origem, col_sem = st.columns([2, 1.5, 1.5, 1.5, 1])
    with col_prof:
        filtro_prof = st.selectbox("Professor", professores, key="cadastro_filtro_professor")
    with col_disc:
        filtro_disc = st.selectbox("Disciplina", disciplinas, key="cadastro_filtro_disciplina")
    with col_turma:
        filtro_turma = st.selectbox("Turma", turmas, key="cadastro_filtro_turma")
    with col_origem:
        filtro_origem = st.selectbox("Origem", origens, key="cadastro_filtro_origem")
    with col_sem:
        apenas_sem_modelo = st.checkbox("Sem DOCX", key="cadastro_filtro_sem_modelo")

    busca = st.text_input("Buscar por professor, disciplina, turma ou horario", key="cadastro_busca")
    busca_norm = _chave_cadastro(busca, "", "", "")[0] if busca else ""

    filtrados = []
    for cadastro in cadastros:
        if filtro_prof != "Todos" and cadastro.get("professor") != filtro_prof:
            continue
        if filtro_disc != "Todas" and cadastro.get("disciplina") != filtro_disc:
            continue
        if filtro_turma != "Todas" and cadastro.get("turma") != filtro_turma:
            continue
        if filtro_origem != "Todas" and cadastro.get("origem") != filtro_origem:
            continue
        if apenas_sem_modelo and not cadastro.get("sem_modelo"):
            continue
        if busca_norm:
            texto = _chave_cadastro(
                cadastro.get("professor", ""),
                cadastro.get("disciplina", ""),
                f"{cadastro.get('turma', '')} {cadastro.get('horario', '')}",
                cadastro.get("componente_curricular", ""),
            )
            if busca_norm not in " ".join(texto):
                continue
        filtrados.append(cadastro)
    return filtrados

def _renderizar_tabela_cadastros(cadastros: list[dict]) -> None:
    linhas = [
        {
            "Professor": cad.get("professor", ""),
            "Disciplina": cad.get("disciplina", ""),
            "Componente": cad.get("componente_curricular", ""),
            "Turma": cad.get("turma", ""),
            "Aulas": cad.get("aulas_semana", ""),
            "Origem": cad.get("origem", ""),
            "DOCX": "ok" if not cad.get("sem_modelo") else "sem modelo",
        }
        for cad in cadastros
    ]
    st.dataframe(linhas, use_container_width=True, hide_index=True)

def _renderizar_editor_cadastro(cadastros: list[dict]) -> None:
    st.markdown("**Consultar e editar cadastros**")
    filtrados = _filtrar_cadastros(cadastros)
    if not filtrados:
        st.info("Nenhum cadastro encontrado com estes filtros.")
        return

    _renderizar_tabela_cadastros(filtrados)
    opcoes = {cad["id_cadastro"]: cad for cad in filtrados}
    if st.session_state.get("cadastro_selecionado") not in opcoes:
        st.session_state["cadastro_selecionado"] = next(iter(opcoes))
    escolha = st.selectbox(
        "Cadastro para editar",
        list(opcoes.keys()),
        format_func=lambda chave: _rotulo_cadastro(opcoes[chave]),
        key="cadastro_selecionado",
    )
    cadastro = opcoes[escolha]
    chave_ui = _slug_key(escolha)
    if not cadastro.get("editavel_banco"):
        st.info("Este cadastro veio somente da pasta de DOCX. Ao salvar, ele sera registrado no banco.")

    with st.form(f"form_editar_cadastro_{chave_ui}"):
        col_prof, col_disc = st.columns(2)
        with col_prof:
            professor_edit = st.text_input("Professor", value=str(cadastro.get("professor") or ""), key=f"edit_prof_{chave_ui}").strip().upper()
        with col_disc:
            disciplina_edit = st.text_input("Disciplina", value=str(cadastro.get("disciplina") or ""), key=f"edit_disc_{chave_ui}").strip()

        col_turma, col_aulas = st.columns([2, 1])
        with col_turma:
            turma_edit = st.text_input("Turma", value=str(cadastro.get("turma") or ""), key=f"edit_turma_{chave_ui}").strip()
        with col_aulas:
            aulas_edit = st.text_input("Aulas por semana", value=str(cadastro.get("aulas_semana") or ""), key=f"edit_aulas_{chave_ui}").strip()

        componente_edit = st.text_input(
            "Componente curricular",
            value=str(cadastro.get("componente_curricular") or cadastro.get("disciplina") or ""),
            key=f"edit_comp_{chave_ui}",
        ).strip()
        arquivo_edit = ""

        dia_edit, horario_edit, total_grade = _renderizar_grade_horarios(
            f"edit_grade_{chave_ui}",
            str(cadastro.get("dia_semana") or ""),
            str(cadastro.get("horario") or ""),
            turma_edit,
        )

        salvar_edicao = st.form_submit_button("Salvar alteracoes", type="primary")
        if salvar_edicao:
            try:
                if not professor_edit or not disciplina_edit or not turma_edit:
                    st.error("Preencha professor, disciplina e turma.")
                else:
                    aulas_final = aulas_edit or (str(total_grade) if total_grade else "")
                    _, aviso = _salvar_cadastro_gerenciado(
                        cadastro.get("id"),
                        professor_edit,
                        disciplina_edit,
                        turma_edit,
                        dia_edit,
                        horario_edit,
                        aulas_final,
                        arquivo_edit,
                        componente_edit,
                    )
                    _limpar_cache_cadastro()
                    if aviso:
                        st.warning(aviso)
                    st.success("Cadastro atualizado.")
                    st.rerun()
            except Exception as exc:
                st.error("Nao foi possivel salvar o cadastro.")
                with st.expander("Ver detalhe tecnico"):
                    st.exception(exc)

    col_dup, col_del = st.columns(2)
    with col_dup:
        with st.expander("Duplicar cadastro"):
            dup_prof = st.text_input("Professor da copia", value=str(cadastro.get("professor") or ""), key=f"dup_prof_{chave_ui}").strip().upper()
            dup_disc = st.text_input("Disciplina da copia", value=str(cadastro.get("disciplina") or ""), key=f"dup_disc_{chave_ui}").strip()
            dup_turma = _selecionar_turma("Turma da copia", f"dup_turma_select_{chave_ui}", f"dup_turma_text_{chave_ui}")
            if st.button("Criar copia", key=f"btn_dup_{chave_ui}"):
                try:
                    if not dup_prof or not dup_disc or not dup_turma:
                        st.error("Informe professor, disciplina e turma para duplicar.")
                    else:
                        componente_dup = str(cadastro.get("componente_curricular") or dup_disc)
                        arquivo_corrigido, aviso = _preparar_modelo_cadastro(
                            dup_prof,
                            dup_disc,
                            dup_turma,
                            str(cadastro.get("aulas_semana") or ""),
                            str(cadastro.get("arquivo") or ""),
                            componente_dup,
                        )
                        if cadastro.get("id"):
                            duplicar_vinculo_professor(
                                cadastro.get("id"),
                                nome=dup_prof,
                                disciplina=dup_disc,
                                turma=dup_turma,
                                arquivo_modelo=arquivo_corrigido,
                                componente_curricular=componente_dup,
                                template_id=resolver_template_id_geracao(
                                    disciplina=dup_disc,
                                    componente_curricular=componente_dup,
                                    arquivo_modelo=arquivo_corrigido,
                                ),
                            )
                        else:
                            salvar_professor_turma(
                                dup_prof,
                                dup_disc,
                                dup_turma,
                                str(cadastro.get("dia_semana") or ""),
                                str(cadastro.get("horario") or ""),
                                str(cadastro.get("aulas_semana") or ""),
                                arquivo_corrigido,
                                componente_dup,
                                resolver_template_id_geracao(
                                    disciplina=dup_disc,
                                    componente_curricular=componente_dup,
                                    arquivo_modelo=arquivo_corrigido,
                                ),
                            )
                        _limpar_cache_cadastro()
                        if aviso:
                            st.warning(aviso)
                        st.success("Cadastro duplicado.")
                        st.rerun()
                except Exception as exc:
                    st.error("Nao foi possivel duplicar o cadastro.")
                    with st.expander("Ver detalhe tecnico da duplicacao"):
                        st.exception(exc)

    with col_del:
        with st.expander("Excluir cadastro"):
            if not cadastro.get("id"):
                st.info("Este item veio apenas da pasta DOCX. Nao ha vinculo no banco para excluir.")
            else:
                confirmar = st.checkbox("Confirmo que quero remover apenas o cadastro do sistema", key=f"confirm_del_{chave_ui}")
                if st.button("Excluir cadastro", key=f"btn_del_{chave_ui}", disabled=not confirmar):
                    if excluir_vinculo_professor(cadastro.get("id")):
                        _limpar_cache_cadastro()
                        st.success("Cadastro removido. O DOCX nao foi apagado.")
                        st.rerun()
                    else:
                        st.warning("Cadastro nao encontrado no banco.")

def _renderizar_novo_cadastro(professores_db) -> None:
    st.markdown("**Novo cadastro**")
    with st.form("form_cadastro_prof", clear_on_submit=True):
        col_prof_cad, col_disc_cad = st.columns(2)
        with col_prof_cad:
            professor_cadastro = st.selectbox(
                "Professor",
                ["Novo professor"] + sorted(professores_db.keys()),
                key="professor_cadastro_select",
            )
            if professor_cadastro == "Novo professor":
                novo_nome = st.text_input("Nome do Professor").strip().upper()
            else:
                novo_nome = professor_cadastro
        with col_disc_cad:
            nova_disc_op = st.selectbox("Disciplina", nomes_disciplinas())
            nova_disc_outra = st.text_input("Qual disciplina?") if nova_disc_op == "Outra" else ""

        col_turma_cad, col_aulas_cad = st.columns([2, 1])
        with col_turma_cad:
            nova_turma = _selecionar_turma("Turma", "nova_turma_select", "nova_turma_digitada")
        with col_aulas_cad:
            novas_aulas_semana = _selecionar_aulas_semana(
                "Qtd. aulas na semana",
                "novas_aulas_semana_select",
                "novas_aulas_semana",
            )

        novo_componente_curricular = st.text_input(
            "Componente curricular (como aparecera no plano)",
            placeholder="Ex.: CDP-E. F -EJA - MATEMATICA",
            key="novo_componente_curricular",
        )
        novo_arquivo_modelo = ""

        novo_dia, novo_horario, total_grade = _renderizar_grade_horarios(
            "cadastro_grade",
            contexto=nova_turma,
        )

        submitted = st.form_submit_button("Salvar cadastro", type="primary")
        if submitted:
            disc_final = nova_disc_outra if nova_disc_op == "Outra" else nova_disc_op
            aulas_semana_final = novas_aulas_semana or (str(total_grade) if total_grade else "")
            if novo_nome and disc_final and nova_turma:
                try:
                    _, aviso = _salvar_cadastro_gerenciado(
                        None,
                        novo_nome,
                        disc_final,
                        nova_turma,
                        novo_dia,
                        novo_horario,
                        aulas_semana_final,
                        novo_arquivo_modelo.strip(),
                        novo_componente_curricular.strip(),
                    )
                    _limpar_cache_cadastro()
                    if aviso:
                        st.warning(aviso)
                    st.success(f"Cadastro de {novo_nome} salvo.")
                    st.rerun()
                except Exception as exc:
                    st.error("Nao foi possivel salvar o cadastro.")
                    with st.expander("Ver detalhe tecnico"):
                        st.exception(exc)
            else:
                st.error("Preencha ao menos nome, disciplina e turma.")

def _renderizar_organizacao_cadastro(cadastros: list[dict], diagnostico: dict) -> None:
    st.markdown("**Organizacao dos cadastros**")
    sem_modelo = [cad for cad in cadastros if cad.get("sem_modelo")]
    somente_pasta = [cad for cad in cadastros if cad.get("origem") == "Pasta DOCX"]
    duplicidades = diagnostico.get("duplicidades", []) if diagnostico else []

    with st.expander("Cadastros sem DOCX vinculado", expanded=bool(sem_modelo)):
        if sem_modelo:
            _renderizar_tabela_cadastros(sem_modelo)
        else:
            st.info("Todos os cadastros listados tem DOCX vinculado.")

    with st.expander("Modelos encontrados na pasta, ainda sem registro no banco", expanded=bool(somente_pasta)):
        if somente_pasta:
            _renderizar_tabela_cadastros(somente_pasta)
        else:
            st.info("Nenhum modelo pendente de importacao.")

    with st.expander("Duplicidades detectadas nos DOCX", expanded=bool(duplicidades)):
        if duplicidades:
            linhas_dup = [
                {
                    "Professor": item.get("professor", ""),
                    "Disciplina": item.get("disciplina", ""),
                    "Turma": item.get("turma", ""),
                    "Arquivos": "\n".join(item.get("arquivos", [])),
                }
                for item in duplicidades
            ]
            st.dataframe(linhas_dup, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma duplicidade foi encontrada.")

def _renderizar_cadastro_professor(professores_db) -> None:
    st.markdown('<div class="section-title">Cadastro de professor</div>', unsafe_allow_html=True)
    st.caption("Consulte, edite, duplique ou exclua vinculos de professor, disciplina, turma e horarios.")

    cadastros = _cadastros_para_gestao()
    diagnostico = _diagnosticar_modelos_professores_cache()
    _renderizar_metricas_cadastro(cadastros, diagnostico)

    aba_editar, aba_novo, aba_organizacao = st.tabs(["Consultar e editar", "Novo cadastro", "Organizacao"])
    with aba_editar:
        _renderizar_editor_cadastro(cadastros)
    with aba_novo:
        _renderizar_novo_cadastro(professores_db)
    with aba_organizacao:
        _renderizar_organizacao_cadastro(cadastros, diagnostico)
