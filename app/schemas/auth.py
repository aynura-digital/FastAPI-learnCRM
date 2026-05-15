from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, examples=["crm_service"])
    password: str = Field(..., min_length=1, examples=["secure-password"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, examples=["crm_service"])
    password: str = Field(..., min_length=8, examples=["secure-password"])
    service_name: str = Field(
        ..., min_length=1, max_length=128, examples=["CRM System"]
    )


class RegisterResponse(BaseModel):
    id: str
    username: str
    service_name: str
    message: str
