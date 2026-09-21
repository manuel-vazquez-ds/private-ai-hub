import io
import pandas as pd
from zipfile import BadZipFile
import openpyxl.utils.exceptions

def obtenir_taules(df0):
    def elimina_bordes_na(df0):
        df =df0.copy()
        prova = True
        while prova:
            if df.iloc[0].isna().all():
                df = df.iloc[1:]
            elif df.iloc[:,0].isna().all():
                df = df.iloc[:,1:]
            else:
                prova = False
        return df

    def obte_taules_x_columnes(df0):
        df =df0.copy()
        df= elimina_bordes_na(df)
        subtaules = []
        ind_inicial = df.index[0]
        col_inicial = df.columns[0]
        ind_final = df.index[-1]
        col_final = df.columns[-1]

        for num, columna in df.items():
            if columna.isna().all():
                if df.loc[ind_inicial:ind_final, num:col_final].notna().any().any():
                    subtaules.extend(obte_taules_x_files(df.loc[ind_inicial:ind_final, num:col_final].copy()))
                col_final = num -1
                break
        subtaules.append([ind_inicial, ind_final, col_inicial, col_final])
        return subtaules

    def obte_taules_x_files(df0):
        df =df0.copy()
        df= elimina_bordes_na(df)
        subtaules = []
        ind_inicial = df.index[0]
        col_inicial = df.columns[0]
        ind_final = df.index[-1]
        col_final = df.columns[-1]

        for num, fila in df.iterrows():
            if fila.isna().all():
                subtaules.extend(obte_taules_x_files(df.loc[num:ind_final, col_inicial:col_final].copy()))
                ind_final = num -1
                break
        subtaules.extend(obte_taules_x_columnes(df.loc[ind_inicial:ind_final, col_inicial:col_final].copy()))
        return subtaules
    def obte_capcelera(elemento, taula0):
        taula = taula0.copy()
        capcelera= []
        # ca: de moment sols calculem taules amb 1 fila de capcelera,
        # això pot canviar en el futur
        capcelera.append(elemento.loc[taula[0],taula[2]:taula[3]].tolist())
        return capcelera

    def obte_fila_titol(elements):
        elements = [str(element).strip() for element in elements]
        return f'# {"".join(elements)}\n\n' if len(elements)==1 else f'### {" | ".join(elements)}\n\n'

    llista_taules= obte_taules_x_files(df0)
    cadena=""
    for taula in reversed(llista_taules):
        if taula[0] != taula[1]:
            capcelera =obte_capcelera(df0, taula)
            dftem=df0.loc[taula[0]:taula[1],taula[2]:taula[3]].copy()
            if len(capcelera)<len(dftem):
                if len(capcelera)==1:
                    dftem.columns=capcelera[0]
                else:
                    dftem.columns=capcelera
                dftem=dftem.iloc[len(capcelera):]
                cadena += dftem.to_markdown(index=False)
                cadena += "\n\n"
        # ca: considerarem files úniques com fila de títol
        else:
            cadena += obte_fila_titol(df0.loc[taula[0],taula[2]:taula[3]].values)
    if cadena == "":
        cadena = "\n\n=== Sheet with tables without records ===\n\n"
    return cadena

async def extreu(elemento):
    contingut = ""

    try:
        dades = await elemento.read()
        # ca: convertir bytes a DataFrame sense passar per fitxer
        
        fitxer = io.BytesIO(dades)
        el_llibre = pd.ExcelFile(fitxer)

    except (pd.errors.EmptyDataError, BadZipFile, ValueError):
        return "=== File with no data ===\n\n"

    try:
        for taula in el_llibre.sheet_names:

            contingut += f"=== Sheet {taula} ===\n\n"

            fitxer.seek(0)

            df = pd.read_excel(fitxer, sheet_name=taula, header=None)

            if df.empty:
                contingut += "=== Sheet with no data ===\n\n"
            else:
                contingut += obtenir_taules(df)

        el_llibre.close()

        return contingut

    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        el_llibre.close()
        return "\n\n=== Unknown data in file ===\n\n"