#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análise Metodológica de PDFs para auditoria pedagógica.
Extrai conteúdo real de cada PDF e classifica recursos presentes.
"""

import pdfplumber
import os
import json
import sys
import re
from pathlib import Path
from collections import defaultdict

# Caminho base dos PDFs
PDF_BASE = r"D:\PDF novos"

# Palavras-chave para detecção de recursos
RECURSOS_KEYWORDS = {
    "noticia": [
        "notícia", "manchete", "lide", "lead", "jornalístico", 
        "jornal", "reportagem", "fato noticioso"
    ],
    "reportagem": [
        "reportagem", "repórter", "jornalismo investigativo",
        "matéria jornalística"
    ],
    "editorial": [
        "editorial", "opinião do jornal", "linha editorial"
    ],
    "cronica": [
        "crônica", "cronista", "cotidiano", "humor no cotidiano",
        "voz narrativa", "olhar do cotidiano"
    ],
    "texto_literario": [
        "literário", "literatura", "poema", "conto", "romance",
        "novela", "narrativa ficcional", "personagem ficcional",
        "modernismo", "modernista", "regionalismo", "prosa"
    ],
    "texto_normativo": [
        "normativo", "legal", "lei", "constituição", "artigo de lei",
        "estatuto", "código", "decreto", "legislação"
    ],
    "tabela": [
        "tabela", "dados tabulados", "preencha a tabela"
    ],
    "grafico": [
        "gráfico", "eixo x", "eixo y", "histograma", "gráfico de barras",
        "gráfico de linhas", "gráfico de pizza", "gráfico de setores"
    ],
    "mapa": [
        "mapa", "cartográfico", "coordenadas geográficas", "mapa-múndi",
        "mapa do brasil", "mapa político", "mapa físico"
    ],
    "experimento": [
        "experimento", "laboratório", "hipótese experimental",
        "procedimento experimental", "materiais e métodos"
    ],
    "producao_textual": [
        "produção textual", "redação", "escreva um texto",
        "produza um texto", "elabore um texto"
    ],
    "calculo": [
        "calcule", "resolva", "equação", "fórmula", "cálculo",
        "operação", "expressão numérica"
    ],
    "debate": [
        "debate", "discussão em grupo", "roda de conversa",
        "argumentar oralmente"
    ],
    "video": [
        "vídeo", "assista", "filme", "documentário", "link para vídeo"
    ],
    "imagem_analise": [
        "analise a imagem", "observe a imagem", "leitura de imagem",
        "análise visual"
    ],
}

# Fontes que NÃO são notícias automaticamente
FONTES_NAO_NOTICIA = [
    "g1.globo.com", "uol.com.br", "bbc.com", "cnn", "folha",
    "estadao", "agência brasil", "reuters", "disponível em:",
    "acesso em:"
]

# Palavras que indicam CITAÇÃO/FONTE e não conteúdo
CONTEXTO_CITACAO = [
    "disponível em:", "acesso em:", "adaptado de:", "fonte:",
    "reprodução", "imagem:", "foto:", "crédito:"
]


def normalizar(texto):
    """Normaliza texto para busca."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def extrair_texto_pdf(pdf_path):
    """Extrai todo o texto de um PDF."""
    texto_completo = ""
    paginas = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                paginas.append(text)
                texto_completo += text + "\n"
    except Exception as e:
        return "", [], str(e)
    return texto_completo, paginas, None


def extrair_titulo_aula(texto, paginas):
    """Extrai título e informações da aula a partir das primeiras páginas."""
    info = {
        "titulo": "",
        "numero_aula": "",
        "disciplina": "",
        "serie": "",
        "bimestre": "",
        "parte": ""
    }
    
    if paginas:
        primeira = paginas[0] if paginas[0] else ""
        segunda = paginas[1] if len(paginas) > 1 else ""
        
        # Disciplina (geralmente primeira linha)
        linhas = primeira.split('\n')
        for linha in linhas[:3]:
            linha_strip = linha.strip()
            if linha_strip and len(linha_strip) > 3:
                info["disciplina"] = linha_strip
                break
        
        # Número da aula
        match = re.search(r'aula\s*(\d+)', primeira, re.IGNORECASE)
        if match:
            info["numero_aula"] = match.group(1)
        
        # Bimestre
        match = re.search(r'(\d+)[oº°]\s*bimestre', primeira, re.IGNORECASE)
        if match:
            info["bimestre"] = f"{match.group(1)}º bimestre"
        
        # Série
        match = re.search(r'(\d+)[oº°]?\s*(ano|série)', primeira, re.IGNORECASE)
        if match:
            info["serie"] = f"{match.group(1)}º {match.group(2)}"
        
        # Ensino Médio/Fundamental
        if re.search(r'ensino\s*médio', primeira, re.IGNORECASE):
            info["serie"] += " (EM)" if info["serie"] else "Ensino Médio"
        elif re.search(r'ensino\s*fundamental', primeira, re.IGNORECASE):
            info["serie"] += " (EF)" if info["serie"] else "Ensino Fundamental"
        
        # Título (nas primeiras linhas, entre disciplina e aula/bimestre)
        for linha in linhas:
            linha_strip = linha.strip()
            if (linha_strip and len(linha_strip) > 5 
                and not re.match(r'^\d+[oº°]\s*bimestre', linha_strip, re.IGNORECASE)
                and not re.match(r'^aula\s*\d+', linha_strip, re.IGNORECASE)
                and not re.match(r'^ensino', linha_strip, re.IGNORECASE)
                and linha_strip != info["disciplina"]
                and not re.match(r'^(●|•)', linha_strip)):
                info["titulo"] = linha_strip
                break
        
        # Parte
        match = re.search(r'parte\s*(\d+)', primeira, re.IGNORECASE)
        if match:
            info["parte"] = f"Parte {match.group(1)}"
    
    return info


def detectar_recursos(texto, paginas):
    """Detecta recursos realmente presentes no PDF."""
    texto_norm = normalizar(texto)
    resultados = {}
    
    for recurso, keywords in RECURSOS_KEYWORDS.items():
        encontrados = []
        for kw in keywords:
            kw_norm = normalizar(kw)
            if kw_norm in texto_norm:
                # Verificar se é citação/fonte ou conteúdo real
                eh_citacao = False
                for ctx in CONTEXTO_CITACAO:
                    # Procurar a keyword perto de contexto de citação
                    pattern = re.compile(
                        rf'{re.escape(ctx)}[^.]*{re.escape(kw_norm)}|{re.escape(kw_norm)}[^.]*{re.escape(ctx)}',
                        re.IGNORECASE
                    )
                    if pattern.search(texto_norm):
                        eh_citacao = True
                        break
                
                encontrados.append({
                    "keyword": kw,
                    "possivelmente_citacao": eh_citacao
                })
        
        if encontrados:
            # Determinar se é recurso real ou falso positivo
            real = any(not e["possivelmente_citacao"] for e in encontrados)
            resultados[recurso] = {
                "presente": real,
                "keywords_encontradas": [e["keyword"] for e in encontrados],
                "risco_falso_positivo": any(e["possivelmente_citacao"] for e in encontrados)
            }
        else:
            resultados[recurso] = {
                "presente": False,
                "keywords_encontradas": [],
                "risco_falso_positivo": False
            }
    
    return resultados


def classificar_perfil(titulo, texto, recursos):
    """Classifica o perfil metodológico da aula."""
    titulo_norm = normalizar(titulo)
    texto_norm = normalizar(texto)
    perfis = []
    
    # Regras de classificação baseadas em título e conteúdo
    regras = [
        ("cronica", ["crônica", "cronista", "cotidiano", "olhar do cotidiano"]),
        ("texto_normativo", ["normativo", "norma", "constituição", "lei", "estatuto", "decreto", "legal"]),
        ("editorial_argumentativo", ["editorial", "opinião"]),
        ("literatura_modernismo", ["modernismo", "modernista", "geração modernista", "prosa de 30", "semana de 22"]),
        ("literatura_prosa", ["romance", "romancista", "prosa", "narrativa", "ficção"]),
        ("poema", ["poema", "poesia", "poeta", "verso", "estrofe", "rima"]),
        ("conto", ["conto", "contista", "narrativa curta"]),
        ("gramatica_analise_linguistica", ["gramática", "sintaxe", "morfologia", "análise linguística", "oração", "sujeito", "predicado"]),
        ("producao_textual", ["produção textual", "redação", "escreva", "texto dissertativo", "texto argumentativo"]),
        ("noticia_leitura_critica", ["notícia", "manchete", "lide"]),
        ("reportagem", ["reportagem", "matéria jornalística"]),
        ("artigo_opiniao", ["artigo de opinião"]),
        ("leitura_interpretacao", ["leitura", "interpretação", "compreensão textual"]),
        ("oralidade", ["oralidade", "apresentação oral", "seminário"]),
        ("matematica_resolucao_problemas", ["problema", "resolução de problemas"]),
        ("matematica_tabela_grafico", ["tabela", "gráfico", "dados"]),
        ("matematica_calculo", ["equação", "cálculo", "expressão algébrica"]),
        ("ciencias_experimento", ["experimento", "laboratório"]),
        ("ciencias_conceitual", ["célula", "organismo", "ecossistema", "átomo", "molécula"]),
        ("geografia_mapa", ["mapa", "cartografia"]),
        ("geografia_grafico_dados", ["dados geográficos", "indicadores"]),
        ("historia_fonte_documental", ["fonte histórica", "documento", "período histórico"]),
        ("arte_leitura_imagem", ["obra de arte", "leitura de imagem", "artista"]),
        ("ingles_vocabulario_leitura", ["vocabulary", "reading", "comprehension"]),
    ]
    
    for perfil, keywords in regras:
        for kw in keywords:
            if normalizar(kw) in titulo_norm:
                if perfil not in perfis:
                    perfis.append(perfil)
                break
    
    # Se não encontrou no título, buscar no texto (menos confiável)
    if not perfis:
        for perfil, keywords in regras:
            count = sum(1 for kw in keywords if normalizar(kw) in texto_norm[:3000])
            if count >= 2:
                if perfil not in perfis:
                    perfis.append(perfil)
    
    return perfis if perfis else ["nao_classificado"]


def detectar_riscos_contaminacao(texto, recursos, perfis):
    """Detecta palavras que podem enganar o sistema automático."""
    riscos = []
    texto_norm = normalizar(texto)
    
    # Se NÃO é notícia mas cita fontes jornalísticas
    if "noticia_leitura_critica" not in perfis and "reportagem" not in perfis:
        for fonte in FONTES_NAO_NOTICIA:
            if normalizar(fonte) in texto_norm:
                riscos.append(f"PDF cita '{fonte}' como fonte, mas NÃO é aula de notícia")
    
    # Se NÃO é tabela mas usa a palavra "quadro"
    if not recursos.get("tabela", {}).get("presente", False):
        if "quadro" in texto_norm:
            riscos.append("PDF usa palavra 'quadro' — não confundir com tabela")
    
    # Se é literatura mas contém palavras que podem confundir
    if any(p in perfis for p in ["cronica", "literatura_prosa", "literatura_modernismo", "conto", "poema"]):
        if "notícia" in texto_norm or "jornal" in texto_norm:
            riscos.append("PDF é literário mas menciona 'notícia'/'jornal' — pode ser menção contextual")
    
    # Se é normativo mas cita fontes
    if "texto_normativo" in perfis:
        if any(f in texto_norm for f in ["g1", "uol", "bbc"]):
            riscos.append("PDF normativo cita fonte jornalística — não classificar como notícia")
    
    return riscos


def gerar_termos_proibidos(perfis, recursos):
    """Gera lista de termos que a metodologia NÃO PODE usar."""
    proibidos = []
    
    # Mapas de proibição por perfil
    if not recursos.get("noticia", {}).get("presente", False):
        proibidos.extend(["notícia", "manchete", "lide", "fato noticioso", 
                         "leitura guiada da notícia"])
    
    if not recursos.get("tabela", {}).get("presente", False):
        proibidos.extend(["tabela", "dados tabulados", "analisar tabelas"])
    
    if not recursos.get("grafico", {}).get("presente", False):
        proibidos.extend(["gráfico", "analisar gráficos"])
    
    if not recursos.get("mapa", {}).get("presente", False):
        proibidos.extend(["mapa", "análise cartográfica", "analisar mapa"])
    
    if not recursos.get("experimento", {}).get("presente", False):
        proibidos.extend(["experimento", "laboratório", "procedimento experimental"])
    
    if not recursos.get("calculo", {}).get("presente", False):
        proibidos.extend(["cálculo", "calcule", "resolva a equação"])
    
    if not recursos.get("debate", {}).get("presente", False):
        proibidos.extend(["debate formal", "confronto de argumentos"])
    
    if not recursos.get("producao_textual", {}).get("presente", False):
        proibidos.extend(["produção textual", "escreva um texto", "redação"])
    
    return list(set(proibidos))


def analisar_pdf(pdf_path, disciplina_pasta):
    """Análise completa de um único PDF."""
    texto, paginas, erro = extrair_texto_pdf(pdf_path)
    
    if erro:
        return {
            "arquivo": os.path.basename(pdf_path),
            "caminho": pdf_path,
            "erro": erro
        }
    
    info = extrair_titulo_aula(texto, paginas)
    recursos = detectar_recursos(texto, paginas)
    perfis = classificar_perfil(info.get("titulo", ""), texto, recursos)
    riscos = detectar_riscos_contaminacao(texto, recursos, perfis)
    termos_proibidos = gerar_termos_proibidos(perfis, recursos)
    
    # Extrair atividades propostas
    atividades = []
    for secao in ["na prática", "todo mundo escreve", "todo mundo conversa", 
                   "atividade", "virem e conversem", "exercício"]:
        if normalizar(secao) in normalizar(texto):
            atividades.append(secao.title())
    
    # Conteúdos trabalhados (keywords do texto das primeiras páginas)
    conteudos = []
    if paginas and len(paginas) > 1:
        segunda = normalizar(paginas[1]) if len(paginas) > 1 else ""
        # Buscar bullet points / objetivos
        for linha in (paginas[1] if len(paginas) > 1 else "").split('\n'):
            linha = linha.strip()
            if linha.startswith('●') or linha.startswith('•'):
                conteudos.append(linha.lstrip('●•').strip())
    
    return {
        "arquivo_pdf": os.path.basename(pdf_path),
        "caminho_completo": pdf_path,
        "disciplina_pasta": disciplina_pasta,
        "numero_aula": info.get("numero_aula", ""),
        "titulo_aula": info.get("titulo", ""),
        "disciplina": info.get("disciplina", disciplina_pasta),
        "serie": info.get("serie", ""),
        "bimestre": info.get("bimestre", ""),
        "parte": info.get("parte", ""),
        "perfil_metodologico": perfis,
        "conteudos_trabalhados": conteudos[:5],
        "atividades_propostas": atividades,
        "recursos_reais": {k: v for k, v in recursos.items() if v.get("presente", False)},
        "recursos_ausentes": [k for k, v in recursos.items() if not v.get("presente", False)],
        "recursos_risco_falso_positivo": {k: v for k, v in recursos.items() if v.get("risco_falso_positivo", False)},
        "termos_proibidos": termos_proibidos,
        "riscos_contaminacao": riscos,
        "texto_primeiras_paginas": texto[:2000] if texto else "",
        "num_paginas": len(paginas),
        "nivel_confianca": "alto" if perfis != ["nao_classificado"] else "baixo"
    }


def processar_disciplina(disciplina_path, disciplina_nome, max_por_turma=None):
    """Processa todos os PDFs de uma disciplina."""
    resultados = []
    
    for root, dirs, files in os.walk(disciplina_path):
        pdfs = sorted([f for f in files if f.lower().endswith('.pdf')])
        if not pdfs:
            continue
        
        # Se max_por_turma, limitar
        if max_por_turma:
            pdfs = pdfs[:max_por_turma]
        
        rel_path = os.path.relpath(root, PDF_BASE)
        print(f"  Processando {rel_path}: {len(pdfs)} PDFs...", file=sys.stderr)
        
        for pdf_file in pdfs:
            pdf_path = os.path.join(root, pdf_file)
            try:
                resultado = analisar_pdf(pdf_path, disciplina_nome)
                resultados.append(resultado)
            except Exception as e:
                resultados.append({
                    "arquivo_pdf": pdf_file,
                    "caminho_completo": pdf_path,
                    "disciplina_pasta": disciplina_nome,
                    "erro": str(e)
                })
    
    return resultados


def main():
    """Executa análise completa de todas as disciplinas."""
    todas_disciplinas = {}
    
    # Listar disciplinas
    for item in sorted(os.listdir(PDF_BASE)):
        item_path = os.path.join(PDF_BASE, item)
        if os.path.isdir(item_path) and not item.startswith('_') and item != 'NAO_CLASSIFICADOS':
            todas_disciplinas[item] = item_path
    
    print(f"Disciplinas encontradas: {len(todas_disciplinas)}", file=sys.stderr)
    
    todos_resultados = {}
    
    for disc_nome, disc_path in todas_disciplinas.items():
        print(f"\n=== {disc_nome} ===", file=sys.stderr)
        resultados = processar_disciplina(disc_path, disc_nome)
        todos_resultados[disc_nome] = resultados
        print(f"  Total PDFs analisados: {len(resultados)}", file=sys.stderr)
    
    # Salvar resultado
    output_path = os.path.join(PDF_BASE, "_ARQUIVOS_AUXILIARES", "analise_metodologica.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Serializar sem texto completo das paginas para economizar espaço
        resultados_limpos = {}
        for disc, res_list in todos_resultados.items():
            resultados_limpos[disc] = []
            for r in res_list:
                r_limpo = {k: v for k, v in r.items() if k != "texto_primeiras_paginas"}
                resultados_limpos[disc].append(r_limpo)
        
        json.dump(resultados_limpos, f, ensure_ascii=False, indent=2)
    
    print(f"\nResultado salvo em: {output_path}", file=sys.stderr)
    
    # Imprimir resumo
    print("\n=== RESUMO GERAL ===")
    for disc, res_list in todos_resultados.items():
        total = len(res_list)
        erros = sum(1 for r in res_list if "erro" in r)
        perfis = defaultdict(int)
        for r in res_list:
            if "erro" not in r:
                for p in r.get("perfil_metodologico", []):
                    perfis[p] += 1
        
        riscos_total = sum(len(r.get("riscos_contaminacao", [])) for r in res_list)
        
        print(f"\n{disc}: {total} PDFs ({erros} erros)")
        print(f"  Perfis: {dict(perfis)}")
        if riscos_total > 0:
            print(f"  ⚠️ Riscos de contaminação: {riscos_total}")
    
    return todos_resultados


if __name__ == "__main__":
    main()
