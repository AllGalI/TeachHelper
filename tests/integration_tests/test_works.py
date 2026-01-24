
from typing import Literal
import uuid
import pytest
import pytest_asyncio

from app.config.config_app import settings
from app.config.db import AsyncSessionLocal
from app.models.model_tasks import Criterions, Exercises, Tasks
from app.models.model_users import Users
from fastapi import HTTPException

from app.models.model_works import StatusWork, Works
from app.services.service_work import ServiceWork
from app.schemas.schema_work import WorkUpdate
from app.exceptions.responses import Success
from app.utils.oAuth import create_access_token
from app.schemas.schema_files import FileSchema

@pytest.fixture
def update_data():
    return WorkUpdate.model_validate(
        {
            "task_id": "7bd1af64-ccb7-448b-bb9e-943b6aaa590b",
            "student_id": "338464b9-b1c8-4f8a-b840-d42597de0eca",
            "finish_date": None,
            "status": "draft",
            "id": "48fd40b4-3d01-4ad3-998e-2338dbacd376",
            "answers": [
                {
                    "work_id": "48fd40b4-3d01-4ad3-998e-2338dbacd376",
                    "exercise_id": "c98ac0ab-69df-4c28-bd81-d255977e7097",
                    "files": [],
                    "id": "d5c8edc9-c427-4bb3-af6a-367f0bf49e16",
                    "assessments": [
                        {
                            "id": "d1a6db6f-2b6a-4cfe-95c0-6c512a9ab953",
                            "answer_id": "0204821c-9d78-442f-a59c-7d85397eb52f",
                            "criterion_id": "d1a6db6f-2b6a-4cfe-95c0-6c512a9ab953",
                            "points": 0
                        }
                    ]
                }
            ]
        }
    )

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_works(subject_id, teacher_id):
    print("start generate_task")
    local_teacher_id = uuid.UUID("9a25a12d-a1ed-4583-a07e-51c592b59d63")
    local_task_id = uuid.UUID("9a25a12d-a1ed-4583-a07e-51c592b59d64")
    local_exercise_id = uuid.UUID("9a25a12d-a1ed-4583-a07e-51c592b59d65")
    local_criterion_id = uuid.UUID("9a25a12d-a1ed-4583-a07e-51c592b59d66")
    async with AsyncSessionLocal() as session:
        teacher = Users(
                id=local_teacher_id,
                first_name="Teacher",
                last_name="Test",
                email="local_teacher_test@example.com",
                password="123456",
                role="teacher",
                is_verificated=True,
                students = []
            )
        task = Tasks(
            id=local_task_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            name= "Задача test_works",
            description= "Тестовая задача созданная в conftest",

            exercises = [
                Exercises(
                    id=local_exercise_id,
                    name="Тестовое упражнение",
                    description="Очень важно",
                    order_index=1,
                    criterions=[
                        Criterions(
                            id=local_criterion_id,
                            name="Посчитал до 10",
                            score=1
                        )
                    ]
                )
            ]
        )
        session.add_all([task, teacher])
        await session.commit()
        yield {
            "local_teacher_id": local_teacher_id,
            "local_task_id": local_task_id,
            "local_exercise_id": local_exercise_id,
            "local_criterion_id": local_criterion_id,
        }

@pytest.fixture(scope="module")
def local_task_id(setup_test_works):
    return setup_test_works["local_task_id"]

@pytest.fixture(scope="module")
def local_teacher_id(setup_test_works):
    return setup_test_works["local_teacher_id"]

@pytest.fixture(scope="module")
def local_exercise_id(setup_test_works):
    return setup_test_works["local_exercise_id"]
         
@pytest.fixture(scope="module")
def local_criterion_id(setup_test_works):
    return setup_test_works["local_criterion_id"]

@pytest.fixture(scope="module")
def local_token_teacher():
    token = create_access_token({"email": "local_teacher_test@example.com"}, settings.SECRET)
    return f"Bearer {token}"
         

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id,expected_status",
    [
        (uuid.UUID("48fd40b4-3d01-4ad3-998e-2338dbacd371"), 404),
        (uuid.UUID("48fd40b4-3d01-4ad3-998e-2338dbacd376"), 200),
    ]
)
async def test_get(client, session_token_student: str, id: uuid.UUID, expected_status: Literal[404] | Literal[200]):
    response = await client.get(
        f"/works/{id}",
        headers={"Authorization": session_token_student}
    )

    assert response.status_code == expected_status

    if response.status_code == 200:
        work = response.json()['work']
        assert work['id'] == "48fd40b4-3d01-4ad3-998e-2338dbacd376"
        assert work['status'] == StatusWork.draft

    if response.status_code == 400:
        assert response.json() == {"detail": "Work not exists"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,expected_status,count",
    [        
        (
            {"students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")]}, 200, 1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")]
            }, 200, 1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")]
            }, 200, 1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")],
                "status_work": StatusWork.draft.value
            }, 200, 1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")],
                "status_work": StatusWork.canceled.value
            }, 200, 0
        ),# не существующий status_work
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6361"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")],
                "status_work": StatusWork.draft.value
            }, 200, 0
        ),# не существующий subject_id
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de1eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f1ba")],
                "status_work": StatusWork.draft.value
            }, 200, 0
        ),# не существующий student_id
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f2ba")],
                "status_work": StatusWork.draft.value
            },
            200, 0
        ),# не существующий classroom_id
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "students_ids": [uuid.UUID("338464b9-b1c8-4f8a-b840-d42597de0eca")],
                "classrooms_ids": [uuid.UUID("345a10c2-78a4-418c-85ac-b230e9f1f2ba")],
                "status_work": StatusWork.draft.value
            },
            200, 1
        ),# не существующий classroom_id но есть students_ids
        
    ]
)
async def test_teacher_get_all(client, session_token_teacher, data: dict, expected_status, count):
    response = await client.get(
        "/works/teacher",
        headers={"Authorization": session_token_teacher},
        params = data
    )
    assert response.status_code == expected_status
    assert len(response.json()) == count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,expected_status,count",
    [
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "status_work": StatusWork.draft.value
            },
            200,
            1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
            },
            200,
            1
        ),
        (
            {
                "status_work": StatusWork.draft.value
            },
            200,
            1
        ),
        (
            {},
            200,
            1
        ),
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6369"),
                "status_work": StatusWork.draft.value
            },
            200,
            0
        ),# не существующий предмет 
        (
            {
                "subject_id": uuid.UUID("6ded87e5-323d-4994-9c9e-38125e5d6362"),
                "status_work": StatusWork.inProgress.value
            },
            200,
            0
        ),# не существующий статус

    ]
)
async def test_student_get_all(client, session_token_student, data: dict, expected_status, count):
    response = await client.get(
        "/works/student",
        headers={"Authorization": session_token_student},
        params = data
    )

    assert response.status_code == expected_status
    assert len(response.json()) == count

# Нужно сделать кейсы где будет уже создана работа и где её еще нет, где будет количество поменятся не должно
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id_fixture,status_code,works_count",
    [
        ("task_id",200,1), #работа уже существует
        ("local_task_id",200,2), #новая работа
    ]
)
async def test_send_work_success(client, student_id, request, session_token_teacher, id_fixture, status_code, works_count):
    task_id = request.getfixturevalue(id_fixture)
    response = await client.post(
        f"/tasks/{task_id}/start",
        headers={"Authorization": session_token_teacher},
        json={
          "students_ids": [str(student_id)],
          "classrooms_ids": []
        }
    )

    assert response.status_code == 201
    assert response.json() == {"status": "ok"}

    response = await client.get(
        "/works/teacher",
        headers={"Authorization": session_token_teacher},

    )

    assert response.status_code == status_code
    assert len(response.json()) == works_count

@pytest.mark.asyncio
@pytest.mark.parametrize(
    """
        task_id_fixture,
        students_ids,
        classrooms_ids,
        token_fixture,
        status_code,
        assert_response
    """,
    [
        (
            "task_id",
            ["student_id"],
            [],
            "session_token_teacher",
            201,
            {"status": "ok"}
        ), #success
        (
            
            "task_id",
            [],
            ["classroom_id"],
            "session_token_teacher",
            201,
            {"status": "ok"}
        ), #success
                (
            
            "task_id",
            ["student_id"],
            ["classroom_id"],
            "session_token_teacher",
            201,
            {"status": "ok"}
        ), #success
        (
            "task_id",
            [],
            [],
            "session_token_teacher",
            400,
            {'detail': 'Add students or classes'}
        ), #error
        (
            "task_id",
            ["student_id"],
            [],
            "session_token_student",
            403,
            {'detail': "Access denied: required role 'RoleUser.teacher', got 'RoleUser.student'"}
        ), #error
        (
            "task_id",
            ["student_id"],
            [],
            "local_token_teacher",
            403,
            {'detail': "This user haven't permission to make this"}
        ), #error
    ]
)
async def test_send_work_errors(
        client,
        request,
        task_id_fixture,
        students_ids,
        classrooms_ids,
        token_fixture,
        status_code,
        assert_response
    ):
    student_ids = [str(request.getfixturevalue(fixture)) for fixture in students_ids]
    classrooms_ids = [str(request.getfixturevalue(fixture)) for fixture in classrooms_ids]
    task_id = request.getfixturevalue(task_id_fixture)
    token = request.getfixturevalue(token_fixture)
    response = await client.post(
        f"/tasks/{str(task_id)}/start",
        headers={"Authorization": token},
        json={
          "students_ids": student_ids,
          "classrooms_ids": classrooms_ids,
        }
    )

    assert response.status_code == status_code
    assert response.json() == assert_response



# @pytest.mark.asyncio
# @pytest.mark.parametrize(
    # "token_fixtrue,work_id_fixture,update_data"
# )
# async def test_update_success
# Учитель в работе может обновлять критерии, создавать комментарии, изменять статус работы
# Ученик в работе может менять статус работы, менять файлы в ответах(с дз)
# Написать разные routers на сущности, отдельно обновлять answers, comments, criterions
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_role,work_exists,initial_status,new_status,conclusion,expected_status,expected_detail",
    [
        ("student", True, StatusWork.draft, StatusWork.inProgress, None, 200, None),
        ("student", True, StatusWork.inProgress, StatusWork.verification, None, 200, None),
        (
            "student",
            True,
            StatusWork.verification,
            StatusWork.inProgress,
            None,
            400,
            "Status can only be increased or kept the same, not decreased",
        ),
        (
            "student",
            True,
            StatusWork.verification,
            StatusWork.verification,
            None,
            403,
            "Student cannot update work with status beyond 'inProgress'",
        ),
        (
            "student",
            True,
            StatusWork.draft,
            StatusWork.verificated,
            None,
            400,
            "Student can only set status to 'inProgress' or 'verification'",
        ),
        (
            "student",
            True,
            StatusWork.draft,
            StatusWork.inProgress,
            "Need conclusion",
            400,
            "Student cannot set conclusion",
        ),
        (
            "teacher",
            True,
            StatusWork.verification,
            StatusWork.verificated,
            "Work completed",
            200,
            None,
        ),
        (
            "teacher",
            True,
            StatusWork.inProgress,
            StatusWork.canceled,
            None,
            200,
            None,
        ),
        (
            "teacher",
            True,
            StatusWork.draft,
            StatusWork.verificated,
            None,
            400,
            "Teacher can set 'verificated' only after 'verification'",
        ),
        ("admin", True, StatusWork.draft, StatusWork.inProgress, None, 403, "Unauthorized role"),
        ("teacher", False, StatusWork.draft, StatusWork.inProgress, None, 404, "This Work, not exists"),
    ],
)
async def test_update_status_rules(
    request,
    async_session,
    work_id,
    user_role,
    work_exists,
    initial_status,
    new_status,
    conclusion,
    expected_status,
    expected_detail,
):
    service = ServiceWork(async_session)  # сервис, чью логику проверяем

    setup_data = request.getfixturevalue("setup_db")  # получаем идентификаторы тестовых пользователей
    if user_role == "student":
        user_id = setup_data["student_id"]
    elif user_role == "teacher":
        user_id = setup_data["teacher_id"]
    elif user_role == "admin":
        user_id = setup_data["admin_id"]
    else:  # защищаемся от опечаток в параметрах
        raise ValueError(f"Unsupported user role: {user_role}")

    user = await async_session.get(Users, user_id)  # загружаем пользователя для передачи в сервис

    target_work_id = work_id if work_exists else uuid.uuid4()  # выбираем существующую или искусственную работу

    if work_exists:
        work = await async_session.get(Works, target_work_id)
        work.status = initial_status  # устанавливаем начальный статус для проверки переходов
        work.conclusion = None  # обнуляем заключение перед тестом
        await async_session.commit()
        await async_session.refresh(work)

    try:
        response = await service.update(
            work_id=target_work_id,
            status=new_status,
            conclusion=conclusion,
            user=user,
        )
    except HTTPException as exc:
        assert exc.status_code == expected_status
        assert exc.detail == expected_detail

        if work_exists:
            persisted_work = await async_session.get(Works, target_work_id)
            await async_session.refresh(persisted_work)  # обновляем данные из базы после отката
            assert persisted_work.status == initial_status  # статус не меняется при ошибке
        return

    assert expected_status == 200
    assert isinstance(response, Success)
    assert response.status_code == 200
    assert response.body == b'{"status":"ok"}'

    updated_work = await async_session.get(Works, target_work_id)
    await async_session.refresh(updated_work)  # убеждаемся, что читаем обновленные данные
    assert updated_work.status == new_status  # статус обновился согласно запросу

    if conclusion is None:
        assert updated_work.conclusion in (None, "")  # для студента заключение остается пустым
    else:
        assert updated_work.conclusion == conclusion  # учитель может сохранить заключение
