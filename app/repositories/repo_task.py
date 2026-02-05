from time import time
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.model_tasks import Exercises, Tasks
from app.models.model_works import Assessments, Answers, Works
from app.models.model_subjects import Subjects
from app.schemas.schema_tasks import TaskRead, TasksFilters
from app.utils.logger import logger

class RepoTasks():
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get(self, id: uuid.UUID):
        stmt = (
            select(Tasks)
            .where(Tasks.id == id)
            .options(
                selectinload(Tasks.exercises)
                .selectinload(Exercises.criterions),
                selectinload(Tasks.exercises)
            )
        )
        response = await self.session.execute(stmt)
        return response.scalars().first()

    async def create_works(
        self,
        task: Tasks,
        students_ids: list[uuid.UUID]
    ):
        stmt = select(Works.student_id).where(Works.task_id == task.id).where(Works.student_id.in_(students_ids))
        response = await self.session.execute(stmt)
        excluded_ids = response.scalars().all()
        works = []
        for student_id in students_ids:
            if student_id not in excluded_ids:
                works.append(Works(task_id=task.id, student_id=student_id))
                

        self.session.add_all(works)
        await self.session.flush()

        all_answers = []
        all_a_criterions = []

        for work in works:
            # Проверяем, что task.exercises существует и является списком (из-за relationship)
            if hasattr(task, 'exercises') and task.exercises: 
                for exercise in task.exercises:
                    # Создаем Answer
                    answer = Answers(id=uuid.uuid4(), work_id=work.id, exercise_id=exercise.id)
                    all_answers.append(answer)

                    # Создаем Assessments для этого Answer
                    if hasattr(exercise, 'criterions') and exercise.criterions:
                        a_criterions = [
                            Assessments(
                                answer_id=answer.id, 
                                criterion_id=e_criterion.id
                            ) 
                            for e_criterion in exercise.criterions
                        ]
                        all_a_criterions.extend(a_criterions)

        self.session.add_all(all_answers)
        self.session.add_all(all_a_criterions)

    async def get_filters(self, teacher_id: uuid.UUID):
        """
        Получение доступных фильтров для учителя: список предметов и задач
        """
        # Запрос для получения уникальных предметов, используемых в задачах учителя
        subjects_stmt = (
            select(
                Subjects.id.label("subject_id"),
                Subjects.name.label("subject_name")
            )
            .select_from(Tasks)
            .join(Subjects, Tasks.subject_id == Subjects.id)
            .where(Tasks.teacher_id == teacher_id)
            .distinct()
        )
        subjects_result = await self.session.execute(subjects_stmt)
        subjects_rows = subjects_result.mappings().all()

        # Запрос для получения уникальных задач учителя
        tasks_stmt = (
            select(
                Tasks.id.label("task_id"),
                Tasks.name.label("task_name")
            )
            .where(Tasks.teacher_id == teacher_id)
            .distinct()
        )
        tasks_result = await self.session.execute(tasks_stmt)
        tasks_rows = tasks_result.mappings().all()

        return {
            "subjects": subjects_rows,
            "tasks": tasks_rows
        }

    async def get_all(self, teacher_id: uuid.UUID, filters: TasksFilters):
        """
        Получение списка задач учителя с применением фильтров
        """
        stmt = (
            select(
                Tasks.id,
                Tasks.name,
                Tasks.subject_id,
                Subjects.name.label("subject"),  # Название предмета
                Tasks.updated_at
            )
            .join(Subjects, Tasks.subject_id == Subjects.id)
            .where(Tasks.teacher_id == teacher_id)
        )
        
        # Применяем фильтр по task_id, если указан
        if filters.task_id is not None:
            stmt = stmt.where(Tasks.id == filters.task_id)

        if filters.subject_id is not None:
            stmt = stmt.where(Tasks.subject_id == filters.subject_id)
        
        result = await self.session.execute(stmt)
        return result.mappings().all()
