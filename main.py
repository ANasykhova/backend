from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routers.predict import router as predict_router

app = FastAPI(title="Ad moderation service")

app.include_router(predict_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # По заданию на невалидный вход отдаем 400 вместо дефолтного 422
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}
