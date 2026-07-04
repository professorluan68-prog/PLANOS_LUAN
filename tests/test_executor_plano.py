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
