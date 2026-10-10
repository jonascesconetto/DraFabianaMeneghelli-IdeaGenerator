# Tasks

## 1. Setup do projeto

- [x] 1.1 Criar `pyproject.toml` (Python 3.12, src layout, script `salvos = "salvos.cli:main"`, dependência `openpyxl`, dev `pytest`) e verificar que `uv sync` instala sem erros
- [x] 1.2 Criar `src/salvos/{__init__,cli,paths}.py` com argparse e os subcomandos `acquire|inspect|ingest|report|triage|export` (stubs) e verificar que `uv run salvos --help` lista todos
- [x] 1.3 Adicionar `data/` e `.venv/` ao `.gitignore` e verificar com `git check-ignore data/raw/x.json`

## 2. Raw: obtenção e inspeção (GATE: parar para validação)

- [x] 2.1 Implementar `acquire.py` (extração do zip para `data/raw/<AAAAMMDD-HHMMSS>/`, rejeitando caminhos absolutos ou com `..`) e verificar com teste usando um zip sintético, incluindo o caso malicioso
- [x] 2.2 Implementar `inspect.py` (busca recursiva por `*saved*.json`, árvore de chaves/tipos, 2 exemplos mascarados, código ≠ 0 se não encontrar nada) e verificar com teste de mascaramento sobre JSON sintético
- [ ] 2.3 Colocar a exportação real em `data/raw/` (via `salvos acquire` ou descompactação manual), rodar `uv run salvos inspect`, mostrar o resumo ao usuário e **parar até ele validar** o schema
- [ ] 2.4 Com o schema validado, registrar os nomes de arquivos/chaves em `meta_schema.py` e criar fixtures sintéticas em `tests/fixtures/` com a mesma estrutura (com mojibake, duplicata com querystring, post em 2 coleções, item sem coleção); verificar que as fixtures passam por `salvos inspect`

## 3. Etapa 1: Ingestão Bronze + Silver

- [ ] 3.1 Implementar `text.fix_mojibake` e verificar com `tests/test_text.py` (`InspiraÃ§Ã£o`→`Inspiração`, emoji quebrado→`🔥`, texto correto inalterado, ASCII inalterado)
- [ ] 3.2 Implementar em `silver.py` as funções puras `normalize_url`, `infer_tipo`, `make_id`, `to_utc_iso` e verificar com testes (querystring, `instagram.com` sem www, `/reel/` vs `/reels/` vs `/p/` vs outro, timestamp Unix → `2023-11-14T22:13:20Z`)
- [ ] 3.3 Implementar `db.py` (conexão, `PRAGMA user_version`, migração v1 com `raw_registros`, `salvos`, `salvo_colecoes`, `triagem_log` e CHECKs) e verificar com teste que `status='talvez'` e `manter` sem nota são rejeitados pelo banco
- [ ] 3.4 Implementar `meta_schema.py` + `bronze.py` (leitura dos JSONs → registros brutos com hash, `INSERT OR IGNORE`) e verificar com teste que duas cargas da mesma fixture não duplicam `raw_registros` e que os arquivos de `data/raw` mantêm hash e mtime
- [ ] 3.5 Implementar o merge Silver (upsert por URL preservando curadoria, `salvo_em` = data mais antiga, `salvo_colecoes` + recálculo de `colecao`, transação única) e verificar com `tests/test_ingest.py`: duplicatas → 1 linha; post em 2 coleções → `colecao='Ideias, Receitas'` + 2 associações
- [ ] 3.6 Teste de reingestão: ingerir, marcar um item `manter` com nota e tags, ingerir uma fixture "exportação nova" (com item novo e coleção nova para o item existente) e verificar que status, nota e tags ficaram intactos, a coleção foi somada e só o item novo entrou como `novo`
- [ ] 3.7 Ligar `salvos ingest` na CLI com o resumo (lidos/novos/existentes) e verificar com `uv run salvos ingest` duas vezes sobre os dados reais (a 2ª reporta 0 novos)
- [ ] 3.8 **Parar para validação da Etapa 1** com o usuário (contagens, amostra de linhas, encoding corrigido)

## 4. Etapa 2: Raio-x do acervo

- [ ] 4.1 Implementar `report.py` (total, por tipo, por status, por coleção, por mês, top 20 autores com `(sem autor)`, sem coleção, mais de 6 meses e mais de 1 ano com data de referência injetável) e verificar com teste sobre banco de fixture com data de referência fixa
- [ ] 4.2 Ligar `salvos report` (com erro orientando `ingest` se o banco não existir) e verificar a saída com `uv run salvos report` nos dados reais
- [ ] 4.3 **Parar para validação da Etapa 2** com o usuário

## 5. Etapa 3: Curadoria (triagem)

- [ ] 5.1 Implementar `triage/curation.py` (fila filtrada/ordenada, aplicar ação com normalização de tags e validação de manter-com-nota, `revisado_em`, `triagem_log` com antes/depois, desfazer por sessão, tags existentes) e verificar com `tests/test_curation.py`, incluindo undo em sequência
- [ ] 5.2 Implementar `triage/server.py` (ThreadingHTTPServer em 127.0.0.1, `--port`, rotas `/`, `/api/fila`, `/api/meta`, `/api/acao`, `/api/desfazer`, erro 422 para manter sem nota) e verificar com teste que sobe o servidor em porta efêmera e chama a API
- [ ] 5.3 Implementar `triage/static/index.html` (item atual com link `target=_blank`, contador, filtros de coleção/autor/datas/ordem, atalhos `k d u s t n z` + Enter/Esc, autocomplete via `<datalist>`, `k` sem nota abre o campo de nota, pular com pilha de undo local) sem recursos externos
- [ ] 5.4 Verificar manualmente no navegador com `uv run salvos triage`: cada atalho, manter sem nota bloqueado, undo, filtros, persistência após recarregar a página
- [ ] 5.5 **Parar para validação da Etapa 3** com o usuário

## 6. Etapa 4: Exportação

- [ ] 6.1 Implementar `export.py` (seleção de `manter`/`usado`, `Nome` truncado em 80 caracteres com `…` e alternativa `<autor> – <tipo>`, `Salvo em` em `AAAA-MM-DD HH:MM`, colunas na ordem do spec) gerando `notion.csv` (UTF-8 sem BOM) e `salvos.xlsx` (openpyxl, URL como hyperlink) e verificar com `tests/test_export.py` (filtro por status, truncagem, round-trip CSV com vírgula/aspas/acentos/emoji, leitura do XLSX)
- [ ] 6.2 Ligar `salvos export` e verificar importando `data/export/notion.csv` no Notion (Tags vira multi-select) e abrindo `salvos.xlsx` no Excel/LibreOffice
- [ ] 6.3 **Parar para validação da Etapa 4** com o usuário

## 7. Documentação e fechamento

- [ ] 7.1 Escrever o README curto: como pedir/baixar a exportação na Central de Contas, `acquire`, `inspect`, `ingest`, `report`, `triage`, `export`, como reimportar uma exportação nova (com backup do `.db`) e o mapa Raw/Bronze/Silver/Curadoria/Export; verificar seguindo o README do zero em um clone limpo
- [ ] 7.2 Rodar `uv run pytest` e confirmar que todos os testes passam, incluindo os quatro casos exigidos (encoding quebrado, duplicatas, múltiplas coleções, reingestão sem perder triagem)
- [ ] 7.3 Confirmar com `grep -rn "requests\|urllib.request\|http.client" src/` que nenhum código faz chamada de rede de saída
