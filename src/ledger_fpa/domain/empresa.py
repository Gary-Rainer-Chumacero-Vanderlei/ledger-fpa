import re
from dataclasses import dataclass

from ledger_fpa.domain.cnpj import cnpj_valido

_CNPJ_SEPARADORES = re.compile(r"[./-]")


@dataclass(frozen=True)
class Empresa:
    """Empresa titular da contabilidade.

    O CNPJ é normalizado (sem pontuação, em maiúsculas) e deve ter 14
    caracteres alfanuméricos, com os dígitos verificadores corretos.
    """

    razao_social: str
    cnpj: str

    def __post_init__(self) -> None:
        razao_social = self.razao_social.strip()
        if not razao_social:
            raise ValueError("A razão social não pode ser vazia.")

        cnpj = _CNPJ_SEPARADORES.sub("", self.cnpj).upper()
        if not cnpj_valido(cnpj):
            raise ValueError("O CNPJ é inválido.")

        object.__setattr__(self, "razao_social", razao_social)
        object.__setattr__(self, "cnpj", cnpj)
