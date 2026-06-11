from types import SimpleNamespace

from core import ia


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
