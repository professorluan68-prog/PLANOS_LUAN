import csv
import json

from core.validacao_sidecars import exportar_relatorio_validacao_sidecars


def test_exportar_relatorio_validacao_sidecars_filtra_apenas_sidecar(tmp_path):
    sidecar = tmp_path / "AULA_1.json"
    sidecar.write_text(
        json.dumps(
            {
                "disciplina": "História",
                "tema": "Tema teste",
                "aprendizagem": "Aprendizagem teste",
                "metodologia": [
                    {"titulo": "Para começar", "texto": "Retomar ideias."},
                    {"titulo": "Na prática", "texto": "Resolver atividade."},
                    {"titulo": "Encerramento", "texto": "Socializar respostas."},
                ],
                "acompanhamento": [
                    "☑ Observar a participação.",
                    "☑ Verificar os registros.",
                    "☑ Conferir a socialização.",
                ],
                "acessibilidade": [
                    "☑ Oferecer leitura guiada.",
                    "☑ Destacar palavras-chave.",
                    "☑ Permitir resposta oral mediada.",
                ],
                "confidence_score": 95,
                "avisos_validacao": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "outro.json").write_text('{"qualquer": "coisa"}', encoding="utf-8")

    saida_csv = tmp_path / "relatorio.csv"
    total = exportar_relatorio_validacao_sidecars(tmp_path, saida_csv)

    assert total == 1
    with saida_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["tema"] == "Tema teste"
