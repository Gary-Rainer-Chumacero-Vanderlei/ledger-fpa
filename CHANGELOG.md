# Changelog

Todas as mudanças relevantes deste projeto são registradas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado

- Estrutura inicial do projeto em layout `src/`
- Configuração de ruff, mypy (modo estrito) e pytest
- Hooks de pre-commit
- Workflow de CI no GitHub Actions
- ADR 0001: uso de SQLite no início do projeto
- Documentação de instalação, desenvolvimento e estrutura no README
- Diagrama do modelo de dados (`docs/modelo-dados.md`)
- Modelo de domínio `Empresa`, com validação e normalização do CNPJ
- Modelo de domínio `ContaContabil`, com natureza, tipo e hierarquia por código
- Modelo de domínio `PartidaLancamento`, com valor em `Decimal` positivo e conta analítica
- Modelo de domínio `Lancamento`, com validação da partida dobrada (débitos iguais a créditos)
- Testes automatizados dos modelos de domínio (35 testes)
- Dependência SQLAlchemy 2.x para a persistência
- ADR 0002: valores monetários guardados em centavos no banco
- Conversão entre `Decimal` e centavos (`infra/dinheiro.py`)
- Tabelas `empresa`, `conta_contabil`, `lancamento` e `partida_lancamento`, com chaves estrangeiras, unicidade de CNPJ, de código de conta e de lote por empresa, e valor positivo
- Testes das tabelas com SQLite em memória (64 testes no total)
- Validação dos dígitos verificadores do CNPJ, com suporte ao formato alfanumérico (`domain/cnpj.py`)
- A `Empresa` passa a exigir CNPJ com dígitos verificadores corretos
- A `ContaContabil` passa a exigir que o código descenda do código do pai
- Repositório de empresas (`RepositorioEmpresa`), que recusa CNPJ duplicado
- Repositório de contas contábeis (`RepositorioContaContabil`), isolado por empresa, que recusa código duplicado, conta pai inexistente e conta pai que não seja sintética
- Testes da validação do CNPJ e dos repositórios, com SQLite em memória (109 testes no total)
- Busca de conta por id no repositório de contas
- Repositório de lançamentos (`RepositorioLancamento`), isolado por empresa: grava o lançamento e as partidas em centavos, verifica tudo antes de gravar (empresa, lote, existência das contas e conta analítica conferida no banco), busca por lote e lista por data e lote
- Testes do repositório de lançamentos, com SQLite em memória (133 testes no total)
- ADR 0003: contrato dos repositórios (sem `commit` nem `rollback`, verificação antes de gravar, erros do projeto)
- ADR 0004: regra do período fechado
- Modelo de competência (`Competencia`): mês contábil formado por ano e mês, ordenável, com conversão a partir de uma data e cálculo do mês seguinte
- Tabela de fechamento, com no máximo um registro por empresa e limites para ano e mês
- Repositório de fechamento (`RepositorioFechamento`): fechamento sequencial por empresa, com primeiro fechamento livre, consulta da última competência fechada e verificação de competência fechada
- Bloqueio de lançamentos em período fechado: o repositório de lançamentos recusa datas em competência igual ou anterior à última fechada, antes de gravar
- Testes do fechamento e do bloqueio (186 testes no total)
