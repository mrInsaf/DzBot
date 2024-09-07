import datetime

import mysql
from mysql.connector import Error, pooling

# Параметры подключения к базе данных MySQL
config = {
    'user': 'stepan',
    'password': 'stepan',
    'host': '185.50.202.243',
    'database': 'dz_bot',
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


def execute_query(query, params):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
        finally:
            cursor.close()
            conn.close()  # Возвращает соединение в пул
    else:
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
                print(query)

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


def check_student_in_db(chat_id: int):
    student = select(f'select * from Students where chat_id = {chat_id}')
    return len(student) != 0


def select_all_groups():
    return select(f'select * from `Groups`')


def select_group_id_by_chat_id(chat_id: int):
    return select(f'select group_id from Students where chat_id = {chat_id}')[0][0]


def select_assignments_by_group_id(group_id: int):
    assignments_raw = select(
        f'select s.name, deadline, description from Assignments a '
        f'join Subjects s on a.subject_id = s.id '
        f'where group_id = {group_id} '
        f'order by deadline asc'
    )
    return assignments_raw


def select_subjects_by_group_id(group_id: int):
    return select(
        f'SELECT s.id, s.name from Subjects s join Group_Subject gs '
        f'on s.id = gs.subject_id join `Groups` g '
        f'on g.id = gs.group_id where g.id = {group_id};'
    )


def select_subject_by_subject_id(subject_id: int):
    return select(f'select name from Subjects where id = {subject_id}')[0][0]


def insert_student(name: str, chat_id: int, tag: str, group_id: int):
    data_list = [name, chat_id, tag, group_id]
    return insert("Students", data_list)


def insert_assignment(subject_id: int, group_id: int, description: str, deadline: datetime.datetime):
    query = """
    INSERT INTO Assignments (subject_id, group_id, description, deadline)
    VALUES (%s, %s, %s, %s)
    """
    params = (subject_id, group_id, description, deadline.strftime('%Y-%m-%d %H:%M:%S'))
    execute_query(query, params)




