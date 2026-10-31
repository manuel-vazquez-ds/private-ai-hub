import re
import markdown
from bs4 import BeautifulSoup
from fastapi import HTTPException

import io
import pymupdf

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

    if contingut["format"] == "pdf":
        components["dades"] = markdown_a_pdf(contingut['content'])
        components["mediaType"] = "application/pdf"
        # Actualitzem l'extensió del fitxer si cal, o es manté amb el format indicat
        # components["nomFitx"] = contingut["answer"] + "_" + dataNeta(contingut["data_creacio"]) + ".pdf"
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

def markdown_a_pdf(text: str) -> bytes:
    # ca: markdown -> html (extra: taules, blocs de codi amb ```, etc.)
    html = markdown.markdown(
        text or " ",
        extensions=["extra", "sane_lists", "nl2br"],
    )

    css = """
        body { font-family: sans-serif; font-size: 11pt; line-height: 1.4; }
        h1 { font-size: 20pt; margin-top: 14pt; }
        h2 { font-size: 16pt; margin-top: 12pt; }
        h3 { font-size: 13pt; margin-top: 10pt; }
        code { font-family: monospace; font-size: 9.5pt; }
        pre { font-family: monospace; font-size: 9.5pt; padding: 6pt; border: 1px solid #cccccc; }
        blockquote { margin-left: 12pt; color: #555555; }
        table { border-collapse: collapse; }
        tr { page-break-inside: avoid; }
        th, td { border: 1px solid #999999; padding: 3pt; }
        th { font-weight: bold; border-bottom: 2px solid #333333; }
    """

    buffer = io.BytesIO()
    writer = pymupdf.DocumentWriter(buffer)
    story = pymupdf.Story(html=html, user_css=css)

    mediabox = pymupdf.paper_rect("a4")           # pàgina A4
    where = mediabox + (50, 50, -50, -50)         # marges de 50 pt

    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()

    writer.close()  # ca: imprescindible: aquí es bolca el PDF al buffer
    return buffer.getvalue()