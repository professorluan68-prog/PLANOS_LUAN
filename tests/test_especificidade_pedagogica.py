from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.classificador import normalizar_texto


def test_acompanhamento_especifico_olho_humano():
    itens = gerar_acompanhamento_aprimorado(
        tema="Olho humano",
        aprendizagem="Identificar estruturas do olho e explicar o caminho da luz.",
        desenvolvimento="Atividade de legenda de figura do olho humano.",
        disciplina="Biologia",
    )
    texto = " ".join(itens).lower()
    assert 2 <= len(itens) <= 3
    assert "caminho da luz" in texto
    assert "estruturas do olho" in texto


def test_acessibilidade_especifica_tabela():
    itens = gerar_acessibilidade_aprimorada(
        tema="Poluição",
        aprendizagem="Organizar informações em tabela.",
        desenvolvimento="Construção de tabela com tipo, fontes e impactos.",
        disciplina="Biologia",
    )
    texto = " ".join(itens).lower()
    assert 2 <= len(itens) <= 3
    assert "tabela" in texto
    assert "exemplo" in texto or "pares" in texto


def test_esquema_generico_nao_dispara_acessibilidade_de_olho():
    itens = gerar_acessibilidade_aprimorada(
        tema="Comparando vírus e células",
        aprendizagem="Comparar estruturas virais e celulares.",
        desenvolvimento="Analisar esquema comparativo entre vírus, células e metabolismo.",
        disciplina="Biologia",
    )
    texto = " ".join(itens).lower()

    assert "estruturas do olho" not in texto
    assert "caminho da luz" not in texto
    assert "olho" not in texto


def test_portugues_tirinha_usa_acompanhamento_e_acessibilidade_contextuais():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Humor e reflexão: a linguagem mista das tirinhas - Parte 1",
        aprendizagem="Inferir efeito de sentido, humor, ironia ou crítica em textos multissemióticos.",
        desenvolvimento="Analisar tirinhas, linguagem verbal e não verbal, conflito e crítica.",
        disciplina="Língua Portuguesa",
        perfil="lingua_portuguesa_ef",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Humor e reflexão: a linguagem mista das tirinhas - Parte 1",
        aprendizagem="Inferir efeito de sentido, humor, ironia ou crítica em textos multissemióticos.",
        desenvolvimento="Analisar tirinhas, linguagem verbal e não verbal, conflito e crítica.",
        disciplina="Língua Portuguesa",
        perfil="lingua_portuguesa_ef",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "tirinha" in texto
    assert "humor" in texto
    assert "linguagem verbal e não verbal" in texto
    assert "produção textual" not in texto
    assert "rascunho" not in texto


def test_portugues_verbo_haver_usa_itens_gramaticais():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Humor e reflexão: a linguagem mista das tirinhas - Parte 2",
        aprendizagem="Identificar o verbo haver em funcionamento no texto.",
        desenvolvimento="Estudar o uso do verbo haver como auxiliar e em situações de existência.",
        disciplina="Língua Portuguesa",
        perfil="lingua_portuguesa_ef",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Humor e reflexão: a linguagem mista das tirinhas - Parte 2",
        aprendizagem="Identificar o verbo haver em funcionamento no texto.",
        desenvolvimento="Estudar o uso do verbo haver como auxiliar e em situações de existência.",
        disciplina="Língua Portuguesa",
        perfil="lingua_portuguesa_ef",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "verbo haver" in texto
    assert "regras" in texto
    assert "produção textual" not in texto


def test_portugues_publicidade_diferencia_anuncio_metafora_e_imperativo():
    casos = [
        (
            "Pilares da publicidade - Parte 1",
            "Reconhecer elementos verbais e visuais dos anúncios publicitários.",
            "Analisar anúncios e estratégias publicitárias.",
            ["elementos verbais e visuais", "estratégias publicitárias"],
        ),
        (
            "Pilares da publicidade - Parte 2",
            "Identificar metáforas visuais e verbais em anúncios.",
            "Analisar metáforas na publicidade.",
            ["metáforas visuais e verbais", "palavras-chave"],
        ),
        (
            "Pilares da publicidade - Parte 3",
            "Analisar figuras de linguagem e uso do imperativo na publicidade.",
            "Reconhecer figuras de linguagem, estratégias persuasivas e imperativo em anúncios.",
            ["figuras de linguagem", "imperativo"],
        ),
    ]

    for tema, aprendizagem, desenvolvimento, esperados in casos:
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina="Língua Portuguesa",
            perfil="lingua_portuguesa_ef",
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina="Língua Portuguesa",
            perfil="lingua_portuguesa_ef",
        )
        texto = " ".join(acompanhamento + acessibilidade).lower()
        for esperado in esperados:
            assert esperado in texto
        assert "produção textual" not in texto


def test_redacao_leitura_trilha_tem_acompanhamento_e_acessibilidade_do_modelo():
    desenvolvimento = (
        "Para comecar: Retomar os acontecimentos ja lidos da obra Alice no Pais das Maravilhas. "
        "Predicao guiada: levantar hipoteses. Leitura compartilhada ou individual: identificar personagens."
    )

    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Trilha Alice no País das Maravilhas",
        aprendizagem="Participar de práticas de compartilhamento de leitura.",
        desenvolvimento=desenvolvimento,
        disciplina="Redação e Leitura",
        perfil="leitura_redacao",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Trilha Alice no País das Maravilhas",
        aprendizagem="Participar de práticas de compartilhamento de leitura.",
        desenvolvimento=desenvolvimento,
        disciplina="Redação e Leitura",
        perfil="leitura_redacao",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "narrativa" in texto
    assert "personagens" in texto
    assert "leitura mediada" in texto
    assert "perguntas orientadoras" in texto


def test_redacao_leitura_producao_final_tem_acompanhamento_e_acessibilidade_do_modelo():
    desenvolvimento = (
        "Para comecar: finalizar a producao textual. Revisao orientada: usar checklist. "
        "Escrita da versao final: incorporar melhorias. Submissao e socializacao: enviar para a Redacao Paulista."
    )

    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Prática de linguagem: Produção de textos",
        aprendizagem="Engajar-se nos processos de planejamento, revisão e reescrita.",
        desenvolvimento=desenvolvimento,
        disciplina="Redação e Leitura",
        perfil="leitura_redacao",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Prática de linguagem: Produção de textos",
        aprendizagem="Engajar-se nos processos de planejamento, revisão e reescrita.",
        desenvolvimento=desenvolvimento,
        disciplina="Redação e Leitura",
        perfil="leitura_redacao",
    )

    texto = " ".join(acompanhamento + acessibilidade).lower()
    assert "versão final" in texto
    assert "revisão" in texto
    assert "checklist" in texto
    assert "conectivos" in texto


def test_tecnologia_inovacao_dispositivos_usa_itens_contextuais():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Entrada e saída no computador",
        aprendizagem="Identificar dispositivos de entrada e saída e classificar corretamente suas funções.",
        desenvolvimento="Analisar teclado, mouse, microfone, câmera, monitor, impressora, projetor e caixa de som.",
        disciplina="Tecnologia e Inovação",
        perfil="tecnologia_inovacao",
        tipo="dispositivos_entrada_saida",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Entrada e saída no computador",
        aprendizagem="Identificar dispositivos de entrada e saída e classificar corretamente suas funções.",
        desenvolvimento="Analisar teclado, mouse, microfone, câmera, monitor, impressora, projetor e caixa de som.",
        disciplina="Tecnologia e Inovação",
        perfil="tecnologia_inovacao",
    )

    texto = normalizar_texto(" ".join(acompanhamento + acessibilidade))
    assert "entrada" in texto
    assert "saida" in texto
    assert "teclado" in texto
    assert "projetor" in texto


def test_tecnologia_inovacao_cultura_digital_e_obsolescencia_ficam_especificas():
    acompanhamento_cultura = gerar_acompanhamento_aprimorado(
        tema="Explorando a cultura digital",
        aprendizagem="Identificar comportamentos respeitosos e inadequados nas interações digitais.",
        desenvolvimento="Discutir cultura digital, respeito, ética, emoções e convivência online.",
        disciplina="Tecnologia e Inovação",
        perfil="tecnologia_inovacao",
        tipo="cultura_digital",
    )
    acompanhamento_obsol = gerar_acompanhamento_aprimorado(
        tema="Desvendando a obsolescência programada",
        aprendizagem="Compreender obsolescência programada e seus impactos ambientais.",
        desenvolvimento="Analisar lixo eletrônico, descarte e consumo consciente de tecnologia.",
        disciplina="Tecnologia e Inovação",
        perfil="tecnologia_inovacao",
        tipo="consumo_tecnologia",
    )

    texto_cultura = normalizar_texto(" ".join(acompanhamento_cultura))
    texto_obsol = normalizar_texto(" ".join(acompanhamento_obsol))
    assert "interacoes digitais" in texto_cultura
    assert "responsabilidade digital" in texto_cultura or "convivencia online" in texto_cultura
    assert "obsolesc" in texto_obsol
    assert "lixo eletrônico" in texto_obsol or "lixo eletronico" in texto_obsol
