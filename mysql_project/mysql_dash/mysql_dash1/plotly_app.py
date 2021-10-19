import dash
import dash_core_components as dcc
import dash_html_components as html
import pymysql
import dash_table
import plotly.graph_objs as go
import datetime
import pandas as pd
from dash.dependencies import  Input,Output,State
from django_plotly_dash import DjangoDash

app = DjangoDash('dash_integration_id')


def data_fetcher(sql_query, *args):
    conn = pymysql.connect(
        host='faboom-replica.cj247vhbkgih.ap-south-1.rds.amazonaws.com',
        user='troops',
        password='W7xBxvf4EFP53v2yyrVuWAA',
        port=3306,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    cursor = conn.cursor()

    cursor.execute(sql_query, args)
    data = cursor.fetchall()

    df = pd.DataFrame(data)
    cursor.close()
    conn.close()

    return df

@app.callback(Output(component_id='table', component_property='figure'),
              [Input(component_id='my_date_pick', component_property='start_date'),
               Input(component_id='my_date_pick', component_property='end_date'),
               Input(component_id='names',component_property='value')])
def call_back(start_date,end_date,value):
    start = datetime.datetime.strptime(start_date[0:10], '%Y-%m-%d')
    end = datetime.datetime.strptime(end_date[0:10], '%Y-%m-%d')
    sql_query = """SELECT round(sum(real_amount+bonus_amount+winning_amount),0) AS total_wagering, 
        u.user_id AS user_id, u.order_id FROM user.vi_order AS u
        where date(u.date_added + interval 330 minute) >= %s and date(u.date_added + interval 330 minute) <= %s
        group by u.user_id"""
    data=data_fetcher(sql_query,start,end)

    query_rake = """SELECT u.user_id,sum(c.site_rake) as Rake FROM user.vi_user as u  inner join fantasy.vi_lineup_master as lm 
                 on lm.user_id=u.user_id inner join fantasy.vi_lineup_master_contest as lmc on lmc.lineup_master_id=lm.lineup_master_id 
                 inner join fantasy.vi_contest as c on c.contest_id=lmc.contest_id 
                 where date(c.season_scheduled_date + interval 330 minute)>=%s and date(c.season_scheduled_date + interval 330 minute)<=%s 
                 and c.status=3 
                 group by u.user_id"""
    data2=data_fetcher(query_rake,start,end)

    df_concat = pd.merge(data, data2, on='user_id', how='outer')
    df_conc=data.join(data2.set_index('user_id'), on='user_id')
    name_query="""SELECT distinct(d.user_name) as Name, d.user_id FROM user.vi_user as d 
    left join user.vi_order as ord on ord.user_id = d.user_id where ord.status=1"""
    name= data_fetcher(name_query)
    final_df= df_conc.join(name.set_index('user_id'), on='user_id')
    final_df=final_df[final_df['Name']==value]
    fig= {
        'data': [go.Table(
                header=dict(values=final_df.columns.values),
                cells=dict(values=[final_df[col] for col in final_df.columns.values]),
            )],
        "layout": {"title": "picked row", "hovermode": "closest"}
    }
    return fig

player_name_query = """ SELECT distinct(d.user_name) as Name, d.user_id FROM user.vi_user as d 
                    left join user.vi_order as ord on ord.user_id = d.user_id where ord.status=1 and 
                     ord.source IN (1,2,3,7,8,128,130,210,212,220,222)"""

player=data_fetcher(player_name_query)
features=player['Name']
option1=[]
for i in features:
    option1.append({'label':i, 'value':i})
app.layout = html.Div([
html.H1 ('Stock Ticker Dashboard'),
      html.Div([
            html.H3('select start and end date: '),
              dcc.DatePickerRange( id='my_date_pick',
                                   min_date_allowed= datetime.date(2019,3,19),
                                   max_date_allowed=datetime.datetime.now().strftime("%Y-%m-%d"),
                                   start_date=datetime.date(2019,1,1),
                                   end_date=datetime.date.today()),
          ], style={'display':'inline-block'}),
          html.Div([
        dcc.Dropdown(id='names',
                     options=option1,
                     value='columns')
    ]),
    dcc.Graph(
        id='table')])
if __name__ == '__main__':
    app.run_server(8052, debug=False)