from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas


TEXTO_AULA_5 = """
Aprofundamento em Geografia
Migrações internacionais
Objetivos da aula
● Identificar as principais causas das migrações internacionais, como conflitos, mudanças climáticas, perseguições políticas e crises econômicas;
● Relacionar como a globalização permite que migrantes busquem melhores condições de trabalho e qualidade de vida em economias emergentes e desenvolvidas.
Habilidades
Analisar criticamente as influências da globalização e mundialização nas juventudes, avaliando como esses processos impactam diferentes contextos sociais, econômicos e culturais e as oportunidades e desafios no mundo do trabalho.
Conteúdos
● Causas das migrações internacionais;
● Migração por oportunidade de trabalho e qualidade de vida.
Ponto de partida
Observe o mapa interativo sobre o fluxo de migração entre países.
COM SUAS PALAVRAS
Construindo o conceito
Causas e fatores da migração
Pause e responda
"""

TEXTO_AULA_6 = """
Aprofundamento em Geografia
Migração legal e ilegal
Objetivos da aula
● Identificar as diferenças entre migrantes legais e ilegais;
● Reconhecer os direitos e as restrições que se aplicam a cada tipo de migrante.
Habilidades
Analisar criticamente as influências da globalização e mundialização nas juventudes, avaliando como esses processos impactam diferentes contextos sociais, econômicos e culturais e as oportunidades e desafios no mundo do trabalho.
Conteúdos
● Migrantes legais e ilegais.
Ponto de partida
Observe as imagens!
VIREM E CONVERSEM
Construindo o conceito
Migração legal e regular
Riscos da migração ilegal
O papel do Estado nas decisões da imigração
Pause e responda
"""

TEXTO_AULA_7 = """
Aprofundamento em Geografia
Refugiados
Objetivos da aula
● Identificar as principais causas que levam ao deslocamento forçado de pessoas e à criação de fluxos de refugiados;
● Analisar mapas e gráficos sobre o fluxo de refugiados no mundo.
Conteúdos
● Causas dos fluxos de refugiados.
Ponto de partida
Observe as imagens de um campo de refugiados.
COM SUAS PALAVRAS
Construindo o conceito
Os termos refugiado e migrante não têm o mesmo significado.
Todo refugiado é migrante, mas nem todo migrante é refugiado.
Pause e responda
"""

TEXTO_AULA_8 = """
Aprofundamento em Geografia
Xenofobia
Objetivos da aula
● Analisar os fatores que impulsionam a xenofobia em países receptores de migrantes;
● Identificar algumas políticas públicas para o acolhimento de imigrantes no Brasil.
Conteúdos
● Migração e xenofobia;
● Políticas públicas para imigrantes no Brasil.
Ponto de partida
Leia a notícia sobre um caso de xenofobia sofrida por uma brasileira em Portugal.
COM SUAS PALAVRAS
Construindo o conceito
Migração global e xenofobia
Mídia, redes sociais e o reforço da xenofobia
Formas de manifestação da xenofobia
Pause e responda
"""


def test_aula_5_metodologia_fala_de_mapa_e_migracoes():
    colunas = montar_colunas_pedagogicas(TEXTO_AULA_5, "AULA 5 - Migrações internacionais")
    desenvolvimento = " ".join(bloco["texto"] for bloco in colunas["metodologia_blocos"]).lower()

    assert "mapa" in desenvolvimento or "fluxos" in desenvolvimento or "migra" in desenvolvimento
    assert "gráficos, tabelas ou dados" not in desenvolvimento
    assert "graficos, tabelas ou dados" not in desenvolvimento


def test_aula_6_metodologia_fala_de_imagens_direitos_e_estado():
    colunas = montar_colunas_pedagogicas(TEXTO_AULA_6, "AULA 6 - Migração legal e ilegal")
    desenvolvimento = " ".join(bloco["texto"] for bloco in colunas["metodologia_blocos"]).lower()

    assert "imagem" in desenvolvimento or "imagens" in desenvolvimento
    assert "estado" in desenvolvimento or "direitos" in desenvolvimento or "restrições" in desenvolvimento or "restricoes" in desenvolvimento


def test_aula_7_metodologia_fala_de_comparacao_conceitual():
    colunas = montar_colunas_pedagogicas(TEXTO_AULA_7, "AULA 7 - Refugiados")
    desenvolvimento = " ".join(bloco["texto"] for bloco in colunas["metodologia_blocos"]).lower()

    assert "disting" in desenvolvimento or "compar" in desenvolvimento or "conceito" in desenvolvimento


def test_aula_8_metodologia_fala_de_noticia_e_xenofobia():
    colunas = montar_colunas_pedagogicas(TEXTO_AULA_8, "AULA 8 - Xenofobia")
    desenvolvimento = " ".join(bloco["texto"] for bloco in colunas["metodologia_blocos"]).lower()

    assert "notícia" in desenvolvimento or "noticia" in desenvolvimento
    assert "xenofobia" in desenvolvimento


def test_colunas_tem_tres_itens_e_sao_menos_genericas():
    colunas = montar_colunas_pedagogicas(TEXTO_AULA_8, "AULA 8 - Xenofobia")

    assert len(colunas["acompanhamento_aprendizagem"]) == 3
    assert len(colunas["acessibilidade"]) == 3

    acompanhamento = " ".join(colunas["acompanhamento_aprendizagem"]).lower()
    acessibilidade = " ".join(colunas["acessibilidade"]).lower()

    assert "eixos, valores" not in acompanhamento
    assert "localizar dados relevantes" not in acessibilidade
