from core import ae_priorizado


def test_contexto_ae_priorizado_so_ativa_para_portugues_em_segundo_bimestre(monkeypatch):
    class DummyPath:
        def exists(self):
            return True

    monkeypatch.setattr(ae_priorizado, "AE_PRIORIZADO_JSON_PATH", DummyPath())

    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "1ª Série A", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "1ª Série A", "1º Bimestre") is False
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Matemática", "1ª Série A", "2º Bimestre") is False


def test_contexto_ae_priorizado_tambem_cobre_turmas_reais_de_segundo_e_terceiro_ano(monkeypatch):
    class DummyPath:
        def exists(self):
            return True

    monkeypatch.setattr(ae_priorizado, "AE_PRIORIZADO_JSON_PATH", DummyPath())

    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "2º ANO B", "2º Bimestre") is True
    assert ae_priorizado.contexto_ae_priorizado_disponivel("Língua Portuguesa", "3º ANO C", "2º Bimestre") is True


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
