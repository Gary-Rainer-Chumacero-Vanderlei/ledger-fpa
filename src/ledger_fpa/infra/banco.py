from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry


def _ligar_chaves_estrangeiras(
    conexao: DBAPIConnection, _registro: ConnectionPoolEntry
) -> None:
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def criar_engine(url: str) -> Engine:
    """Cria o engine do banco, ligando as chaves estrangeiras no SQLite.

    O SQLite ignora as chaves estrangeiras por padrão. Sem o PRAGMA, o banco
    aceitaria, por exemplo, uma conta de uma empresa que não existe.
    """
    engine = create_engine(url)

    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _ligar_chaves_estrangeiras)

    return engine
