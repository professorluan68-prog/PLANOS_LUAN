from core.contexto_aula_pdf import DependenciasContextoAulaPDF, preparar_contexto_aula_pdf


class _LoggerFalso:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None


def _deps_base() -> DependenciasContextoAulaPDF:
    return DependenciasContextoAulaPDF(
        logger=_LoggerFalso(),
        extrair_texto_pdf_fn=lambda caminho: "Texto PDF base",
        tema_por_texto_fn=lambda texto, caminho, disciplina: "Tema PDF",
        material_digital_por_texto_fn=lambda texto, caminho, disciplina, tema: f"AULA 1 - {tema}",
        rotulo_aula_material_fn=lambda texto, caminho: "AULA 1",
        eh_cenario_piloto_pptx_fn=lambda disciplina, turma: False,
        encontrar_pptx_correspondente_fn=lambda caminho, disciplina, turma: None,
        extrair_estrutura_pptx_fn=lambda caminho: {},
        estrutura_pptx_para_dados_aula_fn=lambda estrutura: {},
        eh_cdp_contextual_disciplina_fn=lambda disciplina: False,
        disciplina_base_cdp_por_cadastro_fn=lambda disciplina: "",
        disciplina_base_cdp_contextual_fn=lambda texto, tema, caminho_pdf: "CDP",
        perfil_disciplina_fn=lambda disciplina, turma="": disciplina.lower(),
        obter_dados_aprofundamento_fn=lambda *args, **kwargs: {},
        resolver_contexto_orientacao_estudos_fn=lambda **kwargs: (
            kwargs["texto"],
            kwargs["tema"],
            kwargs["material_digital"],
        ),
        buscar_objetivos_orientacao_estudos_fn=lambda **kwargs: [],
        formatar_objetivos_orientacao_estudos_fn=lambda objetivos: "",
        extracao_pdf_fn=lambda *args, **kwargs: {"texto_prioritario": "Texto prioritario"},
        detectar_tipo_aula_fn=lambda *args, **kwargs: "regular",
        metodologia_fixa_pdf_especial_fn=lambda texto, disciplina, tema: None,
        metodologia_por_blocos_estruturados_fn=lambda blocos: [],
        perfil_suporta_eja_fn=lambda perfil: False,
        eh_cdp_fn=lambda disciplina: False,
        detectar_contexto_metodologico_fn=lambda *args, **kwargs: "regular",
        buscar_item_projeto_vida_fn=lambda turma, bimestre, numero_aula: {},
        montar_aprendizagem_projeto_vida_fn=lambda escopo: "",
        referencia_docx_por_perfil_fn=lambda *args, **kwargs: None,
        habilidade_referencia_docx_fn=lambda referencia: "",
        material_aula_com_titulo_fn=lambda numero, titulo: f"AULA {numero} - {titulo}",
        titulo_escopo_projeto_vida_confiavel_fn=lambda titulo: False,
    )


def test_preparar_contexto_aula_pdf_prioriza_pptx_quando_disponivel():
    deps = _deps_base()
    deps.eh_cenario_piloto_pptx_fn = lambda disciplina, turma: True
    deps.encontrar_pptx_correspondente_fn = lambda caminho, disciplina, turma: "AULA_1.pptx"
    deps.estrutura_pptx_para_dados_aula_fn = lambda estrutura: {
        "texto_base": "Texto vindo do PPTX",
        "tema": "Tema PPTX",
        "material": "AULA 1 - Tema PPTX",
        "blocos_pedagogicos": {"Para começar": "Abrir a aula."},
    }
    deps.metodologia_por_blocos_estruturados_fn = lambda blocos: [
        {"titulo": "Para começar", "texto": blocos["Para começar"]}
    ]
    deps.perfil_disciplina_fn = lambda disciplina, turma="": "lingua_portuguesa_em"

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf="AULA_1.pdf",
        disciplina="Lingua Portuguesa",
        turma="1 ANO A",
        bimestre="3o Bimestre",
        indice_aula=0,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["fonte_extracao"] == "pptx"
    assert contexto["tema"] == "Tema PPTX"
    assert contexto["material_digital"] == "AULA 1 - Tema PPTX"
    assert contexto["metodologia_fixa_pdf"] == [
        {"titulo": "Para começar", "texto": "Abrir a aula."}
    ]


def test_preparar_contexto_aula_pdf_ajusta_orientacao_estudos_com_referencia():
    deps = _deps_base()
    deps.perfil_disciplina_fn = lambda disciplina, turma="": "orientacao_estudos"
    deps.resolver_contexto_orientacao_estudos_fn = lambda **kwargs: (
        "Texto OE",
        "Tema OE",
        "AULA 1 - Tema OE",
    )
    deps.buscar_objetivos_orientacao_estudos_fn = lambda **kwargs: ["Obj 1", "Obj 2"]
    deps.formatar_objetivos_orientacao_estudos_fn = lambda objetivos: "Objetivos formatados"
    deps.referencia_docx_por_perfil_fn = lambda *args, **kwargs: {
        "titulo": "Tema revisado",
        "numero": "7",
        "habilidade": "Habilidade DOCX",
    }
    deps.habilidade_referencia_docx_fn = lambda referencia: referencia["habilidade"]

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf="AULA_1.pdf",
        disciplina="Orientacao de Estudos",
        turma="6 ANO A",
        bimestre="2o Bimestre",
        indice_aula=0,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["numero_aula"] == "1"
    assert contexto["tema"] == "Tema revisado"
    assert contexto["material_digital"] == "AULA 1 - Tema revisado"
    assert contexto["objetivos_orientacao"] == []
    assert contexto["aprendizagem_orientacao"] == "Habilidade DOCX"


def test_preparar_contexto_aula_pdf_preserva_palavras_chave_e_flag_de_extracao():
    deps = _deps_base()
    deps.extracao_pdf_fn = lambda *args, **kwargs: {
        "texto_prioritario": "Texto prioritario",
        "palavras_chave": ["  Termo central ", "Fonte histórica", "termo central"],
    }

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf="AULA_1.pdf",
        disciplina="História",
        turma="8 ANO A",
        bimestre="3o Bimestre",
        indice_aula=0,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["palavras_chave_esperadas"] == [
        "Termo central",
        "Fonte histórica",
    ]
    assert contexto["extracao_palavras_chave_ok"] is True


def test_preparar_contexto_aula_pdf_limpa_titulo_de_arquivo_cdp():
    deps = _deps_base()
    deps.eh_cdp_contextual_disciplina_fn = lambda valor: "CDP_EM" in str(valor)
    deps.perfil_disciplina_fn = lambda disciplina, turma="": "geografia"

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf=r"C:\PDF_AULAS\GEOGRAFIA\CDP_EM\02 - ATIVIDADE 2 - Construção de mapas a legenda.pdf",
        disciplina="Geografia",
        turma="1 ANO J",
        bimestre="3o Bimestre",
        indice_aula=1,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["tema"] == "Construção de mapas a legenda"
    assert contexto["material_digital"] == "Construção de mapas a legenda"
    assert contexto["cdp_contextual"] is True


def test_preparar_contexto_recupera_contexto_cdp_de_upload_temporario(
    monkeypatch, tmp_path
):
    import config
    from core.cdp.gerador_cdp import eh_cdp_contextual_disciplina

    raiz_pdf = tmp_path / "PDF_AULAS"
    original = (
        raiz_pdf
        / "HISTORIA"
        / "EM"
        / "3_BIMESTRE"
        / "CDP_EM"
        / "01 - ATIVIDADE 1 - Fontes.pdf"
    )
    original.parent.mkdir(parents=True)
    original.write_bytes(b"%PDF-1.4")
    temporario = (
        tmp_path
        / "temp_upload"
        / "planos_luan_upload_AbC1__01 - ATIVIDADE 1 - Fontes.pdf"
    )
    temporario.parent.mkdir()
    temporario.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(config, "PDF_AULAS_DIR", raiz_pdf)

    deps = _deps_base()
    deps.eh_cdp_contextual_disciplina_fn = eh_cdp_contextual_disciplina
    deps.perfil_disciplina_fn = lambda disciplina, turma="": "historia"

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf=str(temporario),
        disciplina="Historia",
        turma="",
        bimestre="3o Bimestre",
        indice_aula=0,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["cdp_contextual"] is True
    assert contexto["caminho_pdf_contextual"] == str(original)
    assert contexto["contexto_metodologico"] == "cdp_eja"


def test_preparar_contexto_recupera_cdp_eja_de_sociologia_em_upload_temporario(
    monkeypatch, tmp_path
):
    import config
    from core.cdp.gerador_cdp import eh_cdp_contextual_disciplina

    raiz_pdf = tmp_path / "PDF_AULAS"
    original = (
        raiz_pdf
        / "SOCIOLOGIA"
        / "CDP_EJA"
        / "2_ANO"
        / "01 - ATIVIDADE 1 - Compreensão de texto.pdf"
    )
    original.parent.mkdir(parents=True)
    original.write_bytes(b"%PDF-1.4")
    temporario = (
        tmp_path
        / "temp_upload"
        / "planos_luan_upload_Soc1__01 - ATIVIDADE 1 - Compreensão de texto.pdf"
    )
    temporario.parent.mkdir()
    temporario.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(config, "PDF_AULAS_DIR", raiz_pdf)

    deps = _deps_base()
    deps.eh_cdp_contextual_disciplina_fn = eh_cdp_contextual_disciplina
    deps.perfil_disciplina_fn = lambda disciplina, turma="": "sociologia"

    contexto = preparar_contexto_aula_pdf(
        caminho_pdf=str(temporario),
        disciplina="Sociologia",
        turma="1º/2º/3º E.M",
        bimestre="3º Bimestre",
        indice_aula=0,
        modalidade_eja=False,
        dependencias=deps,
    )

    assert contexto["cdp_contextual"] is True
    assert contexto["caminho_pdf_contextual"] == str(original)
    assert contexto["contexto_metodologico"] == "cdp_eja"
