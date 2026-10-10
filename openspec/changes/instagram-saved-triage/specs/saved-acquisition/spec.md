# Spec Delta

## Purpose

Obter os dados de salvos do Instagram exclusivamente pela exportação oficial da Meta, mantendo os arquivos brutos intactos e permitindo inspecionar o formato real antes de qualquer parser.

## ADDED Requirements

### Requirement: Obtenção via exportação oficial, sem rede
O sistema MUST obter os dados apenas a partir de arquivos locais da exportação oficial da Meta (formato JSON). O sistema MUST NOT fazer requisições de rede, scraping, login ou chamadas a APIs do Instagram em nenhum comando.

#### Scenario: Nenhum comando acessa a rede
- **WHEN** qualquer subcomando `salvos` é executado
- **THEN** nenhuma conexão de saída para hosts externos é aberta

#### Scenario: Instruções para baixar a exportação
- **WHEN** o usuário consulta o README
- **THEN** ele encontra o passo a passo da Central de Contas (Baixar suas informações → JSON → incluir "Salvos") e o comando para importar o `.zip`

### Requirement: Importação do arquivo .zip da exportação
O comando `salvos acquire <arquivo.zip>` MUST extrair a exportação para um novo subdiretório `./data/raw/<AAAAMMDD-HHMMSS>/`, sem sobrescrever exportações anteriores. O sistema MUST rejeitar entradas do zip com caminho absoluto ou com `..`.

#### Scenario: Nova exportação importada
- **WHEN** o usuário roda `salvos acquire ~/Downloads/instagram-xyz.zip`
- **THEN** o conteúdo é extraído em `./data/raw/<carimbo>/` e o caminho é impresso

#### Scenario: Exportação já descompactada manualmente
- **WHEN** o usuário descompacta a exportação manualmente em qualquer subpasta de `./data/raw/`
- **THEN** os comandos seguintes a encontram pela busca recursiva, sem exigir `acquire`

#### Scenario: Zip malicioso
- **WHEN** o zip contém uma entrada como `../../etc/x`
- **THEN** o comando aborta com erro e nada é escrito fora de `./data/raw/`

### Requirement: Imutabilidade do diretório raw
Nenhum comando além de `acquire` MUST criar, alterar ou remover arquivos em `./data/raw/`.

#### Scenario: Ingestão não altera raw
- **WHEN** `salvos ingest` é executado
- **THEN** o conteúdo e o mtime de todos os arquivos em `./data/raw/` permanecem idênticos

### Requirement: Inspeção de schema
O comando `salvos inspect` MUST localizar recursivamente em `./data/raw/` os arquivos JSON relacionados a salvos e coleções (pelo nome do arquivo, ex.: contendo `saved`, sem depender de um nome fixo) e imprimir, para cada um: caminho, estrutura de chaves com tipos e 2 exemplos com valores anonimizados.

#### Scenario: Arquivos encontrados
- **WHEN** existem `saved_posts.json` e `saved_collections.json` em qualquer profundidade de `./data/raw/`
- **THEN** ambos são listados com a árvore de chaves/tipos e 2 exemplos

#### Scenario: Anonimização dos exemplos
- **WHEN** os exemplos são impressos
- **THEN** nomes de usuário, URLs e textos livres aparecem mascarados (ex.: `us***`, `https://www.instagram.com/p/XXXX/`), preservando apenas o formato

#### Scenario: Nada encontrado
- **WHEN** não há arquivos de salvos em `./data/raw/`
- **THEN** o comando informa isso, lembra como obter a exportação e termina com código diferente de zero
