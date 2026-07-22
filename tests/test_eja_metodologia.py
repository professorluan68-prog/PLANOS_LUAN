from pathlib import Path

import core.lote as lote
from core.disciplinas import nomes_disciplinas
from core.eja.adaptador_eja import adaptar_metodologia_eja, perfil_suporta_eja
from core.ia import _montar_prompt


TEXTO_BIOLOGIA_EJA = """
Biologia
Metabolismo energetico: fotossintese
2o bimestre Ensino
Aula 1 Medio
Relembre
VIREM E CONVERSEM
Link para video
A reacao da fotossintese
Pause e responda
TODO MUNDO ESCREVE
Questao do ENEM
"""

NOMES_LEMOV = {
    "VIREM E CONVERSEM",
    "TODO MUNDO ESCREVE",
    "COM SUAS PALAVRAS",
    "HORA DA LEITURA",
    "DE OLHO NO MODELO",
    "UM PASSO DE CADA VEZ",
}


def test_biologia_eja_sem_ia_usa_blocos_e_linguagem_contextualizada(monkeypatch):
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: TEXTO_BIOLOGIA_EJA)

    aula = lote._aula_por_pdf(
        "aula_fotossintese.pdf",
        "Biologia",
        "EJA - 2 termo",
        "2o bimestre",
        usar_ia=False,
        provedor_ia="",
        modalidade_eja=True,
    )

    titulos = [item["titulo"] for item in aula["metodologia"]]
    texto = " ".join(item["texto"] for item in aula["metodologia"])

    assert titulos == ["Para comecar", "Foco no conteudo", "Pause e responda", "Encerramento"]
    assert "linguagem acessivel e adulta" in texto.lower()
    assert "trabalho" in texto.lower()
    assert "video indicado" in texto.lower()
    assert not any(nome in texto.upper() for nome in NOMES_LEMOV)


def test_ingles_eja_sem_ia_prioriza_uso_funcional(monkeypatch):
    monkeypatch.setattr(
        lote,
        "_extrair_texto_pdf",
        lambda caminho: "Ingles\nAt the restaurant\nLISTEN AND REPEAT\nWRITE AND SHARE\nDialogue practice\n",
    )

    aula = lote._aula_por_pdf(
        "aula_ingles.pdf",
        "Ingles",
        "EJA - 1 termo",
        "2o bimestre",
        usar_ia=False,
        provedor_ia="",
        modalidade_eja=True,
    )

    texto = " ".join(item["texto"] for item in aula["metodologia"]).lower()

    assert [item["titulo"] for item in aula["metodologia"]] == [
        "Para comecar",
        "Foco no conteudo",
        "Pause e responda",
        "Encerramento",
    ]
    assert "comunicacao no trabalho" in texto
    assert "situacoes reais" in texto


def test_lideranca_oratoria_eja_preserva_etapas_do_docx_e_contextualiza_trabalho():
    metodologia = [
        {"titulo": "Para começar", "texto": "Aplicar VIREM E CONVERSEM sobre negociação."},
        {"titulo": "Foco no conteúdo", "texto": "Apresentar os elementos da negociação."},
        {"titulo": "Na prática", "texto": "Analisar uma situação em grupo."},
        {"titulo": "Na prática", "texto": "Produzir um registro curto."},
        {"titulo": "Encerramento", "texto": "Retomar as conclusões."},
    ]

    resultado = adaptar_metodologia_eja(
        metodologia,
        "lideranca_oratoria",
        "fundamentos da negociacao",
        "Negociacao no ambiente profissional",
    )

    assert perfil_suporta_eja("lideranca_oratoria")
    assert [item["titulo"] for item in resultado].count("Na prática") == 2
    texto = " ".join(item["texto"] for item in resultado)
    assert "trabalho" in texto.lower()
    assert not any(nome in texto.upper() for nome in NOMES_LEMOV)


def test_prompt_ia_inclui_orientacao_eja_e_bloqueia_lemov():
    prompt = _montar_prompt(TEXTO_BIOLOGIA_EJA, "Biologia", "2 termo", modalidade_eja=True)

    assert "MODALIDADE EJA" in prompt
    assert "linguagem acessivel, adulta" in prompt
    assert "mundo do trabalho" in prompt
    assert "No EJA, nao cite tecnicas LEMOV" in prompt
    assert "cite o nome da tecnica em maiusculas" not in prompt


def test_apenas_tres_perfis_suportam_eja():
    assert perfil_suporta_eja("ingles")
    assert perfil_suporta_eja("biologia")
    assert perfil_suporta_eja("lideranca_oratoria")
    assert not perfil_suporta_eja("historia")


def test_lista_geral_nao_expoe_biologia_eja_como_disciplina_duplicada():
    assert "Biologia-EJA" not in nomes_disciplinas()


def test_interface_tem_aba_eja_sem_seletor_de_modalidade():
    app = Path(__file__).resolve().parents[1] / "planos_luan_app.py"
    texto = app.read_text(encoding="utf-8")

    assert '"CDP - Ciclo I", "EJA", "Cadastro"' in texto
    assert 'modo_eja = modo_tela == "EJA"' in texto
    assert 'st.selectbox("Modalidade", ["Regular", "EJA"]' not in texto
    assert '"Reescrita CDP"' not in texto


def test_prompt_cdp_com_ia_bloqueia_tecnicas_lemov_explicitas():
    prompt = _montar_prompt(
        "Tema: leitura e interpretacao",
        "Português",
        "MULTISSERIADO 1º, 2º e 3º ano",
        modalidade_eja=True,
        permitir_tecnicas_explicitamente=False,
    )

    assert "nao cite tecnicas LEMOV" in prompt
    assert "cite o nome da tecnica em maiusculas" not in prompt
