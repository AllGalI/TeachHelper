import uuid
from httpx import AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config.config_app import settings
from app.models.model_tasks import Criterions, Exercises, Tasks
from app.models.model_users import Users
from app.schemas.schema_tasks import ExerciseCreate, ExerciseCriterionCreate, TaskCreate, SchemaTask, TasksListItem
from app.utils.oAuth import create_access_token

@pytest_asyncio.fixture(scope="function")
async def task10(async_session, subject_id, teacher_id)->TaskCreate:
    task = TaskCreate(
        subject_id= subject_id,
        name= "Задача по математике",
        description= "Решить 10 уравнений",

        exercises= [
            ExerciseCreate(
                name= "Посчитай 10",
                description= "Очень важно",
                order_index= 1,
                criterions= [
                    ExerciseCriterionCreate(
                        name= "Посчитал до 10",
                        score= 1,
                    )
                ]
            )
        ]
    )
    return task

@pytest_asyncio.fixture(scope="module")
async def get_session_task(client, task_id, session_token_teacher) -> SchemaTask:
    response = await client.get(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_teacher, 
        }
    )
    task_db = SchemaTask.model_validate(response.json())
    return task_db


@pytest_asyncio.fixture(scope="function")
async def module_task(async_session) -> SchemaTask:
    stmt = select(Tasks).where(Tasks.name == "Задача по математике").options(selectinload(Tasks.exercises).selectinload(Exercises.criterions))
    response = await async_session.execute(stmt)
    task = SchemaTask.model_validate(response.scalars().first())
    return task




@pytest_asyncio.fixture(scope='function')
async def second_teacher(async_session):
    teacher = Users(
        first_name="Teacher2",
        last_name="Test",
        email="teacher2_test@example.com",
        password="123456",
        role="teacher",
        is_verificated=True
    )
    async_session.add(teacher)
    await async_session.commit()
    return teacher


@pytest_asyncio.fixture(scope='function')
async def second_teacher_token(second_teacher):
    token = create_access_token({"email": "teacher2_test@example.com"}, settings.SECRET)
    return f"Bearer {token}"

@pytest.mark.asyncio(loop_scope="session")
async def test_create_success(client: AsyncClient, session_token_teacher: str, task10: Tasks):
    response = await client.post(
        "/tasks",
        headers = {
            "Authorization": session_token_teacher, 
        },
        json=TaskCreate.model_validate(task10).model_dump(mode='json')
    )
    assert response.status_code == 201
    validate_task = SchemaTask.model_validate(response.json())
    assert task10.name == validate_task.name

@pytest.mark.asyncio(loop_scope="session")
async def test_create_user_have_not_access(client: AsyncClient, session_token_student: str, task10: Tasks):
    
    response = await client.post(
        "/tasks",
        headers = {
            "Authorization": session_token_student, 
        },
        json=TaskCreate.model_validate(task10).model_dump(mode='json')

    )

    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}


@pytest.mark.asyncio(loop_scope="session")
async def test_get_all_success(client: AsyncClient, session_token_teacher: str):
    response = await client.get(
        "/tasks",
        headers = {
            "Authorization": session_token_teacher, 
        },
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio(loop_scope="session")
async def test_get_all_user_have_not_access(client: AsyncClient, session_token_student: str):
    response = await client.get(
        "/tasks",
        headers = {
            "Authorization": session_token_student, 
        },
    )

    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}




@pytest.mark.asyncio(loop_scope="session")
async def test_get_success(client: AsyncClient, task_id, session_token_teacher: str):
    response = await client.get(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_teacher, 
        },
    )

    assert response.status_code == 200
    validate_task = SchemaTask.model_validate(response.json())
    assert validate_task.name == "Задача conftest"

@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_have_not_access(client: AsyncClient, session_token_student: str, task_id: uuid.UUID):
    response = await client.get(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_student, 
        },
    )
    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}

@pytest.mark.asyncio(loop_scope="session")
async def test_task_not_exists(client: AsyncClient, session_token_teacher: str):
    response = await client.get(
        f"/tasks/{uuid.uuid4()}",
        headers = {
            "Authorization": session_token_teacher, 
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest_asyncio.fixture
async def session_task(client, task_id, session_token_teacher):
    response = await client.get(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_teacher, 
        }
    )
    return SchemaTask.model_validate(response.json())


@pytest.mark.asyncio(loop_scope="session")
async def test_update_success(client: AsyncClient, session_task, session_token_teacher: str, task_id: uuid.UUID):

    assert session_task.name      == "Задача conftest"
    assert session_task.exercises[0].name == "Посчитай 10"
    session_task.name              = "New name"
    session_task.exercises[0].name = "New exer name"

    response = await client.put(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_teacher, 
        },
        json=session_task.model_dump(mode='json')
    )

    assert response.status_code == 200
    task = SchemaTask.model_validate(response.json())
    assert task.name                 == "New name"
    assert task.exercises[0].name == "New exer name"

    # откатить изменения
    task.name      = "Задача conftest"
    task.exercises[0].name = "Посчитай 10"

    await client.put(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_teacher, 
        },
        json=task.model_dump(mode='json')
    )

@pytest.mark.asyncio(loop_scope="session")
async def test_update_user_have_not_access(client: AsyncClient, session_task, session_token_student: str, task_id: uuid.UUID):
    assert session_task.name      == "Задача conftest"
    assert session_task.exercises[0].name == "Посчитай 10"
    session_task.name              = "New name1"
    session_task.exercises[0].name = "New exer name1"

    response = await client.put(
        f"/tasks/{task_id}",
        headers = {
            "Authorization": session_token_student, 
        },
        json=session_task.model_dump(mode='json')
    )
    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}

@pytest.mark.asyncio(loop_scope="session")
async def test_update_task_not_exists(client: AsyncClient, session_task, session_token_teacher: str):
    assert session_task.name      == "Задача conftest"
    assert session_task.exercises[0].name == "Посчитай 10"

    session_task.name              = "New name1"
    session_task.exercises[0].name = "New exer name1"

    response = await client.put(
        f"/tasks/{uuid.uuid4()}",
        headers = {
            "Authorization": session_token_teacher, 
        },
        json=session_task.model_dump(mode='json')
    )
    assert response.status_code == 404
    assert response.json()['detail'] == "Task not found"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_student_have_not_access(client: AsyncClient, module_task, session_token_student: str):
    response = await client.delete(
        f"/tasks/{module_task.id}",
        headers = {
            "Authorization": session_token_student, 
        },
    )
    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_teacher_have_not_access(client: AsyncClient, module_task, second_teacher_token):
    response = await client.delete(
        f"/tasks/{module_task.id}",
        headers = {
            "Authorization": second_teacher_token, 
        },
    )

    assert response.status_code == 403
    assert response.json() == {'detail': "User don't have permission to delete this task"}

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_task_not_exists(client: AsyncClient, session_token_teacher: str):
    response = await client.delete(
        f"/tasks/{uuid.uuid4()}",
        headers = {
            "Authorization": session_token_teacher, 
        },
    )
    assert response.status_code == 404
    assert response.json() == {'detail': "Task not found"}

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_success(client: AsyncClient, module_task, session_token_teacher: str):
    response = await client.delete(
        f"/tasks/{module_task.id}",
        headers = {
            "Authorization": session_token_teacher, 
        },
    )

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}