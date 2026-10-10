# Spec Delta

## Purpose

Dar ao usuário um raio-x numérico do acervo de salvos no terminal, para entender volume, distribuição e acúmulo antes e durante a triagem.

## ADDED Requirements

### Requirement: Relatório numérico no terminal
O comando `salvos report` MUST imprimir em texto puro (tabelas simples, sem gráficos) as seções:
- total de salvos;
- distribuição por `tipo` e por `status`;
- distribuição por coleção (um item em N coleções conta em cada uma delas);
- salvos por mês (`AAAA-MM`, ordem cronológica, contagem);
- top 20 autores por quantidade;
- quantidade de itens sem coleção;
- idade: quantos foram salvos há mais de 6 meses e há mais de 1 ano, em relação à data atual.

#### Scenario: Relatório com dados
- **WHEN** o banco tem salvos e o usuário roda `salvos report`
- **THEN** todas as seções são impressas com contagens que somam o total quando aplicável (tipo, status, mês)

#### Scenario: Autor desconhecido
- **WHEN** há itens sem autor na exportação
- **THEN** eles aparecem agrupados como `(sem autor)` no top de autores, se estiverem entre os 20 maiores

#### Scenario: Banco ausente
- **WHEN** `./data/salvos.db` não existe
- **THEN** o comando orienta a rodar `salvos ingest` e termina com código diferente de zero

### Requirement: Relatório somente leitura
O relatório MUST NOT alterar o banco.

#### Scenario: Banco inalterado
- **WHEN** `salvos report` é executado
- **THEN** nenhuma linha do banco é modificada
