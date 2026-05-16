from pydantic import BaseModel, ConfigDict


class PublicModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
