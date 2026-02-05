from app.models.model_users import RoleUser, Users
from app.schemas.schema_work import (
    WorksFilterResponseTeacher,
    WorksFilterResponseStudent,
    UserItem,
    ClassroomItem,
    SubjectItem,
    DatesRange
)


class TransformerWorks:
    
    @staticmethod
    def handle_filters_response(user: Users, rows) -> WorksFilterResponseTeacher | WorksFilterResponseStudent | None:
        """
        Обрабатывает ответ с фильтрами работ, собирая все данные из rows в один объект.
        Возвращает один объект WorksFilterResponseTeacher или WorksFilterResponseStudent.
        """
        # Инициализация структур для сбора данных
        if user.role is RoleUser.teacher:
            students_set = set()  # Множество для уникальных студентов (id, name)
        elif user.role is RoleUser.student:
            teachers_set = set()  # Множество для уникальных учителей (id, name)

        classrooms_set = set()  # Множество для уникальных классов (id, name)
        statuses_set = set()  # Множество для уникальных статусов
        tasks_dict = {}  # Словарь: название задачи -> множество ID задач
        subjects_set = set()  # Множество для уникальных предметов (id, name)
        dates_min = None  # Минимальная дата
        dates_max = None  # Максимальная дата

        # Обработка всех строк из rows
        for row in rows:
            # Обработка студентов (для учителя) или учителей (для студента)
            if user.role is RoleUser.teacher:
                if row.get("student_id") and row.get("student_name"):
                    students_set.add((row["student_id"], row["student_name"]))
            elif user.role is RoleUser.student:
                if row.get("teacher_id") and row.get("teacher_name"):
                    teachers_set.add((row["teacher_id"], row["teacher_name"]))
            
            # Обработка классов
            if row.get("classroom_id") and row.get("classroom_name"):
                classrooms_set.add((row["classroom_id"], row["classroom_name"]))
                
            # Обработка статусов
            if row.get("status"):
                statuses_set.add(row["status"])

            # Обработка задач
            if row.get("name") and row.get("task_id"):
                task_name = row["name"]
                task_id = row["task_id"]
                
                if task_name not in tasks_dict:
                    tasks_dict[task_name] = set()
                    
                tasks_dict[task_name].add(task_id)

            # Обработка дат
            if row.get("created_at"):
                row_date = row["created_at"].date()
                if dates_min is None:
                    dates_min = row_date
                    dates_max = row_date
                else:
                    dates_min = min(dates_min, row_date)
                    dates_max = max(dates_max, row_date)

            # Обработка предметов
            if row.get("subject_id") and row.get("subject"):
                subjects_set.add((row["subject_id"], row["subject"]))

        # Формирование объекта DatesRange, если есть даты
        dates_range = None
        if dates_min is not None and dates_max is not None:
            dates_range = DatesRange(min=dates_min, max=dates_max)

        # Преобразование множеств в списки объектов и формирование финального ответа
        if user.role is RoleUser.teacher:
            # Формирование списка студентов
            students_list = [
                UserItem(id=student_id, name=student_name)
                for student_id, student_name in students_set
            ]
            
            # Формирование списка классов
            classrooms_list = [
                ClassroomItem(id=classroom_id, name=classroom_name)
                for classroom_id, classroom_name in classrooms_set
            ]
            
            # Формирование списка статусов
            statuses_list = list(statuses_set)
            
            # Преобразование словаря задач: множество -> список
            tasks_dict_final = {
                task_name: list(task_ids)
                for task_name, task_ids in tasks_dict.items()
            }
            
            # Формирование списка предметов
            subjects_list = [
                SubjectItem(id=subject_id, name=subject_name)
                for subject_id, subject_name in subjects_set
            ]
            
            # Возврат одного объекта WorksFilterResponseTeacher
            return WorksFilterResponseTeacher(
                students=students_list,
                classrooms=classrooms_list,
                statuses=statuses_list,
                dates=dates_range,
                tasks=tasks_dict_final,
                subjects=subjects_list
            )
        
        elif user.role is RoleUser.student:
            # Формирование списка учителей
            teachers_list = [
                UserItem(id=teacher_id, name=teacher_name)
                for teacher_id, teacher_name in teachers_set
            ]
            
            # Формирование списка статусов
            statuses_list = list(statuses_set)
            
            # Преобразование словаря задач: множество -> список
            tasks_dict_final = {
                task_name: list(task_ids)
                for task_name, task_ids in tasks_dict.items()
            }
            
            # Формирование списка предметов
            subjects_list = [
                SubjectItem(id=subject_id, name=subject_name)
                for subject_id, subject_name in subjects_set
            ]
            
            # Возврат одного объекта WorksFilterResponseStudent
            return WorksFilterResponseStudent(
                teachers=teachers_list,
                statuses=statuses_list,
                dates=dates_range,
                tasks=tasks_dict_final,
                subjects=subjects_list
            )
        
        return None
        

