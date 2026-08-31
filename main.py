from pathlib import Path
# from fastapi import FastAPI, Request
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, status
# from fastapi.params import Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from typing import List, Optional

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

# ca: a partir d'aquí, importacions de les meves llibreries
import context as ctx

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
default_language = "en"
# ca: Idioma actual


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
            stream TEXT DEFAULT 'false', think TEXT DEFAULT 'true',
            options TEXT DEFAULT '{}',
            data_creacio TEXT DEFAULT CURRENT_TIMESTAMP,
            data_modificacio TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE CASCADE)
            """
        # ca: Nou perfil apuntem a un model per defecte
        tbl_perfil = """CREATE TABLE IF NOT EXISTS perfil (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_rol UNIQUE ON CONFLICT IGNORE,
            model_id INTEGER NOT NULL, content NOT NULL, parametres TEXT DEFAULT '{}',
            think TEXT DEFAULT 'true',
            FOREIGN KEY (model_id) REFERENCES models (id) ON DELETE SET DEFAULT)
            """
        tbl_messages = """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversacio_id INTEGER NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            metadades TEXT DEFAULT '{}',
            data_creacio TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversacio_id) REFERENCES conversations (id) ON DELETE CASCADE)
            """

        tbl_arxius = """CREATE TABLE IF NOT EXISTS arxius (
            id INTEGER PRIMARY KEY AUTOINCREMENT, missatge_id INTEGER NOT NULL,
            ordre INTEGER NOT NULL, name TEXT NOT NULL, content TEXT NOT NULL,
            data_creacio TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (missatge_id) REFERENCES messages (id) ON DELETE CASCADE)
            """

        users_data_ini = ("AnonUser",)
        # ca: Per més d'un perfil i model
        # models_data_ini = [("gemma4:12b-it-qat", "Gemma 4", '{"temperature":0.3,"num_ctx":16384, "top_k":35,"top_p":0.9,"repeat_penalty":1.2}'),
        #                   ("qwen3.6:latest", "Qwen 3.6", '{"temperature":0.5,"num_ctx":32768, "top_k":40,"top_p":0.92,"repeat_penalty":1.1}'),
        #                   ("qwen3.5:4b", "Qwen 3.5 4B", '{"temperature":1.1,"num_ctx":16384, "top_k":30,"top_p":0.75,"repeat_penalty":1.1}')]
        models_data_ini = [("gemma4:12b-it-qat", "Gemma 4", '{"temperature":0.3,"num_ctx":131072, "top_k":35,"top_p":0.9,"repeat_penalty":1.2}'),
                          ("qwen3.6:latest", "Qwen 3.6", '{"temperature":0.5,"num_ctx":262144, "top_k":40,"top_p":0.92,"repeat_penalty":1.1}'),
                          ("qwen3.5:4b", "Qwen 3.5 4B", '{"temperature":1.1,"num_ctx":131072, "top_k":30,"top_p":0.75,"repeat_penalty":1.1}'),
                          ("qwen3.8:27b", "Qwen 3.8", '{"temperature":0.5,"num_ctx":262144, "top_k":40,"top_p":0.92,"repeat_penalty":1.1}')]
        # perfil_data_ini = [("Analyst / Analista", 1,
        #                 "Mi rol principal eres un analista estadístico, si puedes responde con estos términos y en el idioma del mensaje", '{}',"true"),
        #                 ("Generalist expert / Experto generalista / Expert generalista", 2,
        #                 "Soy un experto en cualquier área, que además de dar la respuesta más adecuada según el tipo de pregunta, también puede ofrecer consejos y recomendaciones.", '{}',"true"),
        #                 ("Fast Responder / Respondedor Rápido / Responedor Ràpid", 3,
        #                 "Person who answers instantly, assuming knowledge without deep thinking; speed over accuracy. No thinking.", '{}',"false"),
        #                 ("Cultured Thinker / Pensador Culto / Pensador Culte", 1,
        #                 "Mi rol principal es de una persona con conocimiento amplio, buen razonamiento y cultura sólida; inteligente sin ser erudito, si puedes responde con estos términos y en el idioma del mensaje",
        #                  '{"temperature":0.5, "top_k":40, "repeat_penalty":1.1}', "true")]
        perfil_data_ini = [["Analyst / Analista", 1,
                        "Mi rol principal eres un analista estadístico.", '{}',"true"],
                        ["Generalist expert / Experto generalista / Expert generalista", 2,
                        "Soy un experto en cualquier área, que además de dar la respuesta más adecuada según el tipo de pregunta, también puede ofrecer consejos y recomendaciones.", '{}',"true"],
                        ["Fast Responder / Respondedor Rápido / Responedor Ràpid", 3,
                        "Person who answers instantly, assuming knowledge without deep thinking; speed over accuracy. No thinking.", '{}',"false"],
                        ["Cultured Thinker / Pensador Culto / Pensador Culte", 1,
                        "Mi rol principal es de una persona con conocimiento amplio, buen razonamiento y cultura sólida; inteligente sin ser erudito, si puedes responde con estos términos.",
                         '{"temperature":0.5, "top_k":40, "repeat_penalty":1.1}', "true"],
                        ["The wise friend / El amigo sabio / L\'amic savi", 4,
                        "Soy una persona con amplio conocimiento, al que acudir para saber algo de lo que sea, Sugiero las siguientes preguntas a formular.", '{}',"true"]]
        for x in range(len(perfil_data_ini)):
            perfil_data_ini[x][2] += ctx.INFORMACIO_ADDICIONAL

        cursor.execute(tbl_users)
        cursor.execute(tbl_models)
        cursor.execute(tbl_conversations)
        cursor.execute(tbl_perfil)
        cursor.execute(tbl_messages)
        cursor.execute(tbl_arxius)
        # els else: print... no s'han de posar er private ai hub
        if cursor.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None:
            cursor.execute("INSERT INTO users (nom) VALUES (?)", (users_data_ini))
        if cursor.execute("SELECT 1 FROM models LIMIT 1").fetchone() is None:
            # cursor.execute("INSERT INTO models (nom, nom_a_mostrar, parametres) VALUES (?,?,?)", models_data_ini)
            # ara així, que posem 2 models alhora
            cursor.executemany("INSERT INTO models (nom, nom_a_mostrar, parametres) VALUES (?,?,?)", models_data_ini)
        if cursor.execute("SELECT 1 FROM perfil LIMIT 1").fetchone() is None:
            # cursor.execute("INSERT INTO perfil (nom_rol, content) VALUES (?,?)", (perfil_data_ini))
            cursor.executemany("INSERT INTO perfil (nom_rol, model_id, content, parametres, think) VALUES (?,?,?,?,?)", (perfil_data_ini))
except Exception as e:
    print(f"Error loading database / error leyendo la base de detos / error llegint la base de dades: {e}")

# ca: URL del proveïdor per defecte, en principi Ollama
llmProvider = "http://localhost:11434/api/chat"

privateAIH = FastAPI(title="Private AI Hub", version="0.3.0")

# ca: Carreguem directori static a FastAPI
privateAIH.mount("/static", StaticFiles(directory="static"), name="static")


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
        "mida": translations.get("mida", "File size exceeds the allowed limit"),
        "inclos": translations.get("inclos", "Document already included"),
        # afegim una versió per forçar la recàrrega dels fitxers estàtics
        "version": int(time.time()),
        "current_language": current_language,
        "perfils": await recuperaPerfils()
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
# async def chat(request: Request):
# ca: fem el canvi per enviar arxius
async def chat(request: Request,
    message: str = Form(...),
    conversacio_id: Optional[int] = Form(None),
    perfil_id: int = Form(1),
    model_id: Optional[int] = Form(None),
    arxius: List[UploadFile] = File(None)
):
    # ca: llegim el body de la petició
    # ca: ara ja no llegim el body
    # body = await request.json()

    # ca: comprovem el context dels arxius
    if arxius:
        print(f"Arxius: {[x.filename for x in arxius]}")
        problema = ctx.comprovar_arxius(arxius)
        # print(f"Problema: {problema}")
        try:
            if problema:
                # return JSONResponse({"error": problema}, status_code=422)
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=problema)
        except HTTPException as e:
            print(f"HTTPException: {e}")
            raise e
    # ca: v0.3.0 - afegim session_id
    session_id = request.cookies.get("session_id", None)
    if session_id:
        # ca: obtenim l'usuari
        usuari = await get_user(session_id)

        # convesacio_id = body.get("conversacio_id", None)
        convesacio_id = conversacio_id
        # ca: Agafem parametres per defecte, estiguin o no informats
        # perfil_id = body.get("perfil_id", 1) 
        # model_id = body.get("model_id", await modelFromPerfil(perfil_id))
        if model_id is None:
            model_id = await modelFromPerfil(perfil_id)
        
        # print(f"model_id: {model_id}, perfil_id: {perfil_id}, conversacio_id: {convesacio_id}, message: {message}, usuari[0]: {usuari[0]}")

        # conversacio, model_nom, opcions, missatges, metadades, elStream, elThink = await localitza_una(session_id, usuari[0], convesacio_id, perfil_id, model_id)
        conversacio, model_nom, opcions, missatges, elStream, elThink = await localitza_una(session_id, usuari[0], convesacio_id, perfil_id, model_id)
        # he de canviar segurament el que retorna localitza_una perquè sigui més fàcil de tractar
        # per ara ho deixo así

        # ca: afegitm missagte del xat i les metadades buides
        # missatges.append({"role":"user","content":body['message']})
        # metadades.append({})
        # pregunta={"message":{"role":"user","content":body['message']}}
        pregunta={"message":{"role":"user","content":message}}
        missatge_system = {"message":missatges[0]} if len(missatges)==1 else None
        # missatges.append(pregunta["message"])
        missatges.append(pregunta["message"].copy())
        if arxius:
            missatges[-1]["content"], arxius_content =  await ctx.processar_arxius(missatges[-1]["content"], arxius)
            print(missatges[-1]["content"])
        else:
            arxius_content = None

        # Aquesta serà la crida al llm
        try:
            # Path(f".proves/chat_{datetime.datetime.now().strftime('%y%m%d_%H%M')}.json").write_text(json.dumps(missatges, indent=2), encoding="utf-8")
            resposta = await envia_missatge(model_nom, elStream, opcions, missatges, elThink)
            if resposta.status_code == 200:
                resposta = resposta.json()
                # AQUÍ HEM DE GUARDAR EL MISSATGE I LES METADADES ADDICIONALS
                # missatges.append({"role":"assistant","content":resposta["message"]["content"]})
                # metadades.append({k:v for k,v in resposta.items() if k not in ("message",)})
                # # print(resposta["message"])

                # conversacio["messages"] = json.dumps(missatges)
                # conversacio["metadades"] = json.dumps(metadades)
                # await guarda_conversacio(conversacio, pregunta, resposta, missatge_system)
                await guarda_conversacio(conversacio, pregunta, resposta, missatge_system, arxius_content)
                
            else:
                # resposta = "Error en la crida al LLM"
                resposta = {"message": {"content": f"Error de status code {resposta.status_code}"}}
            #resposta= json.dumps({"model": model_nom, "messages": missatges, "stream": False, "options": opcions})
        except requests.exceptions.RequestException as e:
            # resposta = "Error en la crida al LLM"
            resposta = {"message": {"content": f"Error en la crida al LLM: {str(e)}"}}
            pass
        # fem sols la part de l'assistant

        return JSONResponse({"response": f"{resposta['message']['content']}\n","conversacio_id": conversacio["id"]})
        # return JSONResponse({"response": f"Sent / Enviado / Enviat:\n\n{resposta['message']['content']}\n","conversacio_id": conversacio["id"]})
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
                # ca: es recupera un camp menys perquè no pot haver data de modificació
                # conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND session_id = ?", (conversacio_id, session_id)).fetchone()[:10]
                # ara ni missatges ni metadades
                conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND session_id = ?", (conversacio_id, session_id)).fetchone()[:8]
            else:
                # conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversacio_id, user_id)).fetchone()[:9]
                conversacions = cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversacio_id, user_id)).fetchone()[:7]

            # conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "think", "options", "messages", "metadates"], conversacions))
            conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "think", "options"], conversacions))
            model_nom = cursor.execute("SELECT nom FROM models WHERE id = ?", (conversacions["model_id"],)).fetchone()[0]
            opcions = json.loads(conversacions["options"])
            # missatges = json.loads(conversacions["messages"])
            # metadades = json.loads(conversacions["metadates"])
            elStream = json.loads(conversacions["stream"])
            elThink = json.loads(conversacions["think"])

            missatges = await recupera_missatges(conversacio_id)

        else:
            # construim la llista d'elements de la conversació, amb els primers 8 camps per defecte
            # conversacions = [None, user_id, session_id, model_id, translations.get("defaultChatName", "Unnamed Chat"), "false", "true", "{}", "[]", "[]"]
            conversacions = [None, user_id, session_id, model_id, translations.get("defaultChatName", "Unnamed Chat"), "false", "true", "{}"]
            # ca: Convertim conversations en un diccionari
            # conversacions = {
            #     "id": conversacions[0],
            #     "user_id": conversacions[1],
            #     "session_id": conversacions[2],
            #     "model_id": conversacions[3],
            #     "nom": conversacions[4],
            #     "stream": conversacions[5],
            #     "think": conversacions[6],
            #     "options": conversacions[7],
            # }
            # millor ho fem amb zip
            # conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "think", "options", "messages","metadates"], conversacions))
            conversacions = dict(zip(["id", "user_id", "session_id", "model_id", "nom", "stream", "think", "options"], conversacions))
            # ca: Llegim valors bàsics
            model_nom, model_opcions = cursor.execute("SELECT nom, parametres FROM models WHERE id = ?", (model_id,)).fetchone()
            # ca: convertim a diccionari
            model_opcions = json.loads(model_opcions)
            # ca: ara el perfil
            perfil_content, perfil_opcions, perfil_think = cursor.execute("SELECT content, parametres, think FROM perfil WHERE id = ?", (perfil_id,)).fetchone()
            # ca: convertim a diccionari
            perfil_opcions = json.loads(perfil_opcions)
            opcions = {**model_opcions, **perfil_opcions}
            conversacions["options"] = json.dumps(opcions)
            # missatges = [{"role": "system", "content": perfil_content, "metadades": {}}]
            missatges = [{"role": "system", "content": perfil_content}]
            # metadades =[{}]
            # conversacions["messages"] = json.dumps(missatges)
            # conversacions["metadades"] = json.dumps(metadades)

            elStream = json.loads(conversacions["stream"])
            elThink = json.loads(perfil_think)
            conversacions["think"] = json.dumps(elThink)

    # return conversacions, model_nom, opcions, missatges, metadades, elStream, elThink
    return conversacions, model_nom, opcions, missatges, elStream, elThink

async def envia_missatge(model_nom, stream, opcions, missatges, elThink)-> requests:
    # print(json.dumps({"model": model_nom, "messages": missatges, "stream": stream, "think": elThink, "options": opcions}))
    return requests.post(llmProvider, json={"model": model_nom, "messages": missatges, "stream": stream, "think": elThink, "options": opcions}, verify=False)

# async def guarda_conversacio(conversacio: dict):
# async def guarda_conversacio(conversacio: dict, pregunta: dict, resposta: dict, missatge_system: dict):
async def guarda_conversacio(conversacio: dict, pregunta: dict, resposta: dict, missatge_system: dict, arxius_content: list=None):
    # ca: Aquí guardem la conversació
    data_ara = datetime.datetime.now().replace(microsecond=0).isoformat()
    # ca: Hem creat un current_datetime, perquè el del SQLITE es fa en UTC
    with prAIHdb:
        cursor = prAIHdb.cursor()
        # if conversacio["id"]:
        #     cursor.execute("UPDATE conversations SET messages = ?, metadades = ?, data_modificacio = ? WHERE id = ?",
        #      (conversacio["messages"], conversacio["metadades"], data_ara, conversacio["id"]))
        # else:
        #     conversacio["id"] = cursor.execute("INSERT INTO conversations (user_id, session_id, model_id, nom, stream, think, options, messages, metadades, data_creacio, data_modificacio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        #     (conversacio["user_id"], conversacio["session_id"], conversacio["model_id"], conversacio["nom"], 
        #     conversacio["stream"], conversacio["think"], conversacio["options"], conversacio["messages"], conversacio["metadades"], data_ara, data_ara)).lastrowid
        if not conversacio["id"]:
            conversacio["id"] = cursor.execute("INSERT INTO conversations (user_id, session_id, model_id, nom, stream, think, options, data_creacio, data_modificacio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (conversacio["user_id"], conversacio["session_id"], conversacio["model_id"], conversacio["nom"], 
            conversacio["stream"], conversacio["think"], conversacio["options"], data_ara, data_ara)).lastrowid
            afegir_missatge(conversacio["id"], missatge_system, data_ara)
        
        # afegir_missatge(conversacio["id"], pregunta, data_ara)
        afegir_missatge(conversacio["id"], pregunta, data_ara, arxius_content)
        afegir_missatge(conversacio["id"], resposta, data_ara)

        return conversacio["id"]


async def modelFromPerfil(perfil_id: int):
    with prAIHdb:
        cursor = prAIHdb.cursor()
        model_id = cursor.execute("SELECT model_id FROM perfil WHERE id = ?", (perfil_id,)).fetchone()[0]
        return model_id

async def recuperaPerfils():
    with prAIHdb:
        cursor = prAIHdb.cursor()
        perfils = cursor.execute("SELECT id, nom_rol FROM perfil").fetchall()
        return perfils

async def recupera_missatges(la_conversacio:int):
    with prAIHdb:
        # ens interessa veure el que hi ha
        # missatges= cursor.execute("SELECT role, content FROM messages WHERE conversacio_id = ? ORDER BY id", (la_conversacio,)).fetchall()
        missatges= cursor.execute("SELECT role, content, id FROM messages WHERE conversacio_id = ? ORDER BY id", (la_conversacio,)).fetchall()
        llista_missatges = []
        claus= ("role","content")
        # for missatge in missatges:
        #     llista_missatges.append(dict(zip(claus,missatge)))

        for missatge in missatges:
            missatge_ext =dict(zip(claus,missatge[:2]))
            missatge_ext["content"] = ctx.recupera_arxius(missatge[1:])
            llista_missatges.append(missatge_ext)
        return llista_missatges

# def afegir_missatge(la_conversacio:int, resposta:dict, data_ara=None):
def afegir_missatge(la_conversacio:int, resposta:dict, data_ara=None, arxius_content:list=None):
    if data_ara is None:
        data_ara = datetime.datetime.now().replace(microsecond=0).isoformat()
    # no el guardo amb json.dumps() ja que tinc el text del missatge directament
    # i ara no el guardo en una llista
    missatge =resposta["message"]
    with prAIHdb:
        # primer obtenim l'anterior missatge
        missatge_id=cursor.execute("INSERT INTO messages (conversacio_id,role,content,metadades, data_creacio) VALUES (?,?,?,?,?)",
                        (la_conversacio, missatge["role"],missatge["content"],json.dumps({k:v for k,v in resposta.items() if k not in ("message",)}),data_ara)).lastrowid
        cursor.execute("UPDATE OR IGNORE conversations SET (data_modificacio) = (?) WHERE id = ?",
                        (data_ara, la_conversacio))
        
        if arxius_content:
            for arxiu in arxius_content:
                cursor.execute("INSERT INTO arxius (missatge_id,ordre,name,content,data_creacio) VALUES (?,?,?,?,?)",
                                (missatge_id, arxiu["ordre"], arxiu["name"], arxiu["content"], data_ara))

# arranquem la API
if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(privateAIH, host="0.0.0.0", port=8000)
    # ca: Aquest el faig amb --reload per desenvolupar
    uvicorn.run("main:privateAIH", host="0.0.0.0", port=8000, reload=True)
