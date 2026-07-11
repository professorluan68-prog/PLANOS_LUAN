from core import lote


TEXTO_ORIENTACAO_ETAPAS = """
MISSAO 11 - Um mergulho no cordel
Etapa 1
Leitura inicial do cordel e identificacao de tema, ritmo e linguagem.
Registro no caderno das primeiras impressões.

Etapa 2
Analise guiada das estrofes com foco em rimas, vocabulario e sentido.
Discussao coletiva com retomada no quadro.

Etapa 3
Atividade de interpretacao e comparacao entre trechos.
Organizacao de respostas com justificativa.

Etapa final
Sintese final com socializacao das estrategias de leitura e revisao dos pontos principais.
"""

TEXTO_ORIENTACAO_ETAPAS_LINHA_QUEBRADA = """
MISSAO 11 - Um mergulho no cordel
1
ETAPA
Leitura inicial do cordel e identificacao de tema, ritmo e linguagem.

2
ETAPA
Analise guiada das estrofes com foco em rimas, vocabulario e sentido.

3
ETAPA
Atividade de interpretacao e comparacao entre trechos.

ETAPA FINAL
Sintese final com socializacao das estrategias de leitura e revisao dos pontos principais.
"""

TEXTO_ORIENTACAO_ETAPAS_VARIANTES = """
MISSAO 11 - Um mergulho no cordel
1ª ETAPA
Leitura orientada com grifo de palavras-chave.

ETAPA II
Interpretacao com comparacao entre estrofes.

ETAPA 03
Registro no caderno com justificativas.

ETAPA FINAL
Sintese e autoavaliacao das estrategias usadas.
"""

TEXTO_ORIENTACAO_FALSO_POSITIVO = """
Atividades:
1: LP5LERE01 | N2.3 | Fácil
2: LP5LERE02 | N1.1 | Fácil
Nestas etapas seguintes, o estudante deve revisar o caderno.
"""


def test_extrai_etapas_orientacao_estudos():
    etapas = lote._extrair_etapas_orientacao_estudos(TEXTO_ORIENTACAO_ETAPAS)

    assert len(etapas) == 4
    assert etapas[0]["titulo"] == "Etapa 1"
    assert etapas[1]["titulo"] == "Etapa 2"
    assert etapas[2]["titulo"] == "Etapa 3"
    assert etapas[3]["titulo"] == "Etapa final"
    assert "rimas" in etapas[1]["texto"].lower()

def test_extrai_etapas_orientacao_estudos_quando_numero_vem_em_linha_separada():
    etapas = lote._extrair_etapas_orientacao_estudos(TEXTO_ORIENTACAO_ETAPAS_LINHA_QUEBRADA)
    titulos = [e["titulo"] for e in etapas]
    assert titulos == ["Etapa 1", "Etapa 2", "Etapa 3", "Etapa final"]

def test_extrai_etapas_orientacao_estudos_com_variacoes():
    etapas = lote._extrair_etapas_orientacao_estudos(TEXTO_ORIENTACAO_ETAPAS_VARIANTES)
    assert [e["titulo"] for e in etapas] == ["Etapa 1", "Etapa 2", "Etapa 3", "Etapa final"]


def test_parser_nao_confunde_codigos_lp_com_etapas():
    etapas = lote._extrair_etapas_orientacao_estudos(TEXTO_ORIENTACAO_FALSO_POSITIVO)
    assert etapas == []


def test_aula_por_pdf_orientacao_usa_etapa_por_indice(monkeypatch):
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: TEXTO_ORIENTACAO_ETAPAS)

    aula_1 = lote._aula_por_pdf(
        "MISSAO11.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=0,
        total_aulas=4,
    )
    aula_2 = lote._aula_por_pdf(
        "MISSAO11.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=1,
        total_aulas=4,
    )

    assert aula_1["tema"] == "MISSAO 11 - Um mergulho no cordel - ETAPA 1"
    assert aula_2["tema"] == "MISSAO 11 - Um mergulho no cordel - ETAPA 2"
    assert aula_1["material"] == "Etapa 1"
    assert aula_2["material"] == "Etapa 2"
    assert "cordel" in aula_1["aprendizagem"].lower()

    texto_1 = " ".join(item.get("texto", "") for item in aula_1["metodologia"] if isinstance(item, dict)).lower()
    texto_2 = " ".join(item.get("texto", "") for item in aula_2["metodologia"] if isinstance(item, dict)).lower()

    print("DEBUG METODOLOGIA:", aula_1["metodologia"])
    assert "cordel" in texto_1
    assert texto_1 != texto_2


def test_aula_por_pdf_orientacao_reaproveita_ultima_etapa_quando_sobra_aula(monkeypatch):
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: TEXTO_ORIENTACAO_ETAPAS)
    aula_5 = lote._aula_por_pdf(
        "MISSAO11.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=4,
        total_aulas=5,
    )
    assert aula_5["tema"] == "MISSAO 11 - Um mergulho no cordel - ETAPA FINAL"


def test_orientacao_estudos_usa_objetivos_da_missao_como_aprendizagem(monkeypatch):
    texto = """
MISSAO 10 - A voz da poesia
Etapa 2
Gente grande
Leia o poema e identifique quem fala no texto.
"""
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: texto)

    aula = lote._aula_por_pdf(
        "MISSAO10 - ETAPA 2.pdf",
        "Orientação de Estudos",
        "9º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=1,
        total_aulas=4,
    )

    aprendizagem = aula["aprendizagem"]

    assert "Compreender as características de um poema." in aprendizagem
    assert "Analisar as marcas linguísticas de poemas para inferir quem é o eu lírico e com quem ele dialoga." in aprendizagem
