import pandas as pd
import statsmodels.api as sm

df = pd.read_csv('data/incidenti_comuni.csv')

#tengo le osservazioni dopo il 2020
df_noOutliers = df[~df['Anno'].isin([2020, 2024, 2025])]
df_noOutliers = df_noOutliers[~(df_noOutliers['Incidentix1000abitanti'] > 75)]
df_noOutliers = df_noOutliers[~((df_noOutliers['Popolazione'] < 5000) & (df_noOutliers['Incidentixkm²'] > 20))]
df_noOutliers = df_noOutliers[~(df_noOutliers['morti+feriti/incidenti'] > 15)]
#lista dei codici Comune
codici_Comuni = df_noOutliers['Codice Comune'].unique()
#df vuoto con gli indicatori con cui valutare un Comune
board = pd.DataFrame(columns=['Codice Comune', 'Nome', 'Popolazione', 'Trend Incidenti', 'p-value', 'Incidenti', 'Incidentix1000abitanti', 'Incidentixkm²', 'Gravità Incidenti', 'Ampiezza demografica - Theme', 'Ampiezza demografica - SubTheme'])

#per ogni loop genero una osservazione del mio nuovo df
def calculate_slope():
    for i in codici_Comuni:
        #creo un df per un solo Comune
        df = df_noOutliers[df_noOutliers['Codice Comune'] == i]
        #prendo il nome
        name = df['Nome Comune'].iloc[0]
        codice = df['Codice Comune'].iloc[0]
        demografia_theme = df['Ampiezza demografica - Theme'].iloc[0]
        demografia_Subtheme = df['Ampiezza demografica - SubTheme'].iloc[0]
        Incidentix1000abitanti = round(df['Incidentix1000abitanti'].mean(),2)
        Popolazione = round(df['Popolazione'].mean(), 0)
        Incidenti = round(df['Incidenti'].mean(),2)
        Incidentixkm = round(df['Incidentixkm²'].mean(),2)
        Gravità_Incidenti = round(df['morti+feriti/incidenti'].mean(), 2)
        
        #tengo le colonne per cui calcolo il trend annuale
        df = df[['Anno', 'Incidentix1000abitanti']]

        Y = df['Incidentix1000abitanti']
        X = df['Anno']
        X = sm.add_constant(data=X)   # add a constant to the model
        model = sm.OLS(endog=Y,exog=X)
        results = model.fit()

        pendenza = results.params['Anno']
        p_value = results.pvalues['Anno']

        #popolo l'osservazione per questo Comune    
        idx = len(board)
        board.loc[idx, 'Codice Comune'] = codice
        board.loc[idx, 'Nome'] = name
        board.loc[idx, 'Trend Incidenti'] = pendenza
        board.loc[idx, 'p-value'] = p_value
        board.loc[idx, 'Popolazione'] = Popolazione
        board.loc[idx, 'Incidenti'] = Incidenti
        board.loc[idx, 'Incidentix1000abitanti'] = Incidentix1000abitanti
        board.loc[idx, 'Incidentixkm²'] = Incidentixkm
        board.loc[idx, 'Gravità Incidenti'] = Gravità_Incidenti
        board.loc[idx, 'Ampiezza demografica - Theme'] = demografia_theme
        board.loc[idx, 'Ampiezza demografica - SubTheme'] = demografia_Subtheme

calculate_slope()
board.to_csv('data/comuni_dashboard_df.csv', index=False)