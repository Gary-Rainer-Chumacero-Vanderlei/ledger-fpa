from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ledger_fpa.domain.conta_contabil import Natureza, TipoConta
from ledger_fpa.domain.partida_lancamento import TipoPartida


class Base(DeclarativeBase):
    """Base de todas as tabelas. O `metadata` guarda o catálogo do esquema."""


class EmpresaTabela(Base):
    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)


class ContaContabilTabela(Base):
    __tablename__ = "conta_contabil"
    __table_args__ = (UniqueConstraint("empresa_id", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    conta_pai_id: Mapped[int | None] = mapped_column(ForeignKey("conta_contabil.id"))
    codigo: Mapped[str] = mapped_column(String(50))
    nome: Mapped[str] = mapped_column(String(200))
    natureza: Mapped[Natureza] = mapped_column(Enum(Natureza))
    tipo: Mapped[TipoConta] = mapped_column(Enum(TipoConta))


class LancamentoTabela(Base):
    __tablename__ = "lancamento"
    __table_args__ = (UniqueConstraint("empresa_id", "lote"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    data: Mapped[date] = mapped_column(Date)
    lote: Mapped[int]
    historico: Mapped[str] = mapped_column(String(500))


class PartidaLancamentoTabela(Base):
    __tablename__ = "partida_lancamento"
    __table_args__ = (CheckConstraint("valor_centavos > 0"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lancamento_id: Mapped[int] = mapped_column(ForeignKey("lancamento.id"))
    conta_id: Mapped[int] = mapped_column(ForeignKey("conta_contabil.id"))
    tipo: Mapped[TipoPartida] = mapped_column(Enum(TipoPartida))
    valor_centavos: Mapped[int]


class FechamentoTabela(Base):
    __tablename__ = "fechamento"
    __table_args__ = (
        CheckConstraint("ano BETWEEN 1 AND 9999"),
        CheckConstraint("mes BETWEEN 1 AND 12"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), unique=True)
    ano: Mapped[int]
    mes: Mapped[int]
