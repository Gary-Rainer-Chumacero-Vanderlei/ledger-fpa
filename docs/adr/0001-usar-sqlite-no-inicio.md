# ADR 0001: Usar SQLite no início do projeto

## Status

Aceito

## Contexto

(O problema: o sistema precisa de um banco de dados. O projeto é de
portfólio, roda em desktop e precisa ser fácil de instalar.)

## Decisão

(O que foi escolhido: SQLite, acessado via SQLAlchemy.)

## Consequências

**Positivas**

- (sem servidor para instalar)
- (um único arquivo)
- (bom para testes automatizados)

**Negativas**

- (sem acesso concorrente de vários usuários)
- (menos recursos que o PostgreSQL)

**Mitigação**

(O SQLAlchemy permite migrar para PostgreSQL trocando a string de conexão, sem reescrever as consultas.)
