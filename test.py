from db import *

assignments = select_assignments_by_group_id_and_subject_id(3, 8)
for ass in assignments:
    print(ass)

