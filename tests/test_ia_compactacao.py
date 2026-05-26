from core.ia import _compactar_metodologia, _cortar_sem_quebrar_frase


def test_compactacao_da_ia_nao_corta_ultima_frase_no_meio():
    metodologia = [
        {
            "titulo": "Fechamento reflexivo",
            "texto": (
                "Finalizar a atividade com uma reflexao sobre a importancia de discutir "
                "o uso de fontes energeticas e sua sustentabilidade. Realizar uma breve "
                "apresentacao das conclusoes dos grupos, registrando os principais pontos "
                "no quadro para consolidar a aprendizagem da turma."
            ),
        }
    ]

    compactada = _compactar_metodologia(metodologia, "")

    texto = compactada[0]["texto"]
    assert texto.endswith(".")
    assert not texto.endswith("das c.")
    assert "Realizar uma breve apresentacao das c." not in texto


def test_compactacao_da_ia_prefere_remover_frase_que_nao_cabe():
    metodologia = [
        {
            "titulo": "Sintese e fechamento",
            "texto": (
                "Encerrar a aula pedindo que os alunos escrevam um texto-sintese sobre "
                "a importancia do saneamento basico, indicando relacoes entre poluicao, "
                "saude coletiva e prevencao. Incentivar a turma a compartilhar exemplos "
                "do cotidiano para ampliar a discussao."
            ),
        }
    ]

    compactada = _compactar_metodologia(metodologia, "")

    texto = compactada[0]["texto"]
    assert texto.endswith(".")
    assert not texto.endswith("in.")
    assert "saneamento basico, in." not in texto


def test_compactacao_da_ia_nao_cria_frase_com_preposicao_final():
    texto = (
        "Com a técnica Hora da leitura, os alunos leem a tirinha no livro e "
        "identificam como o humor é construído por exageros e contrastes, "
        "além de entenderem a importância do conflito na narrativa para despertar a reflexão."
    )

    cortado = _cortar_sem_quebrar_frase(texto, 165)

    assert not cortado.endswith(" a.")
    assert not cortado.endswith(" para.")
    assert cortado.endswith("contrastes.")


def test_compactacao_da_ia_nao_fecha_trechos_sem_sentido():
    finais_invalidos = [
        "Os alunos devem ler outra tirinha e explicar como aparecem o humor e o conflito, relacionando as",
        "Fazer uma reflexão final onde os alunos sintetizam como e em que situações utilizam o verbo haver como",
        "Concluir com um momento de reflexão utilizando a técnica Com suas palavras, onde os alunos",
    ]

    for texto in finais_invalidos:
        assert _cortar_sem_quebrar_frase(texto, 500) == ""


def test_compactacao_da_ia_mantem_frase_completa_mesmo_longa():
    metodologia = [
        {
            "titulo": "Encerramento",
            "texto": (
                "Promover uma reflexão final utilizando a técnica Com suas palavras, "
                "solicitando que os estudantes sintetizem os efeitos de sentido estudados "
                "e registrem uma conclusão no caderno."
            ),
        }
    ]

    compactada = _compactar_metodologia(metodologia, "")

    texto = compactada[0]["texto"]
    assert texto.endswith("caderno.")
    assert "onde os." not in texto
