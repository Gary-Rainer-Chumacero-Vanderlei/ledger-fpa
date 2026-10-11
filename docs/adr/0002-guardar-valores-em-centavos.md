# ADR 0002: Guardar valores monetários em centavos

## Status

Aceito

## Contexto

O domínio usa `Decimal` para valores monetários, evitando erros de arredondamento do `float`. O SQLite não tem tipo decimal: ele guarda números como inteiro ou ponto flutuante binário. O tipo `Numeric` do SQLAlchemy, no SQLite, passa por `float` na leitura e pode alterar o valor.

## Decisão

Guardar os valores no banco como **inteiros em centavos** (por exemplo, R$ 100,50 vira `10050`), na coluna `valor_centavos`. A conversão entre `Decimal` e centavos acontece na fronteira da camada de infraestrutura, e o domínio continua usando `Decimal`.

## Consequências

**Positivas**

- Exato em qualquer banco, inclusive SQLite e PostgreSQL
- Permite somar e comparar valores direto no SQL
- O domínio não muda

**Negativas**

- Exige converter na ida e na volta
- Limitado a duas casas decimais (já é a regra do domínio)
- Quem consultar o banco direto vê centavos, e não reais

**Mitigação**

A conversão fica em duas funções pequenas e testadas, para que o resto do código nunca lide com centavos diretamente.
