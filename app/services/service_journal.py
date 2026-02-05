from datetime import datetime
from sqlalchemy import select, func

from app.exceptions.responses import ErrorPermissionDenied
from app.models.model_users import Users, teachers_students, RoleUser
from app.models.model_classroom import Classrooms
from app.models.model_tasks import Tasks
from app.models.model_works import Works, Answers, Assessments, StatusWork
from app.models.model_tasks import Criterions, Exercises
from app.schemas.schema_journal import (
    ClassroomPerformanse,
    FiltersClassroomJournalResponse,
    FiltersClassroomJournalRequest,
    NameFilter,
    StudentsPerformanseItem,
    StudentWorkPerformanse
)
from app.services.service_base import ServiceBase
from app.utils.logger import logger
from fastapi import HTTPException


class ServiceJournal(ServiceBase):

    async def get_filters(self, teacher: Users) -> FiltersClassroomJournalResponse:
        """
        Получение фильтров для журнала класса:
        - Список классов учителя
        - Список задач учителя
        - Диапазон дат (min/max из created_at работ)
        """
        try:
            if teacher.role is  RoleUser.student:
                raise ErrorPermissionDenied()

            # Получаем список классов учителя
            classrooms_stmt = (
                select(Classrooms.id, Classrooms.name)
                .where(Classrooms.teacher_id == teacher.id)
            )
            classrooms_result = await self.session.execute(classrooms_stmt)
            classrooms_rows = classrooms_result.all()
            classrooms = [
                NameFilter(id=row.id, name=row.name)
                for row in classrooms_rows
            ]

            # Получаем список задач учителя
            tasks_stmt = (
                select(Tasks.id, Tasks.name)
                .where(Tasks.teacher_id == teacher.id)
            )
            tasks_result = await self.session.execute(tasks_stmt)
            tasks_rows = tasks_result.all()
            tasks = [
                NameFilter(id=row.id, name=row.name)
                for row in tasks_rows
            ]

            # Получаем диапазон дат из работ учителя (min/max created_at)
            dates_stmt = (
                select(
                    func.min(Works.created_at).label("min_date"),
                    func.max(Works.created_at).label("max_date")
                )
                .select_from(Works)
                .join(Tasks, Works.task_id == Tasks.id)
                .where(Tasks.teacher_id == teacher.id)
            )
            dates_result = await self.session.execute(dates_stmt)
            dates_row = dates_result.first()

            # Форматируем даты в строки или используем пустые строки, если данных нет
            start_date = dates_row.min_date.strftime("%Y-%m-%d") if dates_row and dates_row.min_date else ""
            end_date = dates_row.max_date.strftime("%Y-%m-%d") if dates_row and dates_row.max_date else ""

            return FiltersClassroomJournalResponse(
                start_date=start_date,
                end_date=end_date,
                classrooms=classrooms,
                tasks=tasks
            )

        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get(self, filters: FiltersClassroomJournalRequest, teacher: Users) -> ClassroomPerformanse:
        """
        Получение данных журнала класса:
        - Информация о классе
        - Список студентов с их успеваемостью:
          - Количество верифицированных работ
          - Средний балл
          - Список работ
        """
        try:
            if teacher.role is  RoleUser.student:
                raise ErrorPermissionDenied()
            # Проверяем, что указан класс
            if not filters.classroom:
                raise HTTPException(status_code=400, detail="Classroom ID is required")

            # Получаем информацию о классе
            classroom_stmt = (
                select(Classrooms)
                .where(Classrooms.id == filters.classroom)
                .where(Classrooms.teacher_id == teacher.id)
            )
            classroom_result = await self.session.execute(classroom_stmt)
            classroom = classroom_result.scalar_one_or_none()

            if not classroom:
                raise HTTPException(status_code=404, detail="Classroom not found")

            # Получаем список студентов класса
            students_stmt = (
                select(Users.id, Users.first_name, Users.last_name)
                .select_from(teachers_students)
                .join(Users, teachers_students.c.student_id == Users.id)
                .where(teachers_students.c.teacher_id == teacher.id)
                .where(teachers_students.c.classroom_id == filters.classroom)
                .where(Users.role == RoleUser.student)
            )
            students_result = await self.session.execute(students_stmt)
            students_rows = students_result.all()

            # Для каждого студента получаем данные об успеваемости
            students_performance = []
            for student_row in students_rows:
                student_id = student_row.id
                full_name = f"{student_row.first_name} {student_row.last_name}"

                # Базовый запрос для получения работ студента с баллами
                works_stmt = (
                    select(
                        Works.id.label("work_id"),
                        Tasks.name.label("task_name"),
                        Works.status.label("status"),
                        func.sum(Assessments.points).label("score"),
                        func.sum(Criterions.score).label("max_score")
                    )
                    .select_from(Works)
                    .join(Tasks, Works.task_id == Tasks.id)
                    .outerjoin(Answers, Works.id == Answers.work_id)
                    .outerjoin(Exercises, Answers.exercise_id == Exercises.id)
                    .outerjoin(Criterions, Exercises.id == Criterions.exercise_id)
                    .outerjoin(
                        Assessments,
                        (Answers.id == Assessments.answer_id) &
                        (Criterions.id == Assessments.criterion_id)
                    )
                    .where(Works.student_id == student_id)
                    .where(Tasks.teacher_id == teacher.id)
                )

                # Применяем фильтры
                if filters.task:
                    works_stmt = works_stmt.where(Tasks.id == filters.task)

                # Преобразуем строковые даты в datetime для сравнения
                if filters.start_date:
                    try:
                        # Парсим дату в формате "YYYY-MM-DD"
                        start_date_dt = datetime.strptime(filters.start_date, "%Y-%m-%d")
                        works_stmt = works_stmt.where(Works.created_at >= start_date_dt)
                    except (ValueError, TypeError):
                        # Если дата невалидна, пропускаем фильтр
                        pass

                if filters.end_date:
                    try:
                        # Парсим дату в формате "YYYY-MM-DD" и добавляем время конца дня
                        end_date_dt = datetime.strptime(filters.end_date, "%Y-%m-%d")
                        # Добавляем 23:59:59 для включения всего дня
                        end_date_dt = end_date_dt.replace(hour=23, minute=59, second=59)
                        works_stmt = works_stmt.where(Works.created_at <= end_date_dt)
                    except (ValueError, TypeError):
                        # Если дата невалидна, пропускаем фильтр
                        pass

                # Группируем для агрегации баллов
                works_stmt = works_stmt.group_by(
                    Works.id,
                    Tasks.name,
                    Works.status
                )

                works_result = await self.session.execute(works_stmt)
                works_rows = works_result.all()

                # Формируем список работ
                works_list = []
                verificated_works_count = 0
                total_score = 0

                for work_row in works_rows:
                    work_id = work_row.work_id
                    task_name = work_row.task_name
                    status = work_row.status.value if work_row.status else "draft"
                    score = work_row.score if work_row.score is not None else 0
                    max_score = work_row.max_score if work_row.max_score is not None else 0

                    works_list.append(
                        StudentWorkPerformanse(
                            id=work_id,
                            name=task_name,
                            status=status
                        )
                    )

                    # Подсчитываем верифицированные работы и баллы
                    if work_row.status == StatusWork.verificated:
                        verificated_works_count += 1
                        total_score += score/max_score

                # Вычисляем средний балл (только для верифицированных работ)
                average_score = 0
                if verificated_works_count > 0:
                    # Средний балл в процентах, округленный до целого
                    average_score = round((total_score / verificated_works_count) * 100)

                students_performance.append(
                    StudentsPerformanseItem(
                        full_name=full_name,
                        verificated_works_count=verificated_works_count,
                        average_score=average_score,
                        works=works_list
                    )
                )

            return ClassroomPerformanse(
                id=str(classroom.id),
                name=classroom.name,
                students=students_performance
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(exc)
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error")
      
