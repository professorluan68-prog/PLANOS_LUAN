from pathlib import Path

import pytest

from core.helpers import (
    arquivo_parece_id_seduc,
    arquivo_parece_referencia_nao_aula,
    arquivos_na_ordem_de_envio,
    filtrar_pdfs_para_aulas,
    garantir_caminho_na_raiz,
    listar_falhas_ia,
    montar_relatorio_geracao,
    numero_aula_pdf,
    ordenar_pdfs_por_numero,
    ordenar_pdfs_por_sequencia,
    resolver_pasta_pdfs,
    resumir_falhas_ia,
)


class _UploadFake:
    def __init__(self, name: str):
        self.name = name


def test_arquivos_na_ordem_de_envio_preserva_sequencia_personalizada():
    arquivos = [
        _UploadFake("AULA 17 - Histórias que a vida conta.pdf"),
        _UploadFake("AULA 6 - Do interesse de todos.pdf"),
        _UploadFake("AULA 23 - A linguagem literária.pdf"),
    ]

    ordenados = arquivos_na_ordem_de_envio(arquivos)

    assert [arquivo.name for arquivo in ordenados] == [
        "AULA 17 - Histórias que a vida conta.pdf",
        "AULA 6 - Do interesse de todos.pdf",
        "AULA 23 - A linguagem literária.pdf",
    ]


def test_numero_aula_pdf_extrai_numero_do_nome():
    assert numero_aula_pdf(Path("AULA_017.pdf")) == 17
    assert numero_aula_pdf(Path("1612757.pdf")) is None
    assert numero_aula_pdf(Path("material_sem_numero.pdf")) is None


def test_arquivo_parece_id_seduc_detecta_nome_numerico_longo():
    assert arquivo_parece_id_seduc(Path("1612757.pdf")) is True
    assert arquivo_parece_id_seduc(Path("AULA 1.pdf")) is False


def test_arquivo_parece_referencia_nao_aula_detecta_matriz():
    assert arquivo_parece_referencia_nao_aula(Path("Matriz_de_Referencia_de_Lingua_Portuguesa.pdf")) is True
    assert arquivo_parece_referencia_nao_aula(Path("Missao_11_Um_mergulho_no_cordel-1-3.pdf")) is False


def test_filtrar_pdfs_para_aulas_prioriza_arquivos_legiveis():
    arquivos = [Path("1612757.pdf"), Path("AULA 2.pdf"), Path("AULA 1.pdf")]

    filtrados = filtrar_pdfs_para_aulas(arquivos)

    assert [arquivo.name for arquivo in filtrados] == ["AULA 2.pdf", "AULA 1.pdf"]


def test_filtrar_pdfs_para_aulas_remove_matriz_de_referencia():
    arquivos = [
        Path("Matriz_de_Referencia_de_Lingua_Portuguesa.pdf"),
        Path("Missao_11_Um_mergulho_no_cordel-1-3.pdf"),
        Path("Missao_11_Um_mergulho_no_cordel-4-5.pdf"),
    ]

    filtrados = filtrar_pdfs_para_aulas(arquivos)

    assert [arquivo.name for arquivo in filtrados] == [
        "Missao_11_Um_mergulho_no_cordel-1-3.pdf",
        "Missao_11_Um_mergulho_no_cordel-4-5.pdf",
    ]


def test_ordenar_pdfs_por_numero_usa_ordem_natural():
    arquivos = [Path("AULA_10.pdf"), Path("AULA_02.pdf"), Path("AULA_01.pdf")]

    ordenados = ordenar_pdfs_por_numero(arquivos)

    assert [arquivo.name for arquivo in ordenados] == ["AULA_01.pdf", "AULA_02.pdf", "AULA_10.pdf"]


def test_ordenar_pdfs_por_numero_usa_sufixo_real_do_primeiro_ano_em():
    arquivos = [
        Path("Anúncios publicitários em mídias digitais – Parte 1_07.pdf"),
        Path("A literatura medieval portuguesa e suas influências_01.pdf"),
        Path("Versos medievais em ritmos atuais_03.pdf"),
        Path("As origens do Trovadorismo_02.pdf"),
        Path("O Classicismo e Os lusíadas_05.pdf"),
        Path("Gil Vicente e o Auto da Barca do Inferno_04.pdf"),
    ]

    ordenados = ordenar_pdfs_por_numero(arquivos)

    assert [arquivo.name for arquivo in ordenados] == [
        "A literatura medieval portuguesa e suas influências_01.pdf",
        "As origens do Trovadorismo_02.pdf",
        "Versos medievais em ritmos atuais_03.pdf",
        "Gil Vicente e o Auto da Barca do Inferno_04.pdf",
        "O Classicismo e Os lusíadas_05.pdf",
        "Anúncios publicitários em mídias digitais – Parte 1_07.pdf",
    ]


def test_ordenar_pdfs_por_sequencia_prioriza_ae():
    arquivos = [Path("AULA_01.pdf"), Path("AULA_06.pdf"), Path("AULA_17.pdf"), Path("AULA_19.pdf")]

    ordenados = ordenar_pdfs_por_sequencia(arquivos, [17, 19, 6], limite=3)

    assert [arquivo.name for arquivo in ordenados] == ["AULA_17.pdf", "AULA_19.pdf", "AULA_06.pdf"]


def test_resolver_pasta_pdfs_usa_alias_portugues_em():
    caminho = resolver_pasta_pdfs(r"D:\PDF novos", "Portugues", "2 ano C", "2 Bimestre")

    assert caminho == Path(r"D:\PDF novos") / "LINGUA_PORTUGUESA" / "EM" / "2_BIMESTRE" / "2_ANO"


def test_resolver_pasta_pdfs_encontra_subpasta_cdp_em_para_turma_multisseriada(tmp_path):
    cdp = tmp_path / "GEOGRAFIA" / "EM" / "3_BIMESTRE" / "CDP_EM"
    cdp.mkdir(parents=True)
    (cdp / "01 - ATIVIDADE 1 - Mapa.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "Geografia",
        "1º/2º/3º E.M",
        "3º Bimestre",
    )

    assert caminho == cdp


def test_resolver_pasta_pdfs_encontra_cdp_ef_com_hifen_e_subpasta_de_turma(tmp_path):
    cdp = tmp_path / "HISTORIA" / "AF" / "3_BIMESTRE" / "CDP-EF" / "6_ANO_7_ANO"
    cdp.mkdir(parents=True)
    (cdp / "01 - ATIVIDADE 1 - Historia.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "História",
        "6º/7º E.F",
        "3º Bimestre",
    )

    assert caminho == cdp


def test_garantir_caminho_na_raiz_aceita_subpasta(tmp_path):
    raiz = tmp_path / "PDF_AULAS"
    subpasta = raiz / "HISTORIA" / "AF" / "1_BIMESTRE" / "6_ANO"
    subpasta.mkdir(parents=True)

    assert garantir_caminho_na_raiz(subpasta, raiz) == subpasta.resolve()


def test_garantir_caminho_na_raiz_rejeita_caminho_externo(tmp_path):
    raiz = tmp_path / "PDF_AULAS"
    externo = tmp_path / "instalacao_antiga" / "PDF_AULAS"
    raiz.mkdir()
    externo.mkdir(parents=True)

    with pytest.raises(ValueError, match="fora da raiz autorizada"):
        garantir_caminho_na_raiz(externo, raiz)


def test_garantir_caminho_na_raiz_rejeita_travessia(tmp_path):
    raiz = tmp_path / "PDF_AULAS"
    raiz.mkdir()

    with pytest.raises(ValueError, match="fora da raiz autorizada"):
        garantir_caminho_na_raiz(raiz / ".." / "pasta_antiga", raiz)


def test_resolver_pasta_pdfs_silvana_2ano_a_usa_aprofundamento_biologia(tmp_path):
    pasta_aprofundamento = tmp_path / "APROFUNDAMENTO_EM_BIOLOGIA" / "EM" / "3_BIMESTRE" / "2_ANO_A"
    pasta_biologia = tmp_path / "BIOLOGIA" / "EM" / "3_BIMESTRE" / "2_ANO"
    pasta_aprofundamento.mkdir(parents=True)
    pasta_biologia.mkdir(parents=True)
    (pasta_aprofundamento / "AULA_01.pdf").write_bytes(b"%PDF-1.4\n")
    (pasta_biologia / "AULA_01.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "Aprof. em Biologia",
        "2º ANO A",
        "3º Bimestre",
        professor="Silvana Mariano",
    )

    assert caminho == pasta_aprofundamento


def test_resolver_pasta_pdfs_biologia_2ano_b_continua_pasta_normal(tmp_path):
    pasta_biologia = tmp_path / "BIOLOGIA" / "EM" / "3_BIMESTRE" / "2_ANO"
    pasta_biologia.mkdir(parents=True)
    (pasta_biologia / "AULA_01.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "Biologia",
        "2º ANO B",
        "3º Bimestre",
        professor="Silvana Mariano",
    )

    assert caminho == pasta_biologia


def test_resolver_pasta_pdfs_usa_alias_aprofundamento_geografia(tmp_path):
    pasta = tmp_path / "APROFUNDAMENTO_EM_GEOGRAFIA" / "EM" / "3_BIMESTRE" / "3_ANO"
    pasta.mkdir(parents=True)
    (pasta / "AULA_01.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "Aprof. em Geografia",
        "3º ANO A",
        "3º Bimestre",
    )

    assert caminho == pasta


def test_resolver_pasta_pdfs_usa_alias_lideranca_oratoria(tmp_path):
    pasta = tmp_path / "LIDERANCA_E_ORATORIA" / "EM" / "3_BIMESTRE" / "2_ANO"
    pasta.mkdir(parents=True)
    (pasta / "AULA_01.pdf").write_bytes(b"%PDF-1.4\n")

    caminho = resolver_pasta_pdfs(
        str(tmp_path),
        "Liderança Oratória",
        "2º ANO A",
        "3º Bimestre",
    )

    assert caminho == pasta


def test_listar_falhas_ia_e_resumir_fallback_local():
    aulas = [
        {"tema": "Aula de abertura", "ia_usada": True, "ia_erro": ""},
        {
            "tema": "Recursos hidricos",
            "ia_usada": False,
            "ia_erro": "Falha na IA (gemini): 503 UNAVAILABLE. Usando motor heuristico local.",
        },
    ]

    falhas = listar_falhas_ia(aulas)
    resumo = resumir_falhas_ia(falhas)

    assert len(falhas) == 1
    assert "Aula 2 (Recursos hidricos)" in falhas[0]
    assert "503 UNAVAILABLE" in falhas[0]
    assert "motor local" in resumo
    assert "Recursos hidricos" in resumo


def test_listar_falhas_ia_ignora_aula_com_referencia_docx():
    aulas = [
        {
            "tema": "Informações em infográficos, gráficos, tabelas e esquemas",
            "ia_usada": False,
            "ia_erro": "",
            "origem_metodologia": "docx_referencia_orientacao_estudos",
        }
    ]

    assert listar_falhas_ia(aulas) == []


def test_relatorio_geracao_inclui_observacao_ia_quando_houver_fallback():
    relatorio = montar_relatorio_geracao(
        [
            {
                "tema": "Recursos hidricos",
                "data": "12/06",
                "horario": "10h\n10h50",
                "ia_usada": False,
                "ia_erro": "Falha na IA (openai): timeout. Usando motor heuristico local.",
            }
        ],
        disciplina="Ciencias",
        turma="8 ANO B",
        bimestre="3 Bimestre",
        mes="JUNHO",
    )

    assert "Observacao IA: Falha na IA (openai): timeout. Usando motor heuristico local." in relatorio
