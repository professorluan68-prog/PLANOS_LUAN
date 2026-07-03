from core.resultados_aula import DependenciasResultadosAula, montar_resultado_aula_ia, montar_resultado_aula_local


def _deps_resultados_base() -> DependenciasResultadosAula:
    return DependenciasResultadosAula(
        referencia_docx_por_perfil_fn=lambda *args, **kwargs: None,
        habilidade_referencia_docx_fn=lambda referencia: "",
        origem_metodologia_por_referencia_fn=lambda perfil: f"docx_referencia_{perfil}",
        deve_aplicar_referencia_docx_no_resultado_ia_fn=lambda perfil, plano_ia: False,
        sobrescrever_listas_pedagogicas_com_referencia_fn=lambda referencia, acompanhamento, acessibilidade: (acompanhamento, acessibilidade),
        extracao_pdf_fn=lambda *args, **kwargs: {
            "habilidade": "HAB001",
            "conceito_extraido": "Conceito base",
            "recursos_detectados": ["quadro"],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "Texto prioritario",
        },
        detectar_tipo_aula_fn=lambda *args, **kwargs: "regular",
        resolver_habilidade_portugues_fn=lambda habilidade, caminho_pdf, numero_aula: habilidade,
        montar_aprendizagem_inteligente_fn=lambda **kwargs: "Aprendizagem montada",
        tentar_gerador_colunas_pedagogicas_fn=lambda **kwargs: None,
        metodologia_leitura_redacao_modelo_fn=lambda texto, tema, turma="": [{"titulo": "Para começar", "texto": "Modelo leitura"}],
        detectar_tecnicas_lemov_fn=lambda texto, tema: [],
        garantir_tecnicas_lemov_na_metodologia_fn=lambda metodologia, tecnicas: metodologia,
        variar_linguagem_metodologia_fn=lambda metodologia, disciplina, turma, tema: metodologia,
        ajustar_metodologia_por_sequencia_fn=lambda metodologia, **kwargs: metodologia,
        revisar_metodologia_fn=lambda metodologia, **kwargs: (metodologia, []),
        naturalizar_metodologia_professor_fn=lambda metodologia, perfil="": metodologia,
        adaptar_metodologia_eja_fn=lambda metodologia, *args, **kwargs: metodologia,
        texto_metodologia_fn=lambda metodologia: " ".join(item.get("texto", "") for item in metodologia if isinstance(item, dict)),
        gerar_acompanhamento_aprimorado_fn=lambda **kwargs: ["☑ A", "☑ B", "☑ C"],
        gerar_acessibilidade_aprimorada_fn=lambda **kwargs: ["☑ X", "☑ Y", "☑ Z"],
        normalizar_itens_contextuais_fn=lambda acompanhamento, acessibilidade, tema, perfil: (acompanhamento, acessibilidade),
        montar_etapas_metodologia_fn=lambda *args, **kwargs: [{"titulo": "Para começar", "texto": "Etapa local"}],
        aprimorar_historia_pos_processamento_fn=lambda metodologia, acompanhamento, acessibilidade, **kwargs: (metodologia, acompanhamento, acessibilidade),
        detectar_recursos_reais_fn=lambda texto: ["quadro"],
        higienizar_plano_fn=lambda metodologia, acompanhamento, acessibilidade, perfil, disciplina, tema, recursos: (metodologia, acompanhamento, acessibilidade),
        validar_aula_final_fn=lambda aula: [],
    )


def test_montar_resultado_aula_local_core_retorna_motor_local():
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

    assert resultado["origem_metodologia"] == "motor_local"
    assert resultado["ia_usada"] is False
    assert resultado["metodologia"][0]["texto"] == "Etapa local"


def test_montar_resultado_aula_ia_core_aplica_referencia_quando_habilitada():
    deps = _deps_resultados_base()
    referencia = {
        "metodologia": [{"titulo": "Para começar", "texto": "Texto DOCX"}],
        "acompanhamento": ["☑ R1", "☑ R2", "☑ R3"],
        "acessibilidade": ["☑ A1", "☑ A2", "☑ A3"],
        "fonte": "referencia.docx",
    }
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: referencia
    deps.deve_aplicar_referencia_docx_no_resultado_ia_fn = lambda perfil, plano_ia: True

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
            "metodologia": [{"titulo": "Para começar", "texto": "Texto IA"}],
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
    assert resultado["metodologia"][0]["texto"] == "Texto DOCX"
    assert resultado["acompanhamento"] == ["☑ R1", "☑ R2", "☑ R3"]
