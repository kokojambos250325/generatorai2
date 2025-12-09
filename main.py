from fastapi import FastAPI, Depends
from routers import health, generate, tasks
from services.generation_service import GenerationService

app = FastAPI()

# Подключение роутеров
app.include_router(health.router)
app.include_router(generate.router)
app.include_router(tasks.router)


def get_generation_service() -> GenerationService:
    """Зависимость для получения экземпляра GenerationService"""
    return GenerationService()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
