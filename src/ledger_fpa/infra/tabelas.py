from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ledger_fpa.domain.conta_contabil import Natureza, TipoConta


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
