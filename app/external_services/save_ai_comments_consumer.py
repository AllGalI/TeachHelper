from sqlalchemy import select

from app.config.celery import celery_app
from app.config.db import AsyncSessionLocal
from app.exceptions.responses import Success
from app.models.model_comments import Comments, Coordinates
from app.models.model_files import AnswerFiles, StatusAnswerFile
from app.models.model_tasks import Tasks
from app.models.model_works import Answers, Works
from app.repositories.repo_subscription import RepoSubscription
from app.schemas.schema_AI import SchemaOutgoing
from app.utils.logger import logger


@celery_app.task(
    name='tasks.save_ai_comments',
    queue='save_ai_results_queue',
    bind=True,                # Дает доступ к self (объекту задачи)
    autoretry_for=(Exception,), # За чем следим (можно указать конкретно SQLAlchemyError)
    retry_backoff=True,       # Экспоненциальная задержка (1с, 2с, 4с, 8с...)
    retry_kwargs={'max_retries': 5} # Сколько раз пытаться, прежде чем сдаться
)
async def save_ai_results(self, data_dict: dict):
    try:
        data = SchemaOutgoing(**data_dict)
        async with AsyncSessionLocal() as session:       
            # Определяем teacher_id по первому ответу: answer -> work -> task -> teacher_id
            first_answer_id = data.answers[0].id
            stmt_work = (
                select(Works)
                .join(Answers, Works.id == Answers.work_id)
                .where(Answers.id == first_answer_id)
            )
            result_work = await session.execute(stmt_work)
            work = result_work.scalar_one_or_none()
            if work is not None:
                task = await session.get(Tasks, work.task_id)
                if task is not None:
                    repo_subscription = RepoSubscription(session)
                    subscription = await repo_subscription.get_by_user_id_any(task.teacher_id)
                    if subscription is not None:
                        # Считаем забаненные фото в ответе AI
                        banned_count = sum(
                            1
                            for answer in data.answers
                            for a_file in answer.files
                            if a_file.ai_status == StatusAnswerFile.banned
                        )
                        if banned_count > 0:
                            subscription.used_checks = max(
                                0,
                                subscription.used_checks - banned_count,
                            )
                            await session.flush()

            for answer in data.answers:
                orm_comments: list[Comments] = []
                for comment in answer.comments:
                    comment_orm = Comments(
                        answer_id=comment.answer_id,
                        answerfile_id=comment.answerfile_id,
                        description=comment.description,
                        type_id=comment.type_id,
                        human=False,
                    )

                    for coordinate in comment.coordinates:
                        comment_orm.coordinates.append(Coordinates(
                            x1=coordinate.x1,
                            y1=coordinate.y1,
                            x2=coordinate.x2,
                            y2=coordinate.y2,
                        ))
                    orm_comments.append(comment_orm)
                session.add_all(orm_comments)

                # Обрабатываем файлы: обновляем существующие или создаём новые
                for a_file in answer.files:
                    # Проверяем, существует ли файл с таким id в БД
                    existing_file = await session.get(AnswerFiles, a_file.id)
                    
                    if existing_file:
                        # Файл существует - обновляем его статус
                        existing_file.ai_status = a_file.ai_status
                        # Обновляем ключ, если он изменился
                        if existing_file.key != a_file.key:
                            existing_file.key = a_file.key
                    else:
                        # Файл не существует - создаём новый
                        new_file = AnswerFiles(
                            id=a_file.id,
                            answer_id=answer.id,
                            key=a_file.key,
                            ai_status=a_file.ai_status,
                        )
                        session.add(new_file)

            await session.commit()

            return Success()

    except Exception as exc:
        logger.exception(exc)
        await session.rollback()