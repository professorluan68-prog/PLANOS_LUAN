from core.lote import _eh_producao_final_redacao, _metodologia_em_blocos_por_texto
from core.divisor_metodologia import processar_pdf_e_dividir_metodologia
from core.prompts_por_disciplina import get_orientacao_disciplina, get_system_prompt


def test_pratica_de_linguagem_leitura_nao_ativa_fluxo_de_producao_final():
    texto = "AULA 9 Prática de linguagem: Leitura"
    tema = "Prática de linguagem: Leitura"

    assert _eh_producao_final_redacao(texto, tema) is False


def test_divisao_de_metodologia_preserva_blocos_de_redacao_leitura():
    metodologia = (
        "Disparo inicial / contextualizacao:\nApresentar a aula e o objetivo pedagogico.\n\n"
        "Leitura ou exploracao inicial:\nOrientar a leitura do trecho.\n\n"
        "Analise guiada:\nConduzir perguntas de interpretacao.\n\n"
        "Sistematizacao:\nRegistrar os pontos principais.\n\n"
        "Producao textual:\nSolicitar uma escrita breve.\n\n"
        "Revisao e fechamento:\nRevisar e socializar a producao."
    )

    parte1, parte2 = processar_pdf_e_dividir_metodologia(metodologia)
    blocos_1 = _metodologia_em_blocos_por_texto(parte1)
    blocos_2 = _metodologia_em_blocos_por_texto(parte2)

    assert [bloco["titulo"] for bloco in blocos_1] == [
        "Disparo inicial / contextualizacao",
        "Leitura ou exploracao inicial",
        "Analise guiada",
        "Sistematizacao",
        "Encerramento",
    ]
    assert [bloco["titulo"] for bloco in blocos_2] == [
        "Para comecar",
        "Producao textual",
        "Revisao e fechamento",
    ]


def test_redacao_leitura_recebe_prompt_especifico_e_flexivel():
    prompt_sistema = get_system_prompt("Redacao e Leitura", "6o ano A")
    orientacao = get_orientacao_disciplina("Redacao e Leitura", turma="6o ano A")

    assert "Redacao e Leitura" in prompt_sistema
    assert "ordem e o produto real" in orientacao
