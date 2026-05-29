from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas, norm


def test_gerador_colunas_so_insere_lemov_quando_aparece_no_texto():
    texto_sem_lemov = (
        "Conteudos\n"
        "● Inflacao\n"
        "● IPCA\n"
        "Objetivos\n"
        "● Analisar a relacao entre inflacao e poder de compra.\n"
        "A aula apresenta grafico de colunas com variacao do IPCA e leitura de dados.\n"
    )
    texto_com_lemov = texto_sem_lemov + "\nNo momento inicial, fazer Virem e conversem antes da leitura do grafico.\n"

    sem_lemov = montar_colunas_pedagogicas(texto_sem_lemov, "AULA 10 - Inflacao")
    com_lemov = montar_colunas_pedagogicas(texto_com_lemov, "AULA 10 - Inflacao")

    desenvolvimento_sem = sem_lemov["desenvolvimento"].lower()
    desenvolvimento_com = com_lemov["desenvolvimento"].lower()

    assert "virem e conversem" not in desenvolvimento_sem
    assert "todo mundo escreve" not in desenvolvimento_sem
    assert "virem e conversem" in desenvolvimento_com


def test_gerador_colunas_para_inflacao_nao_puxa_credito_sem_necessidade():
    texto = (
        "Conteudos\n"
        "● Inflacao\n"
        "● IPCA\n"
        "● Poder de compra\n"
        "Objetivos\n"
        "● Analisar como a inflacao afeta os precos e o poder de compra.\n"
        "Para comecar: observar manchete sobre inflacao.\n"
        "Foco no conteudo: interpretar grafico e tabela do IPCA.\n"
        "Pause e responda: comparar variacoes e justificar conclusoes.\n"
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 10 - Inflacao e poder de compra")
    desenvolvimento = colunas["desenvolvimento"].lower()
    acompanhamento = " ".join(colunas["acompanhamento_aprendizagem"]).lower()
    acessibilidade = " ".join(colunas["acessibilidade"]).lower()

    desenvolvimento_norm = norm(desenvolvimento)
    assert "grafico" in desenvolvimento_norm or "graficos" in desenvolvimento_norm
    assert "ipca" in desenvolvimento_norm or "poder de compra" in desenvolvimento_norm
    assert "credito" not in desenvolvimento
    assert "parcel" not in desenvolvimento
    assert "credito" not in acompanhamento
    assert "parcel" not in acompanhamento
    assert "credito" not in acessibilidade
    assert "parcel" not in acessibilidade
