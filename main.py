from datetime import datetime
import json
import uuid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.config_app import settings


from app.routes.route_answers import router as router_answers
from app.routes.route_assessments import router as router_assessments
from app.routes.route_auth import router as router_auth
from app.routes.route_classroom import router as router_classroom
from app.routes.route_comments import router as router_comments
from app.routes.route_exersices import router as router_exersices
from app.routes.route_files import router as router_files
from app.routes.route_students import router as router_students
from app.routes.route_students import router2 as router_teachers
from app.routes.route_subjects import router as router_subjects
from app.routes.route_tasks import router as router_tasks
from app.routes.route_works import router as router_works
from app.routes.route_comment_type import router as router_comment_types


def create_app() -> FastAPI:
    app = FastAPI(title="RU-Lang MVP API")
    
    # Настройка CORS из переменных окружения

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONT_URL,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    # Роутеры
    app.include_router(router_answers)
    app.include_router(router_assessments)
    app.include_router(router_auth)
    app.include_router(router_classroom)
    app.include_router(router_comments)
    app.include_router(router_exersices)
    app.include_router(router_files)
    app.include_router(router_students)
    app.include_router(router_teachers)
    app.include_router(router_subjects)
    app.include_router(router_comment_types)
    app.include_router(router_tasks)
    app.include_router(router_works)


    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # da1 = datetime.fromisoformat("2025-12-24T12:44:57.540695+00:00")
    # da2 = datetime.fromisoformat("2025-12-23T12:44:57.540695+00:00")
    # print(da1)
    # dat1 =  da1.date()
    # print(da2)
    # dat2 =  da2.date()
    # print(dat1 < dat2)
    # mini = min(dat1, dat2)
    # print(f"miniii {mini}")
    
