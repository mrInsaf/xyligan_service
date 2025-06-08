from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from transliterate import translit
import os
import re
import time

from xyligan import run_script

# Глобальная "база данных" (в памяти)
models_db = {}

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    load_models_from_disk()


def load_models_from_disk():
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    for filename in os.listdir(download_dir):
        if filename.endswith(".glb"):
            # Извлекаем "чистое" имя файла (без префикса и расширения)
            clean_name = filename.replace(".glb", "")

            # Генерируем ID (например, на основе хэша)
            model_id = f"model_{hash(clean_name) % 100000:05d}"

            models_db[model_id] = {
                "name": clean_name,
                "original_name": filename,
                "likes": 0
            }
    print(f"Загружено моделей: {len(models_db)}")


# === Настройка CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените на ваш фронтенд
    allow_methods=["*"],
    allow_headers=["*"],
)



class PromptRequest(BaseModel):
    prompt: str


def generate_filename(prompt):
    transliterated = translit(prompt, 'ru', reversed=True).lower().replace('j', 'i')
    filename_part = re.sub(r'[^a-z0-9]+', '-', transliterated).strip('-')
    return f"aiprintgen_{filename_part}.glb"


@app.post("/generate_model")
async def generate_model(request: PromptRequest):
    prompt = request.prompt
    try:
        # Генерация файла
        file_path = run_script(prompt)

        model_id = f"model_{hash(prompt) % 100000:05d}"

        models_db[model_id] = {
            "name": prompt,
            "original_name": file_path,
            "likes": 0
        }

        # Возврат файла клиенту
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации модели: {str(e)}")


@app.get("/models")
async def get_models():
    return {
        model_id: {
            "id": model_id,
            "name": model["name"].replace('_', ''),
            "likes": model["likes"]
        } for model_id, model in models_db.items()
    }


@app.get("/models/{model_id}/download")
async def download_model(model_id: str):
    model = models_db.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")

    file_path = os.path.join("downloads", model["original_name"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл модели не найден")

    return FileResponse(
        path=file_path,
        filename=model["original_name"],
        media_type="application/octet-stream"
    )


# === Эндпоинт: Лайк модели ===
@app.post("/models/{model_id}/like")
async def add_like(model_id: str):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Модель не найдена")

    models_db[model_id]["likes"] += 1

    return {"message": "Лайк добавлен", "likes": models_db[model_id]["likes"]}
