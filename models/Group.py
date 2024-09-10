class Group:
    group_id: int
    group_name: str

    def __init__(self, group_id, group_name):
        self.group_id = group_id
        self.group_name = group_name

    def __str__(self):
        return f"Group №{self.group_id} {self.group_name}"
