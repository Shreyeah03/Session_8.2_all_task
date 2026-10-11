# PyMySQL is a pure-Python MySQL driver, so no C compiler or system libs are needed.
try:
    import pymysql
    pymysql.version_info = (2, 2, 1, "final", 0)  # satisfy Django's mysqlclient version check
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
