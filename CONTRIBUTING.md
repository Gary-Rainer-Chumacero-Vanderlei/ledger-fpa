# Como contribuir

## Preparar o ambiente

Siga a seção [Instalação](README.md#instalação) do README e ative o pre-commit com `pre-commit install`.

## Fluxo de trabalho

1. Escolha ou abra uma issue e associe-a a um milestone.
2. Atualize a `main` e crie uma branch a partir dela.
3. Escreva o teste e depois o código.
4. Rode as verificações (veja a seção Desenvolvimento do README).
5. Abra um Pull Request com `Closes #número` na descrição.
6. Com o CI aprovado, faça o merge com **Squash and merge** e apague a branch.

A `main` é protegida: não se faz push direto.

## Nomes de branch

- `feat/nome-curto`: nova funcionalidade
- `fix/nome-curto`: correção
- `docs/nome-curto`: documentação
- `chore/nome-curto`: configuração e manutenção

## Mensagens de commit

Seguem o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/): `tipo: descrição`.

Tipos usados: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.

Exemplo: `feat: adiciona cadastro de empresa`

## Padrões de código

- Type hints em todo o código (mypy em modo estrito)
- Valores monetários com `Decimal`, nunca `float`
- Docstrings nas funções públicas
- Testes para as regras contábeis críticas
