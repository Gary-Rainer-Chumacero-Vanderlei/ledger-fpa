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
