import io
import os
import uuid

from minio import Minio
import pytest_asyncio
from sqlalchemy import insert

from app.config.boto import get_boto_client
from app.models.model_classroom import Classrooms
from app.models.model_subjects import Subjects
from app.models.model_tasks import Criterions, Exercises, Tasks
from app.models.model_users import Users, teachers_students
from app.models.model_works import Assessments, Answers, Works
from app.utils.oAuth import create_access_token

os.environ["ENV_FILE"] = ".env_test" #важно, если оно будет после импорта app переменная не подбросится и тесты снесут бой :)

from httpx import ASGITransport, AsyncClient
import pytest
from app.models.base import Base
from main import app
from app.db import AsyncSessionLocal, engine_async
from app.config.config_app import settings
from app.utils.logger import logger

@pytest_asyncio.fixture(scope="function", autouse=False)
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture(scope="module", autouse=True)
def prepare_minio():    
    mc = Minio(
        "localhost:9000",
        access_key=os.getenv("MINIO_USER"),
        secret_key=os.getenv("MINIO_PASSWORD"),
        secure=False  # Для HTTP (не HTTPS)
    )

    # Создаем единый bucket для всех файлов
    bucket_name = settings.MINIO_BUCKET
    found = mc.bucket_exists(bucket_name)
    if not found:
        mc.make_bucket(bucket_name)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    try:
        print("setup_db")
        async with engine_async.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        admin_id=uuid.UUID("3e8df17a-54a0-4f79-a9e0-f61f9a12cc6b")
        teacher_id=uuid.UUID("ecefeaf2-d21d-426f-b415-9ff1dfb4da0a")
        student_id=uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")
        subject_id=uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362")
        classroom_id=uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")
        task_id=uuid.UUID("7bd1af64-ccb7-448b-bb9e-943b6aaa590b")
        exercise_id=uuid.UUID("c98ac0ab-69df-4c28-bd81-d255977e7097")
        criterion_id=uuid.UUID("0204821c-9d78-442f-a59c-7d85397eb52f")
        work_id=uuid.UUID("48fd40b4-3d01-4ad3-998e-2338dbacd376")
        answer_id=uuid.UUID("d5c8edc9-c427-4bb3-af6a-367f0bf49e16")
        assessment_id=uuid.UUID("d1a6db6f-2b6a-4cfe-95c0-6c512a9ab953")
        student_answer_file_id=uuid.UUID("ecefeaf2-d21d-426f-b415-9ff1dfb4da0a")



        async with AsyncSessionLocal() as session:
            admin = Users(
                id=admin_id,
                first_name="Admin",
                last_name="Test",
                email="admin_test@example.com",
                password="123456",
                role="admin",
                is_verificated=True
            )

            teacher = Users(
                id=teacher_id,
                first_name="Teacher",
                last_name="Test",
                email="teacher_test@example.com",
                password="123456",
                role="teacher",
                is_verificated=True,
                students = []
            )

            student = Users(
                id=student_id,
                first_name="Student",
                last_name="Test",
                email="student_test@example.com",
                password="123456",
                role="student",
                is_verificated=True
            )

            subject = Subjects(
                id=subject_id,
                name="Math"
            )

            session.add_all([admin, subject, teacher, student,])
            await session.commit() 
            await session.refresh(admin)
            await session.refresh(teacher)
            await session.refresh(student)
            await session.refresh(subject)

            stmt = insert(teachers_students).values(teacher_id=teacher.id, student_id=student.id)
            await session.execute(stmt)
            await session.commit()
            classroom = Classrooms(
                id=classroom_id,
                name="test room",
                teacher_id = teacher.id
            )

            task = Tasks(
                id=task_id,
                subject_id= subject.id,
                teacher_id= teacher.id,
                name= "Задача conftest",
                description= "Тестовая задача созданная в conftest",

                exercises = [
                    Exercises(
                        id=exercise_id,
                        name="Посчитай 10",
                        description="Очень важно",
                        order_index=1,
                        criterions=[
                            Criterions(
                                id=criterion_id,
                                name="Посчитал до 10",
                                score=1
                            )
                        ]
                    )
                ]
            )
            session.add(task)

            work = Works(
                id=work_id,
                task_id=task_id,
                student_id=student_id,

                answers = [
                    Answers(
                        id=answer_id,
                        exercise_id=exercise_id,
                        assessments = [
                            Assessments(
                                id=assessment_id,
                                criterion_id=criterion_id,
                            )
                        ]
                    )
                ]
            )

            session.add_all([task, classroom, work])
            await session.commit()
            await session.aclose()
            
            buffer = io.BytesIO("Some usual texts".encode())
            buffer.seek(0, 2)
            size = buffer.tell()
            buffer.seek(0)

            async with get_boto_client() as s3:
                await s3.upload_fileobj(
                    buffer,
                    settings.MINIO_BUCKET,
                    f"{student_answer_file_id}/simple.txt"
                )
            
            file_orm = Files(
                id=student_answer_file_id,
                user_id=student_id,
                filename="simple.txt",
                original_size=size,
                original_mime=".txt",
            )
            session.add(file_orm)
            data = {
                "file_id": student_answer_file_id,
                "answer_id": answer_id
            }

            # Формируем запрос
            await session.flush()
            stmt = insert(answers_files).values(data)
            await session.execute(stmt)
            await session.commit()

        yield {
            "admin_id": admin_id,
            "teacher_id": teacher_id,
            "student_id": student_id,
            "subject_id": subject_id,
            "classroom_id": classroom_id,
            "task_id": task_id,
            "exercise_id": exercise_id,
            "criterion_id": criterion_id,
            "work_id": work_id,
            "answer_id": answer_id,
            "assessment_id": assessment_id,
        }


    except Exception as exc:
        logger.exception(exc)

@pytest.fixture(scope="module")
def admin_id(setup_db) -> uuid.UUID:
    return setup_db["admin_id"]

@pytest.fixture(scope="module")
def teacher_id(setup_db) -> uuid.UUID:
    return setup_db["teacher_id"]

@pytest.fixture(scope="module")
def student_id(setup_db) -> uuid.UUID:
    return setup_db["student_id"]

@pytest.fixture(scope="module")
def subject_id(setup_db) -> uuid.UUID:
    return setup_db["subject_id"]

@pytest.fixture(scope="module")
def classroom_id(setup_db) -> uuid.UUID:
    return setup_db["classroom_id"]

@pytest.fixture(scope="module")
def task_id(setup_db) -> uuid.UUID:
    return setup_db["task_id"]

@pytest.fixture(scope="module")
def exercise_id(setup_db) -> uuid.UUID:
    return setup_db["exercise_id"]

@pytest.fixture(scope="module")
def criterion_id(setup_db) -> uuid.UUID:
    return setup_db["criterion_id"]

@pytest.fixture(scope="module")
def work_id(setup_db) -> uuid.UUID:
    return setup_db["work_id"]

@pytest.fixture(scope="module")
def answer_id(setup_db) -> uuid.UUID:
    return setup_db["answer_id"]

@pytest.fixture(scope="module")
def assessment_id(setup_db) -> uuid.UUID:
    return setup_db["assessment_id"]


@pytest.fixture(scope="module")
def session_token_admin():
    token = create_access_token({"email": "admin_test@example.com"}, settings.SECRET)
    return f"Bearer {token}"

@pytest.fixture(scope="module")
def session_token_teacher():
    token = create_access_token({"email": "teacher_test@example.com"}, settings.SECRET)
    return f"Bearer {token}"

@pytest.fixture(scope="module")
def session_token_student():
    token = create_access_token({"email": "student_test@example.com"}, settings.SECRET)
    return f"Bearer {token}"


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client   

