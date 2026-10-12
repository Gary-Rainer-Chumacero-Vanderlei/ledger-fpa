# ADR 0003: Contrato dos repositórios

## Status

Aceito

## Contexto

Os repositórios traduzem entre as classes do domínio e as tabelas do banco. As classes de domínio não conhecem o banco nem têm identificador. Uma primeira versão do `RepositorioEmpresa` gravava a empresa, capturava o `IntegrityError` de CNPJ duplicado e fazia `rollback`. Isso descartava todo o trabalho pendente da sessão, e não só a empresa duplicada, e foi corrigido no PR #42.

## Decisão

Todo repositório segue este contrato:

- Recebe a `Session` do SQLAlchemy no construtor e não a cria nem a fecha.
- Não faz `commit` nem `rollback`: quem usa o repositório controla a transação.
- Usa `flush` para enviar a gravação ao banco e obter o `id`, sem finalizar a transação.
- Verifica as regras por consulta **antes** de gravar e levanta erros do próprio projeto (`CnpjJaCadastrado`, `CodigoContaJaCadastrado`, `ContaPaiInexistente`, `PaiNaoSintetico`, `EmpresaInexistente`), de modo que quem o usa não depende do SQLAlchemy.
- Devolve o `id` gerado ao adicionar, e devolve objetos de domínio ao buscar.
- O repositório de contas é isolado por empresa: todas as consultas filtram por `empresa_id`.

## Consequências

**Positivas**

- Um erro de regra não descarta o trabalho pendente da sessão.
- O domínio continua sem conhecer o banco, e os erros são do projeto.
- Os testes usam SQLite em memória, sem preparação.
- A camada que orquestra o caso de uso decide quando confirmar ou desfazer.

**Negativas**

- Cada gravação faz consultas extras de verificação.
- Duas sessões simultâneas podem passar na verificação ao mesmo tempo. Nesse caso, as restrições de unicidade do banco ainda barram o segundo registro, com um `IntegrityError` que o repositório não converte.

**Mitigação**

As restrições do banco (CNPJ único, código único por empresa, lote único por empresa, chaves estrangeiras) continuam como última barreira. Quando houver uma camada de aplicação com vários usuários simultâneos, ela deverá tratar o `IntegrityError` residual. Isso será decidido nesse momento, em um novo ADR.
