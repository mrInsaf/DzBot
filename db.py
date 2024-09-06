import mysql
from mysql.connector import Error, pooling

# Параметры подключения к базе данных MySQL
config = {
    'user': 'stepan',
    'password': 'stepan',
    'host': '185.50.202.243',
    'database': 'input correct value',
}

pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **config
)


def get_connection():
    try:
        connection = pool.get_connection()
        if connection.is_connected():
            print("Успешное подключение к базе данных")
            return connection
    except mysql.connector.Error as e:
        print(f"Ошибка подключения: {e}")
        return None


def select(query):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.commit()
            return rows
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
        return None


def insert(table_name: str, data_list: list, auto_increment_id: int = 1):
    try:
        print("Start insert")

        # Получаем соединение из пула
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = [column[0] for column in cursor.fetchall()]
                columns = columns[auto_increment_id:]  # Убираем auto_increment, если нужно
                print(columns)

                placeholders = ', '.join(['%s'] * len(columns))
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                cursor.execute(query, data_list)
                row_id = cursor.lastrowid
                conn.commit()
                print("Finished insert")
                return row_id
            except Exception as e:
                print(f"Исключение при insert: {e}")
            finally:
                cursor.close()
                conn.close()  # Возвращает соединение в пул
        else:
            return None
    except Exception as e:
        print(f"Исключение при получении соединения: {e}")
        return None

