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
    "Adicionar uma semana do mês anterior",
    "Completar a última semana",
    "Completar a última semana + 1 semana",
    "Completar a última semana + 2 semanas",
]

EXTENSAO_MES_VALORES = {
    "Somente o mês": 0,
    "Adicionar uma semana do mês anterior": 0,
    "Completar a última semana": 1,
    "Completar a última semana + 1 semana": 2,
    "Completar a última semana + 2 semanas": 3,
}

EXTENSAO_MES_ANTECIPACOES = {
    "Somente o mês": 0,
    "Adicionar uma semana do mês anterior": 1,
    "Completar a última semana": 0,
    "Completar a última semana + 1 semana": 0,
    "Completar a última semana + 2 semanas": 0,
}
