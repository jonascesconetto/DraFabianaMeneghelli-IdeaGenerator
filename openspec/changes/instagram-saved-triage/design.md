# Design

## Context

Repositório greenfield: hoje só tem `README.md` e `openspec/`. `./data/raw/` ainda não existe, então **o formato real dos JSONs da Meta não foi inspecionado**. O que se sabe de exportações anteriores (não confiável e só usado como hipótese a validar) é algo como `your_instagram_activity/saved/saved_posts.json` e `saved_collections.json`, com timestamps Unix e texto em mojibake. Motivação e escopo: ver `proposal.md`. Requisitos: ver `specs/`.

Restrições: Python 3.12 + `uv`, dependências mínimas, sem rede, `./data/raw/` imutável, trabalho em etapas com validação do usuário ao fim de cada uma.

## Goals / Non-Goals

**Goals:**
- Pipeline em camadas claras: **Raw** (arquivos) → **Bronze** (staging bruto no SQLite) → **Silver** (salvos normalizados) → **Curadoria** (triagem) → **Export** (Notion/Excel).
- Parser isolado em funções puras, testáveis sem banco e sem arquivos reais.
- Uma única CLI `salvos` com subcomandos.

**Non-Goals:**
- Legendas, mídia, transcrição, LLM (fase 2).
- Sincronização direta com a API do Notion (o usuário importa o CSV manualmente).
- Multiusuário, autenticação e deploy remoto do servidor de triagem.

## Decisions

### D1. "Download" = exportação oficial da Meta + `salvos acquire`
O usuário pede a exportação JSON na Central de Contas e baixa o `.zip`; `acquire` só extrai localmente para `data/raw/<carimbo>/`.
*Alternativas rejeitadas:* Graph API (não expõe salvos); instaloader/scraping (exige login, viola os Termos de Uso, risco de bloqueio da conta e quebra a regra "sem rede").

### D2. Gate de schema antes do parser
`salvos inspect` é implementado primeiro e depende só da stdlib: busca recursiva por `*saved*.json`, imprime a árvore de chaves/tipos (mesclando os itens de listas) e 2 exemplos mascarados. O parser só é escrito depois que o usuário valida esse resumo. Os nomes de chave usados pelo parser ficam concentrados em **um único módulo de mapeamento** (`salvos/meta_schema.py`), então mudanças futuras do formato da Meta mexem em um só lugar.

### D3. Layout do pacote
```
pyproject.toml              # [project.scripts] salvos = "salvos.cli:main"
src/salvos/
  cli.py                    # argparse, subcomandos
  paths.py                  # data/raw, data/salvos.db, data/export
  acquire.py                # extração segura do zip           (Raw)
  inspect.py                # resumo de schema                 (Raw)
  text.py                   # fix_mojibake()                   (utilitário)
  meta_schema.py            # chaves da Meta → registros brutos (Bronze)
  bronze.py                 # carga em raw_registros            (Bronze)
  silver.py                 # normalização, dedupe, merge       (Silver)
  db.py                     # conexão, migrações (user_version)
  report.py                 # salvos report
  triage/server.py          # http.server + API JSON           (Curadoria)
  triage/curation.py        # regras de status, log, undo      (Curadoria)
  triage/static/index.html  # página única, JS vanilla
  export.py                 # notion.csv + salvos.xlsx         (Export)
tests/
  fixtures/                 # JSONs sintéticos no formato validado
  test_text.py  test_silver.py  test_ingest.py  test_curation.py  test_export.py
```
CLI com `argparse` (stdlib) em vez de Click/Typer, para não adicionar dependências.

### D4. Modelo de dados (SQLite)
```sql
raw_registros(            -- Bronze
  hash TEXT PRIMARY KEY,  -- sha256 do JSON canônico do registro
  arquivo TEXT, origem TEXT,      -- 'saved_posts' | 'saved_collections'
  payload TEXT, carregado_em TEXT)

salvos(                    -- Silver + campos de curadoria
  id TEXT PRIMARY KEY,     -- sha256(url_normalizada)[:16]
  url TEXT UNIQUE NOT NULL, autor TEXT, tipo TEXT CHECK(tipo IN ('post','reel','outro')),
  salvo_em TEXT,           -- ISO 8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'
  colecao TEXT,            -- derivada: coleções ordenadas, ', '
  status TEXT NOT NULL DEFAULT 'novo' CHECK(status IN ('novo','manter','descartar','usado')),
  tags TEXT, nota TEXT, revisado_em TEXT,
  CHECK(status <> 'manter' OR length(trim(coalesce(nota,''))) > 0))

salvo_colecoes(salvo_id TEXT, colecao TEXT, PRIMARY KEY(salvo_id, colecao))

triagem_log(id INTEGER PRIMARY KEY, sessao TEXT, salvo_id TEXT, acao TEXT,
  antes TEXT, depois TEXT, em TEXT)   -- antes/depois = JSON dos 4 campos de curadoria
```
- A regra "manter exige nota" fica também como `CHECK` no banco (defesa em profundidade).
- `colecao` é coluna desnormalizada (pedida explicitamente), recalculada a partir de `salvo_colecoes`, que é a fonte de verdade.
- **Migrações:** `PRAGMA user_version` + lista ordenada de scripts em `db.py`. A fase 2 vira só uma nova entrada (`ALTER TABLE salvos ADD COLUMN legenda TEXT`, etc.). *Alternativa rejeitada:* criar as colunas vazias agora (polui o schema e o export).

### D5. Idempotência
- Bronze: `INSERT OR IGNORE` pelo hash do conteúdo.
- Silver: `INSERT ... ON CONFLICT(url) DO UPDATE SET salvo_em = min(salvo_em, excluded.salvo_em), autor = coalesce(salvos.autor, excluded.autor)`. Os campos `status/tags/nota/revisado_em` **nunca** aparecem no `DO UPDATE`.
- Coleções: `INSERT OR IGNORE` em `salvo_colecoes`, depois recalcula `colecao` dos itens afetados.
- Tudo em uma única transação por execução.

### D6. Correção de mojibake sem dependência
`fix_mojibake(s)`: se `s` tem caracteres típicos de mojibake (`Ã`, `Â`, `â€`, `ð`), tenta `s.encode('latin-1').decode('utf-8')` e aplica de novo até estabilizar (máx. 2 vezes). Se der `UnicodeEncodeError` ou `UnicodeDecodeError`, devolve o original. *Alternativa:* `ftfy` (mais robusto, mas é dependência extra; dá para trocar depois se aparecerem casos que a heurística não cobre).

### D7. Normalização de URL
`urllib.parse`: esquema `https`, host em minúsculas com `instagram.com` → `www.instagram.com`, sem query e fragmento, path com barra final. `tipo` pelo primeiro segmento do path (`p` → post; `reel`/`reels` → reel).

### D8. Servidor de triagem com stdlib
`http.server.ThreadingHTTPServer` ligado a `127.0.0.1`. API JSON:
- `GET /api/fila?colecao=&autor=&de=&ate=&ordem=asc|desc&pular=id1,id2` → item atual + contadores
- `GET /api/meta` → coleções, autores, tags existentes (autocomplete)
- `POST /api/acao` `{id, status?, tags?, nota?}` → valida, grava e registra em `triagem_log`
- `POST /api/desfazer` → reverte a última entrada do log da sessão

O "pular" é estado do cliente (lista de ids enviada em `pular`) e entra numa pilha de undo local; as demais ações são desfeitas no servidor. A sessão é um uuid gerado quando o servidor inicia. *Alternativa:* FastAPI + uvicorn (mais ergonômico, mas traz ~10 dependências transitivas para 4 endpoints).

### D9. Exportação
`csv` da stdlib (UTF-8 **sem** BOM, porque o Notion importa melhor sem ele) + `openpyxl` para o XLSX (cabeçalho em negrito, coluna URL como hyperlink, largura de colunas ajustada). Os mesmos dados alimentam os dois writers.

## Risks / Trade-offs

- [O formato da exportação da Meta muda ou difere da hipótese] → gate `inspect` + validação do usuário; chaves concentradas em `meta_schema.py`; fixtures de teste geradas a partir do formato validado.
- [O autor não vem explícito em todos os registros] → `autor` nullable; usar apenas o que existe no JSON (nunca extrair do HTML do post). Se só existir na URL (ex.: `/autor/p/...`), decidir na validação do gate.
- [Heurística de mojibake gera falso positivo em texto legítimo com `Ã`] → só aplica se o round-trip decodifica sem erro; há testes com textos corretos acentuados.
- [Dupla escrita de `colecao` e `salvo_colecoes` divergir] → `colecao` sempre recalculada a partir da tabela de associação na mesma transação.
- [Dados pessoais versionados por engano] → `data/` no `.gitignore`.
- [Undo depois de reiniciar o servidor] → o undo só vale para a sessão atual (aceitável; o log histórico continua no banco).

## Migration Plan

Projeto novo, sem migração. Para reimportar: `salvos acquire novo.zip && salvos ingest`. Rollback = apagar `data/salvos.db` (o raw continua intacto) ou restaurar uma cópia; o README recomenda copiar o `.db` antes de reingerir.

## Open Questions

- Nomes exatos de arquivos e chaves da exportação atual: resolvidos pela tarefa 2 (gate). Isso afeta só `meta_schema.py` e as fixtures, não os specs.
- Formato de data preferido no Notion (`AAAA-MM-DD HH:MM` vs só data): ajustável no export sem impacto estrutural.
