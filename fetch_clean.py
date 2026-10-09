import urllib3
import requests
import pandas as pd
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time
from io import StringIO
from io import BytesIO

def fetch_clean():
    current_year = time.localtime().tm_year
    dfs_incidenti =[]
    headers = {'Accept': 'application/vnd.sdmx.data+csv;version=1.0.0'}

#DATI INCIDENTI
#import
    for i in range(2001,current_year): #metto current_year nel range perché il range lo esclude
        url =   "https://esploradati.istat.it/SDMXWS/rest/data/41_983?startPeriod=" + str(i) + "&endPeriod="+ str(i-1)
        response_incidenti = requests.get(url, headers=headers, verify=False)

        df = pd.read_csv(StringIO(response_incidenti.text))

        dfs_incidenti.append(df)

        time.sleep(15)
    df_incidenti_raw = pd.concat(dfs_incidenti, ignore_index=True)
#clean
    df_incidenti_raw = df_incidenti_raw[['DATAFLOW','FREQ', 'REF_AREA', 'DATA_TYPE', 'RESULT', 'TIME_PERIOD', 'OBS_VALUE']]
    df_incidenti_raw[["REF_AREA","TIME_PERIOD"]] = df_incidenti_raw[["REF_AREA","TIME_PERIOD"]].astype(int)
    df_incidenti_raw_pivot = df_incidenti_raw.pivot(index=['DATAFLOW', 'FREQ', 'REF_AREA', 'TIME_PERIOD'],columns='RESULT', values='OBS_VALUE').reset_index()

#DATI COMUNI
#import
    dfs = []
    for i in range(2001, current_year, 1):
        url = 'https://situas-servizi.istat.it/publish/reportspooljson?pfun=74&pdata=31/12/'+ str(i)
        r= requests.get(url, verify=False)

        df = pd.DataFrame.from_dict(r.json()['resultset'])
        dfs.append(df)
    df_comuni_raw = pd.concat(dfs, ignore_index=True)
#clean
    df_comuni_raw = df_comuni_raw[['PRO_COM', 'COMUNE', 'AREA_KMQ', 'POP_RES', 'ANNO_POP_RES', 'COD_RIP', 'COD_REG', 'COD_UTS']]
    df_comuni_raw["ANNO_POP_RES"] = df_comuni_raw["ANNO_POP_RES"].astype(int)

#MERGE
    df_raw = df_incidenti_raw_pivot.merge(df_comuni_raw, how='left', left_on=['REF_AREA', 'TIME_PERIOD'], right_on=['PRO_COM', 'ANNO_POP_RES'])

    df_raw = df_raw[['COMUNE','REF_AREA','AREA_KMQ','POP_RES', '9', 'F', 'M','TIME_PERIOD']]
    df_raw = df_raw.rename(columns={"COMUNE": "Nome Comune","REF_AREA": "Codice Comune", "AREA_KMQ": "Area(kmq)", "POP_RES": "Popolazione", "9": "Incidenti", "F": "Feriti", "M": "Morti", "TIME_PERIOD": "Anno" })
    df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']] = df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']].round()
    df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']] = df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']].astype("Int64")

    df_raw = df_raw[df_raw['Nome Comune'].notna()].reset_index(drop=True)

    df_raw.to_csv('data/incidenti_comuni.csv', index=False)

fetch_clean()