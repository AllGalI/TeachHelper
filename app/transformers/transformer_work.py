from app.models.model_users import RoleUser, Users
from app.schemas.schema_work import WorksFilterResponseTeacher


class TransformerWorks:
    
    @staticmethod
    def handle_filters_response(user: Users, rows)-> list[WorksFilterResponseTeacher] | None:
        response = {}
        
        if user.role is RoleUser.teacher:
            response["students"] = set()
        elif user.role is RoleUser.student:
            response["teachers"] = set()

        response["classrooms"] = set()
        response["statuses"] = set()
        response["dates"] = None
        response["tasks"] = {}
        response["subjects"] = set()

        # for row in rows:
        #     if user.role is RoleUser.teacher:
        #         if row["student_id"]:
        #             response["students"].add((row["student_id"], row["student_name"]))
        #     elif user.role is RoleUser.student:
        #         if row["teacher_id"]:
        #             response["teachers"].add((row["teacher_id"], row["teacher_name"]))
            
        #     if row["classroom_id"]:
        #         response["classrooms"].add((row["classroom_id"], row["classroom_name"]))
                
        #     if row["status"]:
        #         response["statuses"].add(row["status"])

        #     if row["name"]:
        #         task_name = row["name"]
        #         task_id = row["task_id"]

        #         if task_name:
        #             if task_name not in response["tasks"]:
        #                 response["tasks"][task_name] = set()
                    
        #             response["tasks"][task_name].add(task_id)

        #     if row["created_at"]:
        #         row_date = row["created_at"].date()
        #         if response["dates"]:
        #             response["dates"]["min"] = min(response["dates"]["min"], row_date)
        #             response["dates"]["max"] = max(response["dates"]["max"], row_date)
        #         else:
        #             response["dates"] = {"min": None, "max": None}
        #             response["dates"]["min"] = row_date
        #             response["dates"]["max"] = row_date

        #     if row["subject_id"]:
        #         response["subjects"].add((row["subject_id"], row["subject"]))
        if user.role is RoleUser.teacher:
          return [WorksFilterResponseTeacher.model_validate(row) for row in rows]
        

