from core.ia import _normalizar_saida_ia
from core.qualidade_metodologica import (
    detectar_contexto_metodologico,
    extrair_conceito_central,
    naturalizar_metodologia_professor,
    normalizar_texto,
    revisar_metodologia,
)


def test_extrai_conceito_sem_rotulo_de_aula():
    assert extrair_conceito_central("AULA 12 - Juros compostos - Parte 1") == "Juros compostos"


def test_revisa_metodologia_remove_frase_generica():
    metodologia, relatorio = revisar_metodologia(
        [
            {
                "titulo": "Para comecar",
                "texto": "AULA 1 - Retomar conhecimentos prévios da turma sobre fracoes e registrar respostas.",
            }
        ],
        perfil="matematica",
        tema="Fracoes equivalentes",
    )

    texto = normalizar_texto(metodologia[0]["texto"])
    assert "aula 1" not in texto
    assert "retomar conhecimentos previos da turma sobre" not in texto
    assert "fracoes equivalentes" in texto
    assert relatorio["score"] < 100


def test_contexto_cdp_evitaliza_recurso_digital():
    contexto = detectar_contexto_metodologico(
        texto_pdf="Plano CDP EJA com atividade impressa",
        disciplina="Matematica",
        turma="multisseriada",
    )
    metodologia, _ = revisar_metodologia(
        [
            {
                "titulo": "Na pratica",
                "texto": "Orientar a resolucao de atividades usando computador e internet para pesquisar exemplos.",
            }
        ],
        perfil="matematica",
        tema="Proporcionalidade",
        contexto=contexto,
    )

    texto = normalizar_texto(metodologia[0]["texto"])
    assert "computador" not in texto
    assert "internet" not in texto
    assert "o material da aula" in texto


def test_saida_ia_e_filtrada_antes_de_voltar_ao_lote():
    data = {
        "tema": "AULA 3 - Credito e juros - Parte 1",
        "aprendizagem": "Comparar valor a vista, parcelas e custo total.",
        "metodologia": [
            {
                "titulo": "Para comecar",
                "texto": "Retomar conhecimentos prévios da turma sobre credito e juros com perguntas iniciais.",
            },
            {
                "titulo": "Foco no conteudo",
                "texto": "Desenvolver o conteúdo com exemplo de compra parcelada e valor a vista.",
            },
            {
                "titulo": "Na pratica",
                "texto": "Orientar a resolução de atividades envolvendo parcelas e custo total.",
            },
        ],
    }

    plano = _normalizar_saida_ia(data, "", "Educacao Financeira", "7 ano A")
    texto = normalizar_texto(" ".join(item["texto"] for item in plano["metodologia"]))

    assert plano["tema"] == "Credito e juros"
    assert "retomar conhecimentos previos da turma sobre" not in texto
    assert "orientar a resolucao de atividades" not in texto


def test_saida_ia_limita_desenvolvimento_e_preserva_produto_do_material():
    data = {
        "tema": "AULA 9 - Sistema visual",
        "aprendizagem": "Identificar estruturas do olho humano.",
        "metodologia": [
            {"titulo": "Foco no conteudo", "texto": "O docente apresenta o conteúdo e Conduzir uma discussão final onde a turma participa."},
            {"titulo": "Na pratica", "texto": "Esta atividade deve durar cerca de. Os alunos resolvem por."},
            {"titulo": "Encerramento", "texto": "Relacionar a explicação aos registros anteriores para que a turma perceba continuidade, aprofundamento e novos desafios."},
        ],
    }
    texto_pdf = "Na prática: legendar a figura do olho humano e identificar as estruturas principais."
    plano = _normalizar_saida_ia(data, texto_pdf, "Biologia", "1 ANO EM")
    desenvolvimento = " ".join(item["texto"] for item in plano["metodologia"])
    texto = normalizar_texto(desenvolvimento)

    assert len(desenvolvimento) <= 900
    assert "legenda de figura" in texto
    assert "esta atividade deve durar cerca de" not in texto
    assert not texto.endswith("por")


def test_naturaliza_metodologia_com_tecnica_embutida_na_acao_docente():
    metodologia = naturalizar_metodologia_professor(
        [
            {
                "titulo": "Para comecar",
                "texto": (
                    "Iniciar a aula utilizando a tecnica 'Virem e conversem'. "
                    'No momento "TODO MUNDO ESCREVE", os alunos registram hipoteses no caderno. '
                    "Atividade: Mediar a atividade principal do material, preservando o produto esperado: tabela."
                ),
            },
            {
                "titulo": "Foco no conteudo",
                "texto": (
                    'Em "PAUSE E RESPONDA", o professor verifica a compreensao da turma antes de avancar '
                    "para a etapa seguinte. Relacionar a explicacao aos registros anteriores para que a turma "
                    "perceba continuidade, aprofundamento e novos desafios."
                ),
            },
        ]
    )

    texto = normalizar_texto(" ".join(item["texto"] for item in metodologia))

    assert "virem e conversem" in texto
    assert "todo mundo escreve" in texto
    assert "pause e responda" in texto
    assert "preservando o produto esperado" not in texto
    assert "relacionar a explicacao aos registros anteriores" not in texto
    assert "producao de tabela" in texto


def test_limpa_repeticao_tecnicas_lemov_ia():
    from core.lote import _limpar_repeticao_tecnicas_lemov_ia
    metodologia = [
        {
            "titulo": "Para comecar",
            "texto": "Iniciar a aula aplicando a tecnica Virem e conversem, perguntando aos estudantes sobre o tema."
        },
        {
            "titulo": "Foco no conteudo",
            "texto": "Utilizar a tecnica Todo mundo escreve para garantir o registro individual."
        },
        {
            "titulo": "Na pratica",
            "texto": "Orientar a atividade incorporando a tecnica de 'Hora da leitura' de forma contextualizada."
        }
    ]
    limpa = _limpar_repeticao_tecnicas_lemov_ia(metodologia)

    assert "a tecnica Virem e conversem" not in limpa[0]["texto"]
    assert "o Virem e conversem" in limpa[0]["texto"]

    assert "a tecnica Todo mundo escreve" not in limpa[1]["texto"]
    assert "o Todo mundo escreve" in limpa[1]["texto"]

    assert "tecnica de 'Hora da leitura'" not in limpa[2]["texto"]
    assert "Hora da leitura" in limpa[2]["texto"]

