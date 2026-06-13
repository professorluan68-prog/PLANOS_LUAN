from types import SimpleNamespace

from core import ia
import core.lote as lote
import core.revisao_final as revisao_final


def test_processar_plano_ia_openai_usa_chat_completions_parse(monkeypatch):
    capturado = {}

    class DummyParsed:
        def model_dump(self):
            return {
                "tema": "Tema openai",
                "aprendizagem": "AE openai",
                "metodologia": [],
            }

    class DummyResponse:
        choices = [SimpleNamespace(message=SimpleNamespace(parsed=DummyParsed(), content=""))]

    class DummyCompletions:
        def parse(self, **kwargs):
            capturado["parse_kwargs"] = kwargs
            return DummyResponse()

    class DummyClient:
        def __init__(self, api_key=None, timeout=None):
            capturado["api_key"] = api_key
            capturado["timeout"] = timeout
            self.chat = SimpleNamespace(completions=DummyCompletions())

    monkeypatch.setenv("OPENAI_API_KEY", "token-openai")
    monkeypatch.setattr(ia, "OpenAI", DummyClient)
    monkeypatch.setattr(ia, "_montar_prompt", lambda *args, **kwargs: "PROMPT")
    monkeypatch.setattr(ia, "get_system_prompt", lambda disciplina: "SYSTEM")
    monkeypatch.setattr(ia, "_normalizar_saida_ia", lambda data, *args, **kwargs: data)

    saida = ia.processar_plano_ia(
        texto_pdf="texto openai",
        disciplina="Língua Portuguesa",
        turma="1º ANO A",
        provedor="openai",
        modelo="gpt-4o-mini",
    )

    assert saida["tema"] == "Tema openai"
    assert capturado["api_key"] == "token-openai"
    assert capturado["timeout"] == ia.IA_TIMEOUT_SEGUNDOS
    assert capturado["parse_kwargs"]["model"] == "gpt-4o-mini"
    assert capturado["parse_kwargs"]["response_format"] is ia.PlanoAulaIA


def test_processar_plano_ia_gemini_define_timeout_http(monkeypatch):
    capturado = {}

    class DummyResponse:
        text = '{"tema":"Tema teste","aprendizagem":"AE teste","metodologia":[]}'

    class DummyModels:
        def generate_content(self, **kwargs):
            capturado["generate_kwargs"] = kwargs
            return DummyResponse()

    class DummyClient:
        def __init__(self, api_key=None, http_options=None):
            capturado["api_key"] = api_key
            capturado["client_http_options"] = http_options
            self.models = DummyModels()

    monkeypatch.setenv("GEMINI_API_KEY", "token-teste")
    monkeypatch.setattr(ia, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        ia,
        "types",
        SimpleNamespace(
            HttpOptions=lambda **kwargs: dict(kwargs),
            GenerateContentConfig=lambda **kwargs: dict(kwargs),
        ),
    )
    monkeypatch.setattr(ia, "_montar_prompt", lambda *args, **kwargs: "PROMPT")
    monkeypatch.setattr(ia, "get_system_prompt", lambda disciplina: "SYSTEM")
    monkeypatch.setattr(ia, "_normalizar_saida_ia", lambda data, *args, **kwargs: data)

    saida = ia.processar_plano_ia(
        texto_pdf="texto de teste",
        disciplina="Língua Portuguesa",
        turma="2º ANO C",
        provedor="gemini",
        modelo="gemini-2.5-flash",
    )

    timeout_esperado = ia.IA_TIMEOUT_SEGUNDOS * 1000
    assert saida["tema"] == "Tema teste"
    assert capturado["api_key"] == "token-teste"
    assert capturado["client_http_options"]["timeout"] == timeout_esperado
    assert capturado["generate_kwargs"]["config"]["response_mime_type"] == "application/json"
    assert capturado["generate_kwargs"]["config"]["http_options"]["timeout"] == timeout_esperado


def test_montar_prompt_inclui_rascunho_local_como_base_de_refinamento():
    prompt = ia._montar_prompt(
        texto_pdf="Texto do PDF sobre recursos hidricos e consumo consciente.",
        disciplina="Ciencias",
        turma="8 ANO B",
        rascunho_base={
            "tema": "Recursos hidricos e consumo consciente",
            "aprendizagem": "Analisar o uso consciente da agua no cotidiano.",
            "metodologia": [
                {"titulo": "Para comecar", "texto": "Retomar situacoes de consumo de agua na escola e em casa."},
                {"titulo": "Na pratica", "texto": "Interpretar dados e registrar propostas de economia de agua."},
            ],
        },
    )

    assert "RASCUNHO LOCAL DO SISTEMA" in prompt
    assert "Tema base: Recursos hidricos e consumo consciente" in prompt
    assert "Aprendizagem base: Analisar o uso consciente da agua no cotidiano." in prompt
    assert "Metodologia base:" in prompt
    assert "- Para comecar: Retomar situacoes de consumo de agua na escola e em casa." in prompt


def test_aula_por_pdf_envia_rascunho_local_para_refinamento_da_ia(monkeypatch):
    capturado = {}
    rascunho_local = {
        "disciplina": "Ciencias",
        "tema": "Recursos hidricos",
        "material": "AULA 9 - Recursos hidricos",
        "numero_aula": "9",
        "aprendizagem": "Analisar o uso da agua e seus impactos no cotidiano.",
        "metodologia": [{"titulo": "Para comecar", "texto": "Retomar o consumo de agua em situacoes do cotidiano."}],
        "acompanhamento": ["☑ Observar se identifica formas de uso da agua."],
        "acessibilidade": ["☑ Oferecer palavras-chave para apoiar a leitura."],
        "ia_usada": False,
        "ia_provedor": "openai",
        "ia_erro": "",
    }

    monkeypatch.setattr(
        lote,
        "_preparar_contexto_aula_pdf",
        lambda **kwargs: {
            "texto": "Texto do PDF sobre recursos hidricos.",
            "tema": "Recursos hidricos",
            "material_digital": "AULA 9 - Recursos hidricos",
            "numero_aula": "9",
            "cdp_contextual": False,
            "disciplina_base": "Ciencias",
            "perfil": "ciencias_ef",
            "objetivos_orientacao": [],
            "aprendizagem_orientacao": "",
            "extracao_pdf": {},
            "tipo": "ciencias_conceitual",
            "metodologia_fixa_pdf": [],
            "modalidade_eja_ativa": False,
            "contexto_metodologico": "regular",
            "escopo_pv": {},
            "aprendizagem_pv": "",
        },
    )
    monkeypatch.setattr(lote, "_montar_resultado_aula_local", lambda **kwargs: dict(rascunho_local))

    def _fake_processar_plano_ia(*args, **kwargs):
        capturado["rascunho_base"] = kwargs.get("rascunho_base")
        return {
            "tema": "Recursos hidricos",
            "aprendizagem": "Analisar o uso da agua e seus impactos no cotidiano.",
            "metodologia": [{"titulo": "Para comecar", "texto": "Ajuste fino da IA sobre o rascunho local."}],
        }

    monkeypatch.setattr(ia, "processar_plano_ia", _fake_processar_plano_ia)
    monkeypatch.setattr(
        lote,
        "_montar_resultado_aula_ia",
        lambda **kwargs: {
            "disciplina": "Ciencias",
            "tema": kwargs["tema"],
            "material": kwargs["material_digital"],
            "numero_aula": kwargs["numero_aula"],
            "aprendizagem": rascunho_local["aprendizagem"],
            "metodologia": [{"titulo": "Para comecar", "texto": "Ajuste fino da IA sobre o rascunho local."}],
            "acompanhamento": rascunho_local["acompanhamento"],
            "acessibilidade": rascunho_local["acessibilidade"],
            "ia_usada": True,
            "ia_provedor": kwargs["provedor_ia"],
            "ia_erro": "",
        },
    )
    monkeypatch.setattr(revisao_final, "revisar_aula_gerada", lambda aula, perfil: aula)
    monkeypatch.setattr(revisao_final, "gravar_sidecar_json", lambda *args, **kwargs: None)

    aula = lote._aula_por_pdf(
        caminho_pdf="",
        disciplina="Ciencias",
        turma="8 ANO B",
        bimestre="3 Bimestre",
        usar_ia=True,
        provedor_ia="openai",
        modelo_ia="gpt-4o-mini",
    )

    assert capturado["rascunho_base"]["tema"] == "Recursos hidricos"
    assert capturado["rascunho_base"]["metodologia"][0]["texto"] == "Retomar o consumo de agua em situacoes do cotidiano."
    assert aula["ia_usada"] is True
