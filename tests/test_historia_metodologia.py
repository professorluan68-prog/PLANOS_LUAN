from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import _etapas_por_perfil, MotorMetodologico
from core.revisao_final import revisar_aula_gerada

def test_historia_perfil():
    assert perfil_disciplina("História") == "historia"
    assert perfil_disciplina("Historia") == "historia"

def test_historia_detectar_tipo_aula():
    # 1. Fonte Histórica
    assert detectar_tipo_aula(
        "Orientar a leitura de uma carta escrita por um camponês medieval analisando o contexto de produção e autoria.",
        "A vida na Idade Média",
        "História"
    ) == "fonte_historica"
    
    # 2. Debate Crítico
    assert detectar_tipo_aula(
        "Dividir a sala para debater as diferentes narrativas sobre os impactos da Revolução Industrial.",
        "Guerra do Paraguai: conflito de narrativas",
        "História"
    ) == "debate_critico"

    # 3. Análise Geográfica
    assert detectar_tipo_aula(
        "Foco no conteúdo analisando as rotas comerciais no mar Mediterrâneo antigo e sua expansão territorial.",
        "Rotas comerciais na África",
        "História"
    ) == "analise_geografica"

    # 4. Produção Projeto
    assert detectar_tipo_aula(
        "Elaborar em grupos um mapa mental sobre as corporações de ofício.",
        "A economia na Baixa Idade Média",
        "História"
    ) == "producao_projeto"

def test_historia_etapas_config():
    etapas = _etapas_por_perfil("historia", "fonte_historica")
    chaves = [chave for _, chave in etapas]
    assert chaves == ["para_comecar", "foco", "pause", "pratica", "encerramento"]

def test_historia_geracao_metodologia():
    generator = MotorMetodologico()
    texto_pdf = (
        "Texto da aula que orienta a análise de uma fonte histórica (carta de lei da Lei Áurea). "
        "Pedir que os estudantes leiam e respondam o que a lei determinou."
    )
    resultado = generator.gerar(
        texto_pdf=texto_pdf,
        disciplina="História",
        turma="8º ANO",
        tema="A Lei Áurea",
        indice_aula=0,
        total_aulas=1
    )
    
    assert len(resultado) == 5
    # Check if "linha do tempo" is present in the first stage (para_comecar)
    assert "linha do tempo" in resultado[0]["texto"].lower()
    # Check if source analysis questions are in the methodology (pratica)
    assert "quem produziu" in resultado[3]["texto"].lower()
    assert "ponto de vista" in resultado[3]["texto"].lower()
    # Check if past-present connection is in the closing stage (encerramento)
    assert "permanências" in resultado[4]["texto"].lower() or "atualidade" in resultado[4]["texto"].lower()


def test_historia_referencia_curta_sem_ia_permanece_literal(monkeypatch):
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
                {
                    "titulo": "Na pratica",
                    "texto": "Orientar o registro de uma caracteristica das instituicoes politicas romanas.",
                },
                {
                    "titulo": "Encerramento",
                    "texto": "Retomar os conceitos centrais em uma sintese final.",
                },
            ],
            "acompanhamento": [
                "☑ Observar participação dos alunos.",
                "☑ Verificar anotações.",
                "☑ Avaliar respostas.",
            ],
            "acessibilidade": [
                "☑ Fornecer material impresso.",
                "☑ Utilizar recursos visuais.",
                "☑ Oferecer apoio individual.",
            ],
            "fonte": "referencia.docx",
        },
    )

    resultado = lote._montar_resultado_aula_local(
        texto="A monarquia romana apresenta patrícios, reis e instituições políticas. A atividade usa imagem e registro no caderno.",
        tema="A monarquia romana",
        material_digital="AULA 5",
        numero_aula="5",
        disciplina_base="História",
        turma="6º ANO",
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

    metodologia_docx = [
        {
            "titulo": "Para começar",
            "texto": "Inicie a aula apresentando a expressão patrícia e questione a turma sobre Roma Antiga.",
        },
        {
            "titulo": "Foco no conteúdo",
            "texto": "Conduza uma breve explicação sobre reis, patrícios e instituições políticas romanas.",
        },
        {
            "titulo": "Na pratica",
            "texto": "Orientar o registro de uma caracteristica das instituicoes politicas romanas.",
        },
        {
            "titulo": "Encerramento",
            "texto": "Retomar os conceitos centrais em uma sintese final.",
        },
    ]
    assert resultado["metodologia"] == metodologia_docx
    assert len(resultado["acompanhamento"]) == 3
    assert len(resultado["acessibilidade"]) == 3
    assert all(item.startswith("☑") for item in resultado["acompanhamento"])
    assert all(item.startswith("☑") for item in resultado["acessibilidade"])
    assert resultado["texto_central_copiado_literalmente"] is True

    revisado = revisar_aula_gerada(resultado, "historia")
    assert revisado["metodologia"] == metodologia_docx


def test_historia_ia_curta_preserva_docx_e_rejeita_refino_incompleto(monkeypatch):
    import core.lote as lote

    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": "(EF06HI10) Explicar a formação da Grécia Antiga.",
            "conceito_extraido": "pólis gregas",
            "recursos_detectados": ["mapa", "imagem", "texto"],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "As pólis gregas, Atenas e Esparta, cidades-estado e participação política.",
        },
    )
    referencia_docx = {
        "metodologia": [
            {
                "titulo": "Para começar",
                "texto": "Retomar o que os estudantes já sabem sobre pólis gregas.",
            },
            {
                "titulo": "Foco no conteúdo",
                "texto": "Explicar Atenas, Esparta e as cidades-estado da Grécia Antiga.",
            },
            {
                "titulo": "Na prática",
                "texto": "Orientar o registro das diferenças entre Atenas e Esparta no caderno.",
            },
            {
                "titulo": "Encerramento",
                "texto": "Retomar as relações entre pólis, participação política e cidades-estado.",
            },
        ],
        "acompanhamento": ["☑ A1", "☑ A2", "☑ A3"],
        "acessibilidade": ["☑ X1", "☑ X2", "☑ X3"],
        "fonte": "METODOLOGIA_HISTORIA.docx",
    }
    monkeypatch.setattr(
        lote,
        "_referencia_docx_por_perfil",
        lambda *args, **kwargs: referencia_docx,
    )

    resultado = lote._montar_resultado_aula_ia(
        texto="As pólis gregas eram cidades-estado como Atenas e Esparta. O material traz mapa, imagem e atividade no caderno.",
        tema="As pólis gregas: cidades-estado",
        material_digital="AULA 1",
        numero_aula="1",
        disciplina_base="História",
        turma="6º ANO",
        provedor_ia="openai",
        perfil="historia",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=5,
        modalidade_eja_ativa=False,
        plano_ia={
            "tema": "As pólis gregas: cidades-estado",
            "aprendizagem": "Explicar a formação da Grécia Antiga.",
            "metodologia": [
                {
                    "titulo": "Para começar",
                    "texto": "Inicie com o VIREM E CONVERSEM sobre política e democracia nas pólis gregas.",
                },
                {
                    "titulo": "Foco no conteúdo",
                    "texto": "Conduza explicação sobre Atenas, Esparta e cidades-estado, solicitando registro no caderno.",
                },
            ],
            "acompanhamento": [
                "☑ Observar discussão sobre pólis gregas.",
                "☑ Verificar registro sobre Atenas e Esparta.",
                "☑ Conferir síntese sobre cidades-estado.",
            ],
            "acessibilidade": [
                "☑ Realizar leitura guiada sobre pólis gregas.",
                "☑ Usar mapa visual de Atenas e Esparta.",
                "☑ Permitir resposta oral mediada.",
            ],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        caminho_pdf="dummy.pdf",
    )

    texto_metodologia = " ".join(item["texto"] for item in resultado["metodologia"])
    assert len(resultado["metodologia"]) >= 4
    assert "pólis gregas" in texto_metodologia
    assert "Atenas" in texto_metodologia or "Esparta" in texto_metodologia
    assert resultado["status_referencia_docx"] == "docx_preservado_refino_ia_invalido"


def test_historia_variacao_reduz_frases_longas_repetidas():
    import core.lote as lote

    textos = []
    for indice in range(4):
        metodologia = lote._ajustar_metodologia_por_sequencia(
            [
                {
                    "titulo": "Foco no conteudo",
                    "texto": "Conduzir leitura orientada do material, com pausas para destacar informações importantes.",
                },
                {
                    "titulo": "Encerramento",
                    "texto": "Retomar o conceito central com a turma.",
                },
            ],
            indice_aula=indice,
            total_aulas=4,
            tema="Guerras Médicas entre Persas e Gregos",
        )
        textos.append(" ".join(item["texto"] for item in metodologia))

    frase_original = "Conduzir leitura orientada do material, com pausas para destacar informações importantes"
    assert sum(frase_original in texto for texto in textos) <= 2
    assert len(set(textos)) >= 2
