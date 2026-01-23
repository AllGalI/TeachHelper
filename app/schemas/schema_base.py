from pydantic import BaseModel


class BaseModelConfig(BaseModel):
    model_config = {
        "from_attributes": True
    }