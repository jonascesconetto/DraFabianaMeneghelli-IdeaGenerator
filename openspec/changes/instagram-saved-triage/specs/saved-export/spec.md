# Spec Delta

## Purpose

Exportar os itens curados (`manter` e `usado`) em formatos prontos para importar no Notion (CSV) e abrir no Excel (XLSX).

## ADDED Requirements

### Requirement: Exportação dos itens curados
O comando `salvos export` MUST gerar `./data/export/notion.csv` e `./data/export/salvos.xlsx` contendo somente itens com status `manter` ou `usado`, criando o diretório se necessário e sobrescrevendo exportações anteriores. MUST imprimir a quantidade de linhas exportadas.

#### Scenario: Filtragem por status
- **WHEN** o banco tem itens `novo`, `descartar`, `manter` e `usado`
- **THEN** só os `manter` e `usado` aparecem nos arquivos

#### Scenario: Nada para exportar
- **WHEN** não há itens `manter` nem `usado`
- **THEN** os arquivos são gerados só com o cabeçalho e o comando avisa que 0 linhas foram exportadas

### Requirement: Colunas para o Notion
Ambos os arquivos MUST ter exatamente as colunas, nesta ordem: `Nome`, `URL`, `Autor`, `Tipo`, `Tags`, `Coleção`, `Salvo em`, `Status`, `Nota`. `Nome` MUST ser a nota truncada em 80 caracteres (com `…` quando truncada). `Tags` MUST ser separada por vírgula, para virar multi-select no Notion. `Salvo em` MUST usar o formato `AAAA-MM-DD HH:MM` (UTC).

#### Scenario: Nota longa
- **WHEN** a nota tem 120 caracteres
- **THEN** `Nome` tem no máximo 80 caracteres terminando em `…` e `Nota` traz o texto completo

#### Scenario: Item usado sem nota
- **WHEN** um item `usado` não tem nota
- **THEN** `Nome` usa como alternativa `<autor> – <tipo>` para não importar uma linha sem título

### Requirement: Encoding e escaping corretos
O CSV MUST ser UTF-8, com campos contendo vírgula, aspas ou quebra de linha escapados conforme RFC 4180. Acentos e emojis MUST ser preservados nos dois formatos.

#### Scenario: Nota com vírgula e acento
- **WHEN** a nota é `Ideia boa, ótima para "reels"`
- **THEN** o CSV reimportado devolve exatamente o mesmo texto

### Requirement: Exportação somente leitura
A exportação MUST NOT alterar o banco.

#### Scenario: Banco inalterado
- **WHEN** `salvos export` é executado
- **THEN** nenhuma linha do banco é modificada
