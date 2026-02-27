import pandas as pd
import numpy as np
import plotly.graph_objs as go

folder = 'C:/Users/noturno/Desktop/Yuri Melito Fernandes/AirBnB_Analisys/'
t_ny = 'ny.csv'
t_rj = 'rj.csv'
t_bzn = 'bzn.csv'
t_ps = 'ps.csv'

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
                if c.lower() in col.lower():
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
    out['custo'] = pd.to_numeric(df[cost_col], errors = 'coerce') if cost_col is not None else np.nan
    out['nome'] = df[name_col].astype(str) if name_col is not None else[f"Ponto {i}" for i in range(len(df))]

    #remove linhas vazias 
    out = out.dropna(subset = ['lat', 'lon']).reset_index(drop=True)
    
    #preenche o custo ausentes
    if out['custo'].notna().any():
        med = float(out['custo'].median())
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
        lon = float(df['lon'].mean())
    )

# ------------------------ TRACES ----------------------------
def make_point_trace(df: pd.DataFrame, name:str) -> go.Scattermapbox:
    hover = ("<b>%{customdata[0]}</b><br>"
             "Custo: %{customdata[1]}<br>"
             "Lat:%{lat:.5f} - Lon:%{lon:.5f}"
             )
    
    # tamanho dos marcadores (normalizados pelo custo)
    c = df["custo"].astype(float).values
    c_min, c_max = float(np.min(c)), float(np.max(c))

    # Caso Especial: se nao existirem valores numericos ou se todos os custos forem praticamente iguais (diferença menor que 1e-9) cria um array de tamanho fixo 10 para todos os pontos.
    if not np.isfinite(c_min) or not np.isfinite(c_max) or abs(c_max - c_min) < 1e-9:
        size = np.full_like(c, 10.0, dtype=float)

    else:
    # Caso Normal: normaliza os custos para o intervalo [0,1] e escala para variar entre 6 e 26 (20 de amplitude mais deslocamento de 6) pontos de custo baixo ~6, ponto de custo alto ~26
        size = (c - c_min) / (c_max - c_min) * 20 + 6
        #mesmo que os dados estejam fora da faixa de 6,26, ele evita a sua apresentação, forçando a ficar entre o intervalo
    sizes = np.clip(size, 6, 26)
    # axis 1 empilha as colunas lado a lado
    custom = np.stack([df['nome'].values, df['custo'].values], axis=1)
    return go.Scattermapbox(
        lat = df['lat'],
        lon = df['lon'],
        mode = 'markers',
        marker = dict(
            size = sizes,
            color = df['custo'],
            colorscale = "Viridis",
            colorbar = dict(title='Custo')
        ),
        name = f"{name} - Pontos",
        hovertemplate = hover,
        customdata = custom
    )

def make_density_trace(df: pd.DataFrame, name: str) -> go.Densitymapbox:
    return  go.Densitymapbox(
        lat = df['lat'],
        lon = df['lon'],
        z = df['custo'],
        radius = 20,
        colorscale = 'Inferno',
        name = f"{name} - Pontos",
        showscale = True,
        colorbar = dict(title = 'Custo'),
    )

def main():
    # Carregar e padronizar os dados!
    ny = standartize_columns(pd.read_csv(f"{folder}{t_ny}"))
    rj = standartize_columns(pd.read_csv(f"{folder}{t_rj}"))
    bzn = standartize_columns(pd.read_csv(f"{folder}{t_bzn}"))
    ps = standartize_columns(pd.read_csv(f"{folder}{t_ps}"))

    # cria os quatro races (ny pontos / ny calor / rj pontos / rj calor)
    ny_point = make_point_trace(ny, "Nova York")
    ny_heat = make_density_trace (ny, "Nova York")
    rj_point = make_point_trace(rj, "Rio de Janeiro")
    rj_heat = make_density_trace (rj, "Rio de Janeiro")
    bzn_point = make_point_trace(bzn, "Bozeman")
    bzn_heat = make_density_trace (bzn, "Bozeman")
    ps_point = make_point_trace(ps, "Paris")
    ps_heat = make_density_trace (ps, "Paris")

    fig = go.Figure([ny_point, ny_heat, rj_point, rj_heat, bzn_point, bzn_heat, ps_point, ps_heat ])

    fig.data[1].visible = False
    fig.data[2].visible = False
    fig.data[3].visible = False
    fig.data[4].visible = False
    fig.data[5].visible = False
    fig.data[6].visible = False
    fig.data[7].visible = False

    def update_map_layout(df, zoom):
        return {
            "mapbox.center":city_center(df),
            "mapbox.zoom": zoom
        }

    
    buttons = [
        dict(
            label = "Nova York - Pontos",
            method = "update",
            args = [
                {"visible": [True, False, False, False,False,False,False, False]},
                update_map_layout(ny, 9)
            ]
        ),
        dict(
            label = "Nova York - Calor",
            method = "update",
            args = [
                {"visible": [False, True, False, False,False, False,False, False]},
                update_map_layout(ny, 9)
            ]
        ),
        dict(
            label = "Rio de Janeiro - Pontos",
            method = "update",
            args = [
                {"visible": [False, False, True, False, False,False,False, False]},
                update_map_layout(rj, 10)
            ]
        ),
        dict(
            label = "Rio de Janeiro - Calor",
            method = "update",
            args = [
                {"visible": [False, False, False, True, False, False,False, False]},
                update_map_layout(rj, 10)
            ]            
        ),
        dict(
            label = "Bozeman - Pontos",
            method = "update",
            args = [
                {"visible": [False, False, False, False, True,False,False, False]},
                update_map_layout(bzn, 10)
            ]
        ),
        dict(
            label = "Bozeman - Calor",
            method = "update",
            args = [
                {"visible": [False, False, False, False, False, True,False, False]},
                update_map_layout(bzn, 10)
            ]            
        ),
        dict(
            label = "Paris - Pontos",
            method = "update",
            args = [
                {"visible": [False, False, False, False, False,False, True, False]},
                update_map_layout(ps, 10)
            ]
        ),
        dict(
            label = "Paris - Calor",
            method = "update",
            args = [
                {"visible": [False, False, False, False, False, False,False, True]},
                update_map_layout(ps, 10)
            ]            
        )
    ]

    fig.update_layout(
        title = 'Mapa interativo de Custo - Pontos e Mapa de Calor',
        mapbox_style = 'open-street-map',
        mapbox = dict(center = city_center(ny), zoom = 10),
        margin = dict(l = 10, r = 10, t = 50, b = 10),
        updatemenus = [dict(
            buttons = buttons, 
            direction = "down",
            x = 0.01,
            y = 0.99,
            xanchor = 'left', 
            yanchor = 'top',
            bgcolor = 'white',
            bordercolor = 'lightgray'
            )],
        legend = dict(
            orientation = 'h',
            yanchor ='bottom',
            xanchor = 'right',
            y = 0.01,
            x = 0.99

        )

    )

    # Salva o HTML de aprentação
    fig.write_html(
        f"{folder}mapa_custos_interativos.html", include_plotlyjs = 'cdn', full_html = True
    )
    print(f"Arquivo gerado com sucesso em {folder}mapa_custos_interativos.html")
 
# Inciar o servidor:
if __name__ == '__main__':
    main()