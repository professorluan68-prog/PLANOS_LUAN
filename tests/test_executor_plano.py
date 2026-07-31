import pytest

from core.executor_plano import processar_lote_pdfs


def test_processar_lote_pdfs_divide_metodologia_quando_necessario():
    def _gerar_aula(caminho, idx, total, dividir):
        return {
            "tema": f"Tema {idx + 1}",
            "metodologia": [{"titulo": "Etapa", "texto": f"Texto {caminho}"}],
        }

    aulas = processar_lote_pdfs(
        ["AULA_1.pdf", "AULA_2.pdf"],
        gerar_aula_callback=_gerar_aula,
        dividir_metodologia=True,
        dividir_por_pdf=[False, True],
        texto_metodologia_fn=lambda metodologia: metodologia[0]["texto"],
        dividir_texto_fn=lambda texto: (texto + " parte 1", texto + " parte 2"),
        metodologia_por_texto_fn=lambda texto: [{"titulo": "Etapa", "texto": texto}],
    )

    assert len(aulas) == 3
    assert aulas[1]["tema"] == "Tema 2"
    assert aulas[2]["tema"] == "Tema 2 - continuidade"


def test_checkpoint_restaura_somente_itens_do_mesmo_conteudo_e_contexto(tmp_path):
    caminhos = [tmp_path / "aula_1.pdf", tmp_path / "aula_2.pdf"]
    for idx, caminho in enumerate(caminhos, start=1):
        caminho.write_bytes(f"pdf-{idx}".encode())

    chamadas_primeira_execucao = []

    def _falhar_na_segunda(caminho, idx, total, dividir):
        chamadas_primeira_execucao.append(idx)
        if idx == 1:
            raise RuntimeError("falha simulada")
        return {"tema": f"Tema {idx}", "metodologia": []}

    with pytest.raises(RuntimeError, match="falha simulada"):
        processar_lote_pdfs(
            [str(caminho) for caminho in caminhos],
            gerar_aula_callback=_falhar_na_segunda,
            checkpoint_contexto={"turma": "7º A", "bimestre": "3"},
            checkpoint_dir=tmp_path / "checkpoints",
        )

    chamadas_retomada = []
    restauradas = []

    def _retomar(caminho, idx, total, dividir):
        chamadas_retomada.append(idx)
        return {"tema": f"Tema {idx}", "metodologia": []}

    aulas = processar_lote_pdfs(
        [str(caminho) for caminho in caminhos],
        gerar_aula_callback=_retomar,
        checkpoint_contexto={"turma": "7º A", "bimestre": "3"},
        checkpoint_dir=tmp_path / "checkpoints",
        aula_restaurada_callback=lambda aula: restauradas.append(aula["tema"]),
    )

    assert chamadas_primeira_execucao == [0, 1]
    assert chamadas_retomada == [1]
    assert restauradas == ["Tema 0"]
    assert [aula["tema"] for aula in aulas] == ["Tema 0", "Tema 1"]
    assert not list((tmp_path / "checkpoints").glob("*.json"))
    assert not list((tmp_path / "checkpoints").glob("*.tmp"))


def test_checkpoint_nao_reutiliza_resultado_quando_conteudo_muda(tmp_path):
    caminhos = [tmp_path / "aula_1.pdf", tmp_path / "aula_2.pdf"]
    caminhos[0].write_bytes(b"versao-antiga")
    caminhos[1].write_bytes(b"segunda-aula")

    def _falhar(caminho, idx, total, dividir):
        if idx == 1:
            raise RuntimeError("interromper")
        return {"tema": "Resultado antigo", "metodologia": []}

    with pytest.raises(RuntimeError):
        processar_lote_pdfs(
            [str(caminho) for caminho in caminhos],
            gerar_aula_callback=_falhar,
            checkpoint_contexto={"turma": "8º A"},
            checkpoint_dir=tmp_path / "checkpoints",
        )

    caminhos[0].write_bytes(b"versao-nova")
    chamadas = []

    def _gerar_novamente(caminho, idx, total, dividir):
        chamadas.append(idx)
        return {"tema": f"Novo {idx}", "metodologia": []}

    aulas = processar_lote_pdfs(
        [str(caminho) for caminho in caminhos],
        gerar_aula_callback=_gerar_novamente,
        checkpoint_contexto={"turma": "8º A"},
        checkpoint_dir=tmp_path / "checkpoints",
    )

    assert chamadas == [0, 1]
    assert [aula["tema"] for aula in aulas] == ["Novo 0", "Novo 1"]


def test_checkpoint_nao_reutiliza_resultado_de_outro_contexto(tmp_path):
    caminhos = [tmp_path / "aula_1.pdf", tmp_path / "aula_2.pdf"]
    for caminho in caminhos:
        caminho.write_bytes(b"conteudo")

    def _falhar(caminho, idx, total, dividir):
        if idx == 1:
            raise RuntimeError("interromper")
        return {"tema": "Contexto A", "metodologia": []}

    with pytest.raises(RuntimeError):
        processar_lote_pdfs(
            [str(caminho) for caminho in caminhos],
            gerar_aula_callback=_falhar,
            checkpoint_contexto={"turma": "7º A"},
            checkpoint_dir=tmp_path / "checkpoints",
        )

    chamadas = []

    def _gerar_contexto_b(caminho, idx, total, dividir):
        chamadas.append(idx)
        return {"tema": f"Contexto B {idx}", "metodologia": []}

    processar_lote_pdfs(
        [str(caminho) for caminho in caminhos],
        gerar_aula_callback=_gerar_contexto_b,
        checkpoint_contexto={"turma": "9º B"},
        checkpoint_dir=tmp_path / "checkpoints",
    )

    assert chamadas == [0, 1]


def test_checkpoint_reconhece_o_mesmo_upload_em_novo_diretorio_temporario(tmp_path):
    def _criar_upload(token, nome, conteudo):
        diretorio = tmp_path / f"planos_luan_upload_{token}"
        diretorio.mkdir()
        caminho = diretorio / f"planos_luan_upload_{token}__{nome}"
        caminho.write_bytes(conteudo)
        return caminho

    caminhos_primeira_execucao = [
        _criar_upload("aaa", "AULA_1.pdf", b"primeira"),
        _criar_upload("bbb", "AULA_2.pdf", b"segunda"),
    ]

    def _falhar(caminho, idx, total, dividir):
        if idx == 1:
            raise RuntimeError("interromper")
        return {"tema": "Restaurável", "metodologia": []}

    with pytest.raises(RuntimeError):
        processar_lote_pdfs(
            [str(caminho) for caminho in caminhos_primeira_execucao],
            gerar_aula_callback=_falhar,
            checkpoint_contexto={"turma": "7º A"},
            checkpoint_dir=tmp_path / "checkpoints",
        )

    caminhos_reenvio = [
        _criar_upload("ccc", "AULA_1.pdf", b"primeira"),
        _criar_upload("ddd", "AULA_2.pdf", b"segunda"),
    ]
    chamadas = []

    def _retomar(caminho, idx, total, dividir):
        chamadas.append(idx)
        return {"tema": "Novo", "metodologia": []}

    aulas = processar_lote_pdfs(
        [str(caminho) for caminho in caminhos_reenvio],
        gerar_aula_callback=_retomar,
        checkpoint_contexto={"turma": "7º A"},
        checkpoint_dir=tmp_path / "checkpoints",
    )

    assert chamadas == [1]
    assert [aula["tema"] for aula in aulas] == ["Restaurável", "Novo"]
