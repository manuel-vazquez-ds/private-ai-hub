import sqlite3
import extractors.extract_text as et
MIDA_MAXIMA_FITXERS = 1024 * 1024  # 1 MB
# MIDA_MAXIMA_FITXERS = 10 * 1024  # 10 KB
CONTINGUT_MAXIM = 200 * 1024  # 200 KB
EXTENSIONS_PERMESES = [".txt", ".md"] # Més endavant afegirem més
CONTEXTS_PERMESOS = ["text/plain", "text/markdown"] # Més endavant afegirem més
INFORMACIO_ADDICIONAL = """
IMPORTANT: Try to answer in the same language as the user.
User can upload files that can serve to help me answer the question. I will attach to the prompt in this structure:
=== USER ATTACHED {X} FILES === (where X is the number of files)
=== FILE {Y} === (where Y is the file number, from 1 to X)
=== FILE NAME: {filename} === (where filename is the name of the file)
{file_content_1}
===
...
=== FILE {Y} === (where Y is the file number, from 1 to X)
=== FILE NAME: {filename} === (where filename is the name of the file)
{file_content_2}
===
...
{file_content_X}
===
=== END USER ATTACHED {X} FILES ===
"""



def comprovar_arxius(arxius):
    """
    Comprova que els arxius siguin vàlids.
    """
    mida_total = 0
    for arxiu in arxius:
        mida_total += arxiu.size
        if arxiu.size > MIDA_MAXIMA_FITXERS:
            return f"Maximum file size exceeded / Tamaño máximo de archivo excedido / Mida màxima de fitxer excedida / ({arxiu.filename})"
        if arxiu.content_type not in CONTEXTS_PERMESOS:
            return f"Invalid file type / Tipo de archivo no válido / Tipus de fitxer no vàlid / ({arxiu.filename})"
        if not arxiu.filename.endswith(tuple(EXTENSIONS_PERMESES)):
            return f"Invalid file extension / Extensión de archivo no válida / Extensió de fitxer no vàlida / ({arxiu.filename})"
    if mida_total > MIDA_MAXIMA_FITXERS:
        return "Maximum total file size exceeded / Tamaño total máximo de archivos excedido / Mida total màxima de fitxers excedida"
    return None

async def processar_arxius(missatge, arxius):
    """
    Processa els arxius i retorna el contingut.
    """
    contingut = missatge
    arxius_content = []
    contingut += f"\n=== USER ATTACHED {len(arxius)} FILES ===\n"
    for i, arxiu in enumerate(arxius, start=1):
        if arxiu.content_type == "text/plain" or arxiu.content_type == "text/markdown" \
        or arxiu.filename.endswith((".txt", ".md")):
            resultat =  await et.extreu(arxiu)

        contingut += f"=== FILE {i} ===\n"
        contingut += f"=== FILE NAME: {arxiu.filename} ===\n"
        contingut += resultat
        contingut += "\n===\n"
        arxius_content.append({"ordre": i, "name": arxiu.filename, "content": resultat})
    contingut += "=== END USER ATTACHED FILES ===\n"
    return contingut, arxius_content

def recupera_arxius(del_missatge):
    """
    Recupera els arxius del missatge.
    """
    prAIHdb = sqlite3.connect('prAIH.db')
    # prAIHdb.row_factory = sqlite3.Row
    with prAIHdb:
        cursor = prAIHdb.cursor()
        contingut= del_missatge[0]
        arxius_del_missatge = cursor.execute("SELECT ordre, name, content FROM arxius WHERE missatge_id = ?", (del_missatge[1],)).fetchall()
    if arxius_del_missatge:
        contingut += f"\n=== USER ATTACHED {len(arxius_del_missatge)} FILES ===\n"
        for arxiu in arxius_del_missatge:
            contingut += f"=== FILE {arxiu[0]} ===\n"
            contingut += f"=== FILE NAME: {arxiu[1]} ===\n"
            contingut += arxiu[2]
            contingut += "\n===\n"
        contingut += "=== END USER ATTACHED FILES ===\n"
    return contingut