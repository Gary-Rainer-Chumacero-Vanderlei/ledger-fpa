# ledger-fpa

Sistema de contabilidade e FP&A em Python: lançamentos, conciliação bancária, DRE e orçamento.

> **Status:** em desenvolvimento inicial (v0.1.0). Os modelos de domínio, as tabelas do banco e os repositórios de empresas, contas, lançamentos e fechamento de período estão implementados e testados, inclusive o bloqueio de lançamentos em período fechado. Importação de extrato, conciliação, relatórios e interface ainda não existem.

## Funcionalidades planejadas

**Contabilidade**
- [ ] Cadastro de empresas
- [ ] Plano de contas
- [ ] Lançamentos contábeis (partidas dobradas)
- [ ] Fechamento de período
- [ ] Importação de extrato bancário (OFX)
- [ ] Conciliação de lançamentos

**FP&A**
- [ ] DRE gerencial
- [ ] Orçamento vs. realizado

## Instalação

Requisitos: Python 3.11 ou superior e Git.

```powershell
git clone https://github.com/Gary-Rainer-Chumacero-Vanderlei/ledger-fpa.git
cd ledger-fpa
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### Configurar o pre-commit

Depois de instalar as dependências, ative os hooks do Git:

```powershell
pre-commit install
```

A partir daí, o ruff e outras verificações rodam automaticamente antes de cada commit. Se um hook modificar arquivos, rode `git add` e `git commit` novamente.

## Desenvolvimento

Com o ambiente virtual ativo, estes comandos verificam a qualidade do código. O CI do GitHub executa os mesmos.

```powershell
ruff check .            # análise de código (lint)
ruff format --check .   # verifica a formatação
mypy                    # checagem de tipos
pytest                  # testes automatizados
```

Todo trabalho é feito em uma branch e integrado por Pull Request. A `main` é protegida e exige o CI aprovado.

## Estrutura do projeto

```
ledger-fpa/
├── src/ledger_fpa/     # código-fonte
│   ├── domain/         # regras de negócio (empresa, conta, lançamento, CNPJ, competência)
│   ├── infra/          # tabelas, repositórios e conversão de valores
│   └── ui/             # telas
├── tests/              # testes automatizados
├── docs/adr/           # decisões de arquitetura
└── .github/workflows/  # CI (GitHub Actions)
```

O modelo de dados está documentado em [docs/modelo-dados.md](docs/modelo-dados.md).

Decisões técnicas ficam registradas em [docs/adr](docs/adr): o [ADR 0001](docs/adr/0001-usar-sqlite-no-inicio.md) trata do uso de SQLite, o [ADR 0002](docs/adr/0002-guardar-valores-em-centavos.md) do armazenamento de valores em centavos, o [ADR 0003](docs/adr/0003-contrato-dos-repositorios.md) do contrato dos repositórios, o [ADR 0004](docs/adr/0004-regra-do-periodo-fechado.md) da regra do período fechado e o [ADR 0005](docs/adr/0005-importacao-de-extrato-ofx.md) da importação de extrato OFX.

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
