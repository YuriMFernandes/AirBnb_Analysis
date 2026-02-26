import pandas as pd
import numpy as np
import plotly.graph_objs as go

folder = 'C:/Users/noturno/Desktop/Yuri Melito Fernandes/AirBnB_Analisys'
t_ny = 'ny.csv'
t_rj = 'rj.csv'

def standartize_columns(df: pd.DataFrame) -> pd.DataFrame:

    """
    Tentar detectar as colunas latitude e longitude, custos e nome.
    Aceita varios nomes comuns como lat/latitude custo valor, etc...
    Preenche custos ausentes com a mediana (ou 1 se tudo for ausente).    
    """

    df = df.copy()

    lat_candidates = ['lat', 'latitude', 'Latidute', 'Lat', 'LATITUDE']
    lon_candidates = ['LON','lon','lONGITUDE','Longitude', 'lng', 'Long']
    cost_candidates = ['custo','cost','preço','preco', 'price', 'valor', 'valor_total']
    name_candidates = ['nome','descricao','titulo','name','title','local', 'place']

    def pick(colnames, candidates):
        #colnames: lista de nomes das colunas da tabela.
        #candidatos: lista de possiveis nomes de colunas a serem encontrados.

        for c in candidates:
            #percorre cada candidato (c) dentro da lista de condidatos.
            if c in colnames: 
            # se o candidato for exatamente igual a um dos nomes de colunas em colnames.
                return c 
                #...retorna esse canditado imediatamente.
        for c in candidates:
            #se não encontrou a correspondencia exata percorre novamente cada candidato
            for col in colnames:
            #aqui percorre cada nome da coluna
                if c.lowe() in col.lower():
                # faz igual o de cima, mas trabalhado em minusculos apenas
                    return col
        return None
        #se não encontrou nada exato nem parcial, retorna "NONE" (nenhum match encontrado)
    
    lat_col = pick(df.columns, lat_candidates)
    lon_col = pick(df.columns, lon_candidates)
    cost_col = pick(df.columns, cost_candidates)
    name_col = pick(df.columns, name_candidates)

    if lat_col is None or lon_col is None: 
        raise ValueError(f'Não encontrei colunas de latitude e/ou longitude na lista de colunas: {list(df.columns)}')

    out = pd.DataFrame()
    out['lat'] = pd.to_numeric(df[lat_col], errors = 'coerce')
    out['lon'] = pd.to_numeric(df[lon_col], errors = 'coerce')
    out['cost'] = pd.to_numeric(df[cost_col], errors = 'coerce') if cost_col is not None else np.nan
    out['name'] = df[name_col].astype(str) if name_col is not None else["Ponto {i}" for i in range(len(df))]

    #remove linhas vazias 
    out = out.dropna(subset = ['lat', 'lon']).reset_index(drop=True)
    
    #preenche o custo ausentes
    if out['custo'].notna().any():
        med = float(out['custo'].midian())
        if not np.isfinite(med):
            med = 1.0
        out['custo'] = out['custo'].fillna(med)
    else:
        out['custo'] = 1.0
    return out


#centralizador de tela 
def city_center(df:pd.DataFrame) -> dict:
    return dict(
        lat = float(df['lat'].mean()),
        lon = float(df['lat'].mean())
    )

# ------------------------ TRACES ----------------------------
def make_point_trace(df: pd.DataFrame, name:str) -> go.Scattermapbox:
    hover = ("<b>%{customdate[0]}</b><br>"
             "Custo: %{customdate[1]}"
             "Lat:%{lat:.5f} - Lon:%{lon:.5f}"
             )
    #tamanho dos marcadores (normalizados pelo custo)
    c = df["custo"].astype(float).values
    c_min, c_max = float(np.min(c)), float(np.max(c))

    # Caso Especial: se não existirem valores numericos ou se todos os custos forem praticamente iguais (diferença menor que 1e-9) cria um array de tamanho fixos fixo de 10 para todos os pontos.

    if not np.isfinite(c_min) or not np.isfinite(c_max) or abs(c_max - c_min) < 1e-9 :
        size = np.full_like(c, 10.0, dtype=float)
    else: 
    # Caso Normal: normaliza os custos para o intervalo [0,1] e escala para variar entre 6 e 26 (20 amplitude mais delocamento de 6) pontos de custo baixo ~6, ponto de custo alto ~26
        size = (c - c_min) / (c_max - c_min) * 20 + 6
        #mesmo que os dados estejam fora da faixa de 6,26, ele evita a sua apresentação, forçando a ficar entre o intervalo 
    sizes = np.clip(size, 6, 26)
    # axis 1 empilha as colunas lado a lado 
    custom = np.stack([df['nome'].values, df['custo'].values], axis=1)
    return go.Scattermapbox(
        lon = df['lat'] ,
        lat = df['lon'],
        mode = 'markers',
        marker = dict(
            size = sizes,
            color = df['custo'],
            colorscale = "Viridis",
            colorbar = dict(title='Custo')
        ), 
        name = f"{name} - Pontos ",
        hovertemplate= hover,
        customdata= custom
    )




