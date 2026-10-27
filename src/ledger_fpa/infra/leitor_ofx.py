import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ParseError as XmlParseError

from ofxtools.header import OFXHeaderError
from ofxtools.Parser import OFXTree
from ofxtools.Parser import ParseError as OfxParseError

from ledger_fpa.domain.transacao_extrato import Sentido, TransacaoExtrato

_DATA = re.compile(r"[0-9]{8}")
_VALOR = re.compile(r"[+-]?[0-9]+(?:[.,][0-9]+)?")


class ArquivoOfxInvalido(Exception):
    """O arquivo não é um OFX legível ou tem uma transação inválida."""


def ler_extrato(origem: str | Path | BinaryIO) -> list[TransacaoExtrato]:
    """Lê um extrato bancário OFX e devolve as transações, na ordem do arquivo.

    Usa só a leitura da árvore do `ofxtools`, sem a conversão completa, para
    manter a data como o banco escreveu (ADR 0005). Transações de valor zero
    são ignoradas. O arquivo deve ter exatamente um extrato bancário.
    """
    raiz = _ler_arvore(origem)

    extratos = list(raiz.iter("STMTRS"))
    if not extratos:
        raise ArquivoOfxInvalido("O arquivo não contém um extrato bancário.")
    if len(extratos) > 1:
        raise ArquivoOfxInvalido("O arquivo tem mais de um extrato bancário.")

    transacoes = []
    for posicao, elemento in enumerate(raiz.iter("STMTTRN"), start=1):
        transacao = _ler_transacao(posicao, elemento)
        if transacao is not None:
            transacoes.append(transacao)

    return transacoes


def _ler_arvore(origem: str | Path | BinaryIO) -> Element:
    arvore = OFXTree()
    try:
        arvore.parse(origem)
    except (OFXHeaderError, OfxParseError, XmlParseError, UnicodeDecodeError) as erro:
        raise ArquivoOfxInvalido(
            f"Não foi possível ler o arquivo OFX: {erro}"
        ) from erro

    raiz = arvore.getroot()
    if raiz is None:
        raise ArquivoOfxInvalido("O arquivo OFX está vazio.")

    return raiz


def _texto(elemento: Element, nome: str) -> str:
    return (elemento.findtext(nome) or "").strip()


def _ler_transacao(posicao: int, elemento: Element) -> TransacaoExtrato | None:
    data = _ler_data(posicao, _texto(elemento, "DTPOSTED"))
    valor = _ler_valor(posicao, _texto(elemento, "TRNAMT"))

    if valor == 0:
        return None

    try:
        return TransacaoExtrato(
            data=data,
            historico=_texto(elemento, "MEMO") or _texto(elemento, "NAME"),
            valor=abs(valor),
            sentido=Sentido.SOMA if valor > 0 else Sentido.SUBTRAI,
            identificador=_texto(elemento, "FITID"),
            documento=_texto(elemento, "CHECKNUM") or _texto(elemento, "REFNUM"),
        )
    except ValueError as erro:
        raise ArquivoOfxInvalido(f"Transação {posicao}: {erro}") from erro


def _ler_data(posicao: int, texto: str) -> date:
    """Usa os oito primeiros caracteres: a data escrita pelo banco, sem fuso."""
    bruto = texto[:8]
    try:
        if not _DATA.fullmatch(bruto):
            raise ValueError(bruto)
        return datetime.strptime(bruto, "%Y%m%d").date()
    except ValueError as erro:
        raise ArquivoOfxInvalido(
            f"Transação {posicao}: data inválida ({texto!r})."
        ) from erro


def _ler_valor(posicao: int, texto: str) -> Decimal:
    if not _VALOR.fullmatch(texto):
        raise ArquivoOfxInvalido(f"Transação {posicao}: valor inválido ({texto!r}).")

    return Decimal(texto.replace(",", "."))
