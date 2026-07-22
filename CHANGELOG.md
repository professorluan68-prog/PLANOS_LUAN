# Histórico de Atualizações Recentes (CHANGELOG)

Este arquivo serve como um registro de alterações recentes feitas no sistema, para que outros agentes possam consultar e saber o que foi corrigido ou implementado.

## [2026-07-21] - Correção do Bug de Pydantic, Fallback de Leitura de Metodologia e Redução do Tamanho via IA
### Corrigido
- **core/models.py**: Ajustado o método `PlanoCompleto.from_any` para aceitar que o campo `metodologia` venha da IA como uma string (texto longo). Quando isso ocorre, o sistema agora divide a string por blocos (`\n\n`) e estrutura corretamente em lista de dicionários (`titulo` e `texto`). Isso elimina os erros de validação Pydantic (`A entrada deve ser uma lista válida`) quando o JSON da IA saía um pouco fora do formato.
- **core/seletor_referencias.py**: Resolvido o bug que impedia o sistema de achar o arquivo `Metodologias_...docx` quando o plano era gerado pelo Streamlit. Como o Streamlit joga o PDF numa pasta temporária (`temp_...`), a busca local por DOCX falhava. Adicionado o método `_resolver_caminho_original` que mapeia o caminho temporário de volta para o diretório `PDF_AULAS_DIR` e encontra a pasta e o DOCX corretos para injeção de metodologias (crucial para Orientação de Estudos).
- **core/referencias_orientacao_estudos.py**: Flexibilizada a Expressão Regular (Regex) que localizava a string `AULA X - Titulo` (`re.match(r'^AULA\s+(\d{1,2})[\s\-–—.:]*(.+)$')`) no arquivo docx. Agora o regex aceita se o professor não utilizar traço entre o número da aula e o título, reduzindo falhas na associação.

### Alterado
- **core/ia.py**: Atualizado o `_montar_prompt` adicionando uma regra UNIVERSAL e EXTREMAMENTE RESTRITIVA para o tamanho da metodologia gerada via Inteligência Artificial para todas as disciplinas. A regra exige textos de 15 a 40 palavras (2 a 3 linhas por etapa), impedindo que a IA explique os detalhes teóricos, foque apenas na ação docente e deixe a metodologia muito curta, telegráfica e objetiva.


## [2026-07-16] - Correção de leitura de planilha de habilidades (AE) e correção de regex da metodologia
### Corrigido
- **core/lote.py**: Removida a lógica redundante e frágil que usava o `pandas.read_excel` com `regex` para localizar a coluna contendo a palavra "HABILIDADE". Em vez disso, refatoramos a função `_enriquecer_com_planilha` para utilizar a lógica já consolidada de `core.ae_priorizado.carregar_base_habilidades_planilha`, que localiza corretamente a habilidade com base na formatação padrão do sistema para extração da Aprendizagem Essencial (AE). O retorno da função agora busca as chaves corretas `aula_numero` e `habilidade_textos` geradas pela função canônica.
- **docx_generator/preencher.py**: Corrigido um bug onde a geração dos planos perdia os títulos das metodologias (ex: "Para começar:", "Foco no conteúdo:"). A função `_texto_ja_comeca_com_etapa` possuía uma regex (`^[^:]{2,40}:\s*`) muito permissiva que casava com qualquer texto que tivesse um dois-pontos logo no início (por exemplo: `Realizar a leitura do texto "Migrar: um direito humano"`). A regex foi ajustada para `^[^:\"\'\.\?!]{2,40}:\s*`, ignorando aspas ou pontuações de fim de frase, para que o sistema apenas identifique como "título prefixado" quando for de fato um título limpo de etapa, prevenindo falsos-positivos com citações textuais na primeira etapa da metodologia.


## 2026-07-19 - Melhorias de UI e Metodologia Automática
- **UI**: Adicionado painel informativo na interface do Streamlit exibindo a pasta oficial de PDFs resolvida e a quantidade necessária de PDFs para gerar o plano.
- **Core**: Implementada busca automática por arquivos de metodologia (.docx ou .md) contendo a palavra METODOLOGIA diretamente na pasta do PDF oficial, eliminando a necessidade de atualizar o código toda vez que um arquivo de referência for adicionado.
