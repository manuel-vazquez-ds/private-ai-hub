# def main():
#     print("Hello from proj-3!")


# if __name__ == "__main__":
#     main()

from pathlib import Path
from fastapi import FastAPI, Request
# from fastapi.params import Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# ca: per llegir els fitxers de traducció
import json
import time

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
# ca: posteriorment es dupliquen al mirar la cookie
# print(f"Translations: {translations}")

privateAIH = FastAPI(title="Private AI Hub", version="0.2.0")

# ca: Carreguem directori static a FastAPI
privateAIH.mount("/static", StaticFiles(directory="static"), name="static")

def mira_cookie_idioma(request: Request) -> str:
    # ca: Intentem obtenir l'idioma de la cookie
    lang = request.cookies.get("posaAquestIdioma")
    # ca: Si no hi ha cookie, utilitzem l'idioma per defecte
    # print(f"Idioma de la cookie: {lang}")
    if not lang:
        lang = default_language
    return lang

# @privateAIH.get("/")
@privateAIH.get("/",response_class=HTMLResponse)
# @privateAIH.get("/",response_class=HTMLResponse, dependencies=[Depends(mira_cookie_idioma)])
# de moment sense async def
# TODO: Implementar async def quan sigui necessari
async def privateAIH_root(request: Request):
    global current_language
    global translations
    current_language = mira_cookie_idioma(request)
    translations = locales.get(current_language, locales[default_language])
    les_variables = {
        "request": request,
        "byAuthor": translations.get("byAuthor", "by Manuel Vázquez"),
        "msgPlaceholder": translations.get("msgPlaceholder", "Write your message..."),
        "sendButton": translations.get("sendButton", "Send"),
        # afegim una versió per forçar la recàrrega dels fitxers estàtics
        "version": int(time.time()),
        "current_language": current_language
    }
    # return templates.TemplateResponse("index.html", {"request": request})
    # return templates.TemplateResponse("index.html", {"request": {}})
    # print(f"Variables: {les_variables}")
    return templates.TemplateResponse(request,"index.html", les_variables)

@privateAIH.post("/posa_idioma", response_class=JSONResponse)
async def posa_idioma(request: Request):
    global current_language
    global translations
    # ca: llegim el body de la petició
    body = await request.json()
    # ca: actualitzem l'idioma
    current_language = body.get("language", default_language)
    # ca: carreguem les traduccions
    translations = locales.get(current_language, locales[default_language])
    response = JSONResponse(translations)
    response.set_cookie(key="posaAquestIdioma", value=current_language, max_age=2592000)
    # print(f"Response: {response}")
    return response

@privateAIH.post("/chat", response_class=JSONResponse)
async def chat(request: Request):
    # ca: llegim el body de la petició
    body = await request.json()
    # print(f"Body: {body}")
    # ca: retornem la resposta
    return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{body['message']}"})


# arranquem la API
if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(privateAIH, host="0.0.0.0", port=8000)
    # ca: Aquest el faig amb --reload per desenvolupar
    uvicorn.run("main:privateAIH", host="0.0.0.0", port=8000, reload=True)
