import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
import datetime
import locale
from flask import Flask
from waitress import serve
from dash_bootstrap_templates import ThemeSwitchAIO
from dash.exceptions import PreventUpdate
import threading

server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, server=server)

tab_card = {'height': '100%'}

main_config = {
    "hovermode": "x unified",
    "legend": {"yanchor":"top",
                "y":0.9,
                "xanchor":"left",
                "x":0.1,
                "title": {"text": None},
                "font" :{"color":"white"},
                "bgcolor": "rgba(0,0,0,0.5)"},
    "margin": {"l":10, "r":10, "t":10, "b":10}
}

config_graph={"displayModeBar": False, "showTips": False}

template_theme1 = "flatly"
template_theme2 = "darkly"
url_theme1 = dbc.themes.FLATLY
url_theme2 = dbc.themes.DARKLY
lock = threading.Lock()

def obter_dados_firebird():
    conexao = mysql.connector.connect(
        host='modabank.c5zpvuuffn2o.sa-east-1.rds.amazonaws.com',
        user='admin',
        password='B1bl10t3c4',
        database='modapay'
    )

    query = """
        SELECT DAY(c.data_dia) AS DIA, 
               MONTH(c.data_dia) AS MES, 
               YEAR(c.data_dia) AS ANO, 
               e.Fantasia,
               c.`status`,
               'PIX_IN',
               c.valor,
               c.taxa_total,
               c.valor_sem_taxa AS VALOR_MENOS_TAXA
        FROM cobranca c
        INNER JOIN empresa e ON c.fk_empresa = e.codigo

        UNION ALL

        SELECT DAY(s.data_solicitacao) AS DIA, 
               MONTH(s.data_solicitacao) AS MES, 
               YEAR(s.data_solicitacao) AS ANO, 
               e.Fantasia,
               s.status,
               'PIX_OUT',
               s.valor_solicitado,
               s.taxa_total,
               s.valor_sem_taxa AS VALOR_MENOS_TAXA
        FROM saque s
        INNER JOIN empresa e ON s.fk_empresa = e.codigo
        """

    df = pd.read_sql(query, conexao)

    conexao.close()
    return df

df = obter_dados_firebird()
df_cru = df

def convert_to_text(month):
    match month:
        case 0:
            x = 'MÊS ATUAL'
        case 1:
            x = 'JAN'
        case 2:
            x = 'FEV'
        case 3:
            x = 'MAR'
        case 4:
            x = 'ABR'
        case 5:
            x = 'MAI'
        case 6:
            x = 'JUN'
        case 7:
            x = 'JUL'
        case 8:
            x = 'AGO'
        case 9:
            x = 'SET'
        case 10:
            x = 'OUT'
        case 11:
            x = 'NOV'
        case 12:
            x = 'DEZ'
    return x

mes_atual = datetime.datetime.now().month
ano_atual = datetime.datetime.now().year
locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

def formatar_reais(valor):
    return locale.currency(valor, grouping=True)

def year_filter(year):
    if year == 0:
        mask = df['ANO'].isin([datetime.datetime.now().year])
    else:
       mask = df['ANO'].isin([year])
    return mask

def month_filter(month):
    if month == 0:
        mask = df['MES'].isin([datetime.datetime.now().month])
    else:
       mask = df['MES'].isin([month])
    return mask

def year_month_filter(year, month):
    if year == 0 and month == 0:
        mask = df['ANO'].isin([datetime.datetime.now().year]) & df['MES'].isin([datetime.datetime.now().month])
    elif year == 0:
        mask = df['MES'].isin([month])
    elif month == 0:
        mask = df['ANO'].isin([year])
    else:
        mask = (df['ANO'] == year) & (df['MES'] == month)
    return mask

def team_filter(team):
    if team == 0:
        mask = df['Fantasia'].isin(df['Fantasia'].unique())
    else:
        mask = df['Fantasia'].isin([team])
    return mask

def pix_filter(pix_type):
    if pix_type == 'PIX_IN':
        mask = df['PIX_IN'] == 'PIX_IN'
    elif pix_type == 'PIX_OUT':
        mask = df['PIX_IN'] == 'PIX_OUT'
    else:
        mask = df['PIX_IN'].isin(['PIX_IN', 'PIX_OUT'])
    return mask

def status_pix_filter(status_list):
    if isinstance(status_list, str): 
        status_list = [status_list]
    
    if 'Todos' in status_list:
        mask = df['status'].notnull()
    else:
        mask = df['status'].isin(status_list) 
    return mask

authenticated = False
center_style = {'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'height': '100vh'}
login_layout = html.Div(
    [
        html.Div(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Img(src=r'assets/logo.png', alt='logo',className='logo'),
                        html.Br(),
                        dbc.Input(id='username', type='text', placeholder='Usuário', className='input'),
                        html.Br(),
                        dbc.Input(id='password', type='password', placeholder='Senha', className='input'),
                        html.Br(),
                        dbc.Button("Entrar", id='login-button', color="primary",  className='logo input'),  
                        html.Div(id='login-output')
                    ]
                )
            ), style={'max-width': '400px'}
        )
    ], style=center_style
)
    
main_layout = dbc.Container(children=[
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Legend("Ideia System")
                        ], sm=8),
                        dbc.Col([
                            html.I(className='logo', style={'font-size': '300%'})
                        ], sm=4, align="center")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            ThemeSwitchAIO(aio_id="theme", themes=[url_theme1, url_theme2]),
                            html.Legend("DashBoard de Vendas")
                        ])
                    ], style={'margin-top': '10px'}),
                    dbc.Row([
                    html.Div(
                        className='logo-container',
                        children=[
                            html.Img(src=r'assets/logo.png', alt='logo',className='logo')
                        ])
                    ], style={'margin-top': '10px'})
                ])
            ], style=tab_card)
        ], sm=4, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(
                        dbc.Col(
                            html.Legend('Top 5 Empresas')
                        )
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='graph1', className='dbc', config=config_graph)
                        ], sm=12, md=7),
                        dbc.Col([
                            dcc.Graph(id='graph2', className='dbc', config=config_graph)
                        ], sm=12, lg=5)
                    ])
                ])
            ], style=tab_card)
        ], sm=12, lg=7),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(
                        dbc.Col([
                            html.H5('Escolha o ANO'),
                            dbc.RadioItems(
                                id="radio-year",
                                options=[],
                                value=ano_atual if ano_atual in df['ANO'].unique() else 0,
                                inline=True,
                                labelCheckedClassName="text-success",
                                inputCheckedClassName="border border-success bg-success",
                            ),
                            html.Div(id='year-selecty', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                            html.H5('Escolha o MÊS'),
                            dbc.RadioItems(
                                id="radio-month",
                                options=[],
                                value=mes_atual if mes_atual in df['MES'].unique() else 0,
                                inline=True,
                                labelCheckedClassName="text-success",
                                inputCheckedClassName="border border-success bg-success",
                            ),
                            html.Div(id='month-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                            html.H5('Escolha o tipo de transação PIX'),
                            dbc.RadioItems(
                            id="radio-pix",
                            options=[],
                            value='Ambos', 
                            inline=True,
                            labelCheckedClassName="text-success",
                            inputCheckedClassName="border border-success bg-success",
                            ),
                            html.Div(id='pix-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                            html.H5('Escolha o status do PIX'),
                            dbc.Checklist(
                            id="radio-status-pix",
                            options=[],
                            value=[],
                            inline=True,
                            inputCheckedStyle={'margin-right': '10px', 'background-color': '#18bc9c', 'color': '#18bc9c'},
                            labelCheckedStyle={'color':'#18bc9c'} 
                            ),
                        html.Div(id='status-pix-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                        ])
                    )
                ])
            ], style=tab_card)
        ], sm=12, lg=3)
    ], className='g-2 my-auto', style={'margin-top': '7px'}),

    # Row 2
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph3', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph4', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ])
            ], className='g-2 my-auto', style={'margin-top': '7px'})
        ], sm=12, lg=5),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph5', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ], sm=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph6', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ], sm=6)
            ], className='g-2'),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dcc.Graph(id='graph7', className='dbc', config=config_graph)
                    ], style=tab_card)
                ])
            ], className='g-2 my-auto', style={'margin-top': '7px'})
        ], sm=12, lg=4),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='graph8', className='dbc', config=config_graph)
            ], style=tab_card)
        ], sm=12, lg=3)
    ], className='g-2 my-auto', style={'margin-top': '7px'}),

    # Row 3
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Distribuição de Faturamento por Empresa'),
                    dcc.Graph(id='graph9', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph10', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph13', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph11', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph12', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5('Escolha a EMPRESA'),
                    dcc.Dropdown(
                        id="radio-team",
                        options=[],
                        value=0,
                        style={'backgroundColor': '#333333'},
                        clearable=False,
                    ),
                    html.Div(id='team-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                ]),    html.Div(id="output-dados"),
            ], style=tab_card)
        ], sm=12, lg=2),
    ], className='g-2 my-auto', style={'margin-top': '7px'}),
        dcc.Interval(
        id='interval-component',
        interval=5 * 60 * 1000,  
        n_intervals=0
    )
], fluid=True, style={'height': '100vh'})

@app.callback(
    Output("output-dados", "children"),
    Input('interval-component', 'n_intervals')
)
def recarregar_dados(n_intervals):
    global df
    with lock:
        try:
            df = obter_dados_firebird()
        except Exception as e:
            print(f"Erro ao obter dados do Firebird: {e}")
    return None

df = obter_dados_firebird()

@app.callback(
    Output("radio-pix", "options"),
    Output("radio-pix", "value"),
    Input('interval-component', 'n_intervals')
)
def update_radio_pix(n_intervals):
    options = [{'label': 'ENTRADA', 'value': 'PIX_IN'}, {'label': 'SAÍDA', 'value': 'PIX_OUT'}, {'label': 'ENTRADA E SAÍDA', 'value': 'Ambos'}]
    default_value = 'Ambos'
    return options, default_value

@app.callback(
    Output("radio-status-pix", "options"),
    Output("radio-status-pix", "value"),
    Input('interval-component', 'n_intervals'),
)
def update_radio_status_pix(n_intervals):
    unique_status = df['status'].unique()  
    options = [{'label': status, 'value': status} for status in unique_status]
    options.append({'label': 'TODOS', 'value': 'Todos'}) 
    default_value = ['CONCLUIDO', 'CONCLUIDA', 'processing']
    return options, default_value


@app.callback(
    Output('graph1', 'figure'),
    Output('graph2', 'figure'),
    Output('graph3', 'figure'),
    Output('graph4', 'figure'),
    Output('graph5', 'figure'),
    Output('graph6', 'figure'),
    Output('graph7', 'figure'),
    Output('graph8', 'figure'),
    Output('graph9', 'figure'),
    Output('graph10', 'figure'),
    Output('graph11', 'figure'),
    Output('graph12', 'figure'),
    Output('graph13', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input('radio-pix', 'value'), 
    Input('radio-status-pix', 'value'), 
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graphs(month, year, team, pix_type, status_list, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            mask_pix = pix_filter(pix_type)
            mask_status_pix = status_pix_filter(status_list) 
            mask_zero = year_month_filter(year, 0)
            df_filtered = df.loc[mask_year & mask_month & mask_team & mask_pix & mask_status_pix] 
            df_meseano = df.loc[mask_year & mask_month]
            df_zero = df.loc[mask_zero]
            df_team_zero = df.loc[mask_zero & mask_team]
                
            #Grafico 1
            df_1 = df_filtered.groupby(['Fantasia'])['taxa_total'].sum().reset_index()
            df_1 = df_1.groupby('Fantasia').head(1).reset_index()
            df_1 = df_1.sort_values(by='taxa_total', ascending=False)
            df_1 = df_1.head(5)
            df_1['TOTAL_VENDAS'] = df_1['taxa_total'].map(formatar_reais)
            fig1 = go.Figure(go.Bar(x=df_1['Fantasia'], y=df_1['taxa_total'], textposition='auto', text=df_1['TOTAL_VENDAS']))
            fig1.update_layout(main_config, height=200, template=template)

            #Grafico 2
            fig2 = go.Figure(go.Pie(labels=df_1['Fantasia'] + ' - ' + df_1['Fantasia'], values=df_1['taxa_total'], hole=.6))
            fig2.update_layout(main_config, height=200, template=template, showlegend=False)

            #Grafico 3
            df_3 = df_filtered.groupby('DIA')['taxa_total'].sum().reset_index()
            df_3['TOTAL_VENDAS'] = df_3['taxa_total'].map(formatar_reais)
            fig3 = go.Figure(go.Scatter(x=df_3['DIA'], y=df_3['taxa_total'], fill='tonexty', text=df_3['TOTAL_VENDAS'], hoverinfo='text'))
            fig3.add_annotation(text='Faturamento por dia do Mês',xref="paper", yref="paper", font=dict( size=17, color='gray'), align="center", bgcolor="rgba(0,0,0,0.8)", x=0.05, y=0.85, showarrow=False)
            fig3.update_layout(main_config, height=180, template=template)

            #Grafico 4
            df_4 = df_filtered.groupby('MES')['taxa_total'].sum().reset_index()
            df_4['TOTAL_VENDAS'] = df_4['taxa_total'].map(formatar_reais)
            fig4 = go.Figure(go.Scatter(x=df_4['MES'], y=df_4['taxa_total'], fill='tonexty', text=df_4['TOTAL_VENDAS'], hoverinfo='text'))
            fig4.add_annotation(text='Faturamento por Mês', xref="paper", yref="paper",font=dict( size=20, color='gray'),align="center", bgcolor="rgba(0,0,0,0.8)",x=0.05, y=0.85, showarrow=False)
            fig4.update_layout(main_config, height=180, template=template)

            #Grafico 5
            df_5 = df_filtered.groupby(['status', 'Fantasia'])['taxa_total'].sum()
            df_5.sort_values(ascending=False, inplace=True)
            df_5 = df_5.reset_index()
            fig5 = go.Figure()
            if not df_5.empty:
               fig5.add_trace(go.Indicator(mode='number+delta',
                            title={"text": f"<span>{df_5['status'].iloc[0]}</span><br><span style='font-size:70%'>Status com mais movimentações</span><br>"},
                            value=df_5['taxa_total'].iloc[0],
                            number={'prefix': "R$"},
                            delta={'relative': True, 'valueformat': '.1%', 'reference': df_5['taxa_total'].mean()}
                ))
            else:
                fig5.add_trace(go.Indicator(mode='number+delta', value=0, number={'prefix': "R$"}, title={"text": f"<span>- PIX</span>"}))
            fig5.update_layout(main_config, height=200, template=template)
            fig5.update_layout({"margin": {"l": 0, "r": 0, "t": 50, "b": 0}})

            #Grafico 6
            df_6 = df_filtered.groupby('Fantasia')['valor'].sum()
            df_6.sort_values(ascending=False, inplace=True)
            df_6 = df_6.reset_index()
            fig6 = go.Figure()
            if not df_6.empty:
                fig6.add_trace(go.Indicator(mode='number+delta',
                            title={"text": f"<span>{df_6['Fantasia'].iloc[0]}</span><br><span style='font-size:70%'>Empresa com mais movimentações</span><br>"},
                            value=df_6['valor'].iloc[0],
                            number={'prefix': "R$"},
                            delta={'relative': True, 'valueformat': '.1%', 'reference': df_6['valor'].mean()}
                ))
            else:
                fig6.add_trace(go.Indicator(mode='number+delta', value=0, number={'prefix': "R$"}, title={"text": f"<span>- EMPRESA</span>"}))
            fig6.update_layout(main_config, height=200, template=template)
            fig6.update_layout({"margin": {"l": 0, "r": 0, "t": 50, "b": 0}})

            #Grafico 7
            df_7_group = df_zero.groupby(['MES', 'Fantasia'])['taxa_total'].sum().reset_index()
            df_7_total = df_zero.groupby('MES')['taxa_total'].sum().reset_index()
            fig7 = px.line(df_7_group, y="taxa_total", x="MES", color="Fantasia")
            fig7.add_trace(go.Scatter(y=df_7_total["taxa_total"], x=df_7_total["MES"], mode='lines+markers', fill='tonexty', name='Total de Vendas'))
            fig7.update_layout(main_config, yaxis={'title': None}, xaxis={'title': None}, height=190, template=template)
            fig7.update_layout({"legend": {"yanchor": "top", "y": 0.99, "font": {"color": "white", 'size': 10}}})

            #Grafico 8
            df_8 = df_filtered.groupby('Fantasia')['taxa_total'].sum().reset_index()
            df_8['TOTAL_VENDAS'] = df_8['taxa_total'].map(formatar_reais)
            fig8 = go.Figure(go.Bar( x=df_8['Fantasia'], y=df_8['taxa_total'], orientation='v', textposition='auto', text=df_8['TOTAL_VENDAS'], hoverinfo='text',insidetextfont=dict(family='Times', size=12)))
            fig8.update_layout(main_config, height=360, template=template)

            #Grafico 9
            df_9 = df_meseano.groupby('Fantasia')['taxa_total'].sum().reset_index()
            fig9 = go.Figure()
            fig9.add_trace(go.Pie(labels=df_9['Fantasia'], values=df_9['taxa_total'], hole=.7))
            fig9.update_layout(main_config, height=150, template=template, showlegend=False)

            #Grafico 11
            df_11 = df_filtered
            fig11 = go.Figure()
            if not df_11.empty:
                fig11.add_trace(go.Indicator(mode='number',
                            title={"text": f"<span style='font-size:150%'>TAXA</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_11['taxa_total'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig11.add_trace(go.Indicator(mode='number', value=0, number={'prefix': "R$"}, title={"text": f"<span>TAXA</span>"}))
            fig11.update_layout(main_config, height=300, template=template)

            #Grafico 12
            today = datetime.datetime.now()
            df_12 = df_filtered[(df_filtered['DIA'] == today.day) & (df_filtered['MES'] == today.month) & (df_filtered['ANO'] == today.year)].groupby('Fantasia')['taxa_total'].sum()
            df_12.sort_values(ascending=False, inplace=True)
            df_12 = df_12.reset_index()
            fig12 = go.Figure()

            if not df_12.empty:
                fig12.add_trace(go.Indicator(
                            title={"text": f"<span style='font-size:150%'>Vendas de Hoje</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_12['taxa_total'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig12.add_trace(go.Indicator(
                    mode='number',
                    value=0,
                    number={'prefix': "R$"},
                    title={"text": f"<span>VENDAS DIÁRIAS</span>"}
                ))

            fig12.update_layout(main_config, height=300, template=template)

            df_10 = df_filtered
            fig10 = go.Figure()
            if not df_10.empty:
                fig10.add_trace(go.Indicator(mode='number',
                            title={"text": f"<span style='font-size:150%'>VALOR</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_10['valor'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig10.add_trace(go.Indicator(mode='number', value=0, number={'prefix': "R$"}, title={"text": f"<span>VALOR</span>"}))
            fig10.update_layout(main_config, height=300, template=template)

            df_13 = df_filtered
            fig13 = go.Figure()
            if not df_13.empty:
                fig13.add_trace(go.Indicator(mode='number',
                            title={"text": f"<span style='font-size:150%'>VALOR MENOS TAXA</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_13['VALOR_MENOS_TAXA'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig13.add_trace(go.Indicator(mode='number', value=0, number={'prefix': "R$"}, title={"text": f"<span>VALOR MENOS TAXA</span>"}))
            fig13.update_layout(main_config, height=300, template=template)


        except Exception as e:
            print(f"Erro ao obter dados do Firebird: {e}")
    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12, fig13

@app.callback(
    Output("radio-year", "options"),
    Output("radio-year", "value"),
    Output("radio-month", "options"),
    Output("radio-month", "value"),
    Output("radio-team", "options"),
    Output("radio-team", "value"),
    Input('interval-component', 'n_intervals'),
    Input('radio-year', 'value')
)
def update_radio_buttons(n_intervals, selected_year):
    with lock:
         try:
             ano_atual = datetime.datetime.now().year
             unique_years = sorted(df['ANO'].unique(), reverse=True)
             options_year = [{'label': i, 'value': i} for i in unique_years]

             selected_year = selected_year or ano_atual

             if selected_year is not None:
                 df_filtered = df[df['ANO'] == selected_year]
                 options_month = [{'label': convert_to_text(i), 'value': j} for i, j in zip(df_filtered['MES'].unique(), df_filtered['MES'].unique())]
                 options_month = sorted(options_month, key=lambda x: x['value'])

                 default_month = options_month[0]['value'] if options_month else None

             else:
                 options_month = []
                 default_month = None

             options_team = [{'label': 'Todas as Empresas', 'value': 0}]
             for i in df['Fantasia'].unique():
                    options_team.append({'label': i, 'value': i})

         except Exception as e:
             print(f"Erro ao obter dados do Firebird: {e}")

    return options_year, selected_year, options_month, default_month, options_team, 0


@app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [dash.dependencies.State('username', 'value'),
     dash.dependencies.State('password', 'value')]
)
def check_login(n_clicks, username, password):
    global authenticated
    
    if n_clicks:
        if username.lower() == 'admin' and password == 'admin':
            authenticated = True 
            return dcc.Location(pathname='/main_layout', id='main_layout_redirect')
        else:
            return html.Div('Credenciais inválidas. Tente novamente.', style={'color': 'red'})


@app.callback(
    Output('url', 'pathname'),
    [Input('main_layout_redirect', 'pathname')]
)
def update_url(pathname):
    if pathname is not None:
        return pathname

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    global authenticated 
    if pathname == '/main_layout' and authenticated:  
        return main_layout
    elif not authenticated:  
        return login_layout  
    else:
        return login_layout  

mode = "prod"

if __name__ == '__main__':
    if mode == "dev":
        app.run( host='0.0.0.0', port=8050, debug=True)
    else:
        serve(server, host='0.0.0.0', port=8050, threads=10)

