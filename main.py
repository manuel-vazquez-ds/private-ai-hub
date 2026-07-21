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
import time, datetime
# ca: per gestionar les cookies
from fastapi import Cookie
# ca: per fer les crides importem requests i ollama
import requests
import ollama
# ca: per fer la base de dades, i per fer identificadors únics
import sqlite3
import uuid

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

# Tot això hara ho fem directament a la funció
    # current_language = default_language
    # # ca: Carreguem les traduccions
    # translations = locales.get(current_language, locales[default_language])
    # # ca: posteriorment es dupliquen al mirar la cookie
    # # print(f"Translations: {translations}")

# ca: versió 0.3.0 abans de fastapi intentem carregar la llibreria sqlite3
try:
    prAIHdb = sqlite3.connect('prAIH.db')
    # prAIHdb.row_factory = sqlite3.Row
    with prAIHdb:
        cursor = prAIHdb.cursor()
        # per activar les relacions de claus foranes
        cursor.execute("PRAGMA foreign_keys = ON")
        tbl_users = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            hashpw TEXT NULL)"""
        tbl_models = """CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            nom_a_mostrar TEXT NOT NULL,
            parametres TEXT)"""
        tbl_conversations = """CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            model_id INTEGER NOT NULL, nom TEXT DEFAULT 'default chat', 
            stream TEXT DEFAULT 'false', options TEXT DEFAULT '{}',
            messages TEXT DEFAULT '[]', metadades TEXT DEFAULT '[]',
            data_creacio TEXT DEFAULT CURRENT_TIMESTAMP,
            data_modificacio TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE)
            """
        tbl_perfil = """CREATE TABLE IF NOT EXISTS perfil (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_rol UNIQUE ON CONFLICT IGNORE,
            content NOT NULL, parametres TEXT DEFAULT '{}')
            """
        users_data_ini = ("AnonUser",)
        models_data_ini = ("gemma4:12b-it-qat", "Gemma 4", '{"temperature":0.4,"num_ctx":8192, "top_k":35,"top_p":0.9,"repeat_penalty":1.2}')
        perfil_data_ini = ("Analista",
                        "Mi rol principal eres un analista estadístico, si puedes responde con estos términos y en el idioma del mensaje")
        cursor.execute(tbl_users)
        cursor.execute(tbl_models)
        cursor.execute(tbl_conversations)
        cursor.execute(tbl_perfil)
        # els else: print... no s'han de posar er private ai hub
        if cursor.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None:
            cursor.execute("INSERT INTO users (nom) VALUES (?)", (users_data_ini))
        if cursor.execute("SELECT 1 FROM models LIMIT 1").fetchone() is None:
            cursor.execute("INSERT INTO models (nom, nom_a_mostrar, parametres) VALUES (?,?,?)", (models_data_ini))
        if cursor.execute("SELECT 1 FROM perfil LIMIT 1").fetchone() is None:
            cursor.execute("INSERT INTO perfil (nom_rol, content) VALUES (?,?)", (perfil_data_ini))
except Exception as e:
    print(f"Error loading database / error leyendo la base de detos / error llegint la base de dades: {e}")

# ca: URL del proveïdor per defecte, en principi Ollama
llmProvider = "http://localhost:11434/api/chat"

privateAIH = FastAPI(title="Private AI Hub", version="0.3.0")

# ca: Carreguem directori static a FastAPI
privateAIH.mount("/static", StaticFiles(directory="static"), name="static")

# Ara ja no farà falta
    # def mira_cookie_idioma(request: Request) -> str:
    #     # ca: Intentem obtenir l'idioma de la cookie
    #     lang = request.cookies.get("posaAquestIdioma")
    #     # ca: Si no hi ha cookie, utilitzem l'idioma per defecte
    #     # print(f"Idioma de la cookie: {lang}")
    #     # AIXÒ ES PODIA HAVER FET DINS DEL .get() amb un valor per defecte, que es un diccionari!!
    #     if not lang:
    #         lang = default_language
    #     return lang

# @privateAIH.get("/")
@privateAIH.get("/",response_class=HTMLResponse)
# @privateAIH.get("/",response_class=HTMLResponse, dependencies=[Depends(mira_cookie_idioma)])
# de moment sense async def
# TODO: Implementar async def quan sigui necessari
async def privateAIH_root(request: Request):
    global current_language
    global translations
    # current_language = mira_cookie_idioma(request)
    # ho fem directament
    current_language = request.cookies.get("posaAquestIdioma", default_language)
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

    # ca: Ara anem amb 0.3.0 mirem si te session_id associat
    # enlloc de retornar el template directament, el guardem en una variable
    response = templates.TemplateResponse(request, "index.html", les_variables)
    session_id = request.cookies.get("session_id", None)
    if session_id is None:
        # Llavors generem-ne un de nou
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="Lax")
    return response

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
    # return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{body['message']}"})
    # ca: v0.3.0 - afegim session_id
    session_id = request.cookies.get("session_id", None)
    if session_id:
        # ca: obtenim l'usuari
        usuari = await get_user(session_id)

        convesacio_id = body.get("conversacio_id", None)
        # ca: Agafem parametres per defecte, estiguin o no informats
        perfil_id = body.get("perfil_id", 1)
        model_id = body.get("model_id", 1)

        conversacio, model_nom, opcions, missatges, metadades = await localitza_una(session_id, usuari[0], convesacio_id, perfil_id, model_id)
        # he de canviar segurament el que retorna localitza_una perquè sigui més fàcil de tractar
        # per ara ho deixo así

        # ca: afegitm missagte del xat i les metadades buides
        missatges.append({"role":"user","content":body['message']})
        metadades.append({})

        # Aquesta serà la crida al llm
        try:
            resposta = await envia_missatge(model_nom, opcions, missatges)
            if resposta.status_code == 200:
                resposta = resposta.json()
                # AQUÍ HEM DE GUARDAR EL MISSATGE I LES METADADES ADDICIONALS
                missatges.append({"role":"assistant","content":resposta["message"]["content"]})
                metadades.append({k:v for k,v in resposta.items() if k not in ("message",)})

                conversacio["messages"] = json.dumps(missatges)
                conversacio["metadades"] = json.dumps(metadades)
                await guarda_conversacio(conversacio)
                
            else:
                # resposta = "Error en la crida al LLM"
                resposta = {"message": {"content": f"Error de status code {resposta.status_code}"}}
            #resposta= json.dumps({"model": model_nom, "messages": missatges, "stream": False, "options": opcions})
        # except:
        except requests.exceptions.RequestException as e:
            # resposta = "Error en la crida al LLM"
            resposta = {"message": {"content": f"Error en la crida al LLM: {str(e)}"}}
            pass



#        return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{body['message']}\n amb sessió!! {session_id}\n Usuari: {usuari}"})
        # return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{resposta}\n"})
        # fem sols la part de l'assistant

        return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{resposta['message']['content']}\n","conversacio_id": conversacio["id"]})
        # return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{resposta['message']}\n"})
        # return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{resposta}\n"})
        
    else:
        return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{body['message']}\n sense sessió"})

# ca: Aquí les funcions de crida a la base de dades i a ollama
async def  get_user(session_id: str):
    with prAIHdb:
        cursor = prAIHdb.cursor()
        id_usuari = cursor.execute("SELECT user_id FROM conversations WHERE session_id = ?", (session_id,)).fetchone()
        if id_usuari and id_usuari[0]!=1: # Usuari registrat, això pot canviar en el futur
            usuari = cursor.execute("SELECT id, nom FROM users WHERE session_id = ?", (session_id,)).fetchone()
        else:
            # usuari anònim
            usuari = cursor.execute("SELECT id, nom FROM users WHERE id = 1").fetchone()
        return usuari

# LA SEGÜENT ES LA DE LOCALITZAR CONVERSACIONS
async def localitza_una(session_id:str, user_id: int, conversacio_id: int, perfil_id: int, model_id: int):
    with prAIHdb:
        cursor = prAIHdb.cursor()
        if conversacio_id:
            if user_id==1:
                conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND session_id = ?", (conversacio_id, session_id)).fetchone()[:9]
            else:
                conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversacio_id, user_id)).fetchone()[:8]

            conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "options", "messages", "metadates"], conversacions))
            model_nom = cursor.execute("SELECT nom FROM models WHERE id = ?", (conversacions["model_id"],)).fetchone()[0]
            opcions = json.loads(conversacions["options"])
            missatges = json.loads(conversacions["messages"])
            metadades = json.loads(conversacions["metadates"])
        else:
            # construim la llista d'elements de la conversació, amb els primers 8 camps per defecte
            conversacions = [None, user_id, session_id, model_id, translations.get("defaultChatName", "Unnamed Chat"), "false", "{}", "[]", "[]"]
            # id , user_id , session_id , model_id , nom , stream , options , messages , data_creacio , data_modificacio
            # session_id TEXT NOT NULL,
            # model_id INTEGER NOT NULL, nom TEXT DEFAULT 'default chat', 
            # stream TEXT DEFAULT 'false', options TEXT DEFAULT '{}',
            # messages TEXT DEFAULT '[]',
            # data_creacio TEXT DEFAULT CURRENT_TIMESTAMP,
            # data_modificacio TEXT DEFAULT CURRENT_TIMESTAMP,
            # FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            # FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE

            # AFEEGIREM LA RESTA DESPRÉS, PER SI INCORPOREN PARÀMETRES EN UN FUTUR
            # ca: Convertim conversations en un diccionari
            # conversacions = {
            #     "id": conversacions[0],
            #     "user_id": conversacions[1],
            #     "session_id": conversacions[2],
            #     "model_id": conversacions[3],
            #     "nom": conversacions[4],
            #     "stream": conversacions[5],
            #     "options": conversacions[6],
            #     "messages": conversacions[7]
            # }
            # millor ho fem amb zip
            conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "options", "messages","metadades"], conversacions))
            # ca: Llegim valors bàsics
            model_nom, model_opcions = cursor.execute("SELECT nom, parametres FROM models WHERE id = ?", (model_id,)).fetchone()
            # ca: convertim a diccionari
            model_opcions = json.loads(model_opcions)
            # ca: ara el perfil
            perfil_content, perfil_opcions = cursor.execute("SELECT content, parametres FROM perfil WHERE id = ?", (perfil_id,)).fetchone()
            # ca: convertim a diccionari
            perfil_opcions = json.loads(perfil_opcions)
            opcions = {**model_opcions, **perfil_opcions}
            conversacions["options"] = json.dumps(opcions)
            missatges = [{"role": "system", "content": perfil_content}]
            metadades =[{}]
            conversacions["messages"] = json.dumps(missatges)
            conversacions["metadades"] = json.dumps(metadades)

    return conversacions, model_nom, opcions, missatges, metadades

async def envia_missatge(model_nom, opcions, missatges)-> requests:
    return requests.post(llmProvider, json={"model": model_nom, "messages": missatges, "stream": False, "options": opcions}, verify=False)

async def guarda_conversacio(conversacio: dict):
    # ca: Aquí guardem la conversació
    data_ara = datetime.datetime.now().replace(microsecond=0)
    # ca: Hem creat un current_datetime, perquè el del SQLITE es fa en UTC
    with prAIHdb:
        cursor = prAIHdb.cursor()
        if conversacio["id"]:
            cursor.execute("UPDATE conversations SET messages = ?, metadades = ?, data_modificacio = ? WHERE id = ?",
             (conversacio["messages"], conversacio["metadades"], data_ara, conversacio["id"]))
        else:
            conversacio["id"] = cursor.execute("INSERT INTO conversations (user_id, session_id, model_id, nom, stream, options, messages, metadades, data_creacio, data_modificacio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (conversacio["user_id"], conversacio["session_id"], conversacio["model_id"], conversacio["nom"], 
            conversacio["stream"], conversacio["options"], conversacio["messages"], conversacio["metadades"], data_ara, data_ara)).lastrowid
        return conversacio["id"]

# arranquem la API
if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(privateAIH, host="0.0.0.0", port=8000)
    # ca: Aquest el faig amb --reload per desenvolupar
    uvicorn.run("main:privateAIH", host="0.0.0.0", port=8000, reload=True)
