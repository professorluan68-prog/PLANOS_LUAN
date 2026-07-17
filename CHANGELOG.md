# Histórico de Atualizações Recentes (CHANGELOG)

Este arquivo serve como um registro de alterações recentes feitas no sistema, para que outros agentes possam consultar e saber o que foi corrigido ou implementado.

## [2026-07-16] - Correção de leitura de planilha de habilidades (AE) e correção de regex da metodologia
### Corrigido
- **core/lote.py**: Removida a lógica redundante e frágil que usava o `pandas.read_excel` com `regex` para localizar a coluna contendo a palavra "HABILIDADE". Em vez disso, refatoramos a função `_enriquecer_com_planilha` para utilizar a lógica já consolidada de `core.ae_priorizado.carregar_base_habilidades_planilha`, que localiza corretamente a habilidade com base na formatação padrão do sistema para extração da Aprendizagem Essencial (AE). O retorno da função agora busca as chaves corretas `aula_numero` e `habilidade_textos` geradas pela função canônica.
- **docx_generator/preencher.py**: Corrigido um bug onde a geração dos planos perdia os títulos das metodologias (ex: "Para começar:", "Foco no conteúdo:"). A função `_texto_ja_comeca_com_etapa` possuía uma regex (`^[^:]{2,40}:\s*`) muito permissiva que casava com qualquer texto que tivesse um dois-pontos logo no início (por exemplo: `Realizar a leitura do texto "Migrar: um direito humano"`). A regex foi ajustada para `^[^:\"\'\.\?!]{2,40}:\s*`, ignorando aspas ou pontuações de fim de frase, para que o sistema apenas identifique como "título prefixado" quando for de fato um título limpo de etapa, prevenindo falsos-positivos com citações textuais na primeira etapa da metodologia.
