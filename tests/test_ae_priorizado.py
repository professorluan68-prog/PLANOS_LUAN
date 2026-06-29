from core import ae_priorizado
import pandas as pd


def test_contexto_ae_priorizado_so_ativa_para_portugues_em_segundo_bimestre(monkeypatch):
    class DummyPath:
        def exists(self):
            return True

    monkeypatch.setattr(ae_priorizado, "AE_PRIORIZADO_JSON_PATH", DummyPath())

    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "1ª Série A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "1ª Série A", "1º Bimestre") is False
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Filosofia", "1ª Série A", "2º Bimestre") is False



def test_contexto_ae_priorizado_tambem_cobre_turmas_reais_de_segundo_e_terceiro_ano(monkeypatch):
    class DummyPath:
        def exists(self):
            return True

    monkeypatch.setattr(ae_priorizado, "AE_PRIORIZADO_JSON_PATH", DummyPath())

    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "2º ANO B", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "3º ANO C", "2º Bimestre") is True


def test_contexto_ae_priorizado_cobre_novas_disciplinas():
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Biologia", "1º ANO A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Biologia", "2º ANO A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Arte", "1º ANO A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Arte", "6º ANO A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Arte", "9º ANO A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Arte", "5º ANO A", "2º Bimestre") is False


def test_aplica_ae_priorizado_quando_encontra_correspondencia(monkeypatch):
    monkeypatch.setattr(ae_priorizado, "contexto_ae_priorizado_disponivel", lambda disciplina, turma, bimestre: True)
    monkeypatch.setattr(
        ae_priorizado,
        "_indice_por_chave",
        lambda: {
            "portugues_em|2|1a_serie|17": {
                "usar_ae": "AE1 - Texto do AE",
                "ae_codigos": "AE1",
            }
        },
    )

    aulas = [
        {
            "tema": "Tema teste",
            "material": "AULA 17 - Tema teste",
            "numero_aula": "17",
            "aprendizagem": "Habilidade: EM13LP48 texto original",
        }
    ]

    ajustadas, avisos = ae_priorizado.aplicar_ae_priorizado_nas_aulas(
        aulas,
        disciplina="Língua Portuguesa",
        turma="1ª Série A",
        bimestre="2º Bimestre",
    )

    assert avisos == []
    assert ajustadas[0]["aprendizagem"] == "AE1 - Texto do AE"
    assert ajustadas[0]["aprendizagem_original"] == "Habilidade: EM13LP48 texto original"
    assert ajustadas[0]["ae_priorizado_aplicado"] is True
    assert ajustadas[0]["ae_priorizado_codigo"] == "AE1"


def test_mantem_habilidade_normal_quando_nao_encontra_ae(monkeypatch):
    monkeypatch.setattr(ae_priorizado, "contexto_ae_priorizado_disponivel", lambda disciplina, turma, bimestre: True)
    monkeypatch.setattr(ae_priorizado, "_indice_por_chave", lambda: {})
    monkeypatch.setattr(ae_priorizado, "_ordem_por_chave", lambda: {})

    aulas = [
        {
            "tema": "Tema teste",
            "material": "AULA 18 - Tema teste",
            "numero_aula": "18",
            "aprendizagem": "Habilidade: EM13LP08 texto original",
        }
    ]

    ajustadas, avisos = ae_priorizado.aplicar_ae_priorizado_nas_aulas(
        aulas,
        disciplina="Língua Portuguesa",
        turma="1ª Série A",
        bimestre="2º Bimestre",
    )

    assert ajustadas[0]["aprendizagem"] == "Habilidade: EM13LP08 texto original"
    assert ajustadas[0]["ae_priorizado_aplicado"] is False
    assert len(avisos) == 1
    assert "18" in avisos[0]


def test_reordena_aulas_pela_ordem_do_guia_priorizado(monkeypatch):
    monkeypatch.setattr(ae_priorizado, "contexto_ae_priorizado_disponivel", lambda disciplina, turma, bimestre: True)
    monkeypatch.setattr(
        ae_priorizado,
        "_indice_por_chave",
        lambda: {
            "portugues_em|2|1a_serie|17": {"usar_ae": "AE1 - Texto do AE 17", "ae_codigos": "AE1"},
            "portugues_em|2|1a_serie|6": {"usar_ae": "AE2 - Texto do AE 6", "ae_codigos": "AE2"},
        },
    )
    monkeypatch.setattr(
        ae_priorizado,
        "_ordem_por_chave",
        lambda: {
            "portugues_em|2|1a_serie|17": 0,
            "portugues_em|2|1a_serie|6": 1,
        },
    )

    aulas = [
        {
            "tema": "Tema teste 6",
            "material": "AULA 6 - Tema teste",
            "numero_aula": "6",
            "aprendizagem": "Habilidade: EM13LP08 texto original",
        },
        {
            "tema": "Tema teste 17",
            "material": "AULA 17 - Tema teste",
            "numero_aula": "17",
            "aprendizagem": "Habilidade: EM13LP48 texto original",
        },
    ]

    ajustadas, avisos = ae_priorizado.aplicar_ae_priorizado_nas_aulas(
        aulas,
        disciplina="Língua Portuguesa",
        turma="1ª Série A",
        bimestre="2º Bimestre",
    )

    assert avisos == []
    assert [aula["material"] for aula in ajustadas] == [
        "AULA 17 - Tema teste",
        "AULA 6 - Tema teste",
    ]
    assert ajustadas[0]["aprendizagem"] == "AE1 - Texto do AE 17"
    assert ajustadas[1]["aprendizagem"] == "AE2 - Texto do AE 6"


def test_sequencia_aulas_ae_priorizado_mostra_a_ordem_esperada_dos_pdfs(monkeypatch):
    monkeypatch.setattr(ae_priorizado, "contexto_ae_priorizado_disponivel", lambda disciplina, turma, bimestre: True)
    monkeypatch.setattr(
        ae_priorizado,
        "carregar_base_ae_priorizado",
        lambda: {
            "mapa_por_aula": [
                {"chave_lookup": "portugues_em|2|1a_serie|17", "aula_numero": 17},
                {"chave_lookup": "portugues_em|2|1a_serie|19", "aula_numero": 19},
                {"chave_lookup": "portugues_em|2|1a_serie|20", "aula_numero": 20},
                {"chave_lookup": "portugues_em|2|2a_serie|5", "aula_numero": 5},
                {"chave_lookup": "portugues_em|2|1a_serie|6", "aula_numero": 6},
            ]
        },
    )

    sequencia = ae_priorizado.sequencia_aulas_ae_priorizado(
        disciplina="LÃ­ngua Portuguesa",
        turma="1Âª SÃ©rie A",
        bimestre="2Âº Bimestre",
        limite=4,
    )

    assert sequencia == [17, 19, 20, 6]


def test_base_real_ae_priorizado_traz_sequencia_para_segundo_e_terceiro_ano():
    sequencia_segundo = ae_priorizado.sequencia_aulas_ae_priorizado(
        disciplina="Língua Portuguesa",
        turma="2º ANO B",
        bimestre="2º Bimestre",
        limite=5,
    )
    sequencia_terceiro = ae_priorizado.sequencia_aulas_ae_priorizado(
        disciplina="Língua Portuguesa",
        turma="3º ANO A",
        bimestre="2º Bimestre",
        limite=5,
    )

    assert sequencia_segundo == [5, 6, 10, 12, 9]
    assert sequencia_terceiro == [12, 13, 14, 15, 16]


def test_base_real_ae_priorizado_traz_sequencia_para_arte_e_biologia():
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Biologia", "1º ANO A", "2º Bimestre", limite=5) == [1, 2, 3, 6, 7]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Biologia", "2º ANO A", "2º Bimestre", limite=5) == [1, 2, 6, 7, 8]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Arte", "1º ANO A", "2º Bimestre", limite=5) == [1, 5, 7, 10, 12]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Arte", "6º ANO A", "2º Bimestre", limite=5) == [1, 2, 3, 4, 14]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Arte", "9º ANO A", "2º Bimestre", limite=5) == [1, 2, 3, 4, 5]


def test_contexto_ae_priorizado_cobre_lote_af_e_em_2b():
    casos_ativos = [
        ("Ciências", "6º ANO A"),
        ("Geografia", "7º ANO A"),
        ("Geografia", "1º ANO A"),
        ("História", "8º ANO A"),
        ("Língua Inglesa", "1º ANO A"),
        ("Matemática", "9º ANO A"),
        ("Matemática", "1º ANO A"),
        ("Língua Portuguesa", "6º ANO A"),
        ("Química", "2º ANO A"),
        ("Sociologia", "2º ANO A"),
    ]



    for disciplina, turma in casos_ativos:
        assert ae_priorizado.contexto_ae_priorizado_disponivel(disciplina, turma, "2º Bimestre") is True


def test_base_real_ae_priorizado_traz_sequencia_para_lote_novo():
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Ciências", "6º ANO A", "2º Bimestre", limite=4) == [1, 2, 3, 4]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Geografia", "6º ANO A", "2º Bimestre", limite=4) == [1, 2, 3, 4]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("História", "6º ANO A", "2º Bimestre", limite=4) == [1, 2, 3, 4]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Língua Inglesa", "1º ANO A", "2º Bimestre", limite=4) == [1, 3, 5, 7]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Matemática", "6º ANO A", "2º Bimestre", limite=4) == [3, 5, 6, 9]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Química", "1º ANO A", "2º Bimestre", limite=4) == [1, 2, 3, 4]
    assert ae_priorizado.sequencia_aulas_ae_priorizado("Sociologia", "2º ANO A", "2º Bimestre", limite=4) == [1, 2, 3, 4]


def test_base_real_ae_priorizado_consolidou_duplicatas_matematica():
    aulas = [{"material": "AULA 23", "numero_aula": 23, "aprendizagem": "Habilidade original"}]

    ajustadas, avisos = ae_priorizado.aplicar_ae_priorizado_nas_aulas(
        aulas,
        disciplina="Matemática",
        turma="6º ANO A",
        bimestre="2º Bimestre",
    )

    assert avisos == []
    assert ajustadas[0]["ae_priorizado_aplicado"] is True
    assert " | " in ajustadas[0]["aprendizagem"]


def test_contexto_ae_priorizado_tambem_pode_vir_de_planilha_local(tmp_path):
    caminho_planilha = tmp_path / "GUIA_9_ANO_3_BIMESTRE.xlsx"
    pd.DataFrame(
        [
            {
                "AULA": 1,
                "TÍTULO": "Aula 1",
                "Habilidades": "EF89LP32",
                "Aprendizagem Essencial": "AE3 - Texto do AE 1",
            },
            {
                "AULA": 2,
                "TÍTULO": "Aula 2",
                "Habilidades": "EF89LP37",
                "Aprendizagem Essencial": "AE4 - Texto do AE 2",
            },
        ]
    ).to_excel(caminho_planilha, index=False)

    assert (
        ae_priorizado.contexto_ae_priorizado_disponivel(
            "Língua Portuguesa",
            "9º ANO A",
            "3º Bimestre",
            caminho_planilha=str(caminho_planilha),
        )
        is True
    )
    assert ae_priorizado.sequencia_aulas_ae_priorizado(
        "Língua Portuguesa",
        "9º ANO A",
        "3º Bimestre",
        caminho_planilha=str(caminho_planilha),
    ) == [1, 2]


def test_aplica_ae_priorizado_a_partir_da_planilha_local(tmp_path):
    caminho_planilha = tmp_path / "GUIA_9_ANO_3_BIMESTRE.xlsx"
    pd.DataFrame(
        [
            {
                "AULA": 1,
                "TÍTULO": "Aula 1",
                "Habilidades": "EF89LP32",
                "Aprendizagem Essencial": "AE3 - Texto do AE 1",
            },
            {
                "AULA": 2,
                "TÍTULO": "Aula 2",
                "Habilidades": "EF89LP37",
                "Aprendizagem Essencial": "AE4 - Texto do AE 2",
            },
        ]
    ).to_excel(caminho_planilha, index=False)

    aulas = [
        {
            "tema": "Tema teste",
            "material": "AULA 2 - Tema teste",
            "numero_aula": "2",
            "aprendizagem": "Habilidade: EF89LP37 texto original",
        }
    ]

    ajustadas, avisos = ae_priorizado.aplicar_ae_priorizado_nas_aulas(
        aulas,
        disciplina="Língua Portuguesa",
        turma="9º ANO A",
        bimestre="3º Bimestre",
        caminho_planilha=str(caminho_planilha),
    )

    assert avisos == []
    assert ajustadas[0]["aprendizagem"] == "AE4 - Texto do AE 2"
    assert ajustadas[0]["aprendizagem_original"] == "Habilidade: EF89LP37 texto original"
    assert ajustadas[0]["ae_priorizado_aplicado"] is True
    assert ajustadas[0]["ae_priorizado_codigo"] == "AE4"
