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
    from misc import caller_func
    try:
        connection = pool.get_connection()
        if connection.is_connected():
            print(f"Успешное подключение к базе данных. Из {caller_func()}")
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


def select_assignment_by_id(assignment_id: int):
    assignment_list = select(
        f'select s.name, a.group_id, a.description, a.deadline, a.id, s.id from Assignments a join Subjects s '
        f'on a.subject_id = s.id '
        f'where a.id = {assignment_id} '
        f''
    )[0]
    assignment_obj = Assignment(
        subject=assignment_list[0],
        group_id=assignment_list[1],
        description=assignment_list[2],
        deadline=assignment_list[3],
        id=assignment_list[4],
        subject_id=assignment_list[5]
    )
    return assignment_obj


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


def select_students_chat_ids_by_group_id(group_id: int):
    return select(f"select chat_id from Students where group_id = {group_id}")


def insert_student(name: str, chat_id: int, tag: str, group_id: int):
    data_list = [name, chat_id, tag, group_id]
    return insert("Students", data_list)


def insert_assignment(subject_id: int, group_id: int, description: str, deadline: Deadline):
    insert_query = """
    INSERT INTO Assignments (subject_id, group_id, description, deadline)
    VALUES (%s, %s, %s, %s)
    """
    params = (subject_id, group_id, description, deadline.dttm)

    with get_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(insert_query, params)
            conn.commit()

            # Получаем последний вставленный ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            last_id = cursor.fetchone()[0]

        finally:
            cursor.close()

    return last_id


def select_assignments_by_group_id(group_id: int):
    from misc import create_assignments_list
    raw_assignments = select(
        f'SELECT a.id, s.name, a.group_id, a.description, a.deadline, a.created_at '
        f'from Assignments a '
        f'join Subjects s on a.subject_id = s.id '
        f'where a.group_id = {group_id}'
    )

    assignment_list = create_assignments_list(raw_assignments)
    return assignment_list


def select_assignments_by_group_id_and_subject_id(group_id: int, subject_id: int):
    from misc import create_assignments_list
    raw_assignments = select(
        f'SELECT a.id, s.name, a.group_id, a.description, a.deadline, a.created_at, a.subject_id '
        f'from Assignments a '
        f'join Subjects s on a.subject_id = s.id '
        f'where a.group_id = {group_id} and a.subject_id = {subject_id}')
    assignment_list = create_assignments_list(raw_assignments)
    return assignment_list


def update_description_by_assignment_id(assignment_id: int, new_description: str):
    query = f"UPDATE Assignments SET description = %s WHERE id = %s;"
    params = [new_description, assignment_id]
    execute_query(query, params)


def update_deadline_by_assignment_id(assignment_id: int, new_deadline: Deadline):
    query = f"UPDATE Assignments SET deadline = %s WHERE id = %s;"
    params = [new_deadline.dttm, assignment_id]
    execute_query(query, params)


def select_leaders():
    return select(f'select * from Leaders')


def select_leader_name_by_id(leader_id: int):
    return select(f'select name from Leaders where id = {leader_id}')


def select_leader_id_by_chat_id(chat_id: int):
    return select(f'select id from Leaders where chat_id = {chat_id}')[0][0]


def select_leader_with_same_subject(subject_id: int, current_leader_tag: str):
    return select(f'select l.chat_id, l.name, l.id from Group_Subject gs '
                  f'join Leaders l '
                  f'on l.group_id = gs.group_id '
                  f'where subject_id = {subject_id} and l.tag != "{current_leader_tag}"')


def insert_shared_assignment_to_queue(sender_id: int, receiver_id: int, assignment_id: int):
    query = """
    INSERT INTO AssignmentQueue (sender_id, receiver_id, assignment_id)
    VALUES (%s, %s, %s)
    """
    params = (sender_id, receiver_id, assignment_id)

    execute_query(query, params)


def fetch_assignments_queue(receiver_id: int):
    assignments = select(
        f'''SELECT 
                aq.assignment_id, 
                sender.name AS sender_name, 
                receiver.name AS receiver_name, 
                aq.id 
            FROM 
                AssignmentQueue aq 
            JOIN 
                Leaders sender ON aq.sender_id = sender.id 
            JOIN 
                Leaders receiver ON aq.receiver_id = receiver.id
            WHERE receiver.chat_id = {receiver_id} AND aq.status = "pending"'''
    )
    return assignments


def update_assignments_queue(shared_assignment_id: int):
    execute_query('UPDATE `AssignmentQueue` set status = "sent" WHERE id = %s', params=[shared_assignment_id])

