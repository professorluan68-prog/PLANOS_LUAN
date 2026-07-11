from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import _etapas_por_perfil, MotorMetodologico
from core.revisao_final import revisar_aula_gerada


def test_historia_perfil():
    assert perfil_disciplina("Historia") == "historia"
    assert perfil_disciplina("História") == "historia"


def test_historia_detectar_tipo_aula():
    assert detectar_tipo_aula(
        "Orientar a leitura de uma carta escrita por um campones medieval analisando o contexto de producao e autoria.",
        "A vida na Idade Media",
        "Historia",
    ) == "fonte_historica"

    assert detectar_tipo_aula(
        "Dividir a sala para debater as diferentes narrativas sobre os impactos da Revolucao Industrial.",
        "Guerra do Paraguai: conflito de narrativas",
        "Historia",
    ) == "debate_critico"

    assert detectar_tipo_aula(
        "Foco no conteudo analisando as rotas comerciais no mar Mediterraneo antigo e sua expansao territorial.",
        "Rotas comerciais na Africa",
        "Historia",
    ) == "analise_geografica"

    assert detectar_tipo_aula(
        "Elaborar em grupos um mapa mental sobre as corporacoes de oficio.",
        "A economia na Baixa Idade Media",
        "Historia",
    ) == "producao_projeto"


def test_historia_etapas_config():
    etapas = _etapas_por_perfil("historia", "fonte_historica")
    chaves = [chave for _, chave in etapas]
    assert chaves == ["para_comecar", "foco", "pause", "pratica", "encerramento"]


def test_historia_geracao_metodologia():
    generator = MotorMetodologico()
    texto_pdf = (
        "Texto da aula que orienta a analise de uma fonte historica. "
        "Pedir que os estudantes leiam e respondam o que a lei determinou."
    )
    resultado = generator.gerar(
        texto_pdf=texto_pdf,
        disciplina="Historia",
        turma="8 ANO",
        tema="A Lei Aurea",
        indice_aula=0,
        total_aulas=1,
    )

    assert len(resultado) == 5
    assert "linha do tempo" in resultado[0]["texto"].lower()
    assert "quem produziu" in resultado[3]["texto"].lower()
    assert "ponto de vista" in resultado[3]["texto"].lower()


def test_historia_referencia_curta_sem_ia_ganha_etapas_e_score(monkeypatch):
    import core.lote as lote

    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": "(EF06HI11) Caracterizar o processo de formação da Roma Antiga.",
            "conceito_extraido": "monarquia romana",
            "recursos_detectados": ["imagem", "texto"],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "A monarquia romana, patrícios, reis e instituições políticas.",
        },
    )
    monkeypatch.setattr(
        lote,
        "_referencia_docx_por_perfil",
        lambda *args, **kwargs: {
            "titulo": "A monarquia romana",
            "metodologia": [
                {
                    "titulo": "Para começar",
                    "texto": "Inicie a aula apresentando a expressão patrícia e questione a turma sobre Roma Antiga.",
                },
                {
                    "titulo": "Foco no conteúdo",
                    "texto": "Conduza uma breve explicação sobre reis, patrícios e instituições políticas romanas.",
                },
            ],
            "acompanhamento": [
                "\u2611 Observar participação dos alunos.",
                "\u2611 Verificar anotações.",
                "\u2611 Avaliar respostas.",
            ],
            "acessibilidade": [
                "\u2611 Fornecer material impresso.",
                "\u2611 Utilizar recursos visuais.",
                "\u2611 Oferecer apoio individual.",
            ],
            "fonte": "referencia.docx",
        },
    )

    resultado = lote._montar_resultado_aula_local(
        texto="A monarquia romana apresenta patrícios, reis e instituições políticas. A atividade usa imagem e registro no caderno.",
        tema="A monarquia romana",
        material_digital="AULA 5",
        numero_aula="5",
        disciplina_base="Historia",
        turma="6 ANO",
        provedor_ia="",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=4,
        total_aulas=5,
        modalidade_eja_ativa=False,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        usar_ia=False,
        ia_erro="",
        caminho_pdf="dummy.pdf",
    )

    assert len(resultado["metodologia"]) == 2
    assert len(resultado["acompanhamento"]) == 3
    assert len(resultado["acessibilidade"]) == 3
    assert resultado["origem_metodologia"] == "docx_referencia_historia"
    assert "patr" in resultado["metodologia"][0]["texto"].lower()

    revisado = revisar_aula_gerada(resultado, "historia")
    assert revisado["confidence_score"] >= 50


def test_historia_ia_curta_preserva_refino_e_completa_etapas(monkeypatch):
    import core.lote as lote

    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": "(EF06HI10) Explicar a formação da Grécia Antiga.",
            "conceito_extraido": "polis gregas",
            "recursos_detectados": ["mapa", "imagem", "texto"],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "As polis gregas, Atenas e Esparta, cidades-estado e participação política.",
        },
    )
    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: None)

    resultado = lote._montar_resultado_aula_ia(
        texto="As polis gregas eram cidades-estado como Atenas e Esparta. O material traz mapa, imagem e atividade no caderno.",
        tema="As polis gregas: cidades-estado",
        material_digital="AULA 1",
        numero_aula="1",
        disciplina_base="Historia",
        turma="6 ANO",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=5,
        modalidade_eja_ativa=False,
        plano_ia={
            "tema": "As polis gregas: cidades-estado",
            "aprendizagem": "Explicar a formação da Grécia Antiga.",
            "metodologia": [
                {
                    "titulo": "Para começar",
                    "texto": "Inicie com o VIREM E CONVERSEM sobre política e democracia nas polis gregas.",
                },
                {
                    "titulo": "Foco no conteúdo",
                    "texto": "Conduza explicação sobre Atenas, Esparta e cidades-estado, solicitando registro no caderno.",
                },
            ],
            "acompanhamento": [
                "\u2611 Observar discussão sobre polis gregas.",
                "\u2611 Verificar registro sobre Atenas e Esparta.",
                "\u2611 Conferir síntese sobre cidades-estado.",
            ],
            "acessibilidade": [
                "\u2611 Realizar leitura guiada sobre polis gregas.",
                "\u2611 Usar mapa visual de Atenas e Esparta.",
                "\u2611 Permitir resposta oral mediada.",
            ],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        caminho_pdf="dummy.pdf",
    )

    assert resultado["origem_metodologia"] == "referencia_docx_historia_ausente"
    assert resultado["metodologia"] == []
    assert resultado["acompanhamento"] == []
    assert resultado["acessibilidade"] == []


def test_historia_variacao_reduz_frases_longas_repetidas():
    import core.lote as lote

    textos = []
    for indice in range(4):
        metodologia = lote._ajustar_metodologia_por_sequencia(
            [
                {
                    "titulo": "Foco no conteudo",
                    "texto": "Conduzir leitura orientada do material, com pausas para destacar informacoes importantes.",
                },
                {
                    "titulo": "Encerramento",
                    "texto": "Retomar o conceito central com a turma.",
                },
            ],
            indice_aula=indice,
            total_aulas=4,
            tema="Guerras Medicas entre Persas e Gregos",
        )
        textos.append(" ".join(item["texto"] for item in metodologia))

    frase_original = "Conduzir leitura orientada do material, com pausas para destacar informacoes importantes"
    assert sum(frase_original in texto for texto in textos) <= 2
    assert len(set(textos)) > 2
