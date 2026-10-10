# Proposal: Triagem dos salvos do Instagram

## Why

Centenas de posts salvos no Instagram viram um acervo morto: sem triagem, sem contexto e sem saída para uma ferramenta de trabalho. Precisamos de um pipeline **100% local** que pegue a exportação oficial da Meta, normalize os salvos, permita triar item a item com rapidez e exporte só o que vale a pena para o Notion/Excel, virando um banco de ideias.

## What Changes

- **Obtenção dos dados (mecanismo de "download")**: fluxo documentado via exportação oficial da Meta (Central de Contas → Baixar suas informações → JSON). O usuário baixa o `.zip`; o comando `uv run salvos acquire <arquivo.zip>` extrai para `./data/raw/<carimbo-de-data>/` sem nenhum acesso à rede. Nada de scraping, login ou API do Instagram.
- **Inspeção de schema** (`uv run salvos inspect`): localiza recursivamente arquivos de salvos/coleções em `./data/raw/` e imprime chaves, tipos e 2 exemplos anonimizados. É o *gate* obrigatório antes de escrever o parser.
- **Bronze — carga raw** (`uv run salvos ingest`, parte 1): registra cada registro bruto encontrado nos JSONs em tabela de staging no SQLite, sem transformar e sem tocar `./data/raw/`.
- **Silver — normalização** (`uv run salvos ingest`, parte 2): corrige mojibake (UTF-8 lido como latin-1), normaliza URL, infere tipo, converte data para UTC, deduplica por URL e associa múltiplas coleções. Ingestão idempotente que **nunca** sobrescreve `status`, `tags` ou `nota`.
- **Raio-x do acervo** (`uv run salvos report`): números no terminal (totais, tipo, coleção, mês, top 20 autores, sem coleção, idade).
- **Curadoria — triagem rápida** (`uv run salvos triage`): servidor local em `127.0.0.1` com página HTML única, atalhos de teclado (`k d u s t n z`), filtros, progresso, gravação imediata e regra "manter exige nota".
- **Exportação** (`uv run salvos export`): gera `./data/export/notion.csv` (importação no Notion) e `./data/export/salvos.xlsx` (Excel) só com itens `manter` e `usado`.
- **Preparação para a fase 2**: versionamento de schema do SQLite para receber `legenda`, `transcricao` e `resumo` depois, sem implementá-los agora.
- README curto e testes pytest do parser.

## Capabilities

### New Capabilities

- `saved-acquisition`: obtenção local da exportação oficial da Meta (import do `.zip`, layout de `./data/raw/`, imutabilidade do raw) e inspeção de schema.
- `saved-ingestion`: camadas Bronze (carga raw) e Silver (normalização, correção de encoding, deduplicação, coleções múltiplas, idempotência e preservação da triagem).
- `saved-report`: relatório numérico do acervo no terminal.
- `saved-triage`: interface local de curadoria item a item com atalhos, filtros, desfazer e regras de status.
- `saved-export`: exportação dos itens curados para CSV compatível com Notion e XLSX.

### Modified Capabilities

(nenhuma — projeto novo, sem specs existentes)

## Impact

- **Código novo**: pacote Python `salvos` (em `src/salvos/`) com CLI única `salvos` e subcomandos `acquire`, `inspect`, `ingest`, `report`, `triage`, `export`.
- **Dependências**: Python 3.12 via `uv`; runtime apenas `openpyxl` (XLSX); `pytest` como dependência de desenvolvimento. Servidor de triagem com a stdlib (`http.server`), sem frameworks.
- **Dados**: `./data/raw/` (somente leitura após a extração), `./data/salvos.db` (SQLite), `./data/export/`. A pasta `data/` entra no `.gitignore`, pois contém dados pessoais.
- **Rede**: nenhuma. O servidor de triagem escuta só em `127.0.0.1`.
- **Restrição conhecida**: `./data/raw/` está vazio hoje, então o formato real dos JSONs ainda não foi inspecionado. O parser depende da tarefa de inspeção (gate) e da validação do usuário.
