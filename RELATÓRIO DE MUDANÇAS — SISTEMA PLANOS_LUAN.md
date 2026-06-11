# RELATÓRIO DE MUDANÇAS — SISTEMA PLANOS_LUAN
## Documento para Agente de Código (Codex / Gemini)

**Data de geração:** 2026-06-06  
**Baseado em:** Auditoria técnica completa do código-fonte  
**Objetivo:** Instruções precisas de refatoração, correção de bugs e melhorias graduais  
**Ordem de execução:** Seguir exatamente a ordem dos blocos. Cada bloco é independente.

---

## INSTRUÇÕES GERAIS PARA O AGENTE

1. Não reescrever arquivos inteiros — fazer apenas as mudanças descritas em cada bloco
2. Preservar toda lógica existente que não seja mencionada
3. Após cada mudança, verificar se os imports ainda estão corretos
4. Não alterar nomes de funções públicas já existentes (podem ser usadas em outros módulos)
5. Manter o estilo de código existente (aspas duplas, f-strings, type hints)

---

# PARTE 1 — BUGS CRÍTICOS (PRIORIDADE MÁXIMA)
## Executar primeiro. Afetam o output de todos os planos gerados hoje.

---

## BUG-01: Títulos de metodologia perdem acento no DOCX

**Arquivo:** `docx_generator/preencher.py`  
**Severidade:** Alta — afeta todos os planos gerados  
**Problema:** A função `_preencher_celula_metodologia()` chama `_remover_acentos()` no título antes de colocá-lo em negrito, fazendo "Para começar:" virar "Para comecar:" no documento final.

**Localizar este trecho (aproximadamente linha 551):**
```python
match = re.match(r'^([^:]{2,35}):\s*(.*)$', linha)
if match:
    titulo_bold = _remover_acentos(match.group(1)) + ":"
    resto_texto = " " + match.group(2)
    _aplicar_fonte(paragrafo_atual.add_run(titulo_bold), tamanho=tamanho, bold=True)
    _adicionar_texto_com_destaques_formatado(paragrafo_atual, resto_texto, tamanho=tamanho)
```

**Substituir por:**
```python
match = re.match(r'^([^:]{2,60}):\s*(.*)$', linha)
if match:
    titulo_bold = match.group(1) + ":"
    resto_texto = " " + match.group(2)
    _aplicar_fonte(paragrafo_atual.add_run(titulo_bold), tamanho=tamanho, bold=True)
    _adicionar_texto_com_destaques_formatado(paragrafo_atual, resto_texto, tamanho=tamanho)
```

**O que mudou:**
- Removida a chamada `_remover_acentos()` no título (acentos são válidos no DOCX)
- Limite do regex aumentado de `{2,35}` para `{2,60}` para cobrir títulos mais longos como "Disparo inicial / contextualização"

**Verificar após a mudança:**
- Gerar um plano de teste e confirmar que "Para começar:", "Foco no conteúdo:", "Na prática:" aparecem com acento e em negrito no DOCX

---

## BUG-02: Mês hardcoded no nome do arquivo de plano

**Arquivo:** `core/professores_planos.py`  
**Severidade:** Alta — todos os arquivos são nomeados "PLANO_JUNHO" independente do mês real  
**Problema:** A função `nome_padronizado_plano()` tem "JUNHO" fixo no código.

**Localizar este trecho:**
```python
def nome_padronizado_plano(disciplina: str, turma: str) -> str:
    return f"PLANO_JUNHO - {_safe_filename_part(disciplina)} - {_safe_filename_part(turma)}.docx"
```

**Substituir por:**
```python
def nome_padronizado_plano(disciplina: str, turma: str, mes: str = "") -> str:
    from datetime import date
    MESES_ABREV = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARCO", 4: "ABRIL",
        5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
        9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO",
    }
    if mes:
        mes_upper = mes.strip().upper()
    else:
        mes_upper = MESES_ABREV.get(date.today().month, "MES")
    return f"PLANO_{mes_upper} - {_safe_filename_part(disciplina)} - {_safe_filename_part(turma)}.docx"
```

**Verificar após a mudança:**
- Chamar `nome_padronizado_plano("Matemática", "7º ANO A")` sem parâmetro `mes` e confirmar que retorna o mês atual
- Chamar `nome_padronizado_plano("Matemática", "7º ANO A", mes="AGOSTO")` e confirmar que retorna "PLANO_AGOSTO - ..."

---

## BUG-03: Função duplicada em cdp_legacy.py

**Arquivo:** `core/cdp_legacy.py`  
**Severidade:** Alta — a primeira versão da função é silenciosamente sobrescrita pela segunda, causando comportamento imprevisível durante manutenção  
**Problema:** A função `_metodologia_cdp_por_modelo()` aparece duas vezes no mesmo arquivo. A segunda versão (com etapas mais descritivas) é a correta.

**Ação:**
1. Localizar a PRIMEIRA ocorrência de `def _metodologia_cdp_por_modelo(` no arquivo
2. Identificar onde ela termina (antes da segunda ocorrência da mesma função)
3. Remover completamente o bloco da primeira ocorrência (incluindo o `def` e todo o corpo da função)
4. Manter intacta a segunda ocorrência (que tem etapas como "Abertura (acolhimento e ativacao de saberes previos)")

**Como identificar qual é a primeira:**
- A primeira versão tem etapas simples como `"1. Abertura: iniciar com uma conversa breve..."`
- A segunda versão tem etapas detalhadas como `"1. Abertura (acolhimento e ativacao de saberes previos): iniciar com uma conversa simples e acolhedora..."`
- Manter a segunda (mais detalhada), remover a primeira (mais simples)

**Verificar após a mudança:**
- Confirmar que o arquivo tem exatamente UMA definição de `_metodologia_cdp_por_modelo`
- Executar `python -c "from core.cdp_legacy import _metodologia_cdp_por_modelo; print('OK')"` sem erro

---

## BUG-04: Falha silenciosa quando planilha CDP não é encontrada

**Arquivo:** `core/cdp_legacy.py`  
**Severidade:** Média-Alta — o sistema gera planos CDP vazios sem avisar o usuário  
**Problema:** Quando `PLANILHA_CDP` não existe, `carregar_planilha_cdp()` retorna `{}` silenciosamente. O usuário não sabe que o plano foi gerado sem dados reais.

**Localizar a função:**
```python
@lru_cache(maxsize=1)
def carregar_planilha_cdp() -> Dict[str, List[Dict[str, str]]]:
    if not PLANILHA_CDP.exists():
        return {}
    ...
```

**Substituir por:**
```python
@lru_cache(maxsize=1)
def carregar_planilha_cdp() -> Dict[str, List[Dict[str, str]]]:
    if not PLANILHA_CDP.exists():
        import logging
        logging.getLogger(__name__).error(
            f"PLANILHA CDP NÃO ENCONTRADA: {PLANILHA_CDP}. "
            "O plano CDP será gerado sem dados de habilidades. "
            "Verifique se o arquivo existe no caminho correto."
        )
        return {}
    ...
```

**Localizar também a função `carregar_planilha_cdp_multisseriada()` e aplicar o mesmo padrão:**
```python
@lru_cache(maxsize=1)
def carregar_planilha_cdp_multisseriada() -> Dict[str, List[Dict[str, str]]]:
    if not PLANILHA_CDP_MULTISSERIADA.exists():
        import logging
        logging.getLogger(__name__).error(
            f"PLANILHA CDP MULTISSERIADA NÃO ENCONTRADA: {PLANILHA_CDP_MULTISSERIADA}. "
            "O plano será gerado sem dados de habilidades multisseriadas."
        )
        return {}
    ...
```

**Adicionalmente — adicionar aviso na UI do Streamlit:**

**Arquivo:** `planos_luan_app.py`  
Localizar o trecho onde o modo CDP é ativado (onde `eh_cdp(disciplina)` é verificado antes de gerar o plano). Adicionar antes da geração:

```python
# Verificar disponibilidade das planilhas CDP
from core.cdp_legacy import PLANILHA_CDP, PLANILHA_CDP_MULTISSERIADA
if eh_cdp(disciplina) and not PLANILHA_CDP.exists():
    st.warning(
        f"⚠️ Planilha CDP não encontrada em: `{PLANILHA_CDP}`. "
        "O plano será gerado sem habilidades específicas. "
        "Verifique se o arquivo PLANILHACDP.xlsx está na pasta correta."
    )
```

---

## BUG-05: sanitizar_texto_pedagogico() pode truncar frases

**Arquivo:** `core/lib/gerador_colunas_pedagogicas.py`  
**Severidade:** Média — pode gerar frases sem sentido como "Conduzir a leitura da sobre..."  
**Problema:** A função remove "ensino medio" e "aula N" de qualquer posição na frase, inclusive do meio.

**Localizar:**
```python
def sanitizar_texto_pedagogico(txt: str) -> str:
    txt = clean(txt)
    txt = txt.replace("..", ".")
    txt = re.sub(r"\s+,", ",", txt)
    txt = re.sub(r"\s+\.", ".", txt)
    txt = re.sub(r"\b2o bimestre\b", "", txt, flags=re.I)
    txt = re.sub(r"\bensino medio\b", "", txt, flags=re.I)
    txt = re.sub(r"\baula \d+\b", "", txt, flags=re.I)
    txt = txt.strip(" -:;,")
    txt = clean(txt)
    return sentenca(txt)
```

**Substituir por:**
```python
def sanitizar_texto_pedagogico(txt: str) -> str:
    txt = clean(txt)
    txt = txt.replace("..", ".")
    txt = re.sub(r"\s+,", ",", txt)
    txt = re.sub(r"\s+\.", ".", txt)
    # Remover apenas quando o termo está no início ou fim da frase,
    # ou isolado entre vírgulas/pontos — nunca no meio de uma frase
    txt = re.sub(r"(?:^|\.\s+)2o bimestre\b", "", txt, flags=re.I)
    txt = re.sub(r"(?:^|\.\s+)ensino medio\b", "", txt, flags=re.I)
    # "aula N" pode ser removido com segurança pois é sempre referência isolada
    txt = re.sub(r"\baula \d+\b\s*[-:–]?\s*", "", txt, flags=re.I)
    txt = txt.strip(" -:;,")
    txt = clean(txt)
    return sentenca(txt)
```

---

# PARTE 2 — REFATORAÇÃO DE MÉDIO PRAZO
## Executar após a Parte 1. Reduzem acoplamento e facilitam manutenção futura.

---

## REF-01: Tornar públicas as funções compartilhadas entre lote.py e cdp_em_docx.py

**Problema:** `core/cdp_em_docx.py` importa funções com prefixo `_` (privadas por convenção) de `core/lote.py`. Isso cria acoplamento frágil.

**Arquivo:** `core/lote.py`  
**Ação:** Localizar as seguintes funções e remover o prefixo `_` do nome:
- `_acessibilidade_cdp_contextual` → renomear para `acessibilidade_cdp_contextual`
- `_acompanhamento_cdp_contextual` → renomear para `acompanhamento_cdp_contextual`
- `_metodologia_cdp_contextual` → renomear para `metodologia_cdp_contextual`
- `_perfil_disciplina` → renomear para `perfil_disciplina`
- `_normalizar` → renomear para `normalizar_texto_lote` (para não conflitar com outras funções `normalizar` no projeto)
- `_limpar_tema_cdp_contextual` → renomear para `limpar_tema_cdp_contextual`
- `_formatar_material_cdp_contextual` → renomear para `formatar_material_cdp_contextual`

**Atenção:** Após renomear em `lote.py`, atualizar TODAS as chamadas internas dentro do próprio `lote.py` que usam os nomes antigos.

**Arquivo:** `core/cdp_em_docx.py`  
**Ação:** Atualizar o bloco de imports para usar os novos nomes públicos:

```python
# Substituir o import atual:
from core.lote import (
    _acessibilidade_cdp_contextual,
    _acompanhamento_cdp_contextual,
    _formatar_material_cdp_contextual,
    _limpar_tema_cdp_contextual,
    _metodologia_cdp_contextual,
    _normalizar,
    _perfil_disciplina,
)

# Por:
from core.lote import (
    acessibilidade_cdp_contextual,
    acompanhamento_cdp_contextual,
    formatar_material_cdp_contextual,
    limpar_tema_cdp_contextual,
    metodologia_cdp_contextual,
    normalizar_texto_lote,
    perfil_disciplina,
)
```

**Atualizar também** todas as chamadas dentro de `cdp_em_docx.py` que usam os nomes antigos com `_`.

**Verificar após a mudança:**
```bash
python -c "from core.cdp_em_docx import reescrever_docx_cdp_ensino_medio; print('OK')"
python -c "from core.lote import acessibilidade_cdp_contextual, metodologia_cdp_contextual; print('OK')"
```

---

## REF-02: Criar core/normalizacao.py com implementação canônica

**Problema:** Existem pelo menos 5 implementações diferentes de "remover acentos e normalizar espaços" espalhadas pelo projeto, cada uma com pequenas diferenças que causam inconsistências.

**Ação 1 — Criar novo arquivo `core/normalizacao.py`:**

```python
"""
Funções canônicas de normalização de texto para o sistema PLANOS_LUAN.
Todas as outras implementações de normalização devem importar daqui.
"""
from __future__ import annotations

import re
import unicodedata


def normalizar(
    texto: str,
    remover_pontuacao: bool = True,
    lower: bool = True,
) -> str:
    """
    Remove acentos, normaliza espaços e opcionalmente remove pontuação.
    
    Esta é a implementação canônica. Use esta função em vez de implementações
    locais em outros módulos.
    
    Args:
        texto: Texto a normalizar
        remover_pontuacao: Se True, remove pontuação (padrão: True)
        lower: Se True, converte para minúsculas (padrão: True)
    
    Returns:
        Texto normalizado
    """
    resultado = unicodedata.normalize("NFKD", str(texto or ""))
    resultado = "".join(ch for ch in resultado if not unicodedata.combining(ch))
    if remover_pontuacao:
        resultado = re.sub(r"[^\w\s]", " ", resultado, flags=re.UNICODE)
    resultado = re.sub(r"\s+", " ", resultado).strip()
    if lower:
        resultado = resultado.lower()
    return resultado


def normalizar_upper(texto: str) -> str:
    """Normaliza e converte para maiúsculas. Atalho para normalizar(lower=False).upper()"""
    return normalizar(texto, lower=False).upper()


def normalizar_preservar_pontuacao(texto: str) -> str:
    """Normaliza sem remover pontuação. Útil para textos pedagógicos."""
    return normalizar(texto, remover_pontuacao=False)
```

**Ação 2 — Atualizar imports gradualmente (não precisa fazer tudo de uma vez):**

Nos arquivos abaixo, quando for fazer qualquer outra modificação, substituir a função local de normalização pela importação canônica:

- `core/lib/extrator_pdf.py`: substituir `normalizar_texto()` local por `from core.normalizacao import normalizar`
- `core/lib/gerador_colunas_pedagogicas.py`: substituir `norm()` local por `from core.normalizacao import normalizar`
- `core/lib/classificador.py`: a função `normalizar_texto()` existente pode ser mantida por ora (é importada por outros módulos), mas adicionar no topo: `# TODO: migrar para core.normalizacao.normalizar`

**Verificar após criar o arquivo:**
```bash
python -c "from core.normalizacao import normalizar, normalizar_upper; print(normalizar('Ação Pedagógica')); print(normalizar_upper('ção'))"
# Esperado: "acao pedagogica" e "CAO"
```

---

## REF-03: Extrair constantes de domínio de planos_luan_app.py

**Problema:** Constantes de domínio pedagógico estão misturadas com código de UI no arquivo principal do app.

**Ação — Criar `core/constantes.py`:**

```python
"""
Constantes de domínio do sistema PLANOS_LUAN.
Separadas do arquivo de UI para facilitar reutilização e testes.
"""

HORARIOS_AULA = [
    ("07h", "1ª aula"),
    ("07h50", "2ª aula"),
    ("08h40", "3ª aula"),
    ("09h50", "4ª aula"),
    ("10h40", "5ª aula"),
    ("11h30", "6ª aula"),
    ("13h", "1ª aula"),
    ("13h50", "2ª aula"),
    ("14h40", "3ª aula"),
    ("15h50", "4ª aula"),
    ("16h40", "5ª aula"),
    ("17h30", "6ª aula"),
    ("19h", "1ª aula"),
    ("19h45", "2ª aula"),
    ("20h30", "3ª aula"),
    ("21h30", "4ª aula"),
    ("22h15", "5ª aula"),
    # Duplas — manhã
    ("07h - 08h40", "1ª e 2ª aula"),
    ("07h50 - 09h50", "2ª e 3ª aula"),
    ("08h40 - 10h40", "3ª e 4ª aula"),
    ("09h50 - 11h30", "4ª e 5ª aula"),
    ("10h40 - 12h20", "5ª e 6ª aula"),
    # Duplas — tarde
    ("13h - 14h40", "1ª e 2ª aula"),
    ("13h50 - 15h50", "2ª e 3ª aula"),
    ("14h40 - 16h40", "3ª e 4ª aula"),
    ("15h50 - 17h30", "4ª e 5ª aula"),
    ("16h40 - 18h20", "5ª e 6ª aula"),
    # Duplas — noite
    ("19h - 20h30", "1ª e 2ª aula"),
    ("19h45 - 21h30", "2ª e 3ª aula"),
    ("20h30 - 22h15", "3ª e 4ª aula"),
    ("21h30 - 23h", "4ª e 5ª aula"),
    # Alternadas
    ("07h - 10h40", "1ª e 4ª aula"),
    ("13h - 16h40", "1ª e 4ª aula"),
    ("08h40 - 11h30", "3ª e 6ª aula"),
    ("14h40 - 17h30", "3ª e 6ª aula"),
    ("07h50 - 10h40", "2ª e 5ª aula"),
    ("13h50 - 16h40", "2ª e 5ª aula"),
    ("07h50 - 11h30", "2ª e 6ª aula"),
    ("13h50 - 17h30", "2ª e 6ª aula"),
    ("19h - 21h30", "1ª e 4ª aula"),
    ("19h45 - 22h15", "2ª e 5ª aula"),
]

HORARIOS_SIMPLES = HORARIOS_AULA[:17]
HORARIOS_DUPLAS = HORARIOS_AULA[17:]

TURNOS_HORARIOS = {
    "Manhã": ["07h", "07h50", "08h40", "09h50", "10h40", "11h30", "12h20"],
    "Tarde": ["13h", "13h50", "14h40", "15h50", "16h40", "17h30", "18h20"],
    "Noite": ["19h", "19h45", "20h30", "21h30", "22h15", "23h"],
}

MESES = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]

DIAS_SEMANA_CADASTRO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

AULAS_SEMANA_OPCOES = ["(selecione)"] + [str(i) for i in range(1, 26)]

EXTENSAO_MES_OPCOES = [
    "Somente o mês",
    "Completar a última semana",
    "Completar a última semana + 1 semana",
    "Completar a última semana + 2 semanas",
]

EXTENSAO_MES_VALORES = {
    "Somente o mês": 0,
    "Completar a última semana": 1,
    "Completar a última semana + 1 semana": 2,
    "Completar a última semana + 2 semanas": 3,
}
```

**Ação — Atualizar `planos_luan_app.py`:**

No topo do arquivo, adicionar o import:
```python
from core.constantes import (
    HORARIOS_AULA,
    HORARIOS_SIMPLES,
    HORARIOS_DUPLAS,
    TURNOS_HORARIOS,
    MESES,
    DIAS_SEMANA_CADASTRO,
    AULAS_SEMANA_OPCOES,
    EXTENSAO_MES_OPCOES,
    EXTENSAO_MES_VALORES,
)
```

Remover de `planos_luan_app.py` as definições locais dessas constantes (os blocos `HORARIOS_AULA = [...]`, `MESES = [...]`, `TURNOS_HORARIOS = {...}`, `AULAS_SEMANA_OPCOES = [...]`, `EXTENSAO_MES_OPCOES = [...]`).

Substituir a função `_valor_extensao_mes()` em `planos_luan_app.py`:
```python
# Remover esta função:
def _valor_extensao_mes(rotulo: str) -> int:
    mapa = { ... }
    return mapa.get(rotulo, 0)

# E substituir todas as chamadas por:
EXTENSAO_MES_VALORES.get(rotulo, 0)
```

---

## REF-04: Refatorar classificar_perfil() para tabela de regras

**Arquivo:** `core/lib/gerador_colunas_pedagogicas.py`  
**Problema:** A função `classificar_perfil()` tem 60+ variáveis booleanas locais e 20+ ramos `if/elif`. Cada nova disciplina adiciona mais complexidade.

**Ação — Substituir a função por uma baseada em tabela de regras:**

Antes da função `classificar_perfil()`, adicionar a tabela de regras:

```python
# Tabela de regras de perfil: (nome_perfil, lista_de_termos)
# Ordem importa: primeira regra que casar vence
_REGRAS_PERFIL_LP = [
    ("texto_publicitario", [
        "anuncie aqui", "anuncio publicitario", "anúncio publicitário",
        "propaganda", "publicidade", "slogan", "jingle",
        "campanha publicitaria", "campanha publicitária",
        "advergame", "unboxing", "social advertising",
    ]),
    ("biografia", [
        "historia de uma vida", "história de uma vida",
        "biografia", "trajetoria", "trajetória",
        "vida de", "carreira", "nascimento",
        "mapa conceitual", "lygia fagundes telles",
    ]),
    ("noticia_multimodal", [
        "jornalismo em imagens", "fotojornalismo",
        "fotojornalistico", "fotojornalístico",
        "recursos visuais em textos jornalisticos",
        "recursos visuais em textos jornalísticos",
        "textos jornalisticos digitais",
        "textos jornalísticos digitais",
        "fotos e videos", "fotos e vídeos",
        "intencionalidade das imagens",
    ]),
    ("conto_distopico", [
        "conto distopico", "conto distópico",
        "narrativa distopica", "narrativa distópica",
        "distopia", "distopico", "distópico",
        "olhos por bugalhos",
        "uma narrativa pode moldar uma imagem",
    ]),
    ("literatura_prosa", [
        "prosa de 30", "prosa regionalista",
        "romance regionalista", "sertao", "sertão",
        "seca", "retirantes", "o quinze", "vidas secas",
        "capitaes da areia", "capitães da areia",
        "rachel de queiroz", "graciliano ramos", "jorge amado",
    ]),
    ("literatura_modernismo", [
        "semana de arte moderna", "vanguardas europeias",
        "vanguardas", "modernismo", "modernista",
        "mario de andrade", "mário de andrade",
        "oswald de andrade", "drummond", "murilo mendes",
        "manuel bandeira", "manifesto literario", "manifesto literário",
    ]),
    ("poema", [
        "poema", "soneto", "verso", "estrofe",
        "eu lirico", "eu lírico", "rima", "metrica", "métrica",
        "carpe diem", "fugere urbem",
    ]),
    ("cronica", ["cronica", "crônica", "genero cronica", "gênero crônica"]),
    ("editorial_argumentativo", ["editorial", "editoriais", "texto opinativo"]),
    ("artigo_opiniao", [
        "artigo de opiniao", "artigo de opinião",
        "construcao da opiniao", "construção da opinião",
        "tese", "argumentos", "posicionamento",
        "ponto de vista", "persuadir",
    ]),
    ("oralidade_entrevista", [
        "oralidade", "entrevista oral", "entrevista",
        "turnos de fala", "marcas de oralidade",
        "transcricao", "transcrição",
        "variacao linguistica", "variação linguística", "podcast",
    ]),
    ("texto_normativo", [
        "estatuto da pessoa idosa", "constituicao federal",
        "constituição federal", "texto normativo",
        "textos legais", "texto legal", "normas", "direitos assegurados",
    ]),
    ("gramatica_analise_linguistica", [
        "ordem direta", "ordem inversa", "hiperbato", "hipérbato",
        "conjuncoes", "conjunções", "regencia verbal", "regência verbal",
        "regencia nominal", "regência nominal",
        "oracoes subordinadas", "orações subordinadas",
        "modalizacao", "modalização",
        "analise sintatica", "análise sintática",
    ]),
]
```

Substituir a função `classificar_perfil()` por:

```python
def classificar_perfil(
    texto: str,
    titulo: str,
    conteudos: List[str],
    objetivos: List[str],
    blocos: Dict[str, str],
) -> str:
    """
    Classifica o perfil pedagógico da aula com base no conteúdo do PDF.
    Usa tabela de regras em ordem de prioridade.
    """
    base = " ".join([texto, titulo] + conteudos + objetivos)
    n = norm(base)

    # Verificar regras em ordem de prioridade
    for perfil, termos in _REGRAS_PERFIL_LP:
        if any(norm(termo) in n for termo in termos):
            return perfil

    # Regras compostas que dependem de múltiplos sinais
    tem_noticia = any(norm(p) in n for p in PALAVRAS_NOTICIA)
    tem_imagem = any(norm(p) in n for p in PALAVRAS_IMAGEM)
    tem_mapa = any(norm(p) in n for p in PALAVRAS_MAPA)
    tem_comparacao = any(norm(p) in n for p in PALAVRAS_COMPARACAO)
    tem_grafico = any(norm(p) in n for p in PALAVRAS_GRAFICO)
    tem_xenofobia = "xenofobia" in n
    tem_refugiado = "refugiado" in n or "refugiados" in n
    tem_migracao_legal_ilegal = "migracao legal e ilegal" in n or (
        "migrante legal" in n and "migrante ilegal" in n
    )
    tem_estado = any(t in n for t in [
        "estado", "documentos internacionais", "direitos",
        "restricoes", "restrições", "soberania", "fronteiras",
    ])

    if tem_xenofobia and tem_noticia:
        return "noticia_leitura_critica"
    if tem_migracao_legal_ilegal and (tem_imagem or "virem e conversem" in n) and tem_estado:
        return "imagem_debate_direitos"
    if tem_refugiado and tem_comparacao:
        return "comparacao_conceitual"
    if tem_mapa and "migracao" in n:
        return "mapa_fluxos_migratorios"
    if tem_grafico and tem_refugiado:
        return "grafico_fluxos_refugiados"
    if tem_comparacao:
        return "comparacao_conceitual"
    if tem_noticia:
        return "noticia_leitura_critica"
    if tem_imagem:
        return "imagem_debate"
    if "construindo o conceito" in n or blocos.get("Construindo o conceito"):
        return "conceito_reflexivo"

    return "geral"
```

**Verificar após a mudança:**
- Executar os testes existentes em `tests/test_gerador_colunas_pedagogicas.py`
- Confirmar que os perfis retornados são idênticos aos da versão anterior para os casos de teste existentes

---

# PARTE 3 — MELHORIAS DE QUALIDADE TEXTUAL

---

## QT-01: Adicionar validação de frases truncadas pós-geração

**Arquivo:** `core/lib/gerador_colunas_pedagogicas.py`  
**Problema:** Frases geradas podem terminar com preposição ou artigo, indicando truncamento.

**Adicionar esta função após `sanitizar_texto_pedagogico()`:**

```python
_FINAIS_INVALIDOS_FRASE = frozenset({
    "a", "as", "o", "os", "um", "uma",
    "de", "da", "do", "das", "dos",
    "em", "e", "com", "para", "por",
    "que", "se", "na", "no", "nas", "nos",
    "ao", "aos", "à", "às",
})


def validar_frase_completa(texto: str) -> bool:
    """
    Verifica se uma frase parece completa (não termina com preposição ou artigo).
    Retorna True se a frase parece completa, False se parece truncada.
    """
    texto = clean(texto).rstrip(".!?")
    if not texto:
        return False
    ultima_palavra = texto.split()[-1].lower().rstrip(".,;:")
    return ultima_palavra not in _FINAIS_INVALIDOS_FRASE


def sanitizar_e_validar(txt: str, fallback: str = "") -> str:
    """
    Sanitiza o texto pedagógico e verifica se está completo.
    Se truncado, retorna o fallback.
    """
    resultado = sanitizar_texto_pedagogico(txt)
    if not validar_frase_completa(resultado):
        return sanitizar_texto_pedagogico(fallback) if fallback else resultado
    return resultado
```

---

## QT-02: Corrigir _substituir_texto() para preservar formatação do parágrafo

**Arquivo:** `docx_generator/preencher.py`  
**Problema:** A substituição de placeholders limpa o parágrafo inteiro, perdendo formatação (negrito, cor, tamanho de fonte) definida no template.

**Localizar:**
```python
def _substituir_texto(paragraph, substituicoes: dict[str, str]) -> None:
    if not paragraph.runs:
        return
    texto_original = paragraph.text
    texto_novo = texto_original
    for chave, valor in substituicoes.items():
        texto_novo = texto_novo.replace(chave, _sanitizar_texto_xml(valor))
    if texto_novo == texto_original:
        return
    paragraph.clear()
    paragraph.add_run(_sanitizar_texto_xml(texto_novo))
```

**Substituir por:**
```python
def _substituir_texto(paragraph, substituicoes: dict[str, str]) -> None:
    """
    Substitui placeholders preservando a formatação do primeiro run.
    Se o parágrafo tem apenas um run, preserva fonte, tamanho, negrito e cor.
    """
    if not paragraph.runs:
        return
    texto_original = paragraph.text
    texto_novo = texto_original
    for chave, valor in substituicoes.items():
        texto_novo = texto_novo.replace(chave, _sanitizar_texto_xml(valor))
    if texto_novo == texto_original:
        return

    # Preservar formatação do primeiro run antes de limpar
    primeiro_run = paragraph.runs[0]
    fonte_nome = primeiro_run.font.name
    fonte_tamanho = primeiro_run.font.size
    fonte_bold = primeiro_run.bold
    fonte_cor = primeiro_run.font.color.rgb if primeiro_run.font.color and primeiro_run.font.color.type else None

    paragraph.clear()
    novo_run = paragraph.add_run(_sanitizar_texto_xml(texto_novo))

    # Restaurar formatação
    if fonte_nome:
        novo_run.font.name = fonte_nome
    if fonte_tamanho:
        novo_run.font.size = fonte_tamanho
    if fonte_bold is not None:
        novo_run.bold = fonte_bold
    if fonte_cor is not None:
        novo_run.font.color.rgb = fonte_cor
```

---

# PARTE 4 — VERIFICAÇÕES FINAIS

## Após aplicar todas as mudanças, executar:

```bash
# 1. Verificar imports sem erros
python -c "import planos_luan_app; print('app OK')"
python -c "from core.cdp_em_docx import reescrever_docx_cdp_ensino_medio; print('cdp_em_docx OK')"
python -c "from core.lote import processar_varios_pdfs; print('lote OK')"
python -c "from docx_generator.preencher import preencher_documento; print('preencher OK')"
python -c "from docx_generator.preencher_cdp import preencher_documento_cdp; print('preencher_cdp OK')"

# 2. Executar suite de testes existente
python -m pytest tests/ -v

# 3. Verificar que não há mais funções duplicadas
grep -n "def _metodologia_cdp_por_modelo" core/cdp_legacy.py
# Esperado: exatamente 1 resultado

# 4. Verificar que _remover_acentos não é mais chamado em títulos
grep -n "_remover_acentos" docx_generator/preencher.py
# Esperado: apenas a definição da função, não chamadas em _preencher_celula_metodologia

# 5. Verificar que constantes foram movidas
python -c "from core.constantes import HORARIOS_AULA, MESES; print(f'Horários: {len(HORARIOS_AULA)}, Meses: {len(MESES)}')"
# Esperado: Horários: 41, Meses: 12
```

---

## RESUMO DE ARQUIVOS MODIFICADOS

| Arquivo | Tipo de mudança | Bloco(s) |
|---|---|---|
| `docx_generator/preencher.py` | Bug fix + melhoria | BUG-01, QT-02 |
| `core/professores_planos.py` | Bug fix | BUG-02 |
| `core/cdp_legacy.py` | Bug fix + log | BUG-03, BUG-04 |
| `planos_luan_app.py` | Aviso UI + remoção de constantes | BUG-04, REF-03 |
| `core/lib/gerador_colunas_pedagogicas.py` | Bug fix + refatoração + qualidade | BUG-05, REF-04, QT-01 |
| `core/lote.py` | Tornar funções públicas | REF-01 |
| `core/cdp_em_docx.py` | Atualizar imports | REF-01 |
| `core/normalizacao.py` | **NOVO ARQUIVO** | REF-02 |
| `core/constantes.py` | **NOVO ARQUIVO** | REF-03 |

## ARQUIVOS QUE NÃO DEVEM SER TOCADOS

- `core/calendario.py` — perfeito, não alterar
- `core/database.py` — sólido, não alterar
- `core/helpers.py` — correto, não alterar
- `core/modelos_docx.py` — simples e funcional, não alterar
- `core/ae_priorizado.py` — bem estruturado, não alterar
- `core/disciplinas.py` — limpo, não alterar