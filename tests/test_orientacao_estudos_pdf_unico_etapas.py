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

    assert aula_1["tema"] == "ETAPA 1"
    assert aula_2["tema"] == "ETAPA 2"
    assert aula_1["material"] == "ETAPA 1"
    assert aula_2["material"] == "ETAPA 2"
    assert "estratégias de leitura" in aula_1["aprendizagem"].lower()

    texto_1 = " ".join(item.get("texto", "") for item in aula_1["metodologia"] if isinstance(item, dict)).lower()
    texto_2 = " ".join(item.get("texto", "") for item in aula_2["metodologia"] if isinstance(item, dict)).lower()

    assert "leitura" in texto_1
    assert texto_1 != texto_2
