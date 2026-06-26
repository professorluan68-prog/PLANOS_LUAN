class LoteEngine:
    def __init__(
        self, parser, classifier, ia_client, cache_manager, db_gateway, exporter
    ):
        self.parser = parser
        self.classifier = classifier
        self.ia = ia_client
        self.cache = cache_manager
        self.db = db_gateway
        self.exporter = exporter

    def _build_prompt(self, parsed: dict, features: dict, perfil: str) -> str:
        # Implementar template de prompt aqui (externo ou injetado)
        # Exemplo simples:
        resumo = parsed.get("summary", "")
        return f"Perfil: {perfil}\nResumo: {resumo}\nRequisitos: {features}"

    def _heuristic_generate(self, parsed: dict, features: dict, perfil: str) -> dict:
        # Gerador local simples como fallback
        return {"plan": f"Rascunho heurístico para {perfil}", "confidence": "low"}

    def _postprocess(self, resp: dict) -> dict:
        # Normalizar saída da IA / heurística para formato do sistema
        return resp

    def process_file(
        self, file_path: str, usar_ia: bool, perfil: str, prompt_version: str = "v1"
    ) -> dict:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        params = {
            "usar_ia": usar_ia,
            "perfil": perfil,
            "prompt_version": prompt_version,
        }
        key = self.cache.key_for(file_bytes, params)
        cached = self.cache.get(key)
        if cached:
            return cached

        parsed = self.parser.parse(file_path)
        features = self.classifier.classify(parsed)
        if usar_ia:
            try:
                payload = {"prompt": self._build_prompt(parsed, features, perfil)}
                resp = self.ia.generate(payload)
            except Exception:
                resp = self._heuristic_generate(parsed, features, perfil)
        else:
            resp = self._heuristic_generate(parsed, features, perfil)

        post = self._postprocess(resp)
        self.cache.set(key, post)
        self.db.save_plan(file_path, post)
        # exporter.to_docx(post) pode ser chamado externamente
        return post
