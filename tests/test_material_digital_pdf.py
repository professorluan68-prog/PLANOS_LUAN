from core.lote import (
    _ajustar_texto_por_sequencia,
    _detectar_tecnicas_lemov,
    _garantir_tecnicas_lemov_na_metodologia,
    _material_digital_por_texto,
    _montar_etapas_metodologia,
    _normalizar_itens_contextuais,
    _sanitizar_aprendizagem,
    _variar_linguagem_metodologia,
)
from core.referencias_metodologia import carregar_referencia_metodologica
from docx_generator.preencher import _titulo_aula


def test_material_digital_usa_numero_real_do_pdf():
    texto = (
        "Educacao Financeira\n"
        "Por que poupamos? - Parte 1\n"
        "2o bimestre Ensino Fundamental:\n"
        "Aula 06 Anos Finais\n"
        "Reserva de emergencia; Explicar o que e uma reserva\n"
    )

    material = _material_digital_por_texto(
        texto,
        r"D:\PLANOS DE JUNHO\ADRIANA ALDA PALOS\PDF_AULAS\EDUCACAO FINANCEIRA\AULA06_7ANO.pdf",
        "Educacao Financeira",
    )

    assert material == "AULA 06 - Por que poupamos? - Parte 1"


def test_material_digital_preserva_titulo_multilinha_da_capa():
    texto = (
        "Educacao Financeira\n"
        "Por que poupamos?\n"
        "- Parte 2\n"
        "2o bimestre Ensino Fundamental:\n"
        "Aula 7 Anos Finais\n"
    )

    material = _material_digital_por_texto(texto, "AULA07_7ANO.pdf", "Educacao Financeira")

    assert material == "AULA 7 - Por que poupamos? - Parte 2"


def test_material_digital_junta_titulo_quebrado_em_artigo_ou_preposicao():
    texto = (
        "Aprof. em Biologia\n"
        "Virologia: mutacoes virais e a\n"
        "necessidade de manutencao da\n"
        "cobertura vacinal.\n"
        "Parasitologia\n"
        "2o bimestre Ensino Medio\n"
        "Aula 5\n"
    )

    material = _material_digital_por_texto(texto, "AULA05_BIOLOGIA.pdf", "Aprof. em Biologia")

    assert material == "AULA 5 - Virologia: mutacoes virais e a necessidade de manutencao da cobertura vacinal."


def test_material_digital_junta_titulo_quando_continuacao_comeca_com_por():
    texto = (
        "Aprof. em Biologia\n"
        "Principais doencas humanas causadas\n"
        "por virus\n"
        "2o bimestre Ensino Medio\n"
        "Aula 7\n"
    )

    material = _material_digital_por_texto(texto, "AULA07_BIOLOGIA.pdf", "Aprof. em Biologia")

    assert material == "AULA 7 - Principais doencas humanas causadas por virus"


def test_material_digital_junta_titulo_quando_linha_intermediaria_termina_com_dois_pontos():
    texto = (
        "Aprof. em Biologia\n"
        "Principais doencas humanas\n"
        "causadas por platelmintos:\n"
        "esquistossomose\n"
        "Parasitologia\n"
        "Aula 8\n"
    )

    material = _material_digital_por_texto(texto, "AULA08_BIOLOGIA.pdf", "Aprof. em Biologia")

    assert material == "AULA 8 - Principais doencas humanas causadas por platelmintos: esquistossomose"


def test_material_digital_junta_titulo_quando_primeira_parte_termina_com_virgula():
    texto = (
        "Biologia\n"
        "Teorias cientificas:\n"
        "experimentos de Redi,\n"
        "Spallanzani e Pasteur\n"
        "3o bimestre Ensino Medio\n"
        "Aula 10 Medio\n"
    )

    material = _material_digital_por_texto(texto, "AULA_10.pdf", "Biologia")

    assert material == "AULA 10 - Teorias cientificas experimentos de Redi, Spallanzani e Pasteur"


def test_titulos_reais_biologia_silvana_aulas_5_a_8():
    casos = [
        (
            "AULA05_3ANO_EM.pdf",
            "Aprofundamento em Biologia\n"
            "Virologia: mutacoes virais e a\n"
            "necessidade de manutencao da\n"
            "cobertura vacinal.\n"
            "Parasitologia\n"
            "Aula 5\n",
            "AULA 5 - Virologia: mutacoes virais e a necessidade de manutencao da cobertura vacinal.",
        ),
        (
            "AULA06_3ANO_EM.pdf",
            "Aprofundamento em Biologia\n"
            "Por que nem todas as doencas\n"
            "causadas por virus tem vacina?\n"
            "Parasitologia\n"
            "Aula 6\n",
            "AULA 6 - Por que nem todas as doencas causadas por virus tem vacina?",
        ),
        (
            "AULA07_3ANO_EM.pdf",
            "Aprofundamento em Biologia\n"
            "Principais doencas humanas causadas\n"
            "por nematodeos: lombriga e amarelao\n"
            "Parasitologia\n"
            "Aula 7\n",
            "AULA 7 - Principais doencas humanas causadas por nematodeos: lombriga e amarelao",
        ),
        (
            "AULA08_3ANO_EM.pdf",
            "Aprofundamento em Biologia\n"
            "Principais doencas humanas\n"
            "causadas por platelmintos:\n"
            "esquistossomose\n"
            "Parasitologia\n"
            "Aula 8\n",
            "AULA 8 - Principais doencas humanas causadas por platelmintos: esquistossomose",
        ),
    ]

    for nome, texto, esperado in casos:
        assert _material_digital_por_texto(texto, nome, "Aprofundamento em Biologia") == esperado


def test_titulos_biologia_silvana_aulas_6_a_9_nao_ficam_cortados():
    casos = [
        (
            "AULA6_2_ANO_EM.pdf",
            "Biologia\n"
            "Aula desafio: o caso do\n"
            "virus Machupo\n"
            "2o bimestre Ensino\n"
            "Aula 6 Medio\n",
            "AULA 6 - Aula desafio: o caso do virus Machupo",
        ),
        (
            "AULA7_2_ANO_EM.pdf",
            "Biologia\n"
            "Aula desafio: alteracoes\n"
            "ambientais e saude no caso\n"
            "do virus Machupo\n"
            "2o bimestre Ensino\n"
            "Aula 7 Medio\n",
            "AULA 7 - Aula desafio: alteracoes ambientais e saude no caso do virus Machupo",
        ),
        (
            "AULA9_2_ANO_EM.pdf",
            "Biologia\n"
            "Organismos geneticamente\n"
            "modificados sao\n"
            "transgenicos?\n"
            "2o bimestre Ensino\n"
            "Aula 9 Medio\n",
            "AULA 9 - Organismos geneticamente modificados sao transgenicos?",
        ),
    ]

    for nome, texto, esperado in casos:
        assert _material_digital_por_texto(texto, nome, "Biologia") == esperado


def test_redacao_leitura_preserva_titulos_iniciais_dos_pdfs():
    casos = [
        (
            "AULA 5.pdf",
            "AULA 5 -Trilha “Alice no País das Maravilhas”\nHabilidade: (EF69LP46) Participar de práticas de compartilhamento de leitura.",
            "AULA 5 - Trilha “Alice no País das Maravilhas”",
        ),
        (
            "AULA 6 Trilha.pdf",
            "AULA 6 Trilha “O Pequeno Príncipe”\n(EF67LP28) Ler e compreender romances infantojuvenis.",
            "AULA 6 - Trilha “O Pequeno Príncipe”",
        ),
        (
            "AULA 7 Trilha.pdf",
            "AULA 7 Trilha “Peter Pan e Wendy”\n(EF67LP28) Ler e compreender textos literários.",
            "AULA 7 - Trilha “Peter Pan e Wendy”",
        ),
        (
            "AULA 8 Prática de linguagem.pdf",
            "Aulas 5 e 6 | Práticas de Leitura | Versão final do Texto 3 | 6º ano\nAULA 8 Prática de linguagem: Produção de textos\n(EF69LP51) Engajar-se ativamente.",
            "AULA 8 - Prática de linguagem: Produção de textos",
        ),
    ]

    for nome, texto, esperado in casos:
        assert _material_digital_por_texto(texto, nome, "Redação e Leitura") == esperado


def test_redacao_leitura_trilha_usa_modelo_do_docx():
    texto = (
        "AULA 5 -Trilha “Alice no País das Maravilhas”\n"
        "Habilidade: (EF69LP46) Participar de práticas de compartilhamento de leitura.\n"
        "1. Disparo inicial\n"
        "Retome os acontecimentos já lidos e pergunte o que aconteceu com Alice.\n"
        "2. Predição guiada\n"
        "Incentive a formulação de hipóteses a partir do tom fantástico da narrativa.\n"
        "3. Leitura compartilhada ou individual\n"
        "4. Conexão com a produção textual\n"
    )

    metodologia = _montar_etapas_metodologia(
        texto,
        "Redação e Leitura",
        "6º ano",
        "Trilha “Alice no País das Maravilhas”",
    )

    titulos = [item["titulo"] for item in metodologia]
    corpo = " ".join(item["texto"] for item in metodologia).lower()
    assert titulos == [
        "Disparo inicial / contextualizacao",
        "Leitura ou exploracao inicial",
        "Analise guiada",
        "Sistematizacao",
        "Producao textual",
        "Revisao e fechamento",
    ]
    assert "alice no país das maravilhas" in corpo
    assert "personagens" in corpo
    assert "acontecimentos" in corpo
    assert "objetivo pedagogico" in corpo
    assert "producoes textuais criativas" in corpo or "produções textuais criativas" in corpo


def test_redacao_leitura_producao_final_usa_modelo_do_docx():
    texto = (
        "Aulas 5 e 6 | Práticas de Leitura | Versão final do Texto 3 | 6º ano\n"
        "AULA 8 Prática de linguagem: Produção de textos\n"
        "(EF69LP51) Engajar-se ativamente nos processos de planejamento, textualização, revisão/ edição e reescrita.\n"
        "1. Disparo inicial\n"
        "Explique que os estudantes irão finalizar a produção textual, passando do rascunho para a versão final.\n"
        "2. Revisão orientada\n"
        "3. Escrita e submissão da versão final\n"
    )

    metodologia = _montar_etapas_metodologia(
        texto,
        "Redação e Leitura",
        "6º ano",
        "Prática de linguagem: Produção de textos",
    )

    titulos = [item["titulo"] for item in metodologia]
    corpo = " ".join(item["texto"] for item in metodologia).lower()
    assert titulos == [
        "Disparo inicial / contextualizacao",
        "Leitura ou exploracao inicial",
        "Analise guiada",
        "Sistematizacao",
        "Producao textual",
        "Revisao e fechamento",
    ]
    assert "rascunho" in corpo
    assert "versao final" in corpo
    assert "redacao paulista" in corpo
    assert "checklist" in corpo


import pytest
@pytest.mark.skip(reason="Referencias removidas")
def test_redacao_leitura_carrega_guia_metodologico_especifico():
    referencia = carregar_referencia_metodologica("Redação e Leitura", "6º ano")

    assert "LEITURA E REDA" in referencia
    assert "conecta leitura com produ" in referencia.lower()


def test_sanitiza_aprendizagem_truncada_e_incompativel_com_tema():
    aprendizagem = _sanitizar_aprendizagem(
        "Identificar partes do sistema auditivo e impactos da poluicao sonora.",
        "Principais doencas humanas causadas por platelmintos: esquistossomose",
    )

    assert "esquistossomose" in aprendizagem.lower()
    assert "auditivo" not in aprendizagem.lower()
    assert not aprendizagem.endswith(" por")


def test_substitui_acompanhamento_e_acessibilidade_incompativeis_com_parasitologia():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        ["☑ Verificar se descrevem o caminho do som e o sistema auditivo."],
        ["☑ Nomear estruturas do sistema auditivo e discutir decibeis."],
        "Principais doencas humanas causadas por platelmintos: esquistossomose",
        "biologia",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "sistema auditivo" not in texto
    assert "decibeis" not in texto
    assert "saneamento" in texto
    assert "parasita" in texto


def test_substitui_acompanhamento_e_acessibilidade_incompativeis_com_genetica():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        ["â˜‘ Verificar se descrevem o caminho do som e o sistema auditivo."],
        ["â˜‘ Nomear estruturas do sistema auditivo e discutir decibeis."],
        "Primeira lei de Mendel e hereditariedade",
        "ciencias_ef",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "sistema auditivo" not in texto
    assert "decibeis" not in texto
    assert "hereditariedade" in texto or "dna" in texto or "gene" in texto


def test_substitui_visao_incompativel_com_virus_e_celulas():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        ["☑ Verificar se identificam estruturas do olho e o caminho da luz."],
        ["☑ Apresentar imagens e esquemas simples sobre vírus, mutações e vacinação antes da atividade individual."],
        "Comparando vírus e células: estrutura e características essenciais",
        "biologia",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "estruturas do olho" not in texto
    assert "caminho da luz" not in texto
    assert "vacinação" not in texto
    assert "vírus" in texto or "virus" in texto
    assert "célula" in texto or "celula" in texto


def test_substitui_esquema_anatomico_generico_em_tema_nao_anatomico():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        ["☑ Verificar se interpretam a tabela do material."],
        [
            "☑ Ampliar o esquema anatômico e nomear oralmente cada estrutura antes da atividade individual.",
            "☑ Disponibilizar banco de palavras com os nomes das estruturas para apoiar a legenda.",
        ],
        "AULA 6 - vírus Machupo",
        "biologia",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "esquema anatômico" not in texto
    assert "nomes das estruturas" not in texto
    assert "vírus" in texto or "virus" in texto


def test_substitui_visao_incompativel_com_projeto_de_vida():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        ["☑ Verificar se identificam estruturas do olho e o caminho da luz."],
        ["☑ Disponibilizar banco de palavras com os nomes das estruturas do olho."],
        "Mapeando e ativando minha rede de apoio",
        "projeto_de_vida",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "estruturas do olho" not in texto
    assert "caminho da luz" not in texto
    assert "rede de apoio" in texto


def test_mantem_visao_e_audicao_quando_tema_compativel():
    acompanhamento_visao, _ = _normalizar_itens_contextuais(
        ["☑ Verificar se identificam estruturas do olho e explicam o caminho da luz."],
        ["☑ Ampliar o esquema anatômico do olho."],
        "Impactos da poluição nos sistemas fisiológicos: visão",
        "biologia",
    )
    acompanhamento_audicao, _ = _normalizar_itens_contextuais(
        ["☑ Observar se conectam nível de decibéis e sistema auditivo."],
        ["☑ Nomear estruturas do sistema auditivo."],
        "Impactos da poluição nos sistemas fisiológicos: audição",
        "biologia",
    )

    assert "olho" in " ".join(acompanhamento_visao).lower()
    assert "decib" in " ".join(acompanhamento_audicao).lower()


def test_preenchimento_docx_prefere_material_extraido_do_pdf():
    aula = {
        "material": "AULA 06 - Por que poupamos? - Parte 1",
        "tema": "Tema ajustado pela IA",
    }

    assert _titulo_aula(aula, 2) == "AULA 06 - Por que poupamos? - Parte 1"


def test_desenvolvimento_coloca_titulo_entre_aspas():
    metodologia = [
        {
            "titulo": "Para comecar",
            "texto": "Retomar a aula anterior sobre Por que poupamos? - Parte 1 e conectar os registros.",
        }
    ]

    ajustada = _variar_linguagem_metodologia(
        metodologia,
        "Educacao Financeira",
        "7 ano B",
        "Por que poupamos? - Parte 1",
    )

    assert '"Por que poupamos? - Parte 1"' in ajustada[0]["texto"]


def test_metodologia_ignora_rotulo_de_bimestre_como_conceito():
    etapas = _montar_etapas_metodologia(
        texto=(
            "Biologia\n"
            "2o bimestre Ensino\n"
            "Polinizacao e controle biologico\n"
            "Foco no conteudo\n"
            "Abelhas e polinizacao em ecossistemas.\n"
        ),
        disciplina="Biologia",
        turma="2 ano C",
        tema="Polinizacao e controle biologico",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas)
    assert "2o bimestre" not in texto.lower()
    assert "bimestre ensino" not in texto.lower()
    assert "Polinizacao e controle biologico" in texto


def test_metodologia_converte_verbos_para_infinitivo():
    metodologia = [
        {
            "titulo": "Para comecar",
            "texto": "Realize a leitura inicial. O professor explica o conceito. Finalize a atividade com registro.",
        }
    ]

    ajustada = _variar_linguagem_metodologia(
        metodologia,
        "Biologia",
        "1 ano A",
        "Citologia",
    )

    texto = ajustada[0]["texto"]
    assert "Realizar a leitura inicial." in texto
    assert "Explicar o conceito." in texto
    assert "Finalizar a atividade com registro." in texto


def test_aula_de_pdf_novo_nao_recebe_retomada_automatica():
    texto = "Ativar conhecimentos previos sobre o tema."
    ajustado = _ajustar_texto_por_sequencia(
        texto,
        chave="para_comecar",
        indice_aula=1,
        total_aulas=5,
        tema="Crase",
    )

    assert ajustado == texto
    assert "Retomar a aula anterior" not in ajustado
    assert "Dar continuidade ao estudo de" not in ajustado


def test_detecta_tecnicas_lemov_no_pdf():
    tecnicas = _detectar_tecnicas_lemov(
        "Virem e conversem. Em seguida, todo mundo escreve. Pause e responda.",
        "Fracoes",
    )

    assert "VIREM E CONVERSEM" in tecnicas
    assert "TODO MUNDO ESCREVE" in tecnicas
    assert "PAUSE E RESPONDA" in tecnicas


def test_fluxo_ia_reinsere_tecnicas_lemov_quando_sumirem():
    metodologia = [
        {"titulo": "Para comecar", "texto": "Retomar conhecimentos previos sobre fracoes e apresentar o objetivo da aula."},
        {"titulo": "Na pratica", "texto": "Orientar a resolucao das atividades com acompanhamento da turma."},
    ]

    ajustada = _garantir_tecnicas_lemov_na_metodologia(
        metodologia,
        ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE"],
    )

    texto = " ".join(item["texto"] for item in ajustada)
    assert "VIREM E CONVERSEM" in texto
    assert "TODO MUNDO ESCREVE" in texto
    assert "tecnica lemov" not in texto.lower()
    assert "No momento" not in texto


def test_pdf_khan_matematica_revisao_de_funcao_usa_metodologia_fixa():
    from core.lote import _metodologia_fixa_pdf_especial

    texto = (
        "Matematica Aula Khan Revisao: Conceito de funcao. "
        "Representacoes algébrica e grafica de grandezas dependentes. "
        "Relacoes proporcionais. Grandezas diretamente proporcionais e grandezas inversamente proporcionais. "
        "Pratica na Khan. Atividade Khan."
    )

    metodologia = _metodologia_fixa_pdf_especial(texto, "Matematica", "Revisao: Conceito de funcao")

    assert metodologia is not None
    assert [item["titulo"] for item in metodologia] == [
        "Para comecar",
        "Foco no conteudo",
        "Pratica e consolidacao",
        "Fechamento",
    ]
    texto_total = " ".join(item["texto"] for item in metodologia)
    assert "funcao" in texto_total.lower()
    assert "proporcionalidade" in texto_total.lower()
    assert "aplicativo" in texto_total.lower()


def test_sanitiza_aprendizagem_de_redacao_sem_metodologia_colada():
    aprendizagem = _sanitizar_aprendizagem(
        "Habilidade: (EF69LP46) Participar de praticas de compartilhamento de leitura/recepcao de obras literarias. Trilha Harry Potter e o Calice de Fogo 1. Disparo inicial Explique o objetivo da aula.",
        "Trilha Harry Potter e o Calice de Fogo",
    )

    assert aprendizagem.startswith("Habilidade: (EF69LP46)")
    assert "Trilha Harry Potter" not in aprendizagem
    assert "Disparo inicial" not in aprendizagem


def test_sanitiza_aprendizagem_remove_fonte_bibliografica_e_duplicacao():
    aprendizagem = _sanitizar_aprendizagem(
        "Habilidade: Habilidade (EF89LP33) Ler, de forma autônoma, e compreender poemas e outros textos literários. (SÃO PAULO, 2019)",
        "Conexões entre canção e reflexão",
        perfil="lingua_portuguesa_ef",
    )

    assert aprendizagem.startswith("Habilidade: (EF89LP33)")
    assert "Habilidade: Habilidade" not in aprendizagem
    assert "SÃO PAULO" not in aprendizagem
    assert "2019" not in aprendizagem


def test_parece_titulo_atividade_filter():
    from core.lib.extrator_pdf import _parece_titulo_atividade
    assert _parece_titulo_atividade("Discussão sobre tipos de gastos") is True
    assert _parece_titulo_atividade("Comparação de preços de cesta básica") is True
    assert _parece_titulo_atividade("Elaborar uma tabela simples no quadro") is True
    assert _parece_titulo_atividade("Identificar e diferenciar gastos fixos e variáveis em um orçamento familiar.") is False


def test_limpar_placeholders_acessibilidade():
    from core.lib.higienizador_pedagogico import _limpar_placeholders_acessibilidade
    texto = "Organizar despesas em informação do material simples no quadro."
    assert _limpar_placeholders_acessibilidade(texto) == "Organizar despesas em tabela simples no quadro."

    texto = "Permitir respostas orais, desenhos, informações do material mentais ou registros em tópicos."
    assert "mapas mentais" in _limpar_placeholders_acessibilidade(texto)

    texto = "Permitir registro em tópicos, desenho, recurso do material mental ou resposta oral mediada."
    assert "mapa mental" in _limpar_placeholders_acessibilidade(texto)


def test_detectar_tipo_aula_ef_pratica():
    from core.lib.classificador import detectar_tipo_aula
    texto = "Os alunos devem elaborar uma tabela em duplas e simular gastos de compras."
    tipo = detectar_tipo_aula(texto, "Orçamento Familiar", "Educação Financeira")
    assert tipo == "aula_pratica_continuidade"


def test_variacoes_lemov_na_metodologia():
    from core.lib.modalidades import garantir_tecnicas_lemov_na_metodologia
    metodologia = [
        {"titulo": "Para comecar", "texto": "Discussão inicial sobre orçamento familiar."},
        {"titulo": "Na pratica", "texto": "Realizar atividade prática do material."}
    ]
    # Com texto diferente, o hash é diferente, gerando variações
    metodologia_1 = garantir_tecnicas_lemov_na_metodologia(metodologia, ["PAUSE E RESPONDA"])
    
    # Nova metodologia com texto diferente
    metodologia_b = [
        {"titulo": "Para comecar", "texto": "Abertura diferente e mais longa da aula sobre finanças."},
        {"titulo": "Na pratica", "texto": "Realizar atividade prática do material."}
    ]
    metodologia_2 = garantir_tecnicas_lemov_na_metodologia(metodologia_b, ["PAUSE E RESPONDA"])
    
    # Ambas devem conter a técnica PAUSE E RESPONDA mas o acréscimo textual pode variar deterministicamente
    assert "PAUSE E RESPONDA" in metodologia_1[0]["texto"]
    assert "PAUSE E RESPONDA" in metodologia_2[0]["texto"]

