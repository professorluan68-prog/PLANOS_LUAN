import json

from core.reuso_cache_plano import tentar_reutilizar_cache_plano


def _dependencias_padrao():
    return {
        "referencia_docx_por_perfil_fn": lambda *args, **kwargs: None,
        "referencia_docx_sobrescreve_metadados_fn": lambda perfil: True,
        "habilidade_referencia_docx_fn": lambda referencia: "",
        "material_aula_com_titulo_fn": lambda numero, titulo: f"AULA {numero} - {titulo}",
        "sobrescrever_listas_pedagogicas_com_referencia_fn": (
            lambda referencia, acompanhamento, acessibilidade: (
                acompanhamento,
                acessibilidade,
            )
        ),
        "origem_metodologia_por_referencia_fn": lambda perfil: f"docx_referencia_{perfil}",
        "perfil_docx_somente_colunas_pedagogicas_fn": lambda perfil: False,
    }


def test_tentar_reutilizar_cache_plano_reusa_cache_quando_compativel(tmp_path):
    caminho_pdf = tmp_path / "AULA_01.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4")
    caminho_pdf.with_suffix(".json").write_text(
        json.dumps(
            {
                "disciplina": "Arte",
                "tema": "Tema salvo",
                "material": "AULA 1 - Tema salvo",
                "numero_aula": "1",
                "aprendizagem": "Aprendizagem salva",
                "metodologia": [{"titulo": "Para começar", "texto": "Texto salvo"}],
                "acompanhamento": ["Item 1", "Item 2", "Item 3"],
                "acessibilidade": ["Apoio 1", "Apoio 2", "Apoio 3"],
                "ia_usada": False,
                "versao_gerador": "1.2.9",
                "fingerprint_contexto": "fp-ok",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    resultado = tentar_reutilizar_cache_plano(
        caminho_pdf=str(caminho_pdf),
        disciplina="Arte",
        turma="6º ANO A",
        usar_ia=False,
        caminho_pptx_correspondente=None,
        hash_atual="hash-ok",
        hash_fonte_extracao_esperada="",
        fingerprint_atual="fp-ok",
        versao_gerador_atual="1.2.9",
        perfil_metodologico="base",
        **_dependencias_padrao(),
    )

    assert resultado.aula_reutilizada is not None
    assert resultado.aula_reutilizada["cache_reutilizado"] is True
    assert resultado.aula_reutilizada["tema"] == "Tema salvo"
    assert resultado.dados_json_antigos["tema"] == "Tema salvo"


def test_tentar_reutilizar_cache_plano_mantem_json_antigo_mesmo_invalido(tmp_path):
    caminho_pdf = tmp_path / "AULA_03.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4")
    caminho_pdf.with_suffix(".json").write_text(
        json.dumps(
            {
                "disciplina": "Língua Portuguesa",
                "tema": "Tema antigo",
                "material": "AULA 3 - Tema antigo",
                "numero_aula": "3",
                "aprendizagem": "Aprendizagem antiga",
                "metodologia": [{"titulo": "Para começar", "texto": "Texto antigo"}],
                "ia_usada": False,
                "versao_gerador": "1.2.9",
                "fingerprint_contexto": "fp-antigo",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    resultado = tentar_reutilizar_cache_plano(
        caminho_pdf=str(caminho_pdf),
        disciplina="Língua Portuguesa",
        turma="6º ANO A",
        usar_ia=False,
        caminho_pptx_correspondente=None,
        hash_atual="hash-ok",
        hash_fonte_extracao_esperada="",
        fingerprint_atual="fp-novo",
        versao_gerador_atual="1.2.9",
        perfil_metodologico="base",
        **_dependencias_padrao(),
    )

    assert resultado.aula_reutilizada is None
    assert resultado.dados_json_antigos is not None
    assert resultado.dados_json_antigos["tema"] == "Tema antigo"


def test_tentar_reutilizar_cache_plano_reaplica_referencia_sobre_cache_local(tmp_path):
    caminho_pdf = tmp_path / "AULA_01.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4")
    caminho_pdf.with_suffix(".json").write_text(
        json.dumps(
            {
                "disciplina": "História",
                "tema": "Tema antigo",
                "material": "AULA 1 - Tema antigo",
                "numero_aula": "1",
                "aprendizagem": "Aprendizagem antiga",
                "metodologia": [{"titulo": "Para começar", "texto": "Texto antigo"}],
                "acompanhamento": ["Base 1", "Base 2", "Base 3"],
                "acessibilidade": ["Base A", "Base B", "Base C"],
                "ia_usada": False,
                "versao_gerador": "1.2.9",
                "fingerprint_contexto": "fp-ok",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    referencia = {
        "numero": "7",
        "titulo": "Tema revisado",
        "habilidade": "Habilidade revisada",
        "metodologia": [{"titulo": "Foco no conteúdo", "texto": "Texto revisado"}],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
        "fonte": "referencia.docx",
    }

    dependencias = _dependencias_padrao()
    dependencias["referencia_docx_por_perfil_fn"] = lambda *args, **kwargs: referencia
    dependencias["habilidade_referencia_docx_fn"] = lambda ref: ref["habilidade"]
    dependencias["sobrescrever_listas_pedagogicas_com_referencia_fn"] = (
        lambda ref, acompanhamento, acessibilidade: (
            list(ref["acompanhamento"]),
            list(ref["acessibilidade"]),
        )
    )
    dependencias["origem_metodologia_por_referencia_fn"] = lambda perfil: "docx_referencia_historia"

    resultado = tentar_reutilizar_cache_plano(
        caminho_pdf=str(caminho_pdf),
        disciplina="História",
        turma="6º ANO",
        usar_ia=False,
        caminho_pptx_correspondente=None,
        hash_atual="hash-ok",
        hash_fonte_extracao_esperada="",
        fingerprint_atual="fp-ok",
        versao_gerador_atual="1.2.9",
        perfil_metodologico="base",
        **dependencias,
    )

    assert resultado.aula_reutilizada["tema"] == "Tema revisado"
    assert resultado.aula_reutilizada["numero_aula"] == "7"
    assert resultado.aula_reutilizada["aprendizagem"] == "Habilidade revisada"
    assert resultado.aula_reutilizada["origem_metodologia"] == "docx_referencia_historia"
