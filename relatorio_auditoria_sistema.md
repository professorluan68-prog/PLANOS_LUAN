# Relatorio de Auditoria Técnica — SISTEMA PLANOS_LUAN

**Arquivo sugerido:** `relatorio_auditoria_sistema.md`  
**Objetivo:** entrega completa e acionável com diagnóstico, refatorações propostas, trechos de código, plano de ação priorizado, métricas e checklist de segurança. As melhorias profundas listadas abaixo devem ser analisadas automaticamente por agentes especializados (ex.: *Codex* para patches de código e *Gemini* para validação de prompts/heurísticas) e só implementadas após validação dos agentes e revisão humana.

---

## Sumário executivo

- **Problemas críticos identificados:** cache sem assinatura/versionamento; chamadas a LLM sem resiliência; SQLite sem configuração para concorrência; acoplamento alto em `core/lote.py`; heurísticas pedagógicas frágeis.
- **Impacto:** planos desatualizados, bloqueios concorrenciais, custos de IA elevados, falhas silenciosas, baixa testabilidade.
- **Prioridade imediata:** corrigir cache e resiliência das chamadas a IA (P0). Em seguida, refatorar orquestrador e endurecer DB (P0–P1). Por fim, melhorar heurísticas e UX (P1–P2).

---

## 1. Achados críticos e evidências técnicas

| Prioridade | Local | Problema | Efeito imediato |
|---:|---|---|---|
| **P0** | `core/lote.py` / cache | Cache sem assinatura de conteúdo; chaves frágeis | Retorno de planos desatualizados; inconsistência ao mudar flags |
| **P0** | `core/ia.py` | Sem retries/backoff/circuit-breaker; timeouts ausentes | Threads bloqueadas; custos por reenvios; falhas silenciosas |
| **P0** | `core/database.py` | SQLite sem WAL; conexões compartilhadas | `database is locked`; travamentos em escrita concorrente |
| **P1** | `core/lib/*` | Regras pedagógicas duplicadas e espalhadas | Manutenção difícil; inconsistência entre versões |
| **P1** | Parser PDF/PPTX | Heurísticas simples; OCR sem fallback | Falsos negativos/positivos na detecção de recursos |
| **P2** | Streamlit UI | Operações síncronas longas sem feedback | Má experiência do usuário; timeouts no front-end |

**Observação:** os problemas acima decorrem do acoplamento do orquestrador que mistura I/O, lógica de domínio e infra. A correção exige separação de responsabilidades e instrumentação.

---

## 2. Diagnóstico detalhado e recomendações técnicas

### 2.1 Arquitetura e acoplamento
**Sintoma:** `lote.py` orquestra leitura, parsing, IA, cache, DB e export.  
**Risco:** alteração em um componente quebra todo o fluxo.  
**Recomendação:** aplicar *Dependency Injection* e dividir em camadas:

- **Camada Parser**: extrai texto, imagens, metadados, anotações.
- **Camada Classifier**: heurísticas e ML leve para detectar recursos.
- **Camada IAClient**: wrapper resiliente para Gemini/OpenAI.
- **Camada CacheManager**: chave determinística + schema_version.
- **Camada DBGateway**: persistência com transações curtas.
- **Orquestrador (LoteEngine)**: coordena, sem lógica de baixo nível.

### 2.2 Cache e consistência
**Problema:** cache baseado em nome/mtime; não considera flags (`usar_ia`, `perfil`) nem versão de prompt.  
**Solução técnica:**

- **Chave determinística**: `sha256(file_bytes) + ':' + sha256(json.dumps({flags, perfil, prompt_version}))`.
- **Valor armazenado**: incluir `cache_schema_version`, `prompt_template_version`, `created_at`, `source_hash`, `confidence`.
- **Atomicidade**: gravar em arquivo temporário e `os.replace()` para evitar leituras parciais.
- **Invalidation**: incrementar `prompt_template_version` ao alterar templates; TTL e soft-expiry com revalidação em background.
- **Cache metadata**: armazenar tokens consumidos, modelo usado, tempo de geração.

### 2.3 Chamadas a LLM (resiliência)
**Problema:** sem retries, sem timeouts, sem circuit-breaker.  
**Solução técnica:**

- **Retries exponenciais com jitter** (ex.: 3–5 tentativas).
- **Circuit breaker**: abrir após N falhas consecutivas; fechar após período de cooldown.
- **Timeouts por chamada** e **timeout global por lote**.
- **Diferenciar erros**: 4xx (permanente) vs 5xx/429 (transitório).
- **Fallback local**: gerador heurístico quando IA indisponível.
- **Rate-limit awareness**: backoff adaptativo ao receber 429.

### 2.4 SQLite e concorrência
**Problema:** escrita concorrente causa `database is locked`.  
**Solução técnica:**

- `PRAGMA journal_mode=WAL;` e `PRAGMA synchronous=NORMAL;`
- **Uma conexão por thread/processo**; não compartilhar conexões.
- **Transações curtas**; agrupar commits.
- **Índices**: `file_hash`, `status`, `created_at`.
- **Pool simples**: criar/fechar conexões por worker ou usar um pool leve.
- **Migração**: considerar PostgreSQL se concorrência aumentar.

### 2.5 Heurísticas pedagógicas e parser
**Problema:** classificador baseado em regex; detecção de recursos frágil.  
**Solução técnica:**

- **Pipeline multimodal**: extrair XMP, imagens embutidas, anotações; aplicar OCR apenas quando necessário.
- **Classificador híbrido**: embeddings + modelo leve (logistic regression / small transformer) para robustez.
- **Decision logs**: registrar por que uma regra foi aplicada.
- **Test-suite**: conjunto de PDFs/PPTX com casos extremos para validação.

---

## 3. Proposta de refatoração — trechos de código e padrões

> **Princípio:** cada módulo implementa uma interface clara; `LoteEngine` orquestra chamando interfaces.

### 3.1 Interfaces (contratos)
```python
# core/interfaces.py
from typing import Protocol, Any

class IAClientProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> dict: ...

class CacheManagerProtocol(Protocol):
    def key_for(self, file_bytes: bytes, params: dict) -> str: ...
    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict, ttl: int | None = None) -> None: ...

class DocumentParserProtocol(Protocol):
    def parse(self, path: str) -> dict: ...
    def signature(self, path: str) -> str: ...
```

### 3.2 CacheManager robusto
```python
# core/cache_manager.py
import hashlib, json, os, tempfile, time

class CacheManager:
    def __init__(self, cache_dir: str, schema_version: str):
        self.cache_dir = cache_dir
        self.schema_version = schema_version

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def key_for(self, file_bytes: bytes, params: dict) -> str:
        params_hash = self._hash(json.dumps(params, sort_keys=True).encode())
        return f"{self._hash(file_bytes)}:{params_hash}:{self.schema_version}"

    def set(self, key: str, value: dict):
        tmp = tempfile.NamedTemporaryFile(delete=False, dir=self.cache_dir)
        tmp.write(json.dumps(value).encode())
        tmp.flush(); tmp.close()
        os.replace(tmp.name, os.path.join(self.cache_dir, key + '.json'))

    def get(self, key: str):
        path = os.path.join(self.cache_dir, key + '.json')
        if not os.path.exists(path):
            return None
        with open(path,'rb') as f:
            return json.load(f)
```

### 3.3 IAClient resiliente
```python
# core/ia_client.py
import time, random, requests

class IAClient:
    def __init__(self, api_key, base_url, timeout=20, max_failures=5):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.failures = 0
        self.max_failures = max_failures

    def _call(self, payload):
        if self.failures >= self.max_failures:
            raise RuntimeError("Circuit open")
        resp = requests.post(self.base_url, json=payload,
                             timeout=self.timeout,
                             headers={"Authorization": f"Bearer {self.api_key}"})
        resp.raise_for_status()
        self.failures = 0
        return resp.json()

    def generate(self, prompt, **kwargs):
        attempts = 0
        while attempts < 5:
            try:
                return self._call({"prompt": prompt, **kwargs})
            except requests.HTTPError as e:
                status = e.response.status_code
                if 400 <= status < 500 and status != 429:
                    raise
                attempts += 1
                sleep = (2 ** attempts) + random.random()
                time.sleep(sleep)
        raise RuntimeError("Max attempts reached")
```

### 3.4 LoteEngine (orquestrador)
```python
# core/engine.py
class LoteEngine:
    def __init__(self, parser, classifier, ia_client, cache_manager, db_gateway, exporter):
        self.parser = parser
        self.classifier = classifier
        self.ia = ia_client
        self.cache = cache_manager
        self.db = db_gateway
        self.exporter = exporter

    def process(self, file_path: str, usar_ia: bool, perfil: str):
        file_bytes = open(file_path,'rb').read()
        params = {"usar_ia": usar_ia, "perfil": perfil}
        key = self.cache.key_for(file_bytes, params)
        cached = self.cache.get(key)
        if cached:
            return cached
        parsed = self.parser.parse(file_path)
        features = self.classifier.classify(parsed)
        if usar_ia:
            prompt = self._build_prompt(parsed, features, perfil)
            resp = self.ia.generate(prompt, max_tokens=1500)
        else:
            resp = self._heuristic_generate(parsed, features, perfil)
        post = self._postprocess(resp)
        self.cache.set(key, post)
        self.db.save_plan(file_path, post)
        docx_path = self.exporter.to_docx(post)
        return {"plan": post, "docx": docx_path}
```

### 3.5 Boas práticas DB (SQL)
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
```

---

## 4. Heurísticas avançadas e validação por agentes

**Fluxo proposto de validação automática antes de implementação:**

1. **Gerar patches** (diffs) para os arquivos críticos (`core/lote.py`, `core/ia.py`, `core/database.py`, `core/lib/*`) com base nas refatorações propostas.
2. **Agente Codex**: analisar patches de código, detectar regressões sintáticas, sugerir melhorias de estilo e segurança (ex.: tratamento de exceções, fechamento de arquivos).
3. **Agente Gemini**: validar prompts, templates e regras pedagógicas; simular respostas e medir token usage estimado; sugerir compressões de prompt.
4. **Relatório consolidado**: agentes produzem um relatório de compatibilidade e riscos; somente após aprovação humana, aplicar patches no repositório.

**Checklist de validação por agentes (automático):**

- [ ] Patches aplicáveis sem conflitos.
- [ ] Testes unitários mínimos passados (parser, cache key determinism, IAClient mock).
- [ ] Estimativa de tokens por geração e custo projetado.
- [ ] Verificação de secrets hardcoded (nenhum segredo em código).
- [ ] Verificação de performance (latência estimada por etapa).

---

## 5. Otimização de custos e performance (IA)

- **Enviar apenas o necessário**: extrair seções relevantes (sumário, objetivos, recursos) em vez do documento inteiro.
- **Modelos menores para tarefas estruturais**: classificação e sumarização com modelos leves; geração criativa com modelos maiores.
- **Cache de respostas e embeddings**: evitar recomputação; usar TTLs e soft-expiry.
- **Batching**: agrupar solicitações quando possível.
- **Prompt templates versionados**: atualizar `prompt_template_version` para invalidar caches quando mudar prompt.
- **Limitar retries**: evitar reenvios que geram custos.

**Técnica de compressão de prompt (exemplo):**

1. Extrair apenas: título, objetivos, recursos, número de aulas, público-alvo.
2. Gerar um *context summary* de 200–400 tokens.
3. Enviar *system prompt* curto + *context summary* + *instruction template*.

---

## 6. Plano de ação priorizado (30/60/90 dias)

### 30 dias (P0)
- Implementar `CacheManager` com hashing e `schema_version`.
- Ativar WAL no SQLite e criar índices essenciais.
- Encapsular chamadas a IA em `IAClient` com timeout e retries.
- Adicionar logs estruturados e métricas básicas (tempo, tokens, erros).
- Criar testes unitários para `CacheManager` e `IAClient` (mocked).

### 60 dias (P1)
- Refatorar `core/lote.py` para `LoteEngine` com DI.
- Implementar fallback heurístico offline.
- Criar testes de integração com um conjunto de PDFs/PPTX de teste.
- Implementar decision logs para heurísticas.

### 90 dias (P2)
- Avaliar migração para PostgreSQL se concorrência alta.
- Treinar classificador leve com embeddings; integrar busca semântica.
- Implementar painel de custo por token e alertas de orçamento.
- Implementar revisão humana assistida (export com track changes e comentários).

---

## 7. Métricas, testes e observabilidade

**Métricas essenciais:**

- **Latência por etapa**: parse, classify, IA, export.
- **Tokens consumidos** por arquivo, por perfil, por usuário.
- **Cache hit/miss rate**.
- **Erros por tipo**: 4xx, 5xx, timeout, parse errors.
- **Uso de disco**: cache size, TTL expirations.

**Testes recomendados:**

- **Unitários**: parser, cache key determinism, IAClient (mock), classifier rules.
- **Integração**: fluxo completo com arquivos de teste.
- **Carga**: simular N processos concorrentes para validar DB e cache.
- **Fuzzing**: PDFs malformados, arquivos grandes, slides com imagens pequenas.

**Logs e tracing:**

- Gerar `request_id` por lote; logs estruturados (JSON) com campos: `request_id`, `file_hash`, `perfil`, `usar_ia`, `model`, `tokens_in`, `tokens_out`, `duration_ms`, `error_type`.

---

## 8. Segurança e conformidade

- **Segredos**: mover chaves para variáveis de ambiente ou vault; nunca commitar.
- **Sanitização de inputs**: evitar injeção em prompts; validar e escapar strings.
- **Retenção de dados**: política para cache e planos gerados (ex.: 90 dias).
- **Auditoria**: decision logs para cada plano gerado (quem, quando, por que).
- **Privacidade**: remover PII antes de enviar a LLM quando aplicável.

---

## 9. Exemplos de patches e PR checklist (para agentes Codex/Gemini)

### Patch 1 — `core/cache_manager.py`
- Implementa hashing determinística.
- Adiciona `schema_version` e metadata.
- Testes: `test_cache_key_determinism`, `test_cache_atomic_write`.

### Patch 2 — `core/ia_client.py`
- Wrapper com retries, timeout e circuit-breaker.
- Testes: `test_iaclient_retries`, `test_iaclient_circuit_open`.

### Patch 3 — `core/engine.py`
- Substitui `lote.py` por `LoteEngine` desacoplado.
- Testes: `test_engine_cache_hit`, `test_engine_fallback_heuristic`.

**PR checklist (automático):**

- [ ] Lint OK (flake8/black).
- [ ] Unit tests pass.
- [ ] No secrets in diff.
- [ ] Estimativa de tokens e custo incluída.
- [ ] Documentação de breaking changes (se houver).

---

## 10. Artefatos entregáveis e instruções de uso

**Conteúdo do arquivo `relatorio_auditoria_sistema.md`:** todo o conteúdo deste documento (copiar/colar).  
**Observação sobre implementação automatizada:** gerar patches e submetê-los a análise por agentes (Codex para código; Gemini para prompts/heurísticas). Após análise automática, gerar relatório consolidado com riscos e aplicar patches somente após revisão humana.

---

## 11. Checklist final de ações imediatas

- [ ] Implementar `CacheManager` com hashing e `schema_version`.
- [ ] Encapsular chamadas a IA em `IAClient` com retries, timeout e circuit-breaker.
- [ ] Ativar WAL no SQLite e criar índices.
- [ ] Refatorar `core/lote.py` para `LoteEngine` com DI.
- [ ] Implementar fallback heurístico offline.
- [ ] Criar testes unitários e dataset de PDFs/PPTX para validação.
- [ ] Adicionar logs estruturados e métricas de tokens.
- [ ] Submeter patches a agentes Codex/Gemini para validação automática antes de merge.

---

## 12. Conclusão

A base do sistema é funcional, mas **corrigir o cache e tornar as chamadas a IA resilientes** são ações críticas e de alto impacto imediato. A separação de responsabilidades, instrumentação e testes transformarão o projeto em uma plataforma confiável, escalável e com custos controlados. As melhorias propostas são profundas e projetadas para reduzir riscos operacionais, diminuir custos com LLMs e aumentar a qualidade pedagógica dos planos gerados.

---

### Anexo A — Diagrama de fluxo sugerido
```mermaid
flowchart LR
  A[Upload PDF] --> B[DocumentParser]
  B --> C{CacheManager}
  C -- hit --> D[Return cached plan]
  C -- miss --> E[Classifier]
  E --> F[IAClient (resilient)]
  F --> G[PostProcessor (rules)]
  G --> H[CacheManager set + DBGateway persist]
  H --> I[Export .docx]
```

---

### Anexo B — Trechos de código adicionais (resumo)
- **CacheManager**: hashing, atomic write, metadata.
- **IAClient**: retries, circuit-breaker, timeouts.
- **LoteEngine**: orquestrador desacoplado.
- **DB**: WAL, índices, transações curtas.

---

**Observação final:** as melhorias fortes e profundas descritas aqui foram pensadas para serem validadas automaticamente por agentes especializados (Codex para patches de código; Gemini para prompts e heurísticas). Após a validação automática, aplicar as mudanças em branches isoladas, executar a suíte de testes e revisar manualmente antes do merge em `main`.

---  

**Fim do relatório (Markdown pronto para salvar em `relatorio_auditoria_sistema.md`).**