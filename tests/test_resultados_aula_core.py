from core.resultados_aula import (
    DependenciasResultadosAula,
    _registrar_aviso_referencia_metodologica_ia,
    montar_resultado_aula_ia,
    montar_resultado_aula_local,
)


def _deps_resultados_base() -> DependenciasResultadosAula:
    return DependenciasResultadosAula(
        referencia_docx_por_perfil_fn=lambda *args, **kwargs: None,
        localizar_docx_referencia_por_perfil_fn=lambda *args, **kwargs: None,
        habilidade_referencia_docx_fn=lambda referencia: "",
        origem_metodologia_por_referencia_fn=lambda perfil: f"docx_referencia_{perfil}",
        deve_aplicar_referencia_docx_no_resultado_ia_fn=lambda perfil, plano_ia: False,
        sobrescrever_listas_pedagogicas_com_referencia_fn=(
            lambda referencia, acompanhamento, acessibilidade: (
                acompanhamento,
                acessibilidade,
            )
        ),
        extracao_pdf_fn=lambda *args, **kwargs: {
            "habilidade": "HAB001",
            "conceito_extraido": "Conceito base",
            "recursos_detectados": ["quadro"],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "Texto prioritario",
        },
        detectar_tipo_aula_fn=lambda *args, **kwargs: "regular",
        resolver_habilidade_portugues_fn=(
            lambda habilidade, caminho_pdf, numero_aula: habilidade
        ),
        montar_aprendizagem_inteligente_fn=lambda **kwargs: "Aprendizagem montada",
        tentar_gerador_colunas_pedagogicas_fn=lambda **kwargs: None,
        metodologia_leitura_redacao_modelo_fn=(
            lambda texto, tema, turma="": [
                {"titulo": "Para começar", "texto": "Modelo leitura"}
            ]
        ),
        detectar_tecnicas_lemov_fn=lambda texto, tema: [],
        garantir_tecnicas_lemov_na_metodologia_fn=(
            lambda metodologia, tecnicas: metodologia
        ),
        variar_linguagem_metodologia_fn=(
            lambda metodologia, disciplina, turma, tema: metodologia
        ),
        ajustar_metodologia_por_sequencia_fn=lambda metodologia, **kwargs: metodologia,
        revisar_metodologia_fn=lambda metodologia, **kwargs: (metodologia, []),
        naturalizar_metodologia_professor_fn=lambda metodologia, perfil="": metodologia,
        adaptar_metodologia_eja_fn=lambda metodologia, *args, **kwargs: metodologia,
        texto_metodologia_fn=lambda metodologia: " ".join(
            item.get("texto", "")
            for item in metodologia
            if isinstance(item, dict)
        ),
        gerar_acompanhamento_aprimorado_fn=lambda **kwargs: ["☑ A", "☑ B", "☑ C"],
        gerar_acessibilidade_aprimorada_fn=lambda **kwargs: ["☑ X", "☑ Y", "☑ Z"],
        normalizar_itens_contextuais_fn=(
            lambda acompanhamento, acessibilidade, tema, perfil: (
                acompanhamento,
                acessibilidade,
            )
        ),
        montar_etapas_metodologia_fn=lambda *args, **kwargs: [
            {"titulo": "Para começar", "texto": "Etapa local"}
        ],
        aprimorar_historia_pos_processamento_fn=(
            lambda metodologia, acompanhamento, acessibilidade, **kwargs: (
                metodologia,
                acompanhamento,
                acessibilidade,
            )
        ),
        detectar_recursos_reais_fn=lambda texto: ["quadro"],
        higienizar_plano_fn=(
            lambda metodologia, acompanhamento, acessibilidade, perfil, disciplina, tema, recursos: (
                metodologia,
                acompanhamento,
                acessibilidade,
            )
        ),
        validar_aula_final_fn=lambda aula: [],
    )


def test_aviso_de_referencia_metodologica_ausente_entra_na_conferencia():
    resultado = {
        "avisos_validacao": ["Aviso existente"],
        "diagnostico_geracao": {"metodologia_final": []},
    }

    retorno = _registrar_aviso_referencia_metodologica_ia(
        resultado,
        {
            "_aviso_referencia_metodologica": (
                "Referência metodológica oficial não encontrada para História."
            )
        },
    )

    assert retorno["avisos_validacao"] == [
        "Aviso existente",
        "Referência metodológica oficial não encontrada para História.",
    ]
    assert retorno["diagnostico_geracao"]["referencia_metodologica"]["status"] == "ausente"


def test_montar_resultado_aula_local_exige_referencia_docx():
    deps = _deps_resultados_base()

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema local",
        material_digital="AULA 1 - Tema local",
        numero_aula="1",
        disciplina_base="História",
        turma="6º ANO A",
        provedor_ia="",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        usar_ia=False,
        ia_erro="",
        dependencias=deps,
    )

    assert resultado["origem_metodologia"] == "referencia_docx_historia_ausente"
    assert resultado["ia_usada"] is False
    assert resultado["metodologia"] == []
    assert resultado["status_referencia_docx"] == "docx_ausente"
    assert "nao gera metodologia interna" in resultado["avisos_validacao"][-1]


def test_montar_resultado_local_copia_docx_literalmente_sem_higienizar():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [
            {"titulo": "Para começar", "texto": "Texto EXATAMENTE como foi escrito."},
            {"titulo": "Foco no conteúdo", "texto": "Segundo trecho literal."},
            {"titulo": "Na prática", "texto": "Terceiro trecho literal."},
            {"titulo": "Encerramento", "texto": "Terceiro trecho literal."},
        ],
        "acompanhamento": ["Item literal 1", "Item literal 2", "Item literal 3"],
        "acessibilidade": ["Apoio literal 1", "Apoio literal 2", "Apoio literal 3"],
        "fonte": "METODOLOGIA_TESTE.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia
    deps.localizar_docx_referencia_por_perfil_fn = (
        lambda *args, **kwargs: "METODOLOGIA_TESTE.docx"
    )

    def _nao_deve_ser_chamado(*args, **kwargs):
        raise AssertionError("texto literal do DOCX nao pode ser reescrito")

    deps.higienizar_plano_fn = _nao_deve_ser_chamado
    deps.naturalizar_metodologia_professor_fn = _nao_deve_ser_chamado

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema local",
        material_digital="AULA 1 - Tema local",
        numero_aula="1",
        disciplina_base="Ciências",
        turma="6º ANO A",
        provedor_ia="",
        perfil="ciencias_ef",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        usar_ia=False,
        ia_erro="",
        dependencias=deps,
    )

    assert resultado["metodologia"] == referencia["metodologia"]
    assert resultado["acompanhamento"] == referencia["acompanhamento"]
    assert resultado["acessibilidade"] == referencia["acessibilidade"]
    assert resultado["status_referencia_docx"] == "docx_literal"
    assert resultado["texto_central_copiado_literalmente"] is True


def test_montar_resultado_aula_local_bloqueia_docx_com_mais_de_350_caracteres():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [{"titulo": "Para começar", "texto": "A" * 351}],
        "acompanhamento": ["R1", "R2", "R3"],
        "acessibilidade": ["A1", "A2", "A3"],
        "fonte": "referencia_longa.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia

    import pytest
    with pytest.raises(ValueError) as excinfo:
        montar_resultado_aula_local(
            texto="Texto da aula",
            tema="Tema",
            material_digital="AULA 1 - Tema",
            numero_aula="1",
            disciplina_base="História",
            turma="6º ANO A",
            provedor_ia="openai",
            perfil="historia",
            contexto_metodologico="regular",
            indice_aula=0,
            total_aulas=1,
            modalidade_eja_ativa=False,
            metodologia_fixa_pdf=[],
            aprendizagem_pv="",
            objetivos_orientacao=[],
            aprendizagem_orientacao="",
            usar_ia=False,
            ia_erro="",
            dependencias=deps,
        )
    assert "excede(m) o limite máximo de 350 caracteres" in str(excinfo.value)
    assert "Com IA" in str(excinfo.value)


def test_montar_resultado_local_gera_listas_quando_docx_nao_as_traz():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [
            {"titulo": "Na prática", "texto": "Resolver as atividades do material."},
            {"titulo": "Foco no conteúdo", "texto": "Explicar o conceito principal."},
            {"titulo": "Encerramento", "texto": "Registrar uma síntese final."},
            {"titulo": "Relembre", "texto": "Retomar a ideia da aula anterior."},
        ],
        "acompanhamento": [],
        "acessibilidade": [],
        "fonte": "referencia_sem_listas.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema",
        material_digital="AULA 1 - Tema",
        numero_aula="1",
        disciplina_base="História",
        turma="6º ANO A",
        provedor_ia="",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        usar_ia=False,
        ia_erro="",
        dependencias=deps,
    )

    assert resultado["metodologia"] == referencia["metodologia"]
    assert resultado["acompanhamento"] == ["☑ A", "☑ B", "☑ C"]
    assert resultado["acessibilidade"] == ["☑ X", "☑ Y", "☑ Z"]
    assert "foram gerados pelo sistema" in resultado["avisos_validacao"][-1]


def test_montar_resultado_aula_ia_core_usa_referencia_como_fallback_sem_apagar_refino():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [{"titulo": "Para começar", "texto": "Texto DOCX"}],
        "acompanhamento": ["☑ R1", "☑ R2", "☑ R3"],
        "acessibilidade": ["☑ A1", "☑ A2", "☑ A3"],
        "fonte": "referencia.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia
    deps.deve_aplicar_referencia_docx_no_resultado_ia_fn = (
        lambda perfil, plano_ia: True
    )

    resultado = montar_resultado_aula_ia(
        texto="Texto da aula",
        tema="Tema IA",
        material_digital="AULA 1 - Tema IA",
        numero_aula="1",
        disciplina_base="História",
        turma="6º ANO A",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "metodologia": [
                {"titulo": "Para começar", "texto": "Texto IA"},
                {"titulo": "Foco no conteúdo", "texto": "Foco IA"},
                {"titulo": "Na prática", "texto": "Prática IA"},
                {"titulo": "Encerramento", "texto": "Fechamento IA"},
            ],
            "acompanhamento": ["IA1", "IA2", "IA3"],
            "acessibilidade": ["IX1", "IX2", "IX3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
    )

    assert resultado["origem_metodologia"] == "docx_referencia_historia"
    assert resultado["metodologia"][0]["texto"] == "Texto IA"
    assert resultado["acompanhamento"] == ["IA1", "IA2", "IA3"]
    assert resultado["acessibilidade"] == ["IX1", "IX2", "IX3"]
    assert resultado["status_referencia_docx"] == "docx_refinado_ia"


def test_montar_resultado_aula_ia_redacao_preserva_metodologia_da_ia():
    deps = _deps_resultados_base()
    deps.origem_metodologia_por_referencia_fn = lambda perfil: ""

    resultado = montar_resultado_aula_ia(
        texto="Texto do PDF de Redacao e Leitura",
        tema="Leitura e producao textual",
        material_digital="AULA 1 - Leitura e producao textual",
        numero_aula="1",
        disciplina_base="Redacao e Leitura",
        turma="6o ano A",
        provedor_ia="openai",
        perfil="leitura_redacao",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "tema": "Leitura e producao textual",
            "aprendizagem": "Compreender a proposta de leitura e escrita da aula.",
            "metodologia": [
                {"titulo": "Leitura compartilhada", "texto": "Metodologia IA especifica ao PDF."}
            ],
            "acompanhamento": ["IA1", "IA2", "IA3"],
            "acessibilidade": ["IAA1", "IAA2", "IAA3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
    )

    assert resultado["metodologia"][0]["texto"] == "Metodologia IA especifica ao PDF."
    assert resultado["metodologia"][0]["texto"] != "Modelo leitura"
    assert resultado["acompanhamento"] == ["IA1", "IA2", "IA3"]
    assert resultado["acessibilidade"] == ["IAA1", "IAA2", "IAA3"]


def test_montar_resultado_aula_ia_preserva_docx_quando_ia_altera_estrutura():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [
            {"titulo": "Abertura", "texto": "Texto original da abertura."},
            {"titulo": "Pratica", "texto": "Texto original da pratica."},
        ],
        "acompanhamento": ["R1", "R2", "R3"],
        "acessibilidade": ["A1", "A2", "A3"],
        "fonte": "referencia.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia

    resultado = montar_resultado_aula_ia(
        texto="Texto da aula",
        tema="Tema IA",
        material_digital="AULA 1 - Tema IA",
        numero_aula="1",
        disciplina_base="Historia",
        turma="6 ANO A",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "metodologia": [{"titulo": "Novo titulo", "texto": "Texto alterado."}],
            "acompanhamento": ["IA1"],
            "acessibilidade": ["IA2"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
    )

    assert resultado["metodologia"] == referencia["metodologia"]
    assert resultado["acompanhamento"] == referencia["acompanhamento"]
    assert resultado["acessibilidade"] == referencia["acessibilidade"]
    assert resultado["status_referencia_docx"] == "docx_preservado_refino_ia_invalido"
    assert resultado["diagnostico_geracao"]["refino_referencia_docx"]["valido"] is False


def test_montar_resultado_aula_ia_sociologia_nao_injeta_tecnicas_lemov():
    deps = _deps_resultados_base()
    deps.origem_metodologia_por_referencia_fn = lambda perfil: ""
    deps.detectar_tecnicas_lemov_fn = lambda texto, tema: ["VIREM E CONVERSEM"]

    def nao_deve_injetar(*args, **kwargs):
        raise AssertionError("Sociologia nao deve receber injecao automatica de Lemov")

    deps.garantir_tecnicas_lemov_na_metodologia_fn = nao_deve_injetar

    resultado = montar_resultado_aula_ia(
        texto="Texto do PDF de Sociologia",
        tema="Industria cultural",
        material_digital="AULA 1 - Industria cultural",
        numero_aula="1",
        disciplina_base="Sociologia",
        turma="1º/2º/3º E.M",
        provedor_ia="openai",
        perfil="sociologia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "tema": "Industria cultural",
            "aprendizagem": "Analisar o conceito de industria cultural.",
            "metodologia": [
                {"titulo": "Leitura orientada", "texto": "Analisar o texto do material."}
            ],
            "acompanhamento": ["IA1", "IA2", "IA3"],
            "acessibilidade": ["IAA1", "IAA2", "IAA3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
    )

    assert "VIREM E CONVERSEM" not in resultado["metodologia"][0]["texto"]
