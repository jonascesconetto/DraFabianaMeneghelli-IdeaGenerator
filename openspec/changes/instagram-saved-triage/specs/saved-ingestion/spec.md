# Spec Delta

## Purpose

Transformar os JSONs brutos de salvos e coleções em uma base SQLite normalizada, deduplicada e idempotente (camadas Bronze e Silver), preservando sempre a triagem feita pelo usuário.

## ADDED Requirements

### Requirement: Comando de ingestão
O comando `salvos ingest` MUST ler todos os arquivos de salvos e coleções sob `./data/raw/` e gravar o resultado em `./data/salvos.db`, criando o banco e o schema se não existirem. Ao final, MUST imprimir quantos registros brutos foram lidos, quantos itens novos foram inseridos e quantos já existiam.

#### Scenario: Primeira ingestão
- **WHEN** o banco não existe e `salvos ingest` é executado
- **THEN** `./data/salvos.db` é criado e todos os salvos ficam com `status = 'novo'`

### Requirement: Camada Bronze (carga raw)
Cada registro bruto encontrado nos JSONs MUST ser gravado sem transformação em uma tabela de staging, junto com o arquivo de origem e o instante da carga. Registros brutos idênticos (mesmo conteúdo) MUST NOT ser duplicados entre execuções.

#### Scenario: Rastreabilidade
- **WHEN** um item da tabela Silver é consultado
- **THEN** é possível chegar aos registros brutos e aos arquivos que o originaram

### Requirement: Tabela Silver de salvos
A tabela `salvos` MUST conter as colunas: `id` (hash estável da URL normalizada), `url`, `autor`, `tipo` (`post`, `reel` ou `outro`), `salvo_em` (datetime UTC, ISO 8601), `colecao` (nullable), `status` (default `novo`; valores permitidos `novo`, `manter`, `descartar`, `usado`), `tags` (texto separado por vírgula), `nota`, `revisado_em`. Somente campos presentes na exportação MUST ser preenchidos; campos ausentes ficam nulos, sem valores inventados.

#### Scenario: Status inválido
- **WHEN** se tenta gravar `status = 'talvez'`
- **THEN** o banco rejeita a escrita

#### Scenario: Id estável
- **WHEN** a mesma URL normalizada é ingerida em execuções ou exportações diferentes
- **THEN** o `id` gerado é sempre o mesmo

### Requirement: Normalização de URL e tipo
A URL MUST ser normalizada removendo querystring e fragmento, padronizando o esquema `https`, o host em minúsculas e a barra final. O `tipo` MUST ser inferido do caminho: `/p/` → `post`; `/reel/` ou `/reels/` → `reel`; qualquer outro → `outro`.

#### Scenario: Querystring removida
- **WHEN** a URL é `https://www.instagram.com/p/ABC123/?igsh=xyz`
- **THEN** a URL normalizada é `https://www.instagram.com/p/ABC123/` e o tipo é `post`

#### Scenario: Reel
- **WHEN** a URL é `https://www.instagram.com/reel/XYZ/`
- **THEN** o tipo é `reel`

### Requirement: Correção de encoding quebrado
Todo campo de texto vindo da exportação MUST passar por detecção e correção de mojibake (UTF-8 decodificado como latin-1). Textos corretos MUST permanecer inalterados.

#### Scenario: Texto com mojibake
- **WHEN** o nome da coleção vem como `"InspiraÃ§Ã£o"`
- **THEN** é gravado como `"Inspiração"`

#### Scenario: Texto já correto
- **WHEN** o texto vem como `"Inspiração"` ou `"café"`
- **THEN** é gravado sem alteração

#### Scenario: Emoji quebrado
- **WHEN** o texto contém a sequência mojibake de um emoji (ex.: `"ð\u009f\u0094¥"`)
- **THEN** é gravado como o emoji correto (`"🔥"`)

### Requirement: Datas em UTC
`salvo_em` MUST ser convertido de timestamp Unix (ou do formato encontrado na exportação) para datetime UTC. Se um item aparece com datas diferentes em arquivos distintos, MUST prevalecer a mais antiga.

#### Scenario: Timestamp Unix
- **WHEN** o registro traz `timestamp: 1700000000`
- **THEN** `salvo_em` é `2023-11-14T22:13:20Z`

### Requirement: Deduplicação e múltiplas coleções
Itens MUST ser deduplicados pela URL normalizada. Um item presente em várias coleções MUST ter todas as coleções registradas; a coluna `colecao` MUST exibir todas elas (ordenadas, separadas por vírgula), e a relação item↔coleção MUST ficar consultável individualmente. Itens sem coleção ficam com `colecao` nula.

#### Scenario: Duplicata por querystring
- **WHEN** a mesma publicação aparece com e sem `?igsh=...`
- **THEN** existe uma única linha em `salvos`

#### Scenario: Post em duas coleções
- **WHEN** um post está nas coleções "Receitas" e "Ideias"
- **THEN** existe uma única linha com `colecao = 'Ideias, Receitas'` e duas associações registradas

### Requirement: Ingestão idempotente que preserva a triagem
Reexecutar `salvos ingest`, com a mesma exportação ou com uma nova, MUST inserir apenas itens e associações de coleção novos. A ingestão MUST NOT sobrescrever `status`, `tags`, `nota` nem `revisado_em` de itens existentes, e MUST NOT remover coleções já associadas.

#### Scenario: Reexecução sem mudanças
- **WHEN** `salvos ingest` roda duas vezes seguidas sobre os mesmos arquivos
- **THEN** a segunda execução reporta 0 itens novos e o banco fica idêntico

#### Scenario: Nova exportação após triagem
- **WHEN** um item foi marcado `manter` com nota e tags, e uma exportação nova (com esse item e outros novos) é ingerida
- **THEN** o item mantém status, nota e tags, e só os itens novos entram com `status = 'novo'`

#### Scenario: Item ganha nova coleção
- **WHEN** a exportação nova traz um item já existente em uma coleção adicional
- **THEN** a nova coleção é acrescentada sem alterar os campos de triagem

### Requirement: Schema evolutivo
O banco MUST registrar uma versão de schema e aplicar migrações pendentes automaticamente ao abrir, de modo que colunas futuras (`legenda`, `transcricao`, `resumo`) possam ser adicionadas sem perda de dados. Essas colunas MUST NOT ser criadas nem preenchidas nesta mudança.

#### Scenario: Banco antigo aberto por versão nova
- **WHEN** um banco com versão de schema anterior é aberto
- **THEN** as migrações pendentes são aplicadas e os dados existentes são preservados
