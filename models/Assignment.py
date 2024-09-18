from datetime import datetime

from models.Deadline import Deadline


class Assignment:
    def __init__(self,
                 id: int = None,
                 subject_id: int = None,
                 subject: str = None,
                 group_id: int = None,
                 description: str = None,
                 deadline: datetime = None,
                 created_at: datetime = None):
        self.id = id
        self.subject = subject
        self.subject_id = subject_id
        self.group_id = group_id
        self.description = description
        self.deadline = Deadline(deadline_dttm=deadline)
        self.created_at = created_at if created_at else datetime.now()

    def __repr__(self):
        return (f"Assignment(id={self.id}, subject_id={self.subject_id}, subject={self.subject}, group_id={self.group_id}, "
                f"description='{self.description}', deadline={self.deadline}, created_at={self.created_at})")