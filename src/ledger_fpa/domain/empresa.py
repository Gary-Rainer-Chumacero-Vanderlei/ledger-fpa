import re
from dataclasses import dataclass

_CNPJ_SEPARADORES = re.compile(r"[./-]")
_CNPJ_VALIDO = re.compile(r"[0-9A-Z]{14}")


@dataclass(frozen=True)
class Empresa:
    """Empresa titular da contabilidade.

    O CNPJ é normalizado (sem pontuação, em maiúsculas) e deve ter 14
    caracteres alfanuméricos. Os dígitos verificadores não são validados.
    """

    razao_social: str
    cnpj: str

    def __post_init__(self) -> None:
        razao_social = self.razao_social.strip()
        if not razao_social:
            raise ValueError("A razão social não pode ser vazia.")

        cnpj = _CNPJ_SEPARADORES.sub("", self.cnpj).upper()
        if not _CNPJ_VALIDO.fullmatch(cnpj):
            raise ValueError("O CNPJ deve ter 14 caracteres alfanuméricos.")

        object.__setattr__(self, "razao_social", razao_social)
        object.__setattr__(self, "cnpj", cnpj)
