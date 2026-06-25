# def main():
#     print("Hello from proj-3!")


# if __name__ == "__main__":
#     main()

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# ca: per llegir els fitxers de traducció
import json

templates = Jinja2Templates(
    directory="templates"
)

# ca: Directori on estan els fitxers de traducció
LOCALES_DIR = Path("locales")

# ca: Llegir els fitxers de traducció
locales = {}
for lang in LOCALES_DIR.glob("*.json"):
    with open(lang, "r", encoding="utf-8") as f:
        locales[lang.stem] = json.load(f)

# ca: Configurar l'API per utilitzar les traduccions
# TODO: Implementar la lògica per carregar les traduccions
default_language = "en"
# ca: Idioma actual
current_language = default_language
# ca: Carreguem les traduccions
translations = locales.get(current_language, locales[default_language])
print(f"Translations: {translations}")

privateAIH = FastAPI(title="Private AI Hub", version="0.1.1")

# ca: Carreguem directori static a FastAPI
privateAIH.mount("/static", StaticFiles(directory="static"), name="static")

# @privateAIH.get("/")
@privateAIH.get("/",response_class=HTMLResponse)
# de moment sense async def
# TODO: Implementar async def quan sigui necessari
async def privateAIH_root(request: Request):
    les_variables = {
        "request": request,
        "byAuthor": translations.get("byAuthor", "by"),
        "msgPlaceholder": translations.get("msgPlaceholder", "Write your message..."),
        "sendButton": translations.get("sendButton", "Send")
    }
    # return templates.TemplateResponse("index.html", {"request": request})
    # return templates.TemplateResponse("index.html", {"request": {}})
    print(f"Variables: {les_variables}")
    return templates.TemplateResponse(request,"index.html", les_variables)

# arranquem la API
if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(privateAIH, host="0.0.0.0", port=8000)
    # ca: Aquest el faig amb --reload per desenvolupar
    uvicorn.run("main:privateAIH", host="0.0.0.0", port=8000, reload=True)

