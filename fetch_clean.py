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
#Clean
    df_comuni_raw = df_comuni_raw[['PRO_COM', 'COMUNE', 'AREA_KMQ', 'POP_RES', 'ANNO_AREA', 'COD_RIP', 'COD_REG', 'COD_UTS']]
    df_comuni_raw["ANNO_AREA"] = df_comuni_raw["ANNO_AREA"].astype(int)

#MERGE
    df_raw = df_incidenti_raw_pivot.merge(df_comuni_raw, how='inner', left_on=['REF_AREA', 'TIME_PERIOD'], right_on=['PRO_COM', 'ANNO_AREA'])

#Clean
    df_raw = df_raw[['COMUNE','REF_AREA','AREA_KMQ','POP_RES', '9', 'F', 'M','TIME_PERIOD']]
    df_raw = df_raw.rename(columns={"COMUNE": "Nome Comune","REF_AREA": "Codice Comune", "AREA_KMQ": "Area(kmq)", "POP_RES": "Popolazione", "9": "Incidenti", "F": "Feriti", "M": "Morti", "TIME_PERIOD": "Anno" })
    df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']] = df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']].round()
    df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']] = df_raw[['Popolazione','Incidenti', 'Feriti', 'Morti']].astype("Int64")
    df_raw['Area(kmq)'] = round(df_raw['Area(kmq)'], 2)
    
    df_raw['Nome Comune'] = df_raw['Nome Comune'].fillna('None (TO)')

#Segmento popolazione
    df_raw["Ampiezza demografica - Theme"] = [
        "<10k" if i < 10000
        else "10k-60k" if i < 60000
        else "60k-250k" if i < 250000
        else ">250k"
        for i in df_raw["Popolazione"]
    ]
    df_raw["Ampiezza demografica - SubTheme"] = [
        "< 500" if i < 500
        else "500-999" if i < 1000
        else "1k-2k" if i < 2000
        else "2k-3k" if i < 3000
        else "3k-5k" if i < 5000
        else "5k-10k" if i < 10000
        else "10k-20k" if i < 20000
        else "20k-60k" if i < 60000
        else "60k-100k" if i < 100000
        else "100k-250k" if i < 250000
        else "250k-500k" if i < 500000
        else "> 500k"
        for i in df_raw["Popolazione"]
    ]

    #Tasso x 1000 abitanti mi dà la relazione con la popolazione, quanto è diffuso
    df_raw['Incidentix1000abitanti'] = round(df_raw['Incidenti']/(df_raw['Popolazione']/1000), 3)
    #Tasso per km2 mi dà quanto è concentrato.
    df_raw['Incidentixkm²'] = round(df_raw['Incidenti']/(df_raw['Area(kmq)']), 2)
    # abitanti per km2 serve per analisi bivariata
    df_raw['ab/km²'] = round(df_raw['Popolazione']/(df_raw['Area(kmq)']), 2)
    #Tasso di mortiferiti per incidenti mi dà quanto è grave.
    df_raw['morti+feriti/incidenti'] = round((df_raw['Feriti']+df_raw['Morti'])/(df_raw['Incidenti']), 2)

    df_raw.to_csv('data/incidenti_comuni.csv', index=False)

fetch_clean()