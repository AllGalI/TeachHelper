import uuid
from fastapi import HTTPException
from sqlalchemy import case, func, select

from app.models.model_classroom import Classrooms
from app.models.model_subjects import Subjects
from app.models.model_tasks import Criterions, Exercises, Tasks
from app.models.model_users import RoleUser, Users, teachers_students
from app.models.model_works import Assessments, StatusWork, Works, Answers
from app.schemas.schema_work import SmartFiltersWorkStudent, SmartFiltersWorkTeacher, WorkAllFilters
from app.utils.logger import logger

class RepoWorks():
    def __init__(self, session):
        self.session = session

    async def get_all(self, filters: WorkAllFilters, user: Users):
        # 1. Определяем алиасы для удобства
        # Используем алиас для связей, которые будут использоваться в агрегации
        
        # Набранный балл: сумма баллов тех критериев Criterions, где Assessments.points - это баллы
        # Используем CASE для условного суммирования
        
        # 3. Базовый запрос с JOINs
        stmt = (
            select(
                Works.id.label("id"),
                func.concat(Users.first_name, " ", Users.last_name).label("student_name"),
                Tasks.name.label("task_name"),
                func.sum(Assessments.points).label("score"),
                func.sum(Criterions.score).label("max_score"),
                Works.status.label("status_work")
            )
            .select_from(Works)
            .join(Users, Works.student_id == Users.id) 
            .join(Tasks, Works.task_id == Tasks.id)
            .join(Answers, Works.id == Answers.work_id) 
            .join(Exercises, Answers.exercise_id == Exercises.id)
            .join(Criterions, Exercises.id == Criterions.exercise_id)
            .join(Assessments, (Answers.id == Assessments.answer_id) & (Criterions.id == Assessments.criterion_id))
            .join(Subjects, Tasks.subject_id == Subjects.id, isouter=True)
        )

        # 4. Группировка
        # Группируем по уникальным полям работы, чтобы агрегировать баллы (SUM)
        stmt = stmt.group_by(
            Works.id,
            Users.first_name,
            Users.last_name,
            Tasks.name,
            Works.status
        )

        # 5. Фильтрация по роли пользователя
        if user.role == RoleUser.student:
            stmt = stmt.where(Works.student_id == user.id)
        elif user.role == RoleUser.teacher:
            stmt = stmt.where(Tasks.teacher_id == user.id)
            stmt = stmt.join(teachers_students, user.id == teachers_students.c.teacher_id )

            if filters.classroom_id:
                stmt = stmt.join(Classrooms, teachers_students.c.classroom_id == Classrooms.id)
                stmt = stmt.where(Classrooms.id == filters.classroom_id)

            if filters.student_id:
                stmt = stmt.where(Works.student_id == filters.student_id)

        # 6. Фильтрация по параметрам WorkAllFilters
        if filters.subject_id:
            stmt = stmt.where(Tasks.subject_id == filters.subject_id)


        if filters.status_work:
            stmt = stmt.where(Works.status == filters.status_work)


        # 7. Выполнение запроса и расчет процента
        result = await self.session.execute(stmt)
        # Получаем список кортежей (id, student_name, task_name, score, max_score, status_work)
        return result.all()


    async def get_all_student(
        self,
        user: Users,
        subject_id: uuid.UUID|None = None,
        status_work: StatusWork| None = None,
    ):

        stmt = (
            select(
                Works.id.label("id"),
                func.concat(Users.first_name, " ", Users.last_name).label("student_name"),
                Tasks.name.label("task_name"),
                func.sum(Assessments.points).label("score"),
                func.sum(Criterions.score).label("max_score"),
                Works.status.label("status_work")
            )
            .select_from(Works)
            .join(Users, Works.student_id == Users.id) 
            .join(Tasks, Works.task_id == Tasks.id)
            .join(Answers, Works.id == Answers.work_id) 
            .join(Exercises, Answers.exercise_id == Exercises.id)
            .join(Criterions, Exercises.id == Criterions.exercise_id)
            .join(Assessments, (Answers.id == Assessments.answer_id) & (Criterions.id == Assessments.criterion_id))
            .join(Subjects, Tasks.subject_id == Subjects.id, isouter=True)
        )

        stmt = stmt.group_by(
            Works.id,
            Users.first_name,
            Users.last_name,
            Tasks.name,
            Works.status
        )

        # 5. Фильтрация по роли пользователя

        stmt = stmt.where(Works.student_id == user.id)

        # 6. Фильтрация по параметрам WorkAllFilters
        if subject_id:
            stmt = stmt.where(Tasks.subject_id == subject_id)


        if status_work:
            stmt = stmt.where(Works.status == status_work)


        # 7. Выполнение запроса и расчет процента
        result = await self.session.execute(stmt)
        # Получаем список кортежей (id, student_name, task_name, score, max_score, status_work)
        return result.all()

    async def get_all_teacher(
        self,
        user: Users,
        student: uuid.UUID|None = None,
        subject: uuid.UUID|None = None,
        statuses: list[StatusWork]| None = None,
    ):


        stmt = (
            select(
                Works.id.label("id"),
                func.concat(Users.first_name, " ", Users.last_name).label("student_name"),
                Tasks.name.label("task_name"),
                Subjects.name.label('subject'),
                func.sum(Assessments.points).label("score"),
                func.sum(Criterions.score).label("max_score"),
                Works.status.label("status")
            )
            .select_from(Tasks)
            .where(Tasks.teacher_id == user.id)
        )

        stmt = stmt.join(Subjects, Tasks.subject_id == Subjects.id)
        if subject is not None:
            stmt = stmt.where(Subjects.id == subject)

        stmt = stmt.join(Works, Tasks.id == Works.task_id)
        if statuses is not None :
            stmt = stmt.where(Works.status.in_(statuses))

        if student is not None:
            stmt = stmt.where(Works.student_id == student)
        
        stmt = (
            stmt.join(Users, Works.student_id == Users.id) 
            .join(Answers, Works.id == Answers.work_id) 
            .join(Exercises, Answers.exercise_id == Exercises.id)
            .join(Criterions, Exercises.id == Criterions.exercise_id)
            .join(Assessments, (Answers.id == Assessments.answer_id) & (Criterions.id == Assessments.criterion_id))
        )

        stmt = stmt.group_by(
            Works.id,
            Users.first_name,
            Users.last_name,
            Subjects.name,
            Tasks.name,
            Works.status
        )

        result = await self.session.execute(stmt)
        # Получаем список кортежей (id, student_name, task_name, score, max_score, status_work)
        return result.all()

    async def get_smart_filters_teacher(self, teacher_id: uuid.UUID, filters: SmartFiltersWorkTeacher): 
        try:
            stmt = (
                select(
                    teachers_students.c.student_id  ,
                    func.concat(Users.first_name, " ", Users.last_name).label("student_name"),

                    teachers_students.c.classroom_id,
                    Classrooms.name.label("classroom_name"),

                    Works.status,
                    Works.created_at,

                    Tasks.id.label('task_id'),
                    Tasks.name.label('name'),

                    Subjects.id.label('subject_id'),
                    Subjects.name.label('subject'),
                )
                .select_from(teachers_students)
                .join(Users, teachers_students.c.student_id == Users.id)
                .outerjoin(Classrooms, teachers_students.c.classroom_id == Classrooms.id)
                .outerjoin(Works, Users.id == Works.student_id)
                .outerjoin(Tasks, Works.task_id == Tasks.id)
                .outerjoin(Subjects, Tasks.subject_id == Subjects.id)
                .where(teachers_students.c.teacher_id == teacher_id)
                .where(Tasks.teacher_id == teacher_id)
            )

            # 2. Применение динамических фильтров
            if filters.students_ids:
                stmt = stmt.where(Users.id.in_(filters.students_ids))

            if filters.classrooms_ids:
                stmt = stmt.where(Classrooms.id.in_(filters.classrooms_ids))

            if filters.statuses:
                stmt = stmt.where(Works.status.in_(filters.statuses))

            if filters.tasks_ids:                
                stmt = stmt.where(Tasks.id.in_(filters.tasks_ids))

            if filters.subject_id:
                stmt = stmt.where(Subjects.id == filters.subject_id)

            if filters.min:
                stmt = stmt.where(Works.created_at >= filters.min)

            if filters.max:
                stmt = stmt.where(Works.created_at <= filters.max)

            # 4. Добавляем DISTINCT, чтобы не было дублей при множественных связях
            stmt = stmt.distinct()

            response = await self.session.execute(stmt)
            return response.mappings().all()

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
    async def get_smart_filters_student(self, student_id: uuid.UUID, filters: SmartFiltersWorkStudent): 

        try:
            stmt = (
                select(
                    teachers_students.c.teacher_id  ,
                    func.concat(Users.first_name, " ", Users.last_name).label("teacher_name"),

                    teachers_students.c.classroom_id,
                    Classrooms.name.label("classroom_name"),

                    Works.status,
                    Works.created_at,

                    Tasks.id.label('task_id'),
                    Tasks.name.label('name'),

                    Subjects.id.label('subject_id'),
                    Subjects.name.label('subject'),
                )
                .select_from(teachers_students)
                .join(Users, teachers_students.c.teacher_id == Users.id)
                .outerjoin(Classrooms, teachers_students.c.classroom_id == Classrooms.id)
                .outerjoin(Tasks, Users.id == Tasks.teacher_id)
                .outerjoin(Works, Tasks.id == Works.task_id)
                .outerjoin(Subjects, Tasks.subject_id == Subjects.id)
                .where(teachers_students.c.student_id == student_id)
                .where(Works.student_id == student_id)
            )

            # 2. Применение динамических фильтров
            if filters.teachers_ids:
                stmt = stmt.where(Users.id.in_(filters.teachers_ids))

            if filters.classrooms_ids:
                stmt = stmt.where(Classrooms.id.in_(filters.classrooms_ids))

            if filters.statuses:
                stmt = stmt.where(Works.status.in_(filters.statuses))

            if filters.tasks_ids:                
                stmt = stmt.where(Tasks.id.in_(filters.tasks_ids))

            if filters.subject_id:
                stmt = stmt.where(Subjects.id == filters.subject_id)

            if filters.min:
                stmt = stmt.where(Works.created_at >= filters.min)

            if filters.max:
                stmt = stmt.where(Works.created_at <= filters.max)

            # 4. Добавляем DISTINCT, чтобы не было дублей при множественных связях
            stmt = stmt.distinct()

            response = await self.session.execute(stmt)
            return response.mappings().all()

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
      