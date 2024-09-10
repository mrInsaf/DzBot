import datetime
from typing import List

import mysql
from mysql.connector import Error, pooling

from models.Assignment import Assignment
from models.Deadline import Deadline
from models.Group import Group

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


def select_assignments_by_subject_id(subject_id: int):
    return select(f'SELECT * FROM Assignments WHERE subject_id = {subject_id}')


def select_subjects_by_group_id(group_id: int):
    return select(
        f'SELECT s.id, s.name from Subjects s join Group_Subject gs '
        f'on s.id = gs.subject_id join `Groups` g '
        f'on g.id = gs.group_id where g.id = {group_id};'
    )


def select_group_by_subject_id(subject_id: int) -> List[Group]:
    result = []
    group_list = select(
        f'SELECT group_id, g.name from Group_Subject gs '
        f'join `Groups` g on gs.group_id = g.id '
        f'where subject_id = {subject_id};'
    )
    for group in group_list:
        result.append(Group(group[0], group[1]))
    return result


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


def select_assignments_by_group_id_and_subject_id(group_id: int, subject_id: int):
    raw_assignments = select(
        f'SELECT a.id, s.name, a.group_id, a.description, a.deadline, a.created_at '
        f'from Assignments a '
        f'join Subjects s on a.subject_id = s.id '
        f'where a.group_id = {group_id} and a.subject_id = {subject_id}')
    assignment_list = []
    for assignment in raw_assignments:
        assignment_list.append(
            Assignment(
                id=assignment[0],
                subject=assignment[1],
                group_id=assignment[2],
                description=assignment[3],
                deadline=assignment[4],
                created_at=assignment[5],
            )
        )
    return assignment_list


def update_description_by_assignment_id(assignment_id: int, new_description: str):
    query = f"UPDATE Assignments SET description = %s WHERE id = %s;"
    params = [new_description, assignment_id]
    execute_query(query, params)


def update_deadline_by_assignment_id(assignment_id: int, new_deadline: Deadline):
    query = f"UPDATE Assignments SET deadline = %s WHERE id = %s;"
    params = [new_deadline.dttm, assignment_id]
    execute_query(query, params)




