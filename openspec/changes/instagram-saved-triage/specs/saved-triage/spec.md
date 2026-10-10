# Spec Delta

## Purpose

Permitir a curadoria rápida, item a item e pelo teclado, dos salvos com status `novo`, garantindo que nenhuma ideia entre no banco como `manter` sem uma nota de contexto.

## ADDED Requirements

### Requirement: Servidor local de triagem
O comando `salvos triage` MUST iniciar um servidor HTTP acessível apenas em `127.0.0.1` (porta padrão 8765, configurável por opção), servir uma página HTML única sem recursos externos e imprimir a URL de acesso.

#### Scenario: Início
- **WHEN** o usuário roda `salvos triage`
- **THEN** a URL `http://127.0.0.1:8765/` é impressa e a página abre o primeiro item `novo`

#### Scenario: Sem acesso externo
- **WHEN** outra máquina da rede tenta acessar a porta
- **THEN** a conexão não é aceita, porque o servidor escuta só em loopback

### Requirement: Exibição do item atual
A página MUST mostrar um item por vez com: link clicável para a URL (abre em nova aba), autor, tipo, coleções, data de salvamento e tags/nota existentes, além do contador de progresso "triados nesta sessão / restantes no filtro / total `novo`".

#### Scenario: Fila vazia
- **WHEN** não há itens `novo` no filtro atual
- **THEN** a página informa que a fila terminou

### Requirement: Atalhos de teclado
A página MUST responder aos atalhos (ignorados enquanto um campo de texto está em foco, exceto Enter/Esc):
- `k` → `manter`; `d` → `descartar`; `u` → `usado`; `s` → pular (sem alterar o item, vai para o próximo);
- `t` → abre campo de tags com autocomplete das tags já usadas no banco;
- `n` → abre campo de nota (uma frase);
- `z` → desfaz a última ação;
- `Enter` confirma o campo aberto; `Esc` cancela.

#### Scenario: Descartar
- **WHEN** o usuário pressiona `d`
- **THEN** o item passa a `descartar`, `revisado_em` recebe o instante atual em UTC e o próximo item é exibido

#### Scenario: Autocomplete de tags
- **WHEN** o usuário pressiona `t` e digita `rec`
- **THEN** são sugeridas tags existentes que começam com `rec` (ex.: `receita`)

#### Scenario: Pular
- **WHEN** o usuário pressiona `s`
- **THEN** o item continua `novo`, não reaparece nesta sessão e o próximo é exibido

### Requirement: Manter exige nota
O sistema MUST rejeitar a transição para `manter` quando o item não tem nota não vazia, tanto na interface quanto no servidor.

#### Scenario: Manter sem nota
- **WHEN** o usuário pressiona `k` em um item sem nota
- **THEN** o status não muda e o campo de nota é aberto; ao confirmar uma nota não vazia, o item é salvo como `manter`

#### Scenario: Requisição direta sem nota
- **WHEN** uma requisição à API tenta marcar `manter` sem nota
- **THEN** o servidor responde com erro e o banco não é alterado

### Requirement: Persistência imediata
Cada ação (status, tags, nota) MUST ser gravada no SQLite antes de a interface avançar, sem botão de salvar. Tags MUST ser normalizadas (minúsculas, sem espaços nas pontas, sem duplicatas) e gravadas separadas por vírgula.

#### Scenario: Fechar o navegador no meio
- **WHEN** o usuário triou 10 itens e fecha a aba
- **THEN** as 10 ações estão no banco

### Requirement: Desfazer
`z` MUST reverter a última ação desta sessão de triagem, restaurando exatamente os valores anteriores de `status`, `tags`, `nota` e `revisado_em`, e reexibir o item. Ações sucessivas de desfazer MUST reverter ações anteriores em ordem inversa.

#### Scenario: Desfazer descarte
- **WHEN** o usuário marca `descartar` e pressiona `z`
- **THEN** o item volta a `novo` com `revisado_em` anterior e é exibido de novo

### Requirement: Filtros e ordenação
A página MUST permitir filtrar a fila por coleção, por autor e por faixa de data de salvamento (início/fim), e ordenar por mais antigo ou mais recente primeiro. Alterar filtros MUST recalcular a fila e o contador.

#### Scenario: Filtro por coleção e ordem
- **WHEN** o usuário escolhe a coleção "Receitas" e a ordem "mais antigo primeiro"
- **THEN** só itens `novo` dessa coleção aparecem, do mais antigo para o mais recente
