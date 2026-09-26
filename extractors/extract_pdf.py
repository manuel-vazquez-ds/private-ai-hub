import io
import pymupdf, pymupdf4llm

async def extreu(elemento):

    try:
        contingut = await elemento.read()

        if not contingut:
            return "=== Empty file ==="

        # doc = pymupdf.open(stream=contingut, filetype="pdf")
        with pymupdf.open(stream=contingut, filetype="pdf") as doc:
            # ca: ara passem el markdowm a contingut
            contingut = pymupdf4llm.to_markdown(doc)
        return contingut

    except Exception as e:
        return f"=== Unknown error reading pdf: {str(e)} ==="

    finally:
        elemento.close()