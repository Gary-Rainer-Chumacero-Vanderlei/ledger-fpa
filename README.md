# ledger-fpa

Sistema de contabilidade e FP&A em Python: lançamentos, conciliação bancária, DRE e orçamento.

> **Status:** em desenvolvimento inicial (v0.1.0). Nenhuma funcionalidade está pronta ainda.

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

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
