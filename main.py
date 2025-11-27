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


def create_app() -> FastAPI:
    app = FastAPI(title="RU-Lang MVP API")
    
    # Настройка CORS из переменных окружения
    cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
    cors_origins = [origin.strip() for origin in cors_origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/filesWork", StaticFiles(directory="public/filesWork"), name="filesWork")

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
    app.include_router(router_tasks)
    app.include_router(router_works)


    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
