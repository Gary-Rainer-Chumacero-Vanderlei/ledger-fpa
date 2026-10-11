from sqlalchemy import create_engine, text


def test_conecta_ao_sqlite_em_memoria():
    engine = create_engine("sqlite:///:memory:")

    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT 1")).scalar()

    assert resultado == 1
