import datetime


class Deadline:
    dttm: datetime.datetime  # Аннотация типа для атрибута
    string: str
    day_of_week: str
    days_remaining: int

    def __init__(self, deadline_dttm: datetime.datetime):
        # Инициализация атрибутов экземпляра класса
        self.dttm = deadline_dttm
        self.string = self.dttm.strftime("%d.%m.%Y")

        # Определение дня недели
        days_of_week = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье"
        }
        self.day_of_week = days_of_week[self.dttm.weekday()]

        # Вычисление оставшихся дней
        self.days_remaining = (self.dttm.date() - datetime.datetime.now().date()).days

    def __str__(self) -> str:
        return (f"Deadline(Дата: {self.string}, День недели: {self.day_of_week}, "
                f"Осталось дней: {self.days_remaining})")

