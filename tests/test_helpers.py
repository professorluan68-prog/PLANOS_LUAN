from pathlib import Path

from core.helpers import (
    arquivos_na_ordem_de_envio,
    numero_aula_pdf,
    ordenar_pdfs_por_numero,
    ordenar_pdfs_por_sequencia,
    resolver_pasta_pdfs,
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
    assert numero_aula_pdf(Path("material_sem_numero.pdf")) is None


def test_ordenar_pdfs_por_numero_usa_ordem_natural():
    arquivos = [Path("AULA_10.pdf"), Path("AULA_02.pdf"), Path("AULA_01.pdf")]

    ordenados = ordenar_pdfs_por_numero(arquivos)

    assert [arquivo.name for arquivo in ordenados] == ["AULA_01.pdf", "AULA_02.pdf", "AULA_10.pdf"]


def test_ordenar_pdfs_por_sequencia_prioriza_ae():
    arquivos = [Path("AULA_01.pdf"), Path("AULA_06.pdf"), Path("AULA_17.pdf"), Path("AULA_19.pdf")]

    ordenados = ordenar_pdfs_por_sequencia(arquivos, [17, 19, 6], limite=3)

    assert [arquivo.name for arquivo in ordenados] == ["AULA_17.pdf", "AULA_19.pdf", "AULA_06.pdf"]


def test_resolver_pasta_pdfs_usa_alias_portugues_em():
    caminho = resolver_pasta_pdfs(r"D:\PDF novos", "Portugues", "2 ano C", "2 Bimestre")

    assert caminho == Path(r"D:\PDF novos") / "LINGUA_PORTUGUESA" / "EM" / "2_BIMESTRE" / "2_ANO"
