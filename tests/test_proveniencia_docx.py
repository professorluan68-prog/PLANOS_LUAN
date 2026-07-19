from core.proveniencia_docx import resumir_proveniencia_docx


def test_resumir_proveniencia_docx_sucesso_integral():
    turmas = [
        {
            "turma": "6º A",
            "aulas": [
                {
                    "numero_aula": "1",
                    "tema": "Seres vivos",
                    "status_referencia_docx": "docx_literal",
                    "arquivo_referencia_docx": (
                        r"C:\materiais\METODOLOGIA_CIENCIAS_6_A.docx"
                    ),
                },
                {
                    "numero_aula": "2",
                    "tema": "Células",
                    "status_referencia_docx": "docx_literal",
                    "arquivo_referencia_docx": (
                        r"C:\materiais\METODOLOGIA_CIENCIAS_6_A.docx"
                    ),
                },
            ],
        }
    ]

    assert resumir_proveniencia_docx(turmas) == {
        "total_aulas": 2,
        "docx_literal": 2,
        "docx_refinado_ia": 0,
        "fallback": 0,
        "arquivos": ["METODOLOGIA_CIENCIAS_6_A.docx"],
        "falhas": [],
    }


def test_resumir_proveniencia_docx_resultado_misto():
    turmas = [
        {
            "turma": "6º A",
            "aulas": [
                {
                    "numero_aula": "1",
                    "tema": "Seres vivos",
                    "status_referencia_docx": "docx_literal",
                    "fonte_referencia_metodologia": (
                        r"C:\materiais\METODOLOGIA_CIENCIAS_6_A.docx"
                    ),
                },
                {
                    "numero_aula": "2",
                    "tema": "Células",
                    "status_referencia_docx": "aula_ausente_ou_incompleta",
                    "arquivo_referencia_docx": (
                        r"C:\materiais\METODOLOGIA_CIENCIAS_6_A.docx"
                    ),
                    "motivo_referencia_docx": "A aula 2 está incompleta no DOCX.",
                },
            ],
        },
        {
            "turma": "7º B",
            "aulas": [
                {
                    "numero_aula": "3",
                    "tema": "Energia",
                    "status_referencia_docx": "docx_refinado_ia",
                    "arquivo_referencia_docx": (
                        r"D:\referencias\METODOLOGIA_CIENCIAS_7_B.docx"
                    ),
                },
                {
                    "numero_aula": "4",
                    "tema": "Calor",
                    "status_referencia_docx": "docx_ausente",
                    "motivo_referencia_docx": "DOCX de referência não encontrado.",
                },
            ],
        },
    ]

    assert resumir_proveniencia_docx(turmas) == {
        "total_aulas": 4,
        "docx_literal": 1,
        "docx_refinado_ia": 1,
        "fallback": 2,
        "arquivos": [
            "METODOLOGIA_CIENCIAS_6_A.docx",
            "METODOLOGIA_CIENCIAS_7_B.docx",
        ],
        "falhas": [
            {
                "turma": "6º A",
                "numero_aula": "2",
                "tema": "Células",
                "status": "aula_ausente_ou_incompleta",
                "motivo": "A aula 2 está incompleta no DOCX.",
            },
            {
                "turma": "7º B",
                "numero_aula": "4",
                "tema": "Calor",
                "status": "docx_ausente",
                "motivo": "DOCX de referência não encontrado.",
            },
        ],
    }


def test_resumir_proveniencia_docx_entrada_vazia():
    assert resumir_proveniencia_docx([]) == {
        "total_aulas": 0,
        "docx_literal": 0,
        "docx_refinado_ia": 0,
        "fallback": 0,
        "arquivos": [],
        "falhas": [],
    }
