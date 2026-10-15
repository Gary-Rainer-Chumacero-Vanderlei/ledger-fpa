# ADR 0004: Regra do período fechado

## Status

Aceito

## Contexto

A contabilidade fecha períodos mensais. Depois que um mês é fechado, não se lança mais nada nele, o que protege balancetes e demonstrações já emitidos. A tela de fechamento do sistema que inspira este projeto mostra o fechamento atual e o próximo.

A regra "não lançar em mês fechado" depende de um dado que não pertence ao lançamento, o fechamento da empresa. Por isso ela não pode ser verificada apenas pelo domínio do `Lancamento`.

## Decisão

- A competência (ano e mês) é um objeto de domínio imutável e ordenável, com conversão a partir de uma data.
- Cada empresa tem no máximo um registro de fechamento, com a última competência fechada. Sem registro, nenhum período está fechado.
- Um lançamento com data em competência igual ou anterior à última fechada é recusado com o erro `PeriodoFechado`.
- O fechamento é sequencial: só se fecha a competência seguinte à última fechada. O primeiro fechamento de uma empresa pode ser de qualquer competência.
- A verificação fica no `RepositorioLancamento`, que consulta o fechamento da empresa antes de gravar, conforme o ADR 0003. A comparação entre competências é responsabilidade do domínio.
- Reabrir períodos e aplicar a regra a futuras alterações e remoções de lançamentos ficam para depois.

## Alternativas consideradas

- **Camada de aplicação:** um caso de uso consultaria o fechamento antes de chamar o repositório. Foi descartada por ora porque a camada ainda não existe e, sem ela, quem chamasse o repositório diretamente contornaria a regra.
- **Regra dentro do `Lancamento`:** o lançamento receberia o fechamento e se validaria. Foi descartada porque o domínio passaria a depender de dados de outro registro, e o lançamento deixaria de poder ser criado isoladamente.

## Consequências

**Positivas**

- Não há como gravar um lançamento sem passar pela regra, pois o repositório é o único caminho de gravação.
- A comparação entre competências é testável sem banco.
- Segue o contrato dos repositórios (ADR 0003).

**Negativas**

- O `RepositorioLancamento` passa a depender do fechamento.
- Fechar um mês e lançar nele ao mesmo tempo, em sessões diferentes, pode passar pela verificação. É o mesmo limite do ADR 0003.

**Mitigação**

Quando existir uma camada de aplicação com vários usuários simultâneos, ela deverá serializar o fechamento e os lançamentos da mesma empresa. A decisão será tomada nesse momento, em um novo ADR.
