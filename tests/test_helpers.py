from core.helpers import arquivos_na_ordem_de_envio


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
