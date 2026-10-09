import re

def limpar_turma_nome(t_str: str) -> str:
    """
    Normaliza o nome da turma para um formato padrão, removendo sufixos e tratando caracteres parecidos.
    Exemplos:
        "6º ANO A" -> "6A"
        "6O ANO A" -> "6A"
        "1ª SÉRIE B" -> "1B"
    """
    if not t_str:
        return ""
        
    t = str(t_str).upper()
    
    # Troca números seguidos de 'º', 'O' (letra O), ou 'ª' pelo próprio número.
    # Ex: '6º', '6O', '1ª' -> '6', '6', '1'
    t = re.sub(r'(\d)[ºOªA]\b', r'\1', t) # o \b ajuda, mas no meio do texto podemos pegar só os caracteres exatos
    t = re.sub(r'(\d)[ºOª]', r'\1', t) 
    
    # Remove palavras desnecessárias
    for termo in ['ANO', 'SÉRIE', 'SERIE']:
        t = t.replace(termo, '')
        
    # Remove espaços em branco
    t = t.replace(' ', '')
    
    return t

def turmas_sao_iguais(turma1: str, turma2: str) -> bool:
    """Verifica se duas representações de turma referem-se à mesma sala física."""
    return limpar_turma_nome(turma1) == limpar_turma_nome(turma2)
