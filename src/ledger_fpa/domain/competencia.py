from dataclasses import dataclass
from datetime import date
from typing import Self


@dataclass(frozen=True, order=True)
class Competencia:
    """Mês contábil, identificado por ano e mês.

    É imutável e ordenável: compara primeiro o ano e depois o mês.
    """

    ano: int
    mes: int

    def __post_init__(self) -> None:
        for valor in (self.ano, self.mes):
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise TypeError("Ano e mês devem ser inteiros.")

        if not 1 <= self.ano <= 9999:
            raise ValueError("O ano deve estar entre 1 e 9999.")

        if not 1 <= self.mes <= 12:
            raise ValueError("O mês deve estar entre 1 e 12.")

    @classmethod
    def de_data(cls, data: date) -> Self:
        """Competência do mês a que a data pertence."""
        return cls(ano=data.year, mes=data.month)

    def proxima(self) -> Self:
        """Competência do mês seguinte."""
        if self.mes == 12:
            return type(self)(ano=self.ano + 1, mes=1)

        return type(self)(ano=self.ano, mes=self.mes + 1)

    def __str__(self) -> str:
        return f"{self.mes:02d}/{self.ano}"
