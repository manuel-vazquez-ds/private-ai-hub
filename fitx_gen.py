import re
import markdown
from bs4 import BeautifulSoup
from fastapi import HTTPException

def fitxerDeResposta(contingut: dict):
    # ca: contingut és un diccionari amb claus 'id', 'content', 'data_creacio'

    # ca: generem un fitxer amb el contingut
    components={}
    components["nomFitx"]=contingut["answer"]+"_"+dataNeta(contingut["data_creacio"])+"."+contingut["format"]
    if contingut["format"] == "md":
        components["dades"] = contingut['content']
        components["mediaType"] = "text/markdown"
        return components
        # ca: si és markdown ja no calia que seguim

    if contingut["format"] == "txt":
        components["dades"] = markdown_a_text(contingut['content'])
        components["mediaType"] = "text/plain"
        return components
    
    raise HTTPException(
        status_code=415,
        detail="Not supported format / Formato no soportado / Format no suportat"
    )

def dataNeta(data: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', data)

def markdown_a_text(text: str) -> str:
    html = markdown.markdown(text)
    return BeautifulSoup(html, "html.parser").get_text()
