from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.classificador import detectar_tipo_aula, normalizar_texto, perfil_disciplina
from core.lib.extrator_titulo import _limpar_titulo_material
from core.lib.higienizador_pedagogico import higienizar_plano
from core.lib.metodologia import MotorMetodologico, _etapas_por_perfil
from core.ia import _compactar_metodologia, _detectar_produto_atividade, _limpar_texto_curto
from core.lote import _normalizar_itens_contextuais
from core.prompts_por_disciplina import get_orientacao_disciplina, get_system_prompt
from core.qualidade_metodologica import sanitizar_texto_metodologico


def test_ciencias_classifica_tipos_da_analise_metodologica():
    assert perfil_disciplina("Ciencias") == "ciencias_ef"
    assert (
        detectar_tipo_aula(
            "Para comecar. Foco no conteudo com definicao, camadas e estrutura da Terra. Pause e responda.",
            "Camadas da Terra",
            "Ciencias",
        )
        == "conceito_novo"
    )
    assert (
        detectar_tipo_aula(
            "Hora da leitura com noticia do INPE, dados sobre queimadas e perguntas de analise critica.",
            "Desmatamento e queimadas",
            "Ciencias",
        )
        == "leitura_analise"
    )
    assert (
        detectar_tipo_aula(
            "Relembre. Anteriormente estudamos genetica. Exercicio resolvido com quadro de Punnett.",
            "Segunda Lei de Mendel",
            "Ciencias",
        )
        == "revisao_retomada"
    )
    assert (
        detectar_tipo_aula(
            "Estudo de caso sobre fadiga muscular, mitocondria e consequencias para o organismo.",
            "Mitocondria e energia",
            "Ciencias",
        )
        == "estudo_caso"
    )
    assert (
        detectar_tipo_aula(
            "Relembre. Na pratica, organizem a apresentacao do seminario e revisem a cartilha da campanha.",
            "Campanha de saude",
            "Ciencias",
        )
        == "producao_projeto"
    )


def test_ciencias_etapas_mudam_por_tipo_de_aula():
    assert [chave for _, chave in _etapas_por_perfil("ciencias_ef", "conceito_novo")] == [
        "para_comecar",
        "foco",
        "pause",
        "pratica",
        "encerramento",
    ]
    assert "modelo" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "revisao_retomada")]
    assert "estudo_caso" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "estudo_caso")]
    assert "compartilhamento" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "producao_projeto")]


def test_ciencias_classifica_novos_tipos_do_3o_bimestre():
    assert (
        detectar_tipo_aula(
            "Foco no conteudo com anemometro, barometro, pluviometro e analise do infografico com medidas da estacao meteorologica.",
            "Estacao meteorologica",
            "Ciencias",
        )
        == "analise_dados"
    )
    assert (
        detectar_tipo_aula(
            "Mao na massa com construcao de um modelo tridimensional de celula usando materiais de baixo custo e comparacao dos componentes.",
            "Celula animal: organelas",
            "Ciencias",
        )
        == "modelagem_cientifica"
    )
    assert (
        detectar_tipo_aula(
            "Foco no conteudo sobre responsabilidade compartilhada, residuos, coleta seletiva e propostas de acao para a escola.",
            "Logistica reversa e coleta seletiva",
            "Ciencias",
        )
        == "impacto_socioambiental"
    )
    assert (
        detectar_tipo_aula(
            "Voces sao uma equipe contratada para elaborar um plano de acao para a bacia hidrografica do municipio.",
            "Resolucao de problemas: recursos hidricos - Parte 2",
            "Ciencias",
        )
        == "situacao_problema"
    )
    assert (
        detectar_tipo_aula(
            "Apresentar a questao investigativa, levantar hipoteses, observar evidencias e registrar resultados antes da explicacao final.",
            "Como prever o tempo",
            "Ciencias",
        )
        == "investigativa"
    )


def test_ciencias_nao_cai_em_producao_projeto_por_termos_genericos_do_material():
    assert (
        detectar_tipo_aula(
            (
                "Foco no conteudo sobre rotacao e translacao da Terra. "
                "Os dados mostram diferencas entre os movimentos, e a turma registra respostas no caderno "
                "apos a apresentacao inicial do professor."
            ),
            "Movimentos da Terra",
            "Ciencias",
        )
        == "conceito_novo"
    )
    assert (
        detectar_tipo_aula(
            (
                "Grafico sobre desmatamento, biodiversidade e impactos ambientais. "
                "O texto mostra causas e consequencias do problema, com leitura de dados e discussao orientada."
            ),
            "Preservacao da biodiversidade: impacto humano",
            "Ciencias",
        )
        == "impacto_socioambiental"
    )


def test_ciencias_etapas_novas_refletem_analise_implantada():
    assert [chave for _, chave in _etapas_por_perfil("ciencias_ef", "analise_dados")] == [
        "para_comecar",
        "analise_dados",
        "foco",
        "pratica",
        "correcao_dialogada",
        "encerramento",
    ]
    assert [chave for _, chave in _etapas_por_perfil("ciencias_ef", "modelagem_cientifica")] == [
        "relembre",
        "observacao_inicial",
        "mao_na_massa",
        "socializacao",
        "correcao_dialogada",
        "encerramento",
    ]
    assert [chave for _, chave in _etapas_por_perfil("ciencias_ef", "situacao_problema")] == [
        "relembre",
        "situacao_problema",
        "pratica",
        "socializacao",
        "correcao_dialogada",
        "encerramento",
    ]


def test_motor_ciencias_leitura_analise_usa_dados_e_evidencias():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Hora da leitura. Noticia do INPE sobre aumento de queimadas no Brasil. "
            "Dados indicam impacto sobre biodiversidade e servicos ecossistemicos. "
            "Na pratica, responda com evidencias do texto."
        ),
        disciplina="Ciencias",
        turma="7 ano A",
        tema="Desmatamento e queimadas",
    )

    titulos = [etapa["titulo"] for etapa in etapas]
    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "Hora da leitura" in titulos
    assert "Pause e responda" in titulos
    assert "evidencias" in normalizar_texto(texto)
    assert "saude" in texto or "ambiente" in texto or "sociedade" in texto


def test_motor_ciencias_situacao_problema_usa_agentes_impactos_e_socializacao():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Relembre os conceitos de poluicao e saneamento. "
            "Situacao-problema: voces sao uma equipe contratada para propor um plano de acao "
            "para a bacia hidrografica do municipio. Na pratica, os grupos devem apresentar solucoes "
            "e discutir responsabilidades dos agentes envolvidos."
        ),
        disciplina="Ciencias",
        turma="9 ano A",
        tema="Resolucao de problemas: recursos hidricos - Parte 2",
    )

    titulos = [etapa["titulo"] for etapa in etapas]
    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "Situacao-problema" in titulos
    assert "Socializacao" in titulos
    assert "agentes" in texto
    assert "plano de acao" in texto or "acao coletiva" in texto


def test_motor_ciencias_rpg_plano_de_manejo_destaca_papeis_e_negociacao():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Relembre os conceitos de biodiversidade e unidade de conservacao. "
            "RPG: os grupos assumem os papeis de governo, comunidade local e pesquisadores "
            "para construir um plano de manejo. Na pratica, devem negociar propostas e justificar "
            "as medidas com base nas evidencias do material."
        ),
        disciplina="Ciencias",
        turma="9 ano C",
        tema="Aula pratica RPG: construindo um Plano de Manejo",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "papeis" in texto or "papel" in texto
    assert "plano de manejo" in texto
    assert "negoci" in texto


def test_motor_ciencias_conceito_novo_nao_usa_fallback_generico_de_comparacao():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Para comecar, observe a imagem do material e levante hipoteses sobre os movimentos da Terra. "
            "Foco no conteudo com explicacao sobre rotacao, translacao e relacao com a duracao dos dias e anos. "
            "Pause e responda antes da atividade final."
        ),
        disciplina="Ciencias",
        turma="8 ano B",
        tema="Movimentos de rotacao e translacao da Terra",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "movimentos de rotacao e translacao da terra" in texto
    assert "distinguir termos proximos" not in texto


def test_motor_ciencias_aula_inicial_expande_foco_e_numera_atividade():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Introducao a celula; Teoria celular; Seres unicelulares e pluricelulares.\n"
            "Para comecar\n"
            "VIREM E CONVERSEM 5 minutos\n"
            "Analise a imagem inicial da aula.\n"
            "Foco no conteudo\n"
            "A teoria celular\n"
            "Explicacao sobre Robert Hooke e a descoberta das celulas.\n"
            "Foco no conteudo\n"
            "Os pilares da teoria celular\n"
            "Apresentacao dos tres pilares.\n"
            "Na pratica\n"
            "TODO MUNDO ESCREVE\n"
            "Compare as imagens e registre o que os seres vivos tem em comum.\n"
        ),
        disciplina="Ciencias",
        turma="6 ano A",
        tema="A célula como unidade básica da vida",
    )

    por_titulo = {etapa["titulo"]: etapa["texto"] for etapa in etapas}
    texto_foco = por_titulo["Foco no conteudo"].lower()
    texto_pratica = por_titulo["Na pratica"]

    assert "“VIREM E CONVERSEM”" in por_titulo["Para comecar"]
    assert "pilares da teoria celular" in texto_foco
    assert "unicelulares" in texto_foco
    assert texto_pratica.startswith("Atividade 1:")
    assert "“TODO MUNDO ESCREVE”" in texto_pratica


def test_motor_ciencias_prioriza_texto_extraido_antes_da_cauda_legada_do_pdf():
    class ExtratorStub:
        def extrair(self, texto_pdf, tema):
            return {
                "conceito_extraido": "a teoria celular e a célula como unidade básica da vida",
                "atividade_extraida": "comparar seres unicelulares e pluricelulares com base nas imagens da aula",
                "recursos_detectados": ["imagem"],
                "etapas_detectadas": ["Para começar", "Foco no conteúdo", "Na prática"],
                "habilidade": "",
                "texto_prioritario": (
                    "Para começar. Observe a imagem inicial da aula e levante hipoteses sobre a menor unidade dos seres vivos. "
                    "Foco no conteudo com explicacao da teoria celular e comparacao entre seres unicelulares e pluricelulares. "
                    "Na pratica, registre as caracteristicas observadas."
                ),
            }

    motor = MotorMetodologico()
    motor.extrator = ExtratorStub()

    etapas = motor.gerar(
        texto_pdf=(
            "Para começar. Observe a imagem inicial da aula e levante hipoteses sobre a menor unidade dos seres vivos. "
            "Foco no conteudo com explicacao da teoria celular. "
            "Referencias. Revisao tecnica do material. Consolidar as aprendizagens no caderno de exercicios."
        ),
        disciplina="Ciencias",
        turma="6 ano A",
        tema="A célula como unidade básica da vida",
    )

    titulos = [etapa["titulo"] for etapa in etapas]
    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "Relembre" not in titulos
    assert "Para comecar" in titulos
    assert "Foco no conteudo" in titulos
    assert "teoria celular" in texto
    assert "conceitos ja estudados" not in texto


def test_motor_ciencias_ignora_fragmentos_brutos_do_pdf_em_conceito_e_atividade():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Relembre\n"
            "Retome os movimentos da Terra.\n"
            "Foco no conteudo\n"
            "Dinamica de conducao: utilize as imagens para ilustrar o que esta sendo explicado.\n"
            "1) O que e o Sol da meia-noite?\n"
            "2) Por que a linha do Equador e mais quente?\n"
            "Referencias LEITE, L. C. C.; CANTO, E. L. do.\n"
            "Na pratica\n"
            "Atividade 2. Responda a questao a seguir. Elabore hipoteses para o modelo.\n"
        ),
        disciplina="Ciencias",
        turma="8 ano B",
        tema="Inclinacao do eixo de rotacao da Terra",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "criterios de qualidade da producao cientifica" not in texto
    assert "referencias" not in texto
    assert "responda a questao a seguir" not in texto
    assert "aplicativo" not in texto
    assert "inclinacao do eixo de rotacao da terra" in texto


def test_ciencias_acompanhamento_e_acessibilidade_especificos():
    desenvolvimento = (
        "Estudo de caso sobre radiacao, DNA e consequencias para a saude. "
        "Os estudantes devem identificar evidencias e justificar a explicacao cientifica."
    )
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Radiacao e DNA",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Radiacao e DNA",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    assert len(acompanhamento) == 3
    assert len(acessibilidade) == 3
    assert any("caso" in item.lower() for item in acompanhamento)
    assert any("causa" in item.lower() or "evidencias" in item.lower() for item in acessibilidade)


def test_ciencias_acompanhamento_e_acessibilidade_analise_dados_seguem_padrao():
    desenvolvimento = (
        "Analise de dados com grafico do INPE e infografico sobre queimadas no Cerrado. "
        "Os estudantes devem comparar valores, localizar a fonte e justificar conclusoes com evidencias."
    )
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Desmatamento no Cerrado",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Desmatamento no Cerrado",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    assert len(acompanhamento) == 3
    assert len(acessibilidade) == 3
    assert all(item.startswith("☑") for item in acompanhamento)
    assert all(item.startswith("☑") for item in acessibilidade)
    assert any("fonte" in item.lower() or "dados" in item.lower() for item in acompanhamento)
    assert any("perguntas orientadoras" in item.lower() or "fonte" in item.lower() for item in acessibilidade)


def test_prompt_ciencias_reforca_evidencias_e_modelagem():
    prompt = get_system_prompt("Ciencias")
    orientacao = get_orientacao_disciplina("Ciencias")

    assert "nao chame toda atividade de experimento" in prompt.lower()
    assert "analise de dados" in orientacao.lower()
    assert "modelo" in orientacao.lower()
    assert "situacao-problema" in orientacao.lower()


def test_limpeza_titulo_remove_fragmento_da_natureza():
    titulo = _limpar_titulo_material(
        "Ciencias da Natureza Inclinacao do eixo de rotacao da Terra",
        "Ciencias",
    )

    assert titulo == "Inclinacao do eixo de rotacao da Terra"


def test_sanitizacao_ciencias_remove_fragmentos_de_extracao_e_contaminacao():
    texto = sanitizar_texto_metodologico(
        (
            "Conduzir a leitura orientada da noticia e das perguntas propostas, destacando informacoes principais, "
            "pontos de vista, formas de preconceito ou conflito e relacoes com o conceito central da aula. "
            "Aula pratica RPG: construindo um Plano de Manejo, Governo: responsavel pela, Explique que, ao longo da aula, "
            "os grupos irao discutir os elementos que compoem o plano."
        ),
        perfil="ciencias_ef",
        tema="Plano de manejo",
    )

    texto_norm = texto.lower()
    assert "preconceito" not in texto_norm
    assert "governo: responsavel" not in texto_norm
    assert "explique que" not in texto_norm
    assert "evidencias cientificas" in texto_norm


def test_higienizador_ciencias_preserva_tabela_grafico_e_mapa():
    metodologia, acompanhamento, acessibilidade = higienizar_plano(
        [
            {
                "titulo": "Foco no conteudo",
                "texto": "Orientar a leitura de graficos, tabelas e mapas do material antes da analise.",
            }
        ],
        [],
        [],
        "ciencias_ef",
        "Ciencias",
        "Biodiversidade",
        {"tabela": False, "grafico": False, "mapa": False},
    )

    texto = metodologia[0]["texto"].lower()
    assert "informacao do material" not in texto
    assert "graficos" in texto
    assert "tabelas" in texto
    assert "mapas" in texto


def test_ciencias_tabela_astronomia_ganha_acompanhamento_e_acessibilidade_mais_contextuais():
    desenvolvimento = (
        "Na pratica, preencher uma tabela comparando rotacao, translacao e precessao da Terra "
        "a partir do modelo e dos registros da aula."
    )

    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Movimentos da Terra",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Movimentos da Terra",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    texto_acomp = " ".join(acompanhamento).lower()
    texto_acess = " ".join(acessibilidade).lower()

    assert "movimentos da terra" in texto_acomp
    assert "comparar" in texto_acomp or "posicoes" in texto_acomp or "caracteristicas" in texto_acomp
    assert "preencher coletivamente uma linha da tabela" in texto_acess


def test_ciencias_revisao_retomada_nao_usa_exemplo_resolvido():
    desenvolvimento = (
        "Relembre os conceitos estudados sobre estacoes do ano, retome os registros anteriores "
        "e revise as explicacoes antes da atividade final."
    )

    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Estacoes do ano",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Estacoes do ano",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    texto = " ".join([*acompanhamento, *acessibilidade]).lower()

    assert "exemplo resolvido" not in texto
    assert "registros anteriores" in texto or "registro anterior" in texto


def test_normalizacao_ciencias_nao_substitui_modelagem_por_fallback_generico_so_por_legenda():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        [
            "☑ Verificar se os estudantes representam corretamente os movimentos do sistema Sol - Terra - Lua.",
            "☑ Observar se explicam o fenomeno com apoio do modelo construido.",
            "☑ Conferir se registros, falas ou legendas mostram a utilidade do modelo.",
        ],
        [
            "☑ Disponibilizar esquema visual com Sol, Terra e Lua para apoiar a leitura do modelo.",
            "☑ Organizar a atividade em etapas curtas, com demonstracao inicial das posicoes e movimentos.",
            "☑ Permitir registro por desenho identificado, legenda, setas ou explicacao oral mediada.",
        ],
        "Sistema Sol - Terra - Lua",
        "ciencias_ef",
    )

    texto_acess = " ".join(acessibilidade).lower()
    texto_acomp = " ".join(acompanhamento).lower()

    assert "legenda" in texto_acess
    assert "imagens, esquemas e exemplos do cotidiano" not in texto_acess
    assert "movimentos do sistema sol - terra - lua" in texto_acomp


def test_ia_nao_insere_placeholder_generico_quando_ha_produto_mais_concreto():
    texto_pdf = "No Livro do Estudante, responda as perguntas e registre as respostas no livro."
    compactada = _compactar_metodologia(
        [{"titulo": "Foco no conteudo", "texto": "Explicar os conceitos centrais da aula."}],
        texto_pdf,
        perfil="ciencias_ef",
    )

    texto = " ".join(item["texto"] for item in compactada).lower()

    assert _detectar_produto_atividade(texto_pdf) == "respostas no livro"
    assert "atividade do material" not in texto
    assert "respostas no livro" in texto


def test_limpeza_ciencias_corrige_frases_tortas_da_ia():
    texto = _limpar_texto_curto(
        "Iniciar com uma pausa de para que os alunos revisem o conceito. "
        "Assistir a um material impresso, quadro e registro no caderno sobre a movimentacao da Lua."
    )

    texto_norm = texto.lower()

    assert "pausa breve para que" in texto_norm
    assert "assistir a um material impresso" not in texto_norm
    assert "analisar com a turma um esquema" in texto_norm


def test_ciencias_astronomia_introdutoria_ganha_acompanhamento_e_acessibilidade_contextuais():
    desenvolvimento = (
        "Para comecar, observar a imagem de pessoas olhando o ceu e discutir a importancia da observacao "
        "dos astros para diferentes povos e calendarios."
    )

    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Astronomia e Historia da Observacao do Ceu",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Astronomia e Historia da Observacao do Ceu",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    texto = " ".join([*acompanhamento, *acessibilidade]).lower()

    assert "biolog" not in texto
    assert "prevenc" not in texto
    assert "ceu" in texto or "astros" in texto
    assert "calend" in texto or "histor" in texto


def test_normalizacao_ciencias_astronomia_usa_fallback_contextual_em_vez_de_biologia():
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        [
            "☑ Verificar se os estudantes descrevem o caminho do som e relacionam partes do sistema auditivo às funções.",
            "☑ Observar se conectam nível de decibéis, riscos à audição e impactos da poluição sonora.",
            "☑ Conferir se o resumo final apresenta medidas coerentes de prevenção e proteção auditiva.",
        ],
        [
            "☑ Ampliar o esquema anatômico e nomear oralmente cada estrutura antes da atividade individual.",
            "☑ Disponibilizar banco de palavras com os nomes das estruturas para apoiar a legenda.",
            "☑ Permitir apoio em dupla para leitura guiada e conferência das identificações.",
        ],
        "Astronomia e Historia da Observacao do Ceu",
        "ciencias_ef",
    )

    texto_acomp = " ".join(acompanhamento).lower()
    texto_acess = " ".join(acessibilidade).lower()

    assert "biolog" not in texto_acomp
    assert "prevenc" not in texto_acomp
    assert "ceu" in texto_acomp or "astros" in texto_acomp
    assert "sol" in texto_acess or "lua" in texto_acess or "astros" in texto_acess


def test_ciencias_modelagem_astronomia_varia_entre_terra_e_lua():
    desenvolvimento_terra = (
        "Observacao inicial do modelo tridimensional da Terra, com eixo, orbita, rotacao, translacao "
        "e relacao com as estacoes do ano."
    )
    desenvolvimento_lua = (
        "Observacao inicial do modelo com Sol, Terra e Lua para explicar fases da Lua, eclipses "
        "e posicoes relativas entre os astros."
    )

    acessibilidade_terra = gerar_acessibilidade_aprimorada(
        tema="Movimento de translacao da Terra",
        desenvolvimento=desenvolvimento_terra,
        disciplina="Ciencias",
    )
    acessibilidade_lua = gerar_acessibilidade_aprimorada(
        tema="Fases da Lua",
        desenvolvimento=desenvolvimento_lua,
        disciplina="Ciencias",
    )

    texto_terra = " ".join(acessibilidade_terra).lower()
    texto_lua = " ".join(acessibilidade_lua).lower()

    assert texto_terra != texto_lua
    assert "incidencia de luz" in texto_terra or "hemisferios" in texto_terra or "eixo terrestre" in texto_terra
    assert "fases" in texto_lua or "eclipses" in texto_lua or "fonte de luz" in texto_lua


def test_higienizador_corrige_frases_tortas_no_texto_final_de_ciencias():
    metodologia, acompanhamento, acessibilidade = higienizar_plano(
        [
            {
                "titulo": "Observacao inicial",
                "texto": (
                    "Medir a observacao do modelo e explicar a rotacionacao da Terra "
                    "para que os estudiantes compartilhem hipoteses."
                ),
            }
        ],
        ["☑ Orientar a leitura de uma conteudo da aula antes do registro final."],
        ["☑ Permitir que os estudiantes registrem por desenho ou explicacao oral."],
        "ciencias_ef",
        "Ciencias",
        "Movimentos da Terra",
        {"tabela": True, "grafico": True, "mapa": False},
    )

    texto_metodologia = metodologia[0]["texto"].lower()
    texto_acomp = " ".join(acompanhamento).lower()
    texto_acess = " ".join(acessibilidade).lower()

    assert "medir a observacao" not in texto_metodologia
    assert "rotacionacao" not in texto_metodologia
    assert "mediar a observação" in metodologia[0]["texto"].lower()
    assert "rotação" in metodologia[0]["texto"].lower()
    assert "um conteúdo da aula" in " ".join(acompanhamento).lower()
    assert "estudantes" in texto_metodologia
    assert "estudantes" in texto_acess
