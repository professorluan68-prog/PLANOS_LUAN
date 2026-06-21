#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import re
import sqlite3
import unicodedata
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from io import BytesIO

# Configure sys.path so we can import from core and docx_generator
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from config import DB_PATH, inicializar_pastas, PLANOS_FINALIZADOS_DIR
    from core.database import init_db, migrar_json_para_sqlite, salvar_historico_plano
    from core.lote import processar_varios_pdfs
    from docx_generator.preencher import preencher_documento
    from docx_generator.preencher_cdp import preencher_documento_cdp
    from core.disciplinas import eh_cdp, eh_cdp_fundamental, eh_cdp_multisseriada, eh_cdp_contextual
    from core.modelos_docx import caminho_template_por_contexto
    from core.helpers import filtrar_pdfs_para_aulas, ordenar_pdfs_por_numero
    from core.calendario import (
        fim_periodo_mes_com_extensao,
        datas_por_dia_ate_limite,
        datas_feriado_padrao,
        filtrar_datas_sem_aula,
    )
    from core.constantes import DIAS_SEMANA_CADASTRO, HORARIOS_AULA
except ImportError as e:
    print(f"Erro ao importar modulos do PLANOS_LUAN: {e}")
    print("Certifique-se de executar este script a partir do diretorio principal D:\\PLANOS_LUAN usando o .venv.")
    sys.exit(1)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "cli_execution.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("PLANOS_LUAN_CLI")

def normalize_str(val):
    if not val:
        return ""
    # Normalize unicode to remove accents and convert to uppercase
    nfkd_form = unicodedata.normalize('NFKD', str(val))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).strip().upper()

def get_mes_numero(mes_name):
    meses = {
        "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
        "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
    }
    norm = normalize_str(mes_name)
    return meses.get(norm, date.today().month)

def get_dia_semana_numero(texto):
    dias = {
        "SEGUNDA": 0, "SEGUNDA FEIRA": 0, "SEG": 0,
        "TERCA": 1, "TERCA FEIRA": 1, "TER": 1,
        "QUARTA": 2, "QUARTA FEIRA": 2, "QUA": 2,
        "QUINTA": 3, "QUINTA FEIRA": 3, "QUI": 3,
        "SEXTA": 4, "SEXTA FEIRA": 4, "SEX": 4,
        "SABADO": 5, "SAB": 5, "DOMINGO": 6, "DOM": 6,
    }
    norm = normalize_str(texto).replace("-", " ")
    return dias.get(norm)

def parse_db_schedule(dia_semana_str, horario_str):
    """
    Parses 'Segunda - Terça' and '15h50 - 17h30...\n16h40 - 18h20...' into {0: '15h50 - 17h30', 1: '16h40 - 18h20'}
    """
    dias_semana_raw = [p.strip() for p in re.split(r"[-;,]+", dia_semana_str) if p.strip()]
    dias_semana = []
    for d in dias_semana_raw:
        num = get_dia_semana_numero(d)
        if num is not None:
            dias_semana.append(num)
            
    horarios_raw = [p.strip() for p in re.split(r"[\n;]+", horario_str) if p.strip()]
    
    day_to_time = {}
    for idx, day_num in enumerate(dias_semana):
        time_slot = horarios_raw[idx] if idx < len(horarios_raw) else (horarios_raw[0] if horarios_raw else "")
        # Clean the slot, e.g. extract '15h50 - 17h30' from '15h50 - 17h30 - 4ª e 5ª aula'
        match = re.search(r"(\d{1,2}h\d*|\d{1,2}:\d{2})\s*-\s*(\d{1,2}h\d*|\d{1,2}:\d{2})", time_slot, re.I)
        if match:
            clean_time = f"{match.group(1)} - {match.group(2)}"
        else:
            clean_time = time_slot
            
        day_to_time[day_num] = clean_time
        
    return day_to_time

def query_teacher_link(professor, disciplina, turma):
    """Query professor_turmas to get schedule, template, etc."""
    if not os.path.exists(DB_PATH):
        logger.warning(f"Banco de dados nao encontrado em {DB_PATH}")
        return None
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.dia_semana, t.horario, t.aulas_semana, t.arquivo_modelo, t.template_id, t.componente_curricular
            FROM professor_turmas t
            JOIN professores p ON p.id = t.professor_id
            WHERE UPPER(p.nome) = ? AND UPPER(t.disciplina) = ? AND UPPER(t.turma) = ?
        """, (normalize_str(professor), normalize_str(disciplina), normalize_str(turma)))
        row = cursor.fetchone()
        if row:
            return {
                "dia_semana": row[0],
                "horario": row[1],
                "aulas_semana": row[2],
                "arquivo_modelo": row[3],
                "template_id": row[4],
                "componente_curricular": row[5]
            }
    except Exception as e:
        logger.error(f"Erro ao buscar vinculo no banco: {e}")
    finally:
        conn.close()
    return None

def list_available_profiles():
    """Returns a string listing available teacher/disciplines profiles in DB for help."""
    if not os.path.exists(DB_PATH):
        return "Nenhum perfil cadastrado (banco de dados nao encontrado)."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.nome, t.disciplina, t.turma 
            FROM professor_turmas t
            JOIN professores p ON p.id = t.professor_id
            ORDER BY p.nome, t.disciplina, t.turma
        """)
        rows = cursor.fetchall()
        if not rows:
            return "Nenhum cadastro encontrado no banco de dados."
        lines = [f"  - Professor: '{r[0]}' | Disciplina: '{r[1]}' | Turma: '{r[2]}'" for r in rows]
        return "\n".join(lines)
    except Exception:
        return "Erro ao consultar perfis."
    finally:
        conn.close()

def generate_dates_for_month(mes_name, day_to_time, extensao=0):
    """Calculate date instances in the month for weekdays mapped in day_to_time, filtering holidays."""
    ano = date.today().year
    mes_num = get_mes_numero(mes_name)
    inicio = date(ano, mes_num, 1)
    fim = fim_periodo_mes_com_extensao(ano, mes_num, extensao)
    
    all_dates = []
    for dia_semana in day_to_time.keys():
        dates_of_day = datas_por_dia_ate_limite(inicio, fim, dia_semana)
        all_dates.extend(dates_of_day)
        
    # Sort dates chronologically
    all_dates.sort()
    
    # Filter holidays
    holidays = datas_feriado_padrao(all_dates)
    filtered = filtrar_datas_sem_aula([{"data": d} for d in all_dates], holidays)
    
    return [item["data"] for item in filtered]

def nome_arquivo_plano(turma: str, disciplina: str, ia_usada: bool = False) -> str:
    turma_limpa = (turma or "Turma").strip()
    disciplina_limpa = (disciplina or "Disciplina").strip()
    turma_limpa = turma_limpa.replace("º", "").replace("ª", "")
    turma_limpa = re.sub(r"\s+", "", turma_limpa)
    disciplina_limpa = re.sub(r"\s+", "", disciplina_limpa)

    nome = f"{turma_limpa}{disciplina_limpa}"
    if ia_usada:
        nome += "COMIA"
    nome = re.sub(r'[\\/:*?"<>|]', "", nome)
    nome = nome.strip(". ") or "PlanoDeAula"
    return f"{nome}.docx"

def main():
    parser = argparse.ArgumentParser(
        description="CLI para PLANOS_LUAN - Geração automatizada de planos de aula",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Input/Output Config
    parser.add_argument("--input", "-i", type=str, help="Caminho para o PDF de aula ou diretorio contendo PDFs de aula.")
    parser.add_argument("--output", "-o", type=str, help="Diretorio de saida para salvar o plano Word (.docx).")
    parser.add_argument("--template", "-t", type=str, help="Caminho para o modelo Word (.docx) ou ID do modelo (egle, padre, cdp).")
    
    # Generation details (overridden by DB mapping if match found)
    parser.add_argument("--professor", "-p", type=str, required=True, help="Nome do professor cadastrado.")
    parser.add_argument("--disciplina", "-d", type=str, required=True, help="Nome da disciplina (ex: Ciências, Biologia).")
    parser.add_argument("--turma", "-u", type=str, required=True, help="Turma (ex: 9º ANO C, 1º ANO A).")
    parser.add_argument("--mes", "-m", type=str, default="JUNHO", help="Mês da geração (ex: JUNHO, JULHO). Default: JUNHO")
    parser.add_argument("--bimestre", "-b", type=str, default="2º Bimestre", help="Bimestre (ex: 1º Bimestre, 2º Bimestre). Default: 2º Bimestre")
    parser.add_argument("--semana", "-s", type=str, default="", help="Descrição da semana/periodo.")
    parser.add_argument("--observacao", type=str, default="", help="Observações adicionais para colocar no cabeçalho.")
    parser.add_argument("--escola", type=str, default="", help="Nome da escola.")
    parser.add_argument("--aulas-previstas", type=int, help="Número de aulas previstas (override manual).")
    parser.add_argument("--componente-curricular", type=str, help="Componente curricular override.")
    
    # AI Config
    parser.add_argument("--usar-ia", type=str, choices=["Sem IA", "OpenAI", "Gemini"], default="Sem IA",
                        help="Defina se o processamento usará IA (OpenAI, Gemini ou Sem IA). Default: Sem IA")
    parser.add_argument("--modelo-ia", type=str, help="Nome especifico do modelo de IA a utilizar.")
    
    # CDP Config
    parser.add_argument("--cdp-aula-inicial", type=int, default=1, help="Aula inicial para geração de CDP (Default: 1).")
    parser.add_argument("--turma-cdp", type=str, help="Turma multisseriada para CDP.")
    
    # Schedule tuning
    parser.add_argument("--extensao-mes", type=int, default=0, choices=[0, 1, 2, 3],
                        help="Estender o calendario escolar ate o fim da semana util (1), +1 semana (2), +2 semanas (3).")
    parser.add_argument("--dividir-metodologia", action="store_true", help="Ativar divisao da metodologia em duas partes.")
    
    args = parser.parse_args()
    
    logger.info("Iniciando PLANOS_LUAN CLI...")
    
    # 1. Initialize DB and folders
    inicializar_pastas()
    from ui.shared import carregar_chaves_locais
    from config import BASE_DIR
    carregar_chaves_locais(BASE_DIR)
    init_db()
    migrar_json_para_sqlite()
    
    # 2. Look up teacher profile in DB
    logger.info(f"Buscando perfil para: Prof={args.professor}, Disciplina={args.disciplina}, Turma={args.turma}")
    db_config = query_teacher_link(args.professor, args.disciplina, args.turma)
    
    if db_config:
        logger.info("Perfil encontrado no banco de dados!")
        dia_semana_str = db_config["dia_semana"]
        horario_str = db_config["horario"]
        aulas_semana = db_config["aulas_semana"]
        arquivo_modelo = db_config["arquivo_modelo"]
        template_id = db_config["template_id"]
        comp_curricular = db_config["componente_curricular"] or args.componente_curricular or args.disciplina
        logger.info(f"Grade cadastrada: Dias='{dia_semana_str}' | Horario='{horario_str}' | Aulas/Semana={aulas_semana}")
    else:
        logger.warning("Perfil nao encontrado no banco de dados! Usando parametros passados via CLI com fallbacks.")
        dia_semana_str = "Segunda"  # fallback
        horario_str = "07h - 08h40"  # fallback
        aulas_semana = "2"
        arquivo_modelo = ""
        template_id = ""
        comp_curricular = args.componente_curricular or args.disciplina
        
        # Print available profiles to help user
        available = list_available_profiles()
        logger.info(f"Perfis cadastrados disponiveis:\n{available}")
    
    # 3. Resolve output folder
    out_dir = Path(args.output) if args.output else PLANOS_FINALIZADOS_DIR
    os.makedirs(out_dir, exist_ok=True)
    
    # 4. Resolve template path
    template_path = None
    if args.template:
        # Check if direct path
        if os.path.exists(args.template):
            template_path = Path(args.template)
        else:
            # Check ID
            template_path = caminho_template_por_contexto(
                disciplina=args.disciplina,
                componente_curricular=comp_curricular,
                arquivo_modelo=args.template
            )
    else:
        # Resolve from DB or context
        template_path = caminho_template_por_contexto(
            disciplina=args.disciplina,
            componente_curricular=comp_curricular,
            arquivo_modelo=arquivo_modelo or template_id
        )
        
    if not template_path.exists():
        logger.error(f"Modelo Word (.docx) nao encontrado em {template_path}")
        sys.exit(2)
        
    logger.info(f"Modelo Word resolvido: {template_path}")
    modelo_bytes = template_path.read_bytes()
    
    # 5. Parse schedules and dates
    day_to_time = parse_db_schedule(dia_semana_str, horario_str)
    class_dates = generate_dates_for_month(args.mes, day_to_time, extensao=args.extensao_mes)
    
    if not class_dates:
        logger.error(f"Nenhuma data de aula encontrada para o mes {args.mes} com a grade {dia_semana_str}.")
        sys.exit(3)
        
    logger.info(f"Total de datas de aulas geradas para {args.mes}: {len(class_dates)} aulas.")
    for idx, d in enumerate(class_dates):
        wday = d.weekday()
        logger.info(f"  Aula {idx+1}: {d.strftime('%d/%m/%Y')} ({DIAS_SEMANA_CADASTRO[wday]}) - Horario: {day_to_time.get(wday, 'N/A')}")
        
    # Check if CDP or regular mode
    is_cdp_mode = eh_cdp(args.disciplina) or eh_cdp_contextual(args.disciplina) or "CDP" in normalize_str(args.disciplina) or "CDP" in normalize_str(comp_curricular)
    
    if is_cdp_mode:
        logger.info("Modo CDP detectado. Gerando plano CDP...")
        
        # Structure datas_horarios_mes
        datas_horarios_mes = []
        for d in class_dates:
            wday = d.weekday()
            datas_horarios_mes.append({
                "data": d,
                "horario": day_to_time.get(wday, "")
            })
            
        try:
            # Build models overrides
            modelo_openai = args.modelo_ia if args.usar_ia == "OpenAI" else ""
            modelo_gemini = args.modelo_ia if args.usar_ia == "Gemini" else ""
            
            docx_bytes = preencher_documento_cdp(
                BytesIO(modelo_bytes),
                escola=args.escola,
                professor=args.professor,
                turma=args.turma,
                mes=args.mes,
                bimestre=args.bimestre,
                aula_inicial=int(args.cdp_aula_inicial or 1),
                fundamental=eh_cdp_fundamental(args.disciplina),
                multisseriada=eh_cdp_multisseriada(args.disciplina),
                serie_cdp=args.turma_cdp or "",
                usar_ia=args.usar_ia != "Sem IA",
                provedor_ia=args.usar_ia.lower() if args.usar_ia != "Sem IA" else "",
                modelo_ia=(modelo_openai if args.usar_ia == "OpenAI" else modelo_gemini) if args.usar_ia != "Sem IA" else "",
                datas_horarios=datas_horarios_mes,
                semana=args.semana,
                observacao=args.observacao,
                aulas_previstas_manual=str(args.aulas_previstas or len(datas_horarios_mes))
            )
            
            # Save file
            ia_used = args.usar_ia != "Sem IA"
            out_filename = nome_arquivo_plano(args.turma, args.disciplina, ia_usada=ia_used)
            out_filepath = out_dir / out_filename
            out_filepath.write_bytes(docx_bytes.getvalue())
            
            # Save history
            salvar_historico_plano(
                args.professor, 
                args.disciplina, 
                args.turma, 
                out_filename, 
                docx_bytes.getvalue()
            )
            
            logger.info(f"Plano CDP gerado com sucesso em: {out_filepath}")
            print(f"SUCCESS: {out_filepath}")
            sys.exit(0)
            
        except Exception as e:
            logger.exception(f"Erro ao gerar plano CDP: {e}")
            sys.exit(4)
            
    else:
        logger.info("Modo Regular detectado. Processando PDFs...")
        
        # Resolve PDFs input
        if not args.input:
            logger.error("Parametro --input e obrigatorio no modo regular para extrair conteudos dos PDFs.")
            sys.exit(5)
            
        pdf_path = Path(args.input)
        temp_paths = []
        
        if pdf_path.is_file():
            if pdf_path.suffix.lower() == ".pdf":
                temp_paths.append(str(pdf_path.resolve()))
            else:
                logger.error(f"Arquivo de entrada nao e PDF: {pdf_path}")
                sys.exit(6)
        elif pdf_path.is_dir():
            # Find all PDFs in dir
            found_pdfs = ordenar_pdfs_por_numero(filtrar_pdfs_para_aulas(pdf_path.glob("*.pdf")))
            if not found_pdfs:
                logger.error(f"Nenhum arquivo PDF encontrado no diretorio: {pdf_path}")
                sys.exit(7)
            for p in found_pdfs:
                temp_paths.append(str(p.resolve()))
        else:
            logger.error(f"Caminho de entrada invalido ou inexistente: {pdf_path}")
            sys.exit(8)
            
        logger.info(f"Encontrado {len(temp_paths)} PDF(s) para processamento.")
        
        # Configure division list
        dividir_por_pdf = [args.dividir_metodologia] * len(temp_paths)
        
        try:
            modelo_openai = args.modelo_ia if args.usar_ia == "OpenAI" else ""
            modelo_gemini = args.modelo_ia if args.usar_ia == "Gemini" else ""
            
            logger.info("Chamando extrator processar_varios_pdfs...")
            aulas = processar_varios_pdfs(
                temp_paths,
                disciplina=args.disciplina,
                turma=args.turma,
                bimestre=args.bimestre,
                usar_ia=args.usar_ia != "Sem IA",
                provedor_ia=args.usar_ia.lower() if args.usar_ia != "Sem IA" else "",
                modelo_ia=(modelo_openai if args.usar_ia == "OpenAI" else modelo_gemini) if args.usar_ia != "Sem IA" else "",
                dividir_metodologia=args.dividir_metodologia,
                dividir_por_pdf=dividir_por_pdf
            )
            
            if not aulas:
                logger.error("Nenhuma aula extraida dos PDFs.")
                sys.exit(9)
                
            logger.info(f"Extraidas {len(aulas)} aulas dos PDFs.")
            
            # Map calendar dates and times to extracted lessons
            dados_aulas = []
            for idx in range(len(aulas)):
                if idx < len(class_dates):
                    d_date = class_dates[idx]
                    wday = d_date.weekday()
                    slot_time = day_to_time.get(wday, "")
                    
                    dados_aulas.append({
                        "data": d_date.strftime("%d/%m"),
                        "horario": slot_time
                    })
                else:
                    # Fallback for extra lessons beyond class_dates
                    last_date = class_dates[-1] if class_dates else date.today()
                    fallback_date = last_date + timedelta(days=7 * (idx - len(class_dates) + 1))
                    wday = fallback_date.weekday()
                    slot_time = day_to_time.get(wday, "")
                    dados_aulas.append({
                        "data": fallback_date.strftime("%d/%m"),
                        "horario": slot_time
                    })
            
            # Apply date/time tags to the lessons list
            for aula, dados in zip(aulas, dados_aulas):
                aula.update(dados)
                
            # Run post-processing cleaning similar to st.button('PROCESSAR AULAS')
            for aula in aulas:
                metodologia = aula.get("metodologia", [])
                for i, item in enumerate(metodologia):
                    if isinstance(item, dict) and "texto" in item:
                        item["texto"] = re.sub(r'\s+', ' ', re.sub(r'\(\s*\)', '', re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item["texto"]))).strip()
                    elif isinstance(item, str):
                        metodologia[i] = re.sub(r'\s+', ' ', re.sub(r'\(\s*\)', '', re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item))).strip()
            
            logger.info("Preenchendo documento Word final...")
            docx_bytes = preencher_documento(
                BytesIO(modelo_bytes),
                aulas,
                escola=args.escola,
                professor=args.professor,
                disciplina=comp_curricular,
                turma=args.turma,
                mes=args.mes,
                bimestre=args.bimestre,
                semana=args.semana,
                observacao=args.observacao,
                aulas_previstas_manual=str(args.aulas_previstas or len(aulas))
            )
            
            # Save file
            ia_used = args.usar_ia != "Sem IA"
            out_filename = nome_arquivo_plano(args.turma, args.disciplina, ia_usada=ia_used)
            out_filepath = out_dir / out_filename
            out_filepath.write_bytes(docx_bytes.getvalue())
            
            # Save history
            salvar_historico_plano(
                args.professor, 
                args.disciplina, 
                args.turma, 
                out_filename, 
                docx_bytes.getvalue()
            )
            
            logger.info(f"Plano de aula gerado com sucesso em: {out_filepath}")
            print(f"SUCCESS: {out_filepath}")
            sys.exit(0)
            
        except Exception as e:
            logger.exception(f"Erro durante processamento ou geracao regular: {e}")
            sys.exit(10)

if __name__ == "__main__":
    main()
