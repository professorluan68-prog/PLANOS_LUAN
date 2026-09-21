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
    obter_dados_administrativos_professor,
    salvar_dados_administrativos_professor,
    listar_todos_dados_administrativos,
)
from core.modelos_docx import (
    resolver_template_id_geracao,
    caminho_template_central,
)
from core.disciplinas import componentes_curriculares_por_disciplina, nomes_disciplinas
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
    _aulas_disponiveis_turno,
    _numeros_aulas_de_texto,
    DIAS_SEMANA_CADASTRO,
    TURNOS_HORARIOS,
    TURNOS_AULAS_ESPECIAIS,
    TURNO_HORARIO_PERSONALIZADO,
    PREFIXO_HORARIO_PERSONALIZADO,
    _defaults_grade_horarios,
)


def extrair_valor_float(valor_str: str) -> float:
    if not valor_str:
        return 0.0
    limpo = re.sub(r"[^\d,\.]", "", str(valor_str)).strip()
    if not limpo:
        return 0.0
    if "," in limpo and "." in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def formatar_moeda_br(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalizar_nome_dados_professor(nome: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(nome or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto).strip().upper()
    return texto


def _eh_professor_dados_piloto(nome: str = "") -> bool:
    return bool(str(nome or "").strip())


def _opcoes_componente_curricular(disciplina_atual: str = "", componente_atual: str = "") -> list[str]:
    opcoes = [disc for disc in nomes_disciplinas() if disc != "Outra"]
    opcoes.extend(
        componente
        for componente in componentes_curriculares_por_disciplina(disciplina_atual)
        if componente not in opcoes
    )
    extras = []
    for valor in (disciplina_atual, componente_atual):
        valor_limpo = str(valor or "").strip()
        if valor_limpo and valor_limpo not in opcoes and valor_limpo not in extras:
            extras.append(valor_limpo)
    return opcoes + extras


def _selecionar_componente_curricular(
    label: str,
    key: str,
    disciplina_atual: str = "",
    componente_atual: str = "",
) -> str:
    opcoes = _opcoes_componente_curricular(disciplina_atual, componente_atual)
    valor_atual = str(componente_atual or disciplina_atual or "").strip()
    if valor_atual and valor_atual in opcoes:
        indice = opcoes.index(valor_atual)
    elif str(disciplina_atual or "").strip() in opcoes:
        indice = opcoes.index(str(disciplina_atual).strip())
    else:
        indice = 0
    return st.selectbox(label, opcoes, index=indice, key=key)


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
    st.caption("Para corrigir ou incluir outro horário, selecione Personalizado. Para remover, desmarque as aulas ou apague o texto.")
    defaults = _defaults_grade_horarios(dia_texto, horario_texto, contexto)
    selecionados = []
    turnos = (
        list(TURNOS_HORARIOS.keys())
        + list(TURNOS_AULAS_ESPECIAIS.keys())
        + [TURNO_HORARIO_PERSONALIZADO]
    )

    for indice, dia in enumerate(DIAS_SEMANA_CADASTRO):
        default_dia = defaults.get(dia, {})
        turno_default = str(default_dia.get("turno") or "Manhã")
        horario_personalizado_default = str(default_dia.get("horario_personalizado") or "")
        aulas_opcoes_default = [f"{numero}ª" for numero in _aulas_disponiveis_turno(turno_default)]
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
        if turno == TURNO_HORARIO_PERSONALIZADO:
            with col_aulas:
                horario_personalizado = st.text_input(
                    "Horário personalizado",
                    value=horario_personalizado_default,
                    key=f"{prefixo}_horario_personalizado_{indice}",
                    placeholder="Ex.: 6ª aula - 12:25 a 13:15",
                    label_visibility="collapsed",
                ).strip()
            numeros_aulas = _numeros_aulas_de_texto(horario_personalizado)
            aulas = [f"{numero}ª" for numero in numeros_aulas]
            if horario_personalizado and not aulas:
                aulas = ["Personalizada"]
            horario = (
                f"{PREFIXO_HORARIO_PERSONALIZADO} {horario_personalizado}"
                if horario_personalizado
                else None
            )
        else:
            aulas_opcoes = [f"{numero}ª" for numero in _aulas_disponiveis_turno(turno)]
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
            if turno == TURNO_HORARIO_PERSONALIZADO and horario_personalizado:
                st.caption(horario_personalizado)
            else:
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


def _disciplinas_por_professor(cadastros: list[dict], professor: str = "Todos") -> list[str]:
    """Retorna apenas as disciplinas vinculadas ao professor selecionado."""
    return sorted(
        {
            cadastro.get("disciplina", "")
            for cadastro in cadastros
            if cadastro.get("disciplina")
            and (professor == "Todos" or cadastro.get("professor") == professor)
        }
    )


def _filtrar_cadastros(cadastros: list[dict]) -> list[dict]:
    professores = ["Todos"] + sorted({cad.get("professor", "") for cad in cadastros if cad.get("professor")})
    turmas = ["Todas"] + sorted({cad.get("turma", "") for cad in cadastros if cad.get("turma")})
    origens = ["Todas"] + sorted({cad.get("origem", "") for cad in cadastros if cad.get("origem")})
    if st.session_state.get("cadastro_filtro_professor") not in professores:
        st.session_state["cadastro_filtro_professor"] = "Todos"
    if st.session_state.get("cadastro_filtro_turma") not in turmas:
        st.session_state["cadastro_filtro_turma"] = "Todas"
    if st.session_state.get("cadastro_filtro_origem") not in origens:
        st.session_state["cadastro_filtro_origem"] = "Todas"

    col_prof, col_disc, col_turma, col_origem, col_sem = st.columns([2, 1.5, 1.5, 1.5, 1])
    with col_prof:
        filtro_prof = st.selectbox("Professor", professores, key="cadastro_filtro_professor")
    with col_disc:
        disciplinas = ["Todas"] + _disciplinas_por_professor(cadastros, filtro_prof)
        if st.session_state.get("cadastro_filtro_disciplina") not in disciplinas:
            st.session_state["cadastro_filtro_disciplina"] = "Todas"
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

        componente_edit = _selecionar_componente_curricular(
            "Componente curricular",
            key=f"edit_comp_{chave_ui}",
            disciplina_atual=str(cadastro.get("disciplina") or ""),
            componente_atual=str(cadastro.get("componente_curricular") or cadastro.get("disciplina") or ""),
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

        novo_componente_curricular = _selecionar_componente_curricular(
            "Componente curricular (como aparecera no plano)",
            key="novo_componente_curricular",
            disciplina_atual=nova_disc_outra if nova_disc_op == "Outra" else nova_disc_op,
            componente_atual=nova_disc_outra if nova_disc_op == "Outra" else nova_disc_op,
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


def _renderizar_dados_administrativos_professor(cadastros: list[dict], professores_db) -> None:
    st.markdown("**Dados do professor**")
    st.caption("Consulte e gerencie os dados de contato e o valor mensal cobrado de cada professor.")

    nomes = {
        str(nome or "").strip().upper()
        for nome in professores_db.keys()
        if str(nome or "").strip()
    }
    nomes.update(
        str(cadastro.get("professor") or "").strip().upper()
        for cadastro in cadastros
        if str(cadastro.get("professor") or "").strip()
    )
    for admin_item in listar_todos_dados_administrativos():
        nome_admin = str(admin_item.get("professor") or "").strip().upper()
        if nome_admin:
            nomes.add(nome_admin)

    opcoes = sorted(nome for nome in nomes if nome)

    if not opcoes:
        st.info("Nenhum professor encontrado nos cadastros.")
        return

    professor = st.selectbox(
        "Professor",
        opcoes,
        key="dados_admin_professor_selecionado",
    )
    dados = obter_dados_administrativos_professor(professor)

    prof_slug = re.sub(r"\W+", "_", professor.lower()).strip("_")
    with st.form(f"form_dados_administrativos_{prof_slug}"):
        col_cpf, col_email = st.columns(2)
        with col_cpf:
            cpf = st.text_input("CPF", value=dados.get("cpf", ""), key=f"dados_admin_cpf_{prof_slug}").strip()
        with col_email:
            email = st.text_input("Email", value=dados.get("email", ""), key=f"dados_admin_email_{prof_slug}").strip()

        col_valor, col_tel = st.columns(2)
        with col_valor:
            valor_mensal = st.text_input(
                "Valor mensal",
                value=dados.get("valor_mensal", ""),
                key=f"dados_admin_valor_mensal_{prof_slug}",
                placeholder="Ex.: R$ 1.500,00",
            ).strip()
        with col_tel:
            telefone = st.text_input("Telefone", value=dados.get("telefone", ""), key=f"dados_admin_telefone_{prof_slug}").strip()

        observacoes = st.text_area(
            "Observacoes",
            value=dados.get("observacoes", ""),
            key=f"dados_admin_observacoes_{prof_slug}",
            height=140,
        ).strip()

        salvar = st.form_submit_button("Salvar dados do professor", type="primary")
        if salvar:
            try:
                salvar_dados_administrativos_professor(
                    professor,
                    cpf=cpf,
                    email=email,
                    valor_mensal=valor_mensal,
                    telefone=telefone,
                    observacoes=observacoes,
                )
                st.success(f"Dados do professor {professor} salvos com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error("Nao foi possivel salvar os dados do professor.")
                with st.expander("Ver detalhe tecnico"):
                    st.exception(exc)


def _renderizar_faturamento_professores(cadastros: list[dict], professores_db) -> None:
    st.markdown("**Faturamento total do mês**")
    st.caption("Visão consolidada da receita mensal com base nos valores cobrados de cada professor.")

    admin_dados = listar_todos_dados_administrativos()
    admin_by_prof = {item["professor"].upper(): item for item in admin_dados}

    professores_todos = set(professores_db.keys())
    professores_todos.update(
        str(cadastro.get("professor") or "").strip().upper()
        for cadastro in cadastros
        if str(cadastro.get("professor") or "").strip()
    )
    professores_todos.update(admin_by_prof.keys())
    lista_professores = sorted(list(professores_todos))

    if not lista_professores:
        st.info("Nenhum professor cadastrado no momento.")
        return

    vinculos_por_prof = {}
    for c in cadastros:
        p_nome = str(c.get("professor") or "").strip().upper()
        if p_nome:
            vinculos_por_prof[p_nome] = vinculos_por_prof.get(p_nome, 0) + 1

    tabela_linhas = []
    total_faturamento = 0.0
    pagantes_count = 0

    for prof in lista_professores:
        info_admin = admin_by_prof.get(prof, {})
        val_str = info_admin.get("valor_mensal", "")
        val_float = extrair_valor_float(val_str)
        if val_float > 0:
            total_faturamento += val_float
            pagantes_count += 1

        tabela_linhas.append({
            "Professor": prof,
            "Valor mensal": formatar_moeda_br(val_float) if val_float > 0 else (val_str if val_str else "Não cadastrado"),
            "Valor (R$)": val_float,
            "Telefone": info_admin.get("telefone", "") or "-",
            "Email": info_admin.get("email", "") or "-",
            "Vínculos / Turmas": vinculos_por_prof.get(prof, 0),
            "Status": "Pagante" if val_float > 0 else "Sem valor definido",
            "Observações": info_admin.get("observacoes", "") or "-",
        })

    total_professores = len(lista_professores)
    ticket_medio = (total_faturamento / pagantes_count) if pagantes_count > 0 else 0.0

    col_tot, col_pag, col_avg, col_prof = st.columns(4)
    with col_tot:
        st.metric("Faturamento Mensal Total", formatar_moeda_br(total_faturamento))
    with col_pag:
        st.metric("Professores Pagantes", f"{pagantes_count} de {total_professores}")
    with col_avg:
        st.metric("Ticket Médio (Pagantes)", formatar_moeda_br(ticket_medio))
    with col_prof:
        st.metric("Professores Cadastrados", str(total_professores))

    st.markdown("---")
    st.markdown("##### Detalhamento por professor")

    busca = st.text_input("Filtrar por nome do professor", key="busca_faturamento_prof").strip().upper()
    if busca:
        tabela_linhas = [l for l in tabela_linhas if busca in l["Professor"]]

    if tabela_linhas:
        df_exibicao = [
            {
                "Professor": row["Professor"],
                "Valor Mensal": row["Valor mensal"],
                "Status": row["Status"],
                "Vínculos": row["Vínculos / Turmas"],
                "Telefone": row["Telefone"],
                "Email": row["Email"],
                "Observações": row["Observações"],
            }
            for row in tabela_linhas
        ]
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum professor encontrado com os critérios de busca.")


def _renderizar_cadastro_professor(professores_db) -> None:
    st.markdown('<div class="section-title">Cadastro de professor</div>', unsafe_allow_html=True)
    st.caption("Consulte, edite, duplique ou exclua vinculos de professor, disciplina, turma e horarios.")

    cadastros = _cadastros_para_gestao()
    diagnostico = _diagnosticar_modelos_professores_cache()
    _renderizar_metricas_cadastro(cadastros, diagnostico)

    aba_editar, aba_novo, aba_dados, aba_faturamento, aba_organizacao = st.tabs(
        ["Consultar e editar", "Novo cadastro", "Dados do professor", "Faturamento", "Organizacao"]
    )
    with aba_editar:
        _renderizar_editor_cadastro(cadastros)
    with aba_novo:
        _renderizar_novo_cadastro(professores_db)
    with aba_dados:
        _renderizar_dados_administrativos_professor(cadastros, professores_db)
    with aba_faturamento:
        _renderizar_faturamento_professores(cadastros, professores_db)
    with aba_organizacao:
        _renderizar_organizacao_cadastro(cadastros, diagnostico)
