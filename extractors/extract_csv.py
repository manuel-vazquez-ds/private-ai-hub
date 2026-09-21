import io
import pandas as pd


async def extreu(elemento):

    try:
        contingut = await elemento.read()

        if not contingut:
            return "=== Empty file ==="

        df = pd.read_csv(
            io.BytesIO(contingut),
            sep=None,
            engine="python"
        )

        if df.empty:
            return "=== Table with no registers ==="

        return df.to_markdown(index=False)

    except pd.errors.EmptyDataError:
        return "=== EmptyDataError ==="

    except pd.errors.ParserError:
        return "=== Unknown data in file ==="