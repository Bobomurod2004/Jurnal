from config import *
from connector import PostgreSQLConnector
from translations import *

dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

for k, v in UZ.items():
    _res = dbc.translations.get(alias=k).exec()
    if _res:
        dbc.translations.get(alias=k).update(content_uz=v).exec()
    else:
        dbc.translations.add(
            alias = k,
            content_uz = v
        ).exec()

for k, v in EN.items():
    _res = dbc.translations.get(alias=k).exec()
    if _res:
        dbc.translations.get(alias=k).update(content=v).exec()
    else:
        dbc.translations.add(
            alias = k,
            content = v
        ).exec()

for k, v in RU.items():
    _res = dbc.translations.get(alias=k).exec()
    if _res:
        dbc.translations.get(alias=k).update(content_ru=v).exec()
    else:
        dbc.translations.add(
            alias = k,
            content_ru = v
        ).exec()
