from charset_normalizer import from_bytes
async def extreu(el_arxiu):
    contingut = await el_arxiu.read()
    resultat = str(from_bytes(contingut).best())
    await el_arxiu.close()
    return resultat