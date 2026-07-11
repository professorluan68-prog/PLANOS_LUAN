from core.resultados_aula import (
    DependenciasResultadosAula,
    montar_resultado_aula_ia,
    montar_resultado_aula_local,
)


def _deps_resultados_base() -> DependenciasResultadosAula:
    return DependenciasResultadosAula(
        referencia_docx_por_perfil_fn=lambda *args, **kwargs: None,
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
                {"titulo": "Para comecar", "texto": "Modelo leitura"}
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
        gerar_acompanhamento_aprimorado_fn=lambda **kwargs: ["OK A", "OK B", "OK C"],
        gerar_acessibilidade_aprimorada_fn=lambda **kwargs: ["AC X", "AC Y", "AC Z"],
        normalizar_itens_contextuais_fn=(
            lambda acompanhamento, acessibilidade, tema, perfil: (
                acompanhamento,
                acessibilidade,
            )
        ),
        montar_etapas_metodologia_fn=lambda *args, **kwargs: [
            {"titulo": "Para comecar", "texto": "Etapa local"}
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


def test_montar_resultado_aula_local_core_retorna_motor_local():
    deps = _deps_resultados_base()
    deps.origem_metodologia_por_referencia_fn = lambda perfil: ""

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema local",
        material_digital="AULA 1 - Tema local",
        numero_aula="1",
        disciplina_base="Historia",
        turma="6 ANO A",
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

    assert resultado["origem_metodologia"] == "motor_local"
    assert resultado["ia_usada"] is False
    assert resultado["metodologia"][0]["texto"] == "Etapa local"


def test_montar_resultado_aula_ia_core_usa_referencia_como_fallback_sem_apagar_refino():
    deps = _deps_resultados_base()
    deps.origem_metodologia_por_referencia_fn = lambda perfil: ""
    referencia = {
        "metodologia": [{"titulo": "Para comecar", "texto": "Texto DOCX"}],
        "acompanhamento": ["R1", "R2", "R3"],
        "acessibilidade": ["A1", "A2", "A3"],
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
        disciplina_base="Historia",
        turma="6 ANO A",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "metodologia": [{"titulo": "Para comecar", "texto": "Texto IA"}],
            "acompanhamento": ["IA1", "IA2", "IA3"],
            "acessibilidade": ["IX1", "IX2", "IX3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
    )

    assert resultado["origem_metodologia"] == ""
    assert resultado["metodologia"][0]["texto"] == "Texto IA"
    assert resultado["acompanhamento"] == ["IA1", "IA2", "IA3"]
    assert resultado["acessibilidade"] == ["IX1", "IX2", "IX3"]


def test_montar_resultado_aula_local_biologia_prioriza_docx_sem_passar_pelo_motor():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [{"titulo": "Para comecar", "texto": "Texto DOCX Biologia"}],
        "acompanhamento": ["R1", "R2", "R3"],
        "acessibilidade": ["A1", "A2", "A3"],
        "fonte": "referencia_biologia.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia
    deps.naturalizar_metodologia_professor_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria naturalizar")
        )
    )
    deps.higienizar_plano_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria higienizar")
        )
    )
    deps.tentar_gerador_colunas_pedagogicas_fn = (
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria montar colunas")
        )
    )
    deps.montar_etapas_metodologia_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria montar motor local")
        )
    )

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema biologia",
        material_digital="AULA 1 - Tema biologia",
        numero_aula="1",
        disciplina_base="Biologia",
        turma="1 ANO A",
        provedor_ia="",
        perfil="biologia",
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
        caminho_pdf="aula.pdf",
    )

    assert resultado["origem_metodologia"] == "docx_referencia_biologia"
    assert resultado["metodologia"][0]["texto"] == "Texto DOCX Biologia"
    assert resultado["acompanhamento"] == ["R1", "R2", "R3"]
    assert resultado["acessibilidade"] == ["A1", "A2", "A3"]
    assert any(
        "copiados exatamente do arquivo .docx" in aviso.lower()
        for aviso in resultado["avisos_validacao"]
    )


def test_montar_resultado_aula_ia_biologia_copia_docx_sem_usar_ia_nem_higienizacao():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [{"titulo": "Para comecar", "texto": "Texto DOCX Biologia IA"}],
        "acompanhamento": ["R1", "R2", "R3"],
        "acessibilidade": ["A1", "A2", "A3"],
        "fonte": "referencia_biologia.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia
    deps.naturalizar_metodologia_professor_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria naturalizar")
        )
    )
    deps.higienizar_plano_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria higienizar")
        )
    )
    deps.tentar_gerador_colunas_pedagogicas_fn = (
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria montar colunas")
        )
    )

    resultado = montar_resultado_aula_ia(
        texto="Texto da aula",
        tema="Tema biologia IA",
        material_digital="AULA 1 - Tema biologia IA",
        numero_aula="1",
        disciplina_base="Biologia",
        turma="1 ANO A",
        provedor_ia="openai",
        perfil="biologia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "metodologia": [{"titulo": "Para comecar", "texto": "Texto IA"}],
            "acompanhamento": ["IA1", "IA2", "IA3"],
            "acessibilidade": ["IX1", "IX2", "IX3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        dependencias=deps,
        caminho_pdf="aula.pdf",
    )

    assert resultado["origem_metodologia"] == "docx_referencia_biologia"
    assert resultado["metodologia"][0]["texto"] == "Texto DOCX Biologia IA"
    assert resultado["acompanhamento"] == ["R1", "R2", "R3"]
    assert resultado["acessibilidade"] == ["A1", "A2", "A3"]
    assert resultado["ia_usada"] is False


def test_montar_resultado_aula_local_biologia_sem_docx_nao_cai_no_motor():
    deps = _deps_resultados_base()
    deps.tentar_gerador_colunas_pedagogicas_fn = (
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria montar colunas")
        )
    )
    deps.montar_etapas_metodologia_fn = (
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Nao deveria montar motor local")
        )
    )

    resultado = montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema biologia",
        material_digital="AULA 1 - Tema biologia",
        numero_aula="1",
        disciplina_base="Biologia",
        turma="1 ANO A",
        provedor_ia="",
        perfil="biologia",
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
        caminho_pdf="aula.pdf",
    )

    assert resultado["origem_metodologia"] == "referencia_docx_biologia_ausente"
    assert resultado["metodologia"] == []
    assert resultado["acompanhamento"] == []
    assert resultado["acessibilidade"] == []
