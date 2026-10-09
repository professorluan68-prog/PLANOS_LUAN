from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

base_dir = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN'

def add_title(doc, text):
    p = doc.add_heading(text, 0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def add_h1(doc, text):
    doc.add_heading(text, level=1)

def add_h2(doc, text):
    doc.add_heading(text, level=2)

def add_p(doc, text):
    doc.add_paragraph(text)

def add_bullet(doc, text):
    doc.add_paragraph(text, style='List Bullet')

# 1. Relatorio_Atualizacao_Sistema.docx
doc1 = Document()
add_title(doc1, "Relatório de Atualização do Sistema")
add_h1(doc1, "1. Visão Geral das Últimas Atualizações")
add_p(doc1, "Este relatório detalha as últimas implementações e correções de arquitetura no sistema PLANOS LUAN, garantindo que a base de código esteja moderna, resiliente e totalmente funcional.")
add_h2(doc1, "Módulo: Gerador de PEI em Lote (Inclusão)")
add_bullet(doc1, "Criação de um gerador autônomo que interage com os planos regulares para gerar Planos Educacionais Individualizados (PEI).")
add_bullet(doc1, "Integração visual no Streamlit ('PEI Inclusão') com leitura e filtro de tabela DOCX (lista de alunos).")
add_bullet(doc1, "Lógica de correspondência inteligente: o sistema agora busca no banco (SQLite) se o professor já possui plano para a disciplina, semestre e turma exata antes de permitir a geração.")
add_h2(doc1, "Correções e Migração (OneDrive)")
add_bullet(doc1, "O sistema foi migrado para rodar na nuvem do OneDrive, com os caminhos dinamicamente ajustados no arquivo config.py.")
add_bullet(doc1, "Correção crítica no banco de dados SQLite: conversão de strings de Disciplina para letras maiúsculas (UPPERCASE) garantindo precisão absoluta na filtragem das turmas.")
doc1.save(os.path.join(base_dir, "Relatorio_Atualizacao_Sistema.docx"))

# 2. Relatorio_Professores_Grade.docx
doc2 = Document()
add_title(doc2, "Relatório de Professores e Grade")
add_h1(doc2, "1. Gerenciamento de Professores e Turmas")
add_p(doc2, "A estrutura de turmas e professores baseia-se num cruzamento entre o dicionário do sistema e o histórico de planos já salvos no banco de dados.")
add_h2(doc2, "Tabela: historico_planos (SQLite)")
add_bullet(doc2, "professor_nome: Armazena o nome exato do professor (ex: HELOÍSA MORAES DELFINO).")
add_bullet(doc2, "disciplina: Salva a disciplina em UPPERCASE (ex: LÍNGUA PORTUGUESA).")
add_bullet(doc2, "turma: String da turma para a qual o plano foi gerado (ex: 6º Ano A).")
add_bullet(doc2, "bimestre: String do bimestre letivo (ex: 4º Bimestre).")
add_h2(doc2, "Normalização de Listas de Inclusão")
add_p(doc2, "No novo módulo PEI, a grade de alunos especiais vinda de um arquivo DOCX externo tem a string de 'Turma' normalizada (remoção de acentos e de palavras intermediárias como 'Ano') para garantir o 'match' 100% perfeito com as turmas do banco de dados (ex: '6º Ano B' -> '6B').")
doc2.save(os.path.join(base_dir, "Relatorio_Professores_Grade.docx"))

# 3. DOCUMENTACAO_SISTEMA_PLANOS_LUAN.docx
doc3 = Document()
add_title(doc3, "Documentação Geral do Sistema - PLANOS LUAN")
add_h1(doc3, "1. Arquitetura Front-End e UX")
add_p(doc3, "O sistema utiliza Streamlit como motor visual, implementando uma interface moderna (Dark Mode) em 'planos_luan_app.py'.")
add_bullet(doc3, "Navegação por abas horizontais (Planos Gerais, Histórico, PEI Inclusão, Conferência Mensal).")
add_bullet(doc3, "Integração fluida entre UI e Backend via session_state.")
add_h1(doc3, "2. Estrutura de Pastas e Caminhos")
add_p(doc3, "A variável config.py age como orquestradora dos caminhos do sistema. Todos os dados (banco de dados, PDFs de aula, modelos Word e outputs finais) são salvos em 'PLANOS_LUAN_DADOS', preservando o código no repositório isolado.")
add_h1(doc3, "3. Fluxo de Geração de Planos")
add_p(doc3, "Os professores inserem PDFs de aulas ou textos. O sistema extrai Habilidades, Competências e Temas e aciona a API Gemini para elaboração metodológica. Finalmente, a classe python-docx injeta essas respostas em gabaritos (.docx) e salva no repositório final.")
doc3.save(os.path.join(base_dir, "DOCUMENTACAO_SISTEMA_PLANOS_LUAN.docx"))

# 4. DOCUMENTACAO_ESTRUTURA_CORE_PLANOS_LUAN.docx
doc4 = Document()
add_title(doc4, "Documentação do Core (Motor) - PLANOS LUAN")
add_h1(doc4, "1. Visão Técnica do Pacote 'core/'")
add_p(doc4, "O coração do sistema fica no diretório 'core'. Ele separa a interface gráfica da lógica de negócios.")
add_h2(doc4, "Módulos de Extração e Integração IA")
add_bullet(doc4, "ia_client.py / ia.py: Gerenciam os prompts e a comunicação nativa com o Gemini.")
add_bullet(doc4, "lib/extrator_pdf.py: Extrai texto puro e metadados de aulas em PDF usando PyMuPDF (fitz).")
add_bullet(doc4, "lib/higienizador_pedagogico.py: Limpa jargões excessivos e garante coesão didática.")
add_h2(doc4, "Motor PEI Inclusão (gerador_pei.py & leitor_lista_pei.py)")
add_bullet(doc4, "leitor_lista_pei.py: Analisa tabelas de documentos Word para varrer nomes, turmas e segmentos dos alunos de inclusão.")
add_bullet(doc4, "gerador_pei.py: Motor autônomo que (1) localiza os Textos_Adaptados.md (feitos por IAs externas), (2) localiza o Plano Regular pronto do banco, (3) extrai Habilidades e Aprendizagens Essenciais deste plano e (4) compila tudo no gabarito em branco do PEI.")
doc4.save(os.path.join(base_dir, "DOCUMENTACAO_ESTRUTURA_CORE_PLANOS_LUAN.docx"))

print("Arquivos gerados!")
