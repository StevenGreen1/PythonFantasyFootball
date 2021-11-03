import requests, json
import pandas as pd

def getMiniLeague(code = 529064):
    url = "https://fantasy.premierleague.com/api/leagues-classic/{}/standings/".format(code)
    r = requests.get(url).json()
    df = pd.json_normalize(r['standings']['results'])
    return df

def getBenchedPoints(player_id):
    url = "https://fantasy.premierleague.com/api/entry/{}/history/".format(player_id)
    r = requests.get(url).json()
    df = pd.json_normalize(r['current'])
    return(df.points_on_bench.sum())
