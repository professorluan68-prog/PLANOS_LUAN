# 🔍 AUDITORIA TÉCNICA — SISTEMA PLANOS_LUAN
**Versão do Gerador Analisada:** 1.2.10  
**Data da Auditoria:** 2026-07-08  
**Foco Principal:** Falhas na geração de metodologia + problemas estruturais identificados  

---

## 📋 SUMÁRIO EXECUTIVO

O sistema **Planos Luan** é uma aplicação Python/Streamlit sofisticada para geração automatizada de planos de aula. A auditoria identificou **3 problemas críticos**, **7 problemas importantes** e **9 oportunidades de melhoria**, com foco especial nas falhas que afetam diretamente a **qualidade da metodologia gerada** — principal queixa reportada.

### Módulos Auditados (nova rodada)
| Módulo | Tamanho | Status |
|---|---|---|
| `revisao_final.py` | ~200 linhas | ⚠️ Problemas críticos |
| `higienizador_pedagogico.py` | ~49 KB | ⚠️ Problemas importantes |
| `contexto_aula_pdf.py` | ~15 KB | ⚠️ Problemas importantes |
| `models.py` | ~9 KB | ✅ Bem estruturado |
| `planos_luan_app_pipeline.txt` | ~15 KB | ⚠️ Problemas de UX/lógica |
| `qualidade_metodologica.py` | ~58 KB | 🔴 Crítico (já auditado) |
| `validador_plano.py` | ~26 KB | ⚠️ Problemas importantes |
| `lote.py` | ~132 KB | ⚠️ Monolítico |

---

## 🔴 PROBLEMAS CRÍTICOS

### CRÍTICO #1 — Penalização Dupla de Aderência ao PDF
**Arquivo:** `revisao_final.py` — função `revisar_aula_gerada()` — linhas ~90–110

#### ❌ Problema
A aderência ao PDF é penalizada **duas vezes** de formas diferentes e cumulativas:

```python
# Penalização 1: Dedução numérica proporcional
aderencia, avisos_aderencia = calcular_aderencia_pdf(aula)
if avisos_aderencia:
    penalidade = 10 + (80 - aderencia)  # Ex: aderência 60% = penalidade 30
    deducoes += penalidade

# Penalização 2: Teto fixo adicional (aplicado DEPOIS)
if aderencia < 80:
    aula["confidence_score"] = min(aula["confidence_score"], 75)
```

**Exemplo concreto do impacto:**
- Aderência = 60% → penalidade = 10 + (80 - 60) = **30 pontos**
- Score base = 100 - 30 = **70**
- Teto fixo aplica: `min(70, 75)` = **70** (neste caso não muda)
- Mas se score base fosse 80: `min(80, 75)` = **75** (penaliza 5 pontos extras sem justificativa)

#### 💥 Impacto
- Planos com aderência entre 75–79% são penalizados injustamente pelo teto fixo
- `confidence_score` torna-se imprevisível e difícil de calibrar
- Professores recebem alertas de baixa qualidade em planos que podem ser aceitáveis

#### ✅ Solução Recomendada
```python
# SUBSTITUIR o bloco atual por uma única penalização proporcional:
aderencia, avisos_aderencia = calcular_aderencia_pdf(aula)
if aderencia < 80:
    penalidade = max(10, int(80 - aderencia))  # Mínimo 10, máximo 80 pontos
    deducoes += penalidade
    avisos.extend(avisos_aderencia)
# REMOVER o bloco: if aderencia < 80: aula["confidence_score"] = min(...)
```

---

### CRÍTICO #2 — Regeneração Cíclica Sem Proteção Adequada
**Arquivo:** `revisao_final.py` — função `revisar_aula_gerada()` — linhas ~130–145

#### ❌ Problema
O mecanismo de regeneração seletiva chama `revisar_aula_gerada()` recursivamente, mas a proteção contra loop infinito depende de um campo interno `_tentativas_regeneracao` que é **removido ao final da função**:

```python
# Proteção existe...
tentativas_regeneracao = aula.get("_tentativas_regeneracao", 0)
if aula["confidence_score"] < SCORE_MINIMO_ACEITAVEL and tentativas_regeneracao < 1:
    aula_corrigida = _regenerar_etapas_historia(aula, etapas_problematicas)
    if aula_corrigida:
        aula_corrigida["_tentativas_regeneracao"] = tentativas_regeneracao + 1
        return revisar_aula_gerada(aula_corrigida, perfil)  # ← Chamada recursiva

# ...mas o campo é removido ANTES de retornar na chamada recursiva
aula.pop("_tentativas_regeneracao", None)  # ← Isso ocorre na chamada recursiva também
```

**Cenário de risco:**
1. `_regenerar_etapas_historia()` retorna `aula_corrigida` com `_tentativas_regeneracao = 1`
2. `revisar_aula_gerada()` é chamada recursivamente
3. Na chamada recursiva, `tentativas_regeneracao = 1`, então `< 1` é False → OK
4. **Mas:** se `_regenerar_etapas_historia()` retornar `None` (sem correção), o fluxo continua normalmente — sem loop. O risco real é se a lógica de `_regenerar_etapas_historia()` for expandida para outros perfis sem atualizar o limite.

#### 💥 Impacto Atual e Futuro
- Atualmente limitado a `perfil == "historia"` — risco controlado
- Se expandido para outros perfis sem cuidado, pode gerar loops
- Consumo desnecessário de processamento em PDFs de baixa qualidade

#### ✅ Solução Recomendada
```python
# Adicionar limite explícito como parâmetro e usar iteração em vez de recursão:
def revisar_aula_gerada(
    aula: dict | PlanoCompleto,
    perfil: str,
    _max_regeneracoes: int = 1,  # Parâmetro interno de controle
) -> dict:
    aula = PlanoCompleto.from_any(aula).to_dict()
    tentativas = aula.pop("_tentativas_regeneracao", 0)
    
    # ... lógica de validação ...
    
    if aula["confidence_score"] < SCORE_MINIMO_ACEITAVEL and tentativas < _max_regeneracoes:
        etapas_problematicas = _identificar_etapas_com_aviso(avisos)
        if etapas_problematicas and perfil == "historia":
            aula_corrigida = _regenerar_etapas_historia(aula, etapas_problematicas)
            if aula_corrigida:
                aula_corrigida["_tentativas_regeneracao"] = tentativas + 1
                logger.info("Regeneração seletiva: tentativa %d/%d", tentativas + 1, _max_regeneracoes)
                return revisar_aula_gerada(aula_corrigida, perfil, _max_regeneracoes)
    
    aula.pop("_tentativas_regeneracao", None)
    return PlanoCompleto.from_any(aula).to_dict()
```

---

### CRÍTICO #3 — Higienizador Pedagógico Sobrescreve Termos Válidos
**Arquivo:** `higienizador_pedagogico.py` — função `detectar_perfil_pedagogico_real()`

#### ❌ Problema
O higienizador classifica **toda aula de Língua Portuguesa** que não seja explicitamente jornalística como `"literatura"`, e então substitui termos como `"notícia"`, `"reportagem"` e `"manchete"` por equivalentes literários — mesmo quando o PDF contém genuinamente esses recursos:

```python
# Padrão para português se não for explicitamente jornalístico é considerado literário/geral
return "literatura"  # ← Fallback agressivo
```

**Exemplo de falha:**
- PDF: Aula sobre "Análise de Notícias Digitais" (LP EF)
- Tema extraído: "Textos jornalísticos digitais"
- Higienizador detecta: `"noticia_multimodal"` → OK
- **Mas:** se o tema for "Leitura e interpretação de textos" (genérico), cai no fallback `"literatura"`
- Resultado: `"a notícia apresentada"` → `"a obra apresentada"` — **ERRADO**

#### 💥 Impacto Direto na Metodologia
Este é um dos **principais causadores do problema reportado** de metodologia incorreta:
- Metodologias de aulas jornalísticas recebem linguagem literária
- Termos técnicos corretos são substituídos por termos inadequados
- O professor recebe um plano com terminologia errada para o tipo de aula

#### ✅ Solução Recomendada
```python
def detectar_perfil_pedagogico_real(tema: str, disciplina: str, texto_pdf: str = "") -> str:
    tema_norm = normalizar_para_busca(tema)
    disc_norm = normalizar_para_busca(disciplina)
    
    if "portuguesa" in disc_norm or "portugues" in disc_norm:
        # ... detecções específicas existentes ...
        
        # NOVO: Verificar também no texto do PDF antes do fallback
        texto_norm = normalizar_para_busca(texto_pdf or "")
        if any(t in texto_norm for t in ["noticia", "reportagem", "manchete", "lide", "jornalistico"]):
            return "jornalistico_valido"
        
        # Fallback mais conservador: não assumir literatura automaticamente
        return "geral_nao_jornalistica"  # Em vez de "literatura"
```

**Adicionalmente:** passar `texto_pdf` como parâmetro para `detectar_perfil_pedagogico_real()` em todos os pontos de chamada.

---

## 🟡 PROBLEMAS IMPORTANTES

### IMPORTANTE #4 — Validação de Palavras-Chave Silenciosamente Ignorada
**Arquivo:** `revisao_final.py` — linhas ~95–115  
*(Confirmado pela auditoria externa — auditoria1.docx, CRÍTICO #2)*

#### ❌ Problema
```python
palavras_chave_esperadas = aula.get("palavras_chave_esperadas") or []
if palavras_chave_esperadas:  # ← Só valida se a lista NÃO for vazia
    resultado_pc = validar_aderencia_palavras_chave(aula, palavras_chave_esperadas)
```

Se a extração de palavras-chave do DOCX auxiliar falhar silenciosamente em `contexto_aula_pdf.py`, a lista fica vazia e **nenhuma penalidade é aplicada**, mesmo que o PDF tenha palavras-chave destacadas.

#### ✅ Solução
```python
palavras_chave_esperadas = aula.get("palavras_chave_esperadas") or []
origem_metodologia = aula.get("origem_metodologia", "")
pdf_requer_validacao = "pdf" in origem_metodologia.lower()

if palavras_chave_esperadas:
    # Validação normal
    resultado_pc = validar_aderencia_palavras_chave(aula, palavras_chave_esperadas)
    # ... aplicar penalidades ...
elif pdf_requer_validacao and not palavras_chave_esperadas:
    # NOVO: Detectar ausência suspeita
    avisos.append("ATENÇÃO: Extração de palavras-chave falhou ou PDF não contém destaques. Verifique o material.")
    deducoes += 10  # Penalidade leve por incerteza
```

---

### IMPORTANTE #5 — `contexto_aula_pdf.py`: Falha Silenciosa na Extração de Palavras-Chave
**Arquivo:** `contexto_aula_pdf.py` — bloco de extração de palavras-chave — linhas ~180–220

#### ❌ Problema
```python
try:
    caminho_docx_aux = converter_pdf_para_docx_auxiliar(caminho_pdf, pasta_docx_aux)
    if caminho_docx_aux and caminho_docx_aux.exists():
        palavras_chave_esperadas = extrair_palavras_chave_docx(caminho_docx_aux)
    # ...
except Exception as exc:
    dependencias.logger.warning("Falha na conversão/extração de palavras-chave DOCX para %s: %s", ...)
    # palavras_chave_esperadas permanece [] — sem nenhuma indicação ao usuário
```

A falha é logada mas **não propagada ao plano gerado**. O campo `palavras_chave_esperadas` fica vazio sem que o sistema saiba se foi porque o PDF não tem destaques ou porque a conversão falhou.

#### ✅ Solução
```python
extracao_palavras_chave_ok = True
try:
    # ... extração ...
except Exception as exc:
    extracao_palavras_chave_ok = False
    dependencias.logger.warning(...)

# Retornar flag de status junto com o resultado
return {
    # ... campos existentes ...
    "palavras_chave_esperadas": palavras_chave_esperadas,
    "extracao_palavras_chave_ok": extracao_palavras_chave_ok,  # NOVO
}
```

---

### IMPORTANTE #6 — `DependenciasContextoAulaPDF`: Acoplamento Excessivo por Injeção de Dependências
**Arquivo:** `contexto_aula_pdf.py` — dataclass `DependenciasContextoAulaPDF`

#### ❌ Problema
O dataclass possui **26 campos do tipo `Callable`**, tornando a instanciação extremamente verbosa e frágil. Qualquer nova função adicionada ao pipeline exige atualização em todos os pontos de instanciação do dataclass.

```python
@dataclass
class DependenciasContextoAulaPDF:
    logger: Any
    extrair_texto_pdf_fn: Callable[[str], str]
    tema_por_texto_fn: Callable[[str, str, str], str]
    # ... 23 campos adicionais de Callable ...
```

#### 💥 Impacto
- Alta probabilidade de erro ao instanciar (argumento na posição errada)
- Dificulta testes unitários
- Qualquer refatoração de assinatura de função quebra silenciosamente

#### ✅ Solução
Agrupar dependências em sub-dataclasses por domínio:
```python
@dataclass
class DepsExtracao:
    extrair_texto_pdf_fn: Callable
    eh_cenario_piloto_pptx_fn: Callable
    encontrar_pptx_correspondente_fn: Callable
    extrair_estrutura_pptx_fn: Callable
    estrutura_pptx_para_dados_aula_fn: Callable

@dataclass
class DepsClassificacao:
    perfil_disciplina_fn: Callable
    detectar_tipo_aula_fn: Callable
    eh_cdp_contextual_disciplina_fn: Callable
    # ...

@dataclass
class DependenciasContextoAulaPDF:
    logger: Any
    extracao: DepsExtracao
    classificacao: DepsClassificacao
    # ...
```

---

### IMPORTANTE #7 — `higienizador_pedagogico.py`: Regras de Substituição Não Compiladas
**Arquivo:** `higienizador_pedagogico.py` — dicionário `REGRAS_SUBSTITUICAO`

#### ❌ Problema
O dicionário `REGRAS_SUBSTITUICAO` contém centenas de tuplas `(padrão_regex, substituição)` que são compiladas **a cada chamada** da função de higienização, em vez de serem pré-compiladas no carregamento do módulo:

```python
# Atual: compilação a cada chamada
for padrao, substituicao in REGRAS_SUBSTITUICAO[perfil]:
    texto = re.sub(padrao, substituicao, texto, flags=re.I)  # ← re.sub compila internamente
```

Com ~20 padrões por perfil e ~12 perfis, isso representa **240+ compilações de regex por aula gerada**.

#### ✅ Solução
```python
# No nível do módulo (executado uma vez no import):
_REGRAS_COMPILADAS: dict[str, list[tuple[re.Pattern, str]]] = {
    perfil: [
        (re.compile(padrao, re.I), substituicao)
        for padrao, substituicao in regras
    ]
    for perfil, regras in REGRAS_SUBSTITUICAO.items()
}

# Na função:
for padrao_compilado, substituicao in _REGRAS_COMPILADAS.get(perfil, []):
    texto = padrao_compilado.sub(substituicao, texto)
```

**Ganho estimado:** 30–50% de redução no tempo de higienização por aula.

---

### IMPORTANTE #8 — `PlanoCompleto`: Campo `metodologia` Aceita Tipos Mistos Sem Normalização Consistente
**Arquivo:** `models.py` — classe `PlanoCompleto`

#### ❌ Problema
```python
metodologia: list[EtapaMetodologia | str] = Field(default_factory=list)
```

O campo aceita tanto `EtapaMetodologia` (Pydantic) quanto `str` (legado). Isso força verificações `isinstance()` em **todo o código** que processa metodologia:

```python
# Padrão repetido em preencher.py, acompanhamento.py, validador_plano.py, etc.
for item in metodologia:
    if isinstance(item, dict):
        titulo = item.get("titulo", "")
        texto = item.get("texto", "")
    else:
        texto = str(item)
```

#### 💥 Impacto na Metodologia
Esta inconsistência é uma das causas de **etapas sendo perdidas ou mal formatadas** no documento final, pois diferentes módulos tratam o tipo misto de formas ligeiramente diferentes.

#### ✅ Solução
```python
# Adicionar validador Pydantic para normalizar na entrada:
from pydantic import field_validator

class PlanoCompleto(ModeloPlanoBase):
    metodologia: list[EtapaMetodologia] = Field(default_factory=list)
    
    @field_validator("metodologia", mode="before")
    @classmethod
    def normalizar_metodologia(cls, v):
        if not isinstance(v, list):
            return []
        resultado = []
        for item in v:
            if isinstance(item, str) and item.strip():
                resultado.append(EtapaMetodologia(titulo="", texto=item.strip()))
            elif isinstance(item, dict):
                resultado.append(EtapaMetodologia(**item))
            elif isinstance(item, EtapaMetodologia):
                resultado.append(item)
        return resultado
```

---

### IMPORTANTE #9 — `revisao_final.py`: `_regenerar_etapas_historia()` Limitada a Um Perfil
**Arquivo:** `revisao_final.py` — função `_regenerar_etapas_historia()`

#### ❌ Problema
A regeneração seletiva pós-validação existe **apenas para o perfil `"historia"`**. Todos os outros perfis (Matemática, Ciências, LP, etc.) que geram planos com `confidence_score < 70` simplesmente entregam o plano ruim sem tentativa de correção.

```python
if etapas_problematicas and perfil == "historia":  # ← Apenas história
    aula_corrigida = _regenerar_etapas_historia(aula, etapas_problematicas)
```

#### ✅ Solução
Criar um dispatcher genérico:
```python
_REGENERADORES_POR_PERFIL = {
    "historia": _regenerar_etapas_historia,
    # Adicionar conforme necessário:
    # "matematica": _regenerar_etapas_matematica,
    # "lingua_portuguesa_ef": _regenerar_etapas_lp,
}

regenerador = _REGENERADORES_POR_PERFIL.get(perfil)
if etapas_problematicas and regenerador:
    aula_corrigida = regenerador(aula, etapas_problematicas)
```

---

### IMPORTANTE #10 — Pipeline UI: Validação de Palavras-Chave Duplicada
**Arquivo:** `planos_luan_app_pipeline.txt` — trecho de revisão de aulas

#### ❌ Problema
A validação de aderência de palavras-chave é executada **duas vezes** na UI:
1. Para exibição do alerta ao usuário (antes da edição)
2. Para salvar no objeto `ae` (após a edição)

```python
# Execução 1: Para exibição
resultado_pc = validar_aderencia_palavras_chave(aula_temp, palavras_chave_esperadas)

# ... campos de edição ...

# Execução 2: Para salvar
resultado_pc_final = validar_aderencia_palavras_chave(ae, palavras_chave_esperadas)
```

A segunda execução é necessária (pois o usuário pode ter editado), mas a primeira poderia ser cacheada no `session_state` para evitar reprocessamento a cada re-render do Streamlit.

#### ✅ Solução
```python
cache_key = f"pc_result_{rev_tok}_{t_idx}_{a_idx}"
if cache_key not in st.session_state:
    st.session_state[cache_key] = validar_aderencia_palavras_chave(aula_temp, palavras_chave_esperadas)
resultado_pc = st.session_state[cache_key]
# Invalidar cache quando campos de edição mudarem
```

---

## 🟢 OPORTUNIDADES DE MELHORIA

### MELHORIA #11 — Causa Raiz do Problema de Metodologia: Pipeline Desconexo

#### 🔍 Diagnóstico do Problema Reportado
O sistema está gerando metodologia de forma incorreta. Com base na análise completa dos módulos, identificamos **4 pontos de falha encadeados** que explicam o problema:

```
PDF → ExtratorPDF → [PONTO 1: Extração fraca]
    → detectar_tipo_aula() → [PONTO 2: Tipo errado detectado]
    → MotorMetodologico.gerar() → [PONTO 3: Frases genéricas]
    → higienizador_pedagogico → [PONTO 4: Substituições incorretas]
    → revisar_metodologia() → [PONTO 5: Consolidação perde etapas]
```

**Ponto 1 — Extração fraca do PDF:**
- `ExtratorPDF._extrair_conceito()` usa apenas as primeiras 12 linhas
- Se o PDF tem cabeçalho longo (escola, professor, bimestre), o conceito real fica fora do range
- **Correção:** Aumentar `limite_linhas` para 20 e adicionar busca por seção "Foco no conteúdo"

**Ponto 2 — Tipo de aula detectado incorretamente:**
- `detectar_tipo_aula()` em `classificador.py` usa heurísticas de palavras-chave no texto completo
- PDFs com múltiplos tipos de atividade (ex: leitura + produção) podem ser classificados no tipo errado
- **Correção:** Priorizar a seção "Na prática" do PDF para detecção do tipo

**Ponto 3 — Frases genéricas na metodologia:**
- `_frases_por_contexto()` em `metodologia.py` tem fallbacks muito genéricos
- Quando o perfil não é reconhecido ou o tipo não tem frases específicas, usa base genérica
- **Correção:** Adicionar logging quando fallback genérico é usado, para identificar casos não cobertos

**Ponto 4 — Higienizador com fallback agressivo:**
- Descrito no CRÍTICO #3 acima

**Ponto 5 — `consolidar_quatro_etapas()` perde etapas específicas:**
```python
# Em qualidade_metodologica.py
def consolidar_quatro_etapas(metodologia: list[dict], tema: str = "") -> list[dict]:
    # Mapeia TODAS as etapas para apenas 4 canônicas
    # Etapas específicas como "Análise de caso", "Cálculos financeiros" são perdidas
```
Para perfis como Educação Financeira que têm etapas específicas, a consolidação em 4 etapas canônicas **destrói a estrutura pedagógica correta**.

**Correção urgente:**
```python
def consolidar_quatro_etapas(metodologia: list[dict], tema: str = "", perfil: str = "") -> list[dict]:
    # Perfis com etapas específicas não devem ser consolidados
    PERFIS_SEM_CONSOLIDACAO = {"educacao_financeira", "projeto_de_vida", "ingles"}
    if perfil in PERFIS_SEM_CONSOLIDACAO:
        return metodologia  # Retornar sem consolidar
    # ... lógica existente ...
```

---

### MELHORIA #12 — Adicionar Logging Estruturado ao Pipeline de Metodologia

#### 📋 Situação Atual
Não há logging suficiente para diagnosticar por que uma metodologia específica foi gerada de determinada forma. O campo `diagnostico_geracao` existe no `PlanoCompleto` mas não é populado consistentemente.

#### ✅ Implementação Recomendada
```python
# Em MotorMetodologico.gerar():
diagnostico = {
    "perfil_detectado": perfil,
    "tipo_detectado": tipo,
    "conceito_extraido": conceito,
    "recursos_detectados": recursos,
    "tecnicas_selecionadas": tecnicas,
    "etapas_configuradas": [t for t, _ in etapas_config],
    "frases_usadas_fallback": [],  # Registrar quando fallback genérico é usado
    "metodologia_local": metodologia,  # Antes da higienização
}
```

Isso permitiria usar o **Relatório Técnico** já existente na UI (tabs de pipeline) para diagnosticar problemas de metodologia.

---

### MELHORIA #13 — `lote.py` com 3146 Linhas: Decomposição Urgente

#### 📋 Situação Atual
`lote.py` é um orquestrador monolítico que mistura:
- Extração de título e conceito
- Detecção de tipo de aula
- Geração de metodologia fixa
- Integração com CDP contextual
- Lógica de Orientação de Estudos
- Integração com PPTX

#### ✅ Decomposição Sugerida
```
lote.py (orquestrador puro ~300 linhas)
├── core/extratores/titulo_extrator.py
├── core/extratores/conceito_extrator.py  
├── core/geradores/metodologia_fixa.py
├── core/integradores/cdp_integrador.py
└── core/integradores/pptx_integrador.py
```

---

### MELHORIA #14 — `qualidade_metodologica.py`: Separação de Responsabilidades

O arquivo com 1225 linhas deve ser dividido em:

| Novo Arquivo | Responsabilidade | Funções |
|---|---|---|
| `correcao_encoding.py` | Mojibake + ortografia | `corrigir_mojibake`, `corrigir_ortografia_basica` |
| `sanitizacao_metodologica.py` | Frases problemáticas + perfis | `sanitizar_texto_metodologico`, `sanitizar_texto_cdp_estrito` |
| `revisao_estrutural.py` | Consolidação + scoring | `revisar_metodologia`, `consolidar_quatro_etapas` |
| `naturalizacao.py` | Humanização do texto | `naturalizar_texto_metodologico` |

---

### MELHORIA #15 — Adicionar Testes Unitários para Funções Críticas

As seguintes funções não têm cobertura de testes visível e são críticas para a qualidade da metodologia:

| Função | Arquivo | Risco sem Teste |
|---|---|---|
| `_trecho_descartavel()` | `extrator_pdf.py` | Alto — falsos positivos descartam conteúdo válido |
| `detectar_perfil_pedagogico_real()` | `higienizador_pedagogico.py` | Alto — fallback errado contamina metodologia |
| `consolidar_quatro_etapas()` | `qualidade_metodologica.py` | Alto — perde etapas específicas |
| `calcular_aderencia_pdf()` | `validador_plano.py` | Médio — fuzzy matching pode ser impreciso |
| `_etapas_por_perfil()` | `metodologia.py` | Alto — tipo duplicado `pratica_oral` em LP EM |

**Exemplo de teste mínimo:**
```python
def test_higienizador_nao_substitui_noticia_em_aula_jornalistica():
    perfil = detectar_perfil_pedagogico_real(
        tema="Elementos da notícia jornalística",
        disciplina="Língua Portuguesa"
    )
    assert perfil == "jornalistico_valido", f"Esperado 'jornalistico_valido', obtido '{perfil}'"
```

---

### MELHORIA #16 — Dead Code: Bloco `elif perfil == "arte"` Duplicado

**Arquivo:** `metodologia.py` — linhas ~1650 e ~1670

```python
elif perfil == "arte":
    _frases_arte = _metodologia_arte(...)  # ← Primeiro bloco (executado)
    if _frases_arte is not None:
        base.update(_frases_arte)
        return base

# ... outros elif ...

elif perfil == "arte":  # ← DEAD CODE: nunca alcançado
    base["foco"] = (...)
    base["pratica"] = (...)
```

**Ação:** Remover o segundo bloco `elif perfil == "arte"` completamente.

---

### MELHORIA #17 — Dead Code: `pratica_oral` Duplicado em LP Ensino Médio

**Arquivo:** `metodologia.py` — função `_etapas_por_perfil()` — perfil `lingua_portuguesa_em`

```python
if tipo == "pratica_oral":
    return [("Relembre", "relembre"), ("Foco no conteúdo", "foco"), ...]  # ← Executado

if tipo == "pratica_oral":  # ← DEAD CODE: nunca alcançado
    return [("Relembre", "relembre"), ("Na prática", "pratica"), ...]
```

**Ação:** Remover o segundo bloco `if tipo == "pratica_oral"` e verificar qual estrutura de etapas é a correta para LP EM.

---

### MELHORIA #18 — Mojibake Residual em Strings Hardcoded

**Arquivo:** `acompanhamento.py` — tipo `futureme`

```python
# Atual (corrompido):
"sem buscar â€˜a resposta certaâ€™"

# Correto:
"sem buscar 'a resposta certa'"
```

**Ação:** Buscar e corrigir todas as ocorrências de `â€˜`, `â€™`, `â€œ`, `â€` no código-fonte.

```bash
# Comando para localizar:
grep -rn "â€" core/ --include="*.py"
```

---

### MELHORIA #19 — Cache de Extração de PDF Ausente

**Situação:** O mesmo PDF pode ser extraído múltiplas vezes (geração em lote, regeneração, revisão).

**Solução simples:**
```python
import functools

@functools.lru_cache(maxsize=128)
def extrair_texto_pdf_cached(caminho_pdf: str, hash_pdf: str) -> str:
    """Cache por hash garante invalidação quando o arquivo muda."""
    return extrair_texto_pdf(caminho_pdf)
```

**Ganho estimado:** 40–60% de redução no tempo de geração em lote para PDFs já processados.

---

## 📊 MATRIZ DE PRIORIZAÇÃO

| # | Problema | Severidade | Esforço | Impacto na Metodologia | Prioridade |
|---|---|---|---|---|---|
| 3 | Higienizador com fallback agressivo | 🔴 Crítico | Médio | **Direto** | 🥇 1ª |
| 11 | Pipeline desconexo (causa raiz) | 🔴 Crítico | Alto | **Direto** | 🥇 1ª |
| 8 | `metodologia` aceita tipos mistos | 🟡 Importante | Médio | **Direto** | 🥈 2ª |
| 1 | Penalização dupla de aderência | 🔴 Crítico | Baixo | Indireto | 🥈 2ª |
| 4 | Palavras-chave ignoradas silenciosamente | 🟡 Importante | Baixo | Indireto | 🥈 2ª |
| 5 | Falha silenciosa na extração | 🟡 Importante | Baixo | Indireto | 🥉 3ª |
| 16 | Dead code `arte` duplicado | 🟢 Melhoria | Baixo | Baixo | 🥉 3ª |
| 17 | Dead code `pratica_oral` duplicado | 🟢 Melhoria | Baixo | **Direto** | 🥉 3ª |
| 18 | Mojibake em strings hardcoded | 🟢 Melhoria | Baixo | Baixo | 🥉 3ª |
| 7 | Regras regex não compiladas | 🟡 Importante | Baixo | Performance | 4ª |
| 2 | Regeneração cíclica sem proteção | 🔴 Crítico | Médio | Indireto | 4ª |
| 9 | Regeneração só para história | 🟡 Importante | Médio | Indireto | 4ª |
| 6 | DependenciasContextoAulaPDF acoplado | 🟡 Importante | Alto | Manutenção | 5ª |
| 13 | `lote.py` monolítico | 🟢 Melhoria | Alto | Manutenção | 5ª |
| 14 | `qualidade_metodologica.py` monolítico | 🟢 Melhoria | Alto | Manutenção | 5ª |

---

## 🛠️ PLANO DE AÇÃO RECOMENDADO

### Sprint 1 — Correções Imediatas (1–3 dias)
1. **Corrigir fallback do higienizador** (`"literatura"` → `"geral_nao_jornalistica"`) — CRÍTICO #3
2. **Remover dead code** `elif perfil == "arte"` duplicado — MELHORIA #16
3. **Remover dead code** `pratica_oral` duplicado em LP EM — MELHORIA #17
4. **Corrigir mojibake** em strings hardcoded — MELHORIA #18
5. **Corrigir penalização dupla** de aderência ao PDF — CRÍTICO #1
6. **Adicionar parâmetro `perfil`** em `consolidar_quatro_etapas()` para não consolidar EF/PV/Inglês — MELHORIA #11

### Sprint 2 — Correções Estruturais (1–2 semanas)
7. **Normalizar `metodologia`** no Pydantic via `field_validator` — IMPORTANTE #8
8. **Pré-compilar regras regex** do higienizador — IMPORTANTE #7
9. **Adicionar flag `extracao_palavras_chave_ok`** no contexto — IMPORTANTE #5
10. **Implementar logging estruturado** no `MotorMetodologico` — MELHORIA #12
11. **Adicionar testes unitários** para funções críticas — MELHORIA #15

### Sprint 3 — Refatoração (2–4 semanas)
12. **Decompor `lote.py`** em módulos menores — MELHORIA #13
13. **Decompor `qualidade_metodologica.py`** — MELHORIA #14
14. **Refatorar `DependenciasContextoAulaPDF`** — IMPORTANTE #6
15. **Implementar cache de extração de PDF** — MELHORIA #19
16. **Expandir regeneração seletiva** para outros perfis — IMPORTANTE #9

---

## ✅ PONTOS POSITIVOS CONFIRMADOS

Apesar dos problemas identificados, o sistema possui fundamentos sólidos:

| Aspecto | Avaliação |
|---|---|
| Variação determinística (blake2b) | ✅ Excelente — reproduzível e sem aleatoriedade |
| Modelo Pydantic (`PlanoCompleto`) | ✅ Bem estruturado com `extra="allow"` e compatibilidade v1/v2 |
| SQLite WAL + migrações versionadas | ✅ Robusto para concorrência |
| Catálogo de técnicas Lemov | ✅ Abrangente e bem organizado |
| Fallback em camadas (acessibilidade/acompanhamento) | ✅ Resiliente |
| Sanitização CDP/EJA estrita | ✅ Correta e necessária |
| Diagnóstico de geração na UI (tabs de pipeline) | ✅ Excelente para debugging |
| `gravar_sidecar_json()` com SHA-256 | ✅ Integridade de cache garantida |

---

*Auditoria gerada em 2026-07-08 | Sistema: Planos Luan v1.2.10*