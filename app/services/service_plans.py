from sqlalchemy import select
from app.models.model_subscription import Plans
from app.schemas.schema_plan import PlanRead
from app.services.service_base import ServiceBase


class ServicePlans(ServiceBase):

    async def get_all(self) -> list[PlanRead]:
        stmt = select(Plans)
        result = await self.session.execute(stmt)
        return [PlanRead.model_validate(plan) for plan in result.scalars().all()]