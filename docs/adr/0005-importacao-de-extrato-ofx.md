# ADR 0005: Importação de extrato bancário OFX

## Status

Aceito

## Contexto

O sistema que inspira este projeto importa extratos bancários em formato OFX e gera lançamentos contábeis a partir deles. O usuário informa a competência, a conta contábil do banco e o arquivo, escolhe quais transações gerar e grava.

Arquivos OFX de bancos brasileiros podem estar em OFX 1.x (marcação SGML, sem tags de fechamento) ou em OFX 2.x (XML), geralmente em Windows-1252, com datas que carregam um fuso horário (por exemplo, `20171231220000[-3:BRT]`). O extrato traz apenas o lado do banco de cada movimento.

Testes feitos antes desta decisão, com o `ofxtools` 1.1.1:

- A conversão completa (`convert()`) transforma as datas em UTC. Uma transação postada em 31/12/2017 às 22h (horário de Brasília) volta como 01/01/2018, o que a levaria para o mês contábil errado.
- A conversão completa é estrita e recusa arquivos sem elementos que a especificação exige, como o saldo do livro (`LEDGERBAL`).
- A leitura sem conversão (`parse()`) entende OFX 1.x e 2.x, respeita a codificação do cabeçalho e não valida o conteúdo.

## Decisão

**Leitura**

- Usar a biblioteca `ofxtools` (mantida, sem dependências externas, Python 3.10 ou superior), adicionada em PR próprio.
- Usar apenas o `parse()` e ler os textos originais da árvore. Não usar o `convert()`.
- A data da transação é a data escrita pelo banco: os oito primeiros caracteres de `DTPOSTED`, sem conversão de fuso.
- O valor vem de `TRNAMT` como `Decimal`. A vírgula decimal é aceita. Separador de milhar é recusado com erro claro.
- Transações de valor zero não têm efeito contábil e são ignoradas na leitura.
- A conta contábil do banco é escolhida pelo usuário, como na tela de referência. Os dados da conta no arquivo (banco e número) são lidos, mas não decidem nada.

**Modelo de domínio**

- `TransacaoExtrato`, imutável: data, histórico (não vazio), documento (opcional, de `CHECKNUM` ou, na falta, `REFNUM`), valor (`Decimal` positivo, até duas casas), sentido e identificador (`FITID`, obrigatório).
- O sentido é dado pelo **sinal** de `TRNAMT`, e não por `TRNTYPE`, que pode ser genérico. Positivo é **soma** (entrada no banco) e negativo é **subtrai** (saída). O valor é guardado em módulo, como na tela de referência.

**Geração de lançamentos**

- Soma: débito na conta do banco e crédito na contrapartida. Subtrai: crédito na conta do banco e débito na contrapartida.
- A contrapartida é escolhida pelo usuário para cada transação. Só as transações marcadas para gerar viram lançamento.
- A geração passa pelo `RepositorioLancamento`, então a regra do período fechado (ADR 0004) e as demais regras de lançamento continuam valendo sem código novo.

**Duplicidade**

- Cada transação importada é registrada em tabela própria, com unicidade por empresa, conta contábil do banco e identificador (`FITID`).
- Importar de novo o mesmo extrato não gera lançamentos repetidos: as transações já registradas são puladas, e a quantidade é informada.

## Alternativas consideradas

- **`ofxparse`:** a última versão é a 0.21, de maio de 2021, e depende de `beautifulsoup4`, `lxml` e `six`. Foi descartado por estar parado.
- **Leitor próprio:** o OFX 1.x não fecha as tags e exige tratar a codificação do cabeçalho. O risco de erro é maior que o custo de depender de uma biblioteca mantida.
- **`convert()` do `ofxtools`:** descartado pelos dois motivos acima (data em UTC e rigidez com a especificação).
- **Decidir o sentido por `TRNTYPE`:** descartado porque o tipo pode ser `OTHER` ou `XFER`, sem indicar o lado.

## Consequências

**Positivas**

- A data usada é a do banco, então o mês contábil e o fechamento ficam corretos.
- Arquivos que fogem da especificação, mas têm as transações, continuam sendo lidos.
- A duplicidade é barrada pelo banco, além da verificação no repositório.

**Negativas**

- Ler a árvore bruta amarra o código à estrutura do OFX (nomes dos elementos), e não a uma API tipada.
- A leitura depende de uma biblioteca externa e do comportamento do `parse()`.
- A especificação define o `FITID` como único por conta, mas um arquivo real pode não respeitar isso. Nesse caso, transações legítimas seriam tratadas como duplicadas.
- Ignorar transações de valor zero esconde esses registros do usuário.

**Mitigação**

- Arquivos de exemplo versionados em `tests/dados/` cobrem OFX 1.x e 2.x, acentos, fuso, vírgula decimal e arquivo sem saldo. Cada caso real que falhar vira um teste.
- Se um banco repetir o `FITID`, a chave de unicidade será ajustada (por exemplo, incluindo data e valor) em um novo ADR.

## Pontos em aberto

- A numeração do lote dos lançamentos gerados.
- Se a geração é tudo-ou-nada (verificar o período de todas as transações antes de gravar a primeira). Como os repositórios não fazem `commit` nem `rollback` (ADR 0003), isso será decidido no PR de geração, junto com a camada que orquestra a importação.
