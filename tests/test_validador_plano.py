from core.validador_plano import validar_aulas_geradas


def test_validador_aceita_etapas_embutidas_no_texto():
    aulas = [
        {
            "tema": "Trilha Harry Potter",
            "aprendizagem": "Participar de praticas de leitura e producao textual com foco em interpretacao e argumentacao.",
            "metodologia": [
                {
                    "titulo": "Desenvolvimento",
                    "texto": (
                        "Disparo inicial: retomar acontecimentos da obra. "
                        "Leitura ou exploracao inicial: orientar leitura do trecho. "
                        "Analise guiada: conduzir perguntas de compreensao e reflexao. "
                        "Sistematizacao: registrar os pontos principais. "
                        "Producao textual: propor escrita breve. "
                        "Revisao e fechamento: revisar o texto e socializar aprendizagens."
                    ),
                }
            ],
            "acompanhamento": [
                "☑ Observar a participacao nas leituras e discussões.",
                "☑ Verificar se os estudantes relacionam texto e producao escrita.",
                "☑ Conferir os registros produzidos durante a aula.",
            ],
            "acessibilidade": [
                "☑ Oferecer leitura mediada com pausas e retomadas.",
                "☑ Disponibilizar roteiro com palavras-chave para apoiar o registro.",
                "☑ Apoiar respostas orais mediadas antes do registro escrito.",
            ],
        }
    ]

    assert validar_aulas_geradas(aulas) == []


def test_validador_mantem_bloqueio_quando_ha_mesmo_poucas_etapas():
    aulas = [
        {
            "tema": "Tema qualquer",
            "aprendizagem": "Desenvolver habilidades de leitura e escrita relacionadas ao tema trabalhado em sala.",
            "metodologia": [{"titulo": "Desenvolvimento", "texto": "Explicar o conteudo e orientar uma atividade final."}],
            "acompanhamento": [
                "☑ Item 1 completo.",
                "☑ Item 2 completo.",
                "☑ Item 3 completo.",
            ],
            "acessibilidade": [
                "☑ Item 1 completo.",
                "☑ Item 2 completo.",
                "☑ Item 3 completo.",
            ],
        }
    ]

    problemas = validar_aulas_geradas(aulas)
    assert any("metodologia com poucas etapas" in problema for problema in problemas)


def test_validador_aceita_metodologia_curta_quando_modo_simples_esta_liberado():
    aulas = [
        {
            "tema": "Tema dividido em dois encontros",
            "aprendizagem": "Desenvolver habilidades de leitura e escrita relacionadas ao tema trabalhado em sala.",
            "metodologia": [
                {"titulo": "Para comecar", "texto": "Retomar o encontro anterior e apresentar a atividade do dia."},
                {"titulo": "Encerramento", "texto": "Socializar as respostas e preparar a continuidade para o proximo dia."},
            ],
            "acompanhamento": [
                "☑ Item 1 completo.",
                "☑ Item 2 completo.",
                "☑ Item 3 completo.",
            ],
            "acessibilidade": [
                "☑ Item 1 completo.",
                "☑ Item 2 completo.",
                "☑ Item 3 completo.",
            ],
        }
    ]

    assert validar_aulas_geradas(aulas, permitir_metodologia_simples=True) == []


def test_validador_exige_exatamente_tres_itens_com_marcador():
    aulas = [
        {
            "tema": "Leitura de noticia",
            "aprendizagem": "Interpretar informacoes explicitas e inferir efeitos de sentido em noticia.",
            "metodologia": [
                {
                    "titulo": "Para comecar",
                    "texto": "O professor apresenta uma noticia curta e conversa com os estudantes sobre o tema.",
                },
                {
                    "titulo": "Hora da leitura",
                    "texto": "O professor conduz a leitura guiada e os estudantes registram respostas no caderno.",
                },
                {
                    "titulo": "Encerramento",
                    "texto": "A turma socializa respostas e o professor sistematiza as ideias principais no quadro.",
                },
            ],
            "acompanhamento": ["Observar respostas.", "Verificar registro."],
            "acessibilidade": ["☑ Leitura guiada.", "Palavras-chave.", "☑ Resposta oral mediada."],
        }
    ]

    problemas = validar_aulas_geradas(aulas)
    assert any("acompanhamento da aprendizagem deve ter exatamente 3 itens" in item for item in problemas)
    assert any("acompanhamento da aprendizagem deve ter todos os itens iniciando com ☑" in item for item in problemas)
    assert any("acessibilidade deve ter todos os itens iniciando com ☑" in item for item in problemas)


def test_validador_coerencia_recursos():
    from core.validador_plano import validar_aula_final

    # 1. Sem correspondência de vídeo
    aula_sem_video = {
        "disciplina": "Ciências",
        "tema": "Sistema Solar",
        "aprendizagem": "Identificar os planetas do sistema solar.",
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Professor apresenta o tema."},
            {"titulo": "Foco no conteudo", "texto": "Assista ao vídeo explicativo sobre planetas."},
            {"titulo": "Encerramento", "texto": "Conclusão da aula."}
        ],
        "texto_fonte": "Texto sobre o sistema solar com informacoes teoricas apenas.",
        "recursos_detectados": ["slide", "texto"],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
    }
    avisos = validar_aula_final(aula_sem_video)
    assert any("nenhum" in a and "detectado" in a and "origem" in a for a in avisos)

    # 2. Com correspondência de vídeo no material
    aula_com_video = {
        "disciplina": "Ciências",
        "tema": "Sistema Solar",
        "aprendizagem": "Identificar os planetas do sistema solar.",
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Professor apresenta o tema."},
            {"titulo": "Foco no conteudo", "texto": "Assista ao vídeo explicativo sobre planetas."},
            {"titulo": "Encerramento", "texto": "Conclusão da aula."}
        ],
        "texto_fonte": "Veja o video no canal youtube.",
        "recursos_detectados": ["video", "texto"],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
    }
    avisos_ok = validar_aula_final(aula_com_video)
    assert not any("nenhum" in a and "detectado" in a and "origem" in a for a in avisos_ok)

    # 3. Sem correspondência de gráfico
    aula_sem_grafico = {
        "disciplina": "Ciências",
        "tema": "Sistema Solar",
        "aprendizagem": "Identificar os planetas.",
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Professor apresenta o tema."},
            {"titulo": "Foco no conteudo", "texto": "Analise a tabela e o grafico de distancias."},
            {"titulo": "Encerramento", "texto": "Conclusão da aula."}
        ],
        "texto_fonte": "Planetas distantes do sol.",
        "recursos_detectados": ["texto"],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
    }
    avisos_g = validar_aula_final(aula_sem_grafico)
    assert any("tabela" in a and "correspond" in a for a in avisos_g)

    # 4. Sem correspondência de experimento
    aula_sem_experimento = {
        "disciplina": "Ciências",
        "tema": "Reações Químicas",
        "aprendizagem": "Identificar reações.",
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Professor apresenta o tema."},
            {"titulo": "Foco no conteudo", "texto": "Faremos um experimento de misturar vinagre e bicarbonato."},
            {"titulo": "Encerramento", "texto": "Conclusão da aula."}
        ],
        "texto_fonte": "Teoria das reações químicas.",
        "recursos_detectados": ["texto"],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
    }
    avisos_exp = validar_aula_final(aula_sem_experimento)
    assert any("experimento" in a and "procedimento" in a for a in avisos_exp)
