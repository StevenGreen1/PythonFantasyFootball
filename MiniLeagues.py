import requests
import logging
import pandas as pd

def getMiniLeague(code = 1):
    keep_going = True
    index = 1
    entries = []
    names = []
    team = []

    # Loop over all page_standings table until next page does not exist
    while keep_going:
        url = "https://fantasy.premierleague.com/api/leagues-classic/{}/standings/?page_standings={}".format(code, index)
        index += 1
        r = requests.get(url).json()
        df_ = pd.json_normalize(r['standings']['results'])
        entries += df_.entry.to_list()
        names += df_.player_name.to_list()
        team += df_.entry_name.to_list()
        keep_going = r['standings']['has_next']

        if index % 25 == 0:
            logging.info('At page standings number {}'.format(index))
    return entries, names, team

def getBenchedPoints(player_id):
    url = "https://fantasy.premierleague.com/api/entry/{}/history/".format(player_id)
    df = pd.json_normalize(requests.get(url).json()['current'])
    return(df.points_on_bench.sum(), df.event_transfers_cost.sum(), df.event_transfers.sum())
