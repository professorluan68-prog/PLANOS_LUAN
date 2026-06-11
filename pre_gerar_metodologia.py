#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd

# Add current directory to path
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from core.lote import _aula_por_pdf
    from config import DB_PATH, inicializar_pastas
    from core.database import init_db
except ImportError as e:
    print(f"Erro ao importar módulos do sistema: {e}")
    sys.exit(1)

def print_progress(current, total, bar_length=40):
    percent = float(current) / total
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    sys.stdout.write(f"\rProgresso: [{arrow}{spaces}] {current}/{total} ({percent*100:.2f}%)")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(
        description="Pré-gerador de Metodologia, Acompanhamento e Acessibilidade para PDFs do PLANOS_LUAN."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=r"D:\PDF novos\mapa_arquivos.csv",
        help="Caminho para o CSV de mapeamento de arquivos."
    )
    parser.add_argument(
        "--usar-ia",
        action="store_true",
        help="Se definido, utiliza o motor de IA configurado em vez de heurística local."
    )
    parser.add_argument(
        "--provedor-ia",
        type=str,
        choices=["openai", "gemini"],
        default="gemini",
        help="Provedor de IA a ser utilizado se --usar-ia estiver ativo (openai ou gemini)."
    )
    parser.add_argument(
        "--modelo-ia",
        type=str,
        default="",
        help="Modelo de IA específico a utilizar."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Se definido, sobrescreve arquivos JSON já existentes."
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Limite máximo de PDFs para processar nesta rodada (útil para testes)."
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Erro: O arquivo de mapeamento CSV não foi encontrado em: {csv_path}")
        sys.exit(1)

    print("Inicializando pastas e banco de dados...")
    inicializar_pastas()
    init_db()

    diretorio_base = Path(args.csv).parent if args.csv and Path(args.csv).exists() else Path(r"D:\PDF novos")
    if getattr(args, 'dir', None) and Path(args.dir).exists():
        diretorio_base = Path(args.dir)

    print(f"Buscando PDFs em {diretorio_base}...")
    
    # Mapeamento do CSV (opcional, para pegar turma/disciplina se o caminho bater exato)
    mapa_csv = {}
    if Path(args.csv).exists():
        try:
            df = pd.read_csv(args.csv, encoding="latin-1")
            for _, row in df.iterrows():
                if pd.notna(row.get("destino")):
                    mapa_csv[str(Path(row["destino"]))] = {
                        "disciplina": str(row.get("disciplina", "")).strip(),
                        "turma": str(row.get("turma", "")).strip()
                    }
        except Exception:
            pass

    # Buscar todos os PDFs recursivamente
    todos_pdfs = list(diretorio_base.rglob("*.pdf"))
    total_linhas = len(todos_pdfs)
    print(f"Total de PDFs encontrados: {total_linhas}")

    if args.limite:
        todos_pdfs = todos_pdfs[:args.limite]
        print(f"Limitando o processamento aos primeiros {args.limite} itens.")

    processados = 0
    criados = 0
    pulados = 0
    erros = 0

    print("\nIniciando pré-geração...")
    for pdf_path in todos_pdfs:
        caminho_pdf_str = str(pdf_path)
        
        # Tentar pegar do CSV
        info_csv = mapa_csv.get(caminho_pdf_str, {})
        disciplina = info_csv.get("disciplina", "")
        turma = info_csv.get("turma", "")
        
        # Se não tem no CSV, inferir do caminho (ex: D:\PDF novos\ARTE\...)
        if not disciplina:
            try:
                rel_path = pdf_path.relative_to(diretorio_base)
                if len(rel_path.parts) > 1:
                    disciplina = rel_path.parts[0]
            except ValueError:
                pass

        json_path = pdf_path.with_suffix(".json")
        if json_path.exists() and not args.overwrite:
            pulados += 1
            print_progress(processados + 1, len(todos_pdfs))
            processados += 1
            continue

        try:
            # Chamar a geração do lote
            aula = _aula_por_pdf(
                caminho_pdf=caminho_pdf_str,
                disciplina=disciplina,
                turma=turma,
                bimestre="2º Bimestre",
                usar_ia=args.usar_ia,
                provedor_ia=args.provedor_ia,
                modelo_ia=args.modelo_ia,
                indice_aula=0,
                total_aulas=1
            )
            
            dados_salvar = {
                "disciplina": aula.get("disciplina", disciplina),
                "tema": aula.get("tema", ""),
                "material": aula.get("material", pdf_path.name),
                "numero_aula": aula.get("numero_aula", ""),
                "aprendizagem": aula.get("aprendizagem", ""),
                "metodologia": aula.get("metodologia", []),
                "acompanhamento": aula.get("acompanhamento", []),
                "acessibilidade": aula.get("acessibilidade", []),
                "ia_usada": aula.get("ia_usada", False),
                "ia_provedor": aula.get("ia_provedor", ""),
                "ia_erro": aula.get("ia_erro", "")
            }

            with open(json_path, "w", encoding="utf-8") as fj:
                json.dump(dados_salvar, fj, ensure_ascii=False, indent=2)
            
            criados += 1
        except Exception as e:
            erros += 1
            print(f"\nErro ao processar {pdf_path.name}: {e}")
            
        print_progress(processados + 1, len(todos_pdfs))
        processados += 1

    print("\n\n=== FIM DO PROCESSAMENTO ===")
    print(f"Registros avaliados: {processados}")
    print(f"JSONs criados/atualizados: {criados}")
    print(f"Ignorados/Não existentes/Já existentes: {pulados}")
    print(f"Erros encontrados: {erros}")

if __name__ == "__main__":
    main()
