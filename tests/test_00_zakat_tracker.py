import zakat


def test_zakat_tracker():
    zakat.test(
        debug=True,
        dict_model=True,
        sqlite_model=True,
        mysql_model=False,
        mariadb_model=False,
        postgresql_model=False,
        cockroachdb_model=False,
    )
