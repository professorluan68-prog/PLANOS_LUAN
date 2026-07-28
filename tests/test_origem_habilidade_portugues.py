from pathlib import Path

from openpyxl import Workbook

import core.lote as lote
from core.revisao_final import VERSAO_GERADOR_ATUAL


def _referencia_docx_portugues_fake() -> dict:
    return {
        "titulo": "AULA 3 - Titulo revisado",
        "numero": "3",
        "habilidade": "Habilidade: TEXTO VINDO DO DOCX QUE NAO DEVE ENTRAR.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "Texto do DOCX."},
            {"titulo": "Foco no conteúdo", "texto": "Foco do DOCX."},
            {"titulo": "Na prática", "texto": "Prática do DOCX."},
            {"titulo": "Encerramento", "texto": "Encerramento do DOCX."},
        ],
        "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
        "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
        "fonte": "referencia_revisada.docx",
    }


def _colunas_planejamento_fake() -> dict:
    return {
        "metodologia": [{"titulo": "Para começar", "texto": "Texto base da aula."}],
        "acompanhamento": ["☑ Verificar leitura.", "☑ Observar interpretacao.", "☑ Acompanhar registros."],
        "acessibilidade": ["☑ Disponibilizar palavras-chave.", "☑ Oferecer leitura guiada.", "☑ Permitir resposta oral."],
    }


def _criar_planilha_habilidade(caminho: Path, numero_aula: int, habilidade: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(["AULA", "HABILIDADE", "TITULO DA AULA"])
    ws.append([numero_aula, habilidade, "Titulo da aula"])
    wb.save(caminho)


def test_portugues_resultado_local_prefere_habilidade_do_pdf_ao_docx(monkeypatch, tmp_path):
    caminho_pdf = tmp_path / "AULA_03.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: _referencia_docx_portugues_fake())
    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": (
                "(EF67LP28) Ler, de forma autonoma, e compreender textos literarios, "
                "selecionando estrategias de leitura adequadas aos objetivos da aula."
            ),
            "conceito_extraido": "Leitura literaria",
            "recursos_detectados": [],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "Texto da aula",
        },
    )
    monkeypatch.setattr(lote, "_tentar_gerador_colunas_pedagogicas", lambda **kwargs: _colunas_planejamento_fake())

    resultado = lote._montar_resultado_aula_local(
        texto="Texto da aula",
        tema="Tema do PDF",
        material_digital="AULA 3 - Tema do PDF",
        numero_aula="3",
        disciplina_base="Língua Portuguesa",
        turma="6º ANO A",
        provedor_ia="",
        perfil="lingua_portuguesa_ef",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        usar_ia=False,
        ia_erro="",
        caminho_pdf=str(caminho_pdf),
    )

    assert "EF67LP28" in resultado["aprendizagem"]
    assert "DOCX" not in resultado["aprendizagem"]
    assert resultado["tema"] == "Tema do PDF"
    assert resultado["material"] == "AULA 3 - Tema do PDF"
    assert resultado["numero_aula"] == "3"
    assert resultado["metodologia"][0]["texto"] == "Texto do DOCX."
    assert resultado["acompanhamento"] == ["☑ Item 1", "☑ Item 2", "☑ Item 3"]
    assert resultado["acessibilidade"] == ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"]


def test_portugues_resultado_ia_mantem_metadados_do_pdf_e_colunas_do_docx(monkeypatch, tmp_path):
    caminho_pdf = tmp_path / "AULA_03.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: _referencia_docx_portugues_fake())
    monkeypatch.setattr(
        lote._extrator_lib,
        "extrair",
        lambda *args, **kwargs: {
            "habilidade": (
                "(EF67LP28) Ler, de forma autonoma, e compreender textos literarios, "
                "selecionando estrategias de leitura adequadas aos objetivos da aula."
            ),
            "conceito_extraido": "Leitura literaria",
            "recursos_detectados": [],
            "objetivos_secao": [],
            "conteudos_secao": [],
            "texto_prioritario": "Texto da aula",
        },
    )
    monkeypatch.setattr(lote, "_tentar_gerador_colunas_pedagogicas", lambda **kwargs: _colunas_planejamento_fake())

    resultado = lote._montar_resultado_aula_ia(
        texto="Texto da aula",
        tema="Tema do PDF",
        material_digital="AULA 3 - Tema do PDF",
        numero_aula="3",
        disciplina_base="Língua Portuguesa",
        turma="6º ANO A",
        provedor_ia="openai",
        perfil="lingua_portuguesa_ef",
        contexto_metodologico="regular",
        indice_aula=0,
        total_aulas=1,
        modalidade_eja_ativa=False,
        plano_ia={
            "tema": "Tema inventado pela IA",
            "aprendizagem": "Aprendizagem da IA",
            "metodologia": [
                {"titulo": "Para começar", "texto": "Texto da IA."},
                {"titulo": "Foco no conteúdo", "texto": "Foco da IA."},
                {"titulo": "Na prática", "texto": "Prática da IA."},
                {"titulo": "Encerramento", "texto": "Encerramento da IA."},
            ],
            "acompanhamento": ["Item IA 1", "Item IA 2", "Item IA 3"],
            "acessibilidade": ["Acesso IA 1", "Acesso IA 2", "Acesso IA 3"],
        },
        metodologia_fixa_pdf=[],
        aprendizagem_pv="",
        objetivos_orientacao=[],
        aprendizagem_orientacao="",
        caminho_pdf=str(caminho_pdf),
    )

    assert resultado["tema"] == "Tema do PDF"
    assert resultado["material"] == "AULA 3 - Tema do PDF"
    assert "EF67LP28" in resultado["aprendizagem"]
    assert "Texto da IA." in resultado["metodologia"][0]["texto"]
    assert "Item IA" in resultado["acompanhamento"][0]
    assert "Acesso IA" in resultado["acessibilidade"][0]


def test_portugues_nao_reutiliza_cache_antigo_quando_ha_docx_referencia(monkeypatch, tmp_path):
    pdf_file = tmp_path / "AULA_03.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy contents")

    json_file = tmp_path / "AULA_03.json"
    json_file.write_text(
        """
{
  "disciplina": "Língua Portuguesa",
  "tema": "Tema errado vindo do DOCX antigo",
  "material": "AULA 3 - Tema errado vindo do DOCX antigo",
  "numero_aula": "3",
  "aprendizagem": "Habilidade errada do DOCX antigo",
  "metodologia": [{"titulo": "Para começar", "texto": "Texto antigo em cache."}],
  "acompanhamento": ["Item antigo 1", "Item antigo 2", "Item antigo 3"],
  "acessibilidade": ["Acesso antigo 1", "Acesso antigo 2", "Acesso antigo 3"],
  "ia_usada": false,
  "ia_provedor": "",
  "ia_erro": "",
  "versao_gerador": "%s",
  "fingerprint_contexto": "fingerprint-antigo"
}
""" % VERSAO_GERADOR_ATUAL,
        encoding="utf-8",
    )

    monkeypatch.setattr(lote, "_referencia_docx_por_perfil", lambda *args, **kwargs: _referencia_docx_portugues_fake())
    monkeypatch.setattr(
        lote,
        "_preparar_contexto_aula_pdf",
        lambda *args, **kwargs: {
            "texto": "Texto da aula",
            "tema": "Tema do PDF",
            "material_digital": "AULA 3 - Tema do PDF",
            "numero_aula": "3",
            "cdp_contextual": False,
            "disciplina_base": "Língua Portuguesa",
            "perfil": "lingua_portuguesa_ef",
            "objetivos_orientacao": [],
            "aprendizagem_orientacao": "",
            "extracao_pdf": {
                "habilidade": "(EF67LP28) Ler textos literarios.",
                "conceito_extraido": "Leitura literaria",
                "recursos_detectados": [],
                "objetivos_secao": [],
                "conteudos_secao": [],
                "texto_prioritario": "Texto da aula",
            },
            "tipo": "regular",
            "metodologia_fixa_pdf": [],
            "modalidade_eja_ativa": False,
            "contexto_metodologico": "regular",
            "escopo_pv": {},
            "aprendizagem_pv": "",
            "fonte_extracao": "pdf",
            "arquivo_fonte_extracao": str(pdf_file),
        },
    )
    monkeypatch.setattr(
        lote,
        "_montar_resultado_aula_local",
        lambda **kwargs: {
            "disciplina": "Língua Portuguesa",
            "tema": kwargs["tema"],
            "material": kwargs["material_digital"],
            "numero_aula": kwargs["numero_aula"],
            "aprendizagem": "Habilidade: (EF67LP28) Ler textos literarios.",
            "metodologia": [{"titulo": "Para começar", "texto": "Texto do DOCX."}],
            "acompanhamento": ["☑ Item 1", "☑ Item 2", "☑ Item 3"],
            "acessibilidade": ["☑ Apoio 1", "☑ Apoio 2", "☑ Apoio 3"],
            "ia_usada": False,
            "ia_provedor": "",
            "ia_erro": "",
            "origem_metodologia": "docx_referencia_portugues",
            "fonte_referencia_metodologia": "referencia_revisada.docx",
            "avisos_validacao": [],
        },
    )

    resultado = lote._aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="Língua Portuguesa",
        turma="6º ANO A",
        bimestre="3º Bimestre",
        usar_ia=False,
        provedor_ia="",
        professor="Luan",
    )

    assert resultado["tema"] == "Tema do PDF"
    assert resultado["material"] == "AULA 3 - Tema do PDF"
    assert "DOCX antigo" not in resultado["aprendizagem"]
    assert resultado["metodologia"][0]["texto"] == "Texto do DOCX."


def test_resolver_habilidade_portugues_faz_fallback_para_planilha_local(tmp_path):
    caminho_pdf = tmp_path / "AULA_03.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4\n")
    _criar_planilha_habilidade(
        tmp_path / "planilha.xlsx",
        3,
        "(EF67LP28) Ler, de forma autonoma, e compreender textos literarios com foco em estrategias de leitura.",
    )

    habilidade = lote._resolver_habilidade_portugues("", str(caminho_pdf), "3")

    assert "EF67LP28" in habilidade


def test_enriquecer_com_planilha_nao_sobrescreve_habilidade_valida_do_pdf(tmp_path):
    caminho_pdf = tmp_path / "AULA_03.pdf"
    caminho_pdf.write_bytes(b"%PDF-1.4\n")
    _criar_planilha_habilidade(
        tmp_path / "planilha.xlsx",
        3,
        "(EF67LP99) Texto diferente da planilha que nao deve substituir o PDF.",
    )

    resultado = {
        "aprendizagem": (
            "Habilidade: (EF67LP28) Ler, de forma autonoma, e compreender textos literarios "
            "com foco em estrategias de leitura."
        ),
        "tema": "Tema atual",
        "disciplina": "Língua Portuguesa",
        "fonte_referencia_metodologia": "",
    }

    lote._enriquecer_com_planilha(resultado, str(caminho_pdf))

    assert "EF67LP28" in resultado["aprendizagem"]
    assert "EF67LP99" not in resultado["aprendizagem"]
