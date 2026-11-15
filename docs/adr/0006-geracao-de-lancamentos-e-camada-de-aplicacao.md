# ADR 0006: Geração de lançamentos a partir do extrato e a camada de aplicação

## Status

Aceito

## Contexto

O ADR 0005 deixou em aberto a numeração do lote e o comportamento tudo-ou-nada da geração de lançamentos. Os ADRs 0003 e 0004 deixaram a camada de aplicação para quando fosse necessária.

Gerar os lançamentos de um extrato faz várias gravações em duas tabelas (lançamento e partidas) e registra cada transação como importada. O resultado precisa ser tudo-ou-nada. Os repositórios não fazem `commit` nem `rollback` (ADR 0003) e verificam antes de gravar.

Teste feito antes desta decisão, com SQLite, Python 3.12 e SQLAlchemy 2.1.8:

- Um SAVEPOINT (`begin_nested`) aberto depois de uma gravação desfez corretamente só o que estava dentro dele quando houve erro.
- Um SAVEPOINT aberto depois de apenas consultas, seguido de uma gravação bem-sucedida e de um `rollback` feito por quem chamou, **não** desfez a gravação: o driver ainda não havia aberto uma transação, e a liberação do SAVEPOINT a efetivou.

## Decisão

**Camada de aplicação**

- Nasce o pacote `ledger_fpa.app`, com os casos de uso. Um caso de uso recebe a `Session` e os dados, usa o domínio e os repositórios, e devolve um resultado.
- As dependências seguem uma direção só: `domain` não depende de ninguém, `infra` depende de `domain`, `app` depende de `domain` e `infra`, e a interface futura depende de `app`.

**Transação**

- Quem chama o caso de uso controla a transação. O caso de uso não faz `commit`, `rollback` nem usa SAVEPOINT.

**Tudo-ou-nada por verificação prévia**

- Antes de gravar a primeira linha, o caso de uso verifica todas as transações selecionadas. Se houver qualquer problema, nada é gravado.
- O erro lista **todos** os problemas encontrados (identificador e mensagem), para o usuário corrigir de uma vez.
- Só depois de todas passarem o caso de uso grava. Os repositórios continuam verificando, como última barreira.

**Verificações prévias**

- A empresa existe.
- A conta do banco existe na empresa e é analítica.
- Cada contrapartida existe, é analítica e é diferente da conta do banco (um lançamento com a mesma conta nos dois lados não tem efeito).
- O período de cada transação não está fechado.
- Nenhum identificador se repete dentro da seleção.
- Cada lançamento montado é válido no domínio.

**Já importadas**

- Antes de verificar, o caso de uso separa as transações cujo identificador já está registrado (ADR 0005). Elas são puladas, e o resultado informa a quantidade e os identificadores.

**Lote**

- Um lançamento por transação. Os lotes são sequenciais a partir do próximo lote livre da empresa (o maior lote existente mais um, ou 1 se não houver), na ordem em que as transações foram informadas.
- O cálculo do próximo lote fica no `RepositorioLancamento`.

**Entrada e saída**

- A entrada é a conta do banco (pelo código) e, para cada transação **marcada** para gerar, a transação lida e o código da contrapartida. O caso de uso não lê arquivos.
- O lançamento gerado usa a data e o histórico da transação. Soma: débito no banco e crédito na contrapartida. Subtrai: o inverso. O documento da transação não é aproveitado, porque o `Lancamento` não tem esse campo.
- O resultado informa os lançamentos gerados e as transações puladas.
- Para obter o `id` das contas a partir dos códigos, o `RepositorioContaContabil` ganha um método que devolve o `id` pelo código.

## Alternativas consideradas

- **SAVEPOINT em volta da gravação:** descartado. O teste acima mostrou que, quando aberto antes de qualquer gravação, ele pode efetivar os dados e anular o `rollback` de quem chamou.
- **Parar no primeiro problema:** é mais simples, mas com centenas de transações obrigaria o usuário a descobrir os erros um a um.
- **Colocar a orquestração dentro do `RepositorioLancamento`:** misturaria as regras da importação com a persistência.
- **Um único lote para toda a importação:** exigiria permitir vários lançamentos por lote, o que muda a unicidade de `(empresa, lote)`. Descartado por ora.

## Consequências

**Positivas**

- O usuário recebe todos os problemas de uma vez, e nada é gravado se houver algum.
- Quem chama controla a transação, e o caso de uso funciona igual em testes, na interface e em scripts.
- A camada de aplicação fica pronta para os próximos casos de uso.

**Negativas**

- As verificações existem no caso de uso e nos repositórios, e precisam ser mantidas em acordo.
- A camada `app` depende da infraestrutura.
- Duas sessões simultâneas podem calcular o mesmo lote. A unicidade de `(empresa, lote)` barra a segunda, com um `IntegrityError`.
- A verificação prévia cobre as falhas previsíveis. Uma falha inesperada no meio da gravação deixa a sessão com gravações parciais, que quem chama precisa desfazer.
- O documento da transação se perde.

**Mitigação**

- Quem chama deve desfazer a transação (`rollback`) diante de qualquer exceção do caso de uso.
- Se um SAVEPOINT for adotado no futuro, deverá usar a configuração recomendada pelo SQLAlchemy para o driver do SQLite e ser coberto por um teste do cenário acima, em novo ADR.
