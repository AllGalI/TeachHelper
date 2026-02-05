import uuid

import pytest

from app.models.model_works import Assessments


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_fixture,points,expected_status,expected_detail",
    [
        ("session_token_teacher", 1, 200, None),
        ("session_token_teacher", 10, 400, "Too many points"),
        ("session_token_student", 1, 404, "Assessment not found"),
    ],
)
async def test_assessments_update(
    request,
    client,
    work_id,
    answer_id,
    assessment_id,
    async_session,
    token_fixture,
    points,
    expected_status,
    expected_detail,
):

    token = request.getfixturevalue(token_fixture)

    if expected_status == 200:
        await _reset_points(async_session, assessment_id, 0)  # перед успехом сбрасываем значения, чтобы сравнивать результат

    response = await client.put(
        f"/worsk/{work_id}/answers/{answer_id}/assessments/{assessment_id}",
        headers={"Authorization": token},
        params={"points": points},
    )

    assert response.status_code == expected_status

    if expected_detail is None:
        assert response.json() == {"status": "ok"}
        updated = await async_session.get(Assessments, assessment_id)
        await async_session.refresh(updated)
        assert updated.points == points  # убеждаемся, что баллы обновились
    else:
        assert response.json() == {"detail": expected_detail}


@pytest.mark.asyncio
async def test_assessments_update_not_found(
    request,
    client,
    session_token_teacher,
):
    setup_ids = request.getfixturevalue("setup_db")
    missing_assessment_id = uuid.uuid4()  # генерируем отсутствующий идентификатор оценки

    response = await client.put(
        f"/worsk/{setup_ids['work_id']}/answers/{setup_ids['answer_id']}/assessments/{missing_assessment_id}",
        headers={"Authorization": session_token_teacher},
        params={"points": 1},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Assessment not found"}


async def _reset_points(async_session, assessment_id, points: int) -> None:
    assessment = await async_session.get(Assessments, assessment_id)
    assessment.points = points  # принудительно выставляем количество баллов перед тестом
    await async_session.commit()
    await async_session.refresh(assessment)

