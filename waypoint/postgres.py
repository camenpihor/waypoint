from contextlib import contextmanager

import psycopg2


@contextmanager
def connect(url):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(url)
        cursor = connection.cursor()
        yield cursor
        connection.commit()
    except Exception as error:
        if connection:
            connection.rollback()
        raise error
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
