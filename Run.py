import math
import sys
import logging

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable

from MiniLeagues import *
from SixZeroSixCode import *

BASE_URL = 'https://fantasy.premierleague.com/api/'
RECENT_MATCHES = 5
MIN_RECOMMENDATION_MINUTES = 270

#=====================================
# element options for an individual players:
# history - previous weeks in this season
# history_past - previous seasons data

def get_player_history(player_id, elements = 'history'):
    '''get all gameweek info for a given player_id'''
    req_json = requests.get(BASE_URL + 'element-summary/' + str(player_id) + '/').json()
    return pd.json_normalize(req_json[elements])

#=====================================

def get_fixture_data():
    '''get all gameweek info for a given player_id'''
    req_json = requests.get(BASE_URL + 'fixtures/').json()
    return pd.json_normalize(req_json)

#=====================================
# element options for global data:
# teams = individual team data
# elements = all player data

def get_global_info(elements = 'teams'):
    '''get all team data'''
    req_json = requests.get(BASE_URL + 'bootstrap-static/').json()
    return pd.json_normalize(req_json[elements])

#=====================================

def displayTopPlayers():
    full_elements_df = get_global_info('elements')
    full_elements_df = full_elements_df.astype({"form": float, "total_points": int})
    fig, axs = plt.subplots(2,2)
    fig.suptitle('Player Form')

    # element_type: 0 = GKP, 1 = DEF, 2 = MID, 3 = FWD
    for idx, element_type in enumerate(range(1,5)):
        row = idx % 2
        col = math.floor(idx/2)
        elements_df = full_elements_df[full_elements_df.element_type == element_type]
        elements_df = elements_df.sort_values(by='form', ascending=False).head(3)

        for unused_idx, element in elements_df.iterrows():
            name = element['second_name']
            scores = get_player_history(element['id'])['total_points'].to_list()
            gwk = get_player_history(element['id'])['round'].to_list()
            moving_avg = movingaverage(scores, min(3, len(scores)))
#            print(scores)
#            print(moving_avg)
#            print(gwk)
            x = []
            if len(scores) < 3:
                x = gwk[-1]
            else:
                x = gwk[1:-1]
            axs[row, col].plot(x, moving_avg, 'o-', label = name)

        axs[row, col].legend(loc="upper left")
        axs[row, col].set_xlabel('Gameweek')
        axs[row, col].set_ylabel('Running Ava. Points')
    plt.tight_layout()
    plt.savefig('Plot.png')

#=====================================

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'valid')

#=====================================

def printTeamForm():
    all_fixtures_df = get_fixture_data()
    all_fixtures_df = all_fixtures_df[all_fixtures_df.finished == True]
    all_fixtures_df = all_fixtures_df.astype({"team_h_score": int, "team_a_score": int})

    team_df = get_global_info('teams')
    id_to_name = team_df.set_index('id')['name'].to_dict()

    x = PrettyTable()
    names = ["Team", "Points Per Game [5]", "Goals Per Game [5]",
             "Goals Conceded Per Game [5]", "Goal Difference Per Game [5]",
             "Clean Sheet Rate [5]", "Scored In Rate [5]",
             "Points Per Game Overall"]
    x.field_names = names

    for id, name in id_to_name.items():
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) |
            (all_fixtures_df.team_a == id))].copy()
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['team_goals'] = np.where(fixtures_df.is_home_team == True,
                fixtures_df.team_h_score , fixtures_df.team_a_score)
        fixtures_df['opp_goals'] = np.where(fixtures_df.is_home_team == False,
                fixtures_df.team_h_score , fixtures_df.team_a_score)
        fixtures_df['clean_sheets'] = np.where(fixtures_df.opp_goals == 0, 1, 0)
        fixtures_df['did_team_score'] = np.where(fixtures_df.team_goals > 0, 1, 0)
        fixtures_df['points'] = np.where(fixtures_df.team_goals > fixtures_df.opp_goals, 3, np.where(fixtures_df.team_goals == fixtures_df.opp_goals, 1, 0))
        fixtures_df = fixtures_df.sort_values(by=['event'])
        recent_fixtures = fixtures_df.tail(RECENT_MATCHES)

        row = [name, round(recent_fixtures.points.mean(), 2),
               round(recent_fixtures.team_goals.mean(), 2),
               round(recent_fixtures.opp_goals.mean(), 2),
               round((recent_fixtures.team_goals - recent_fixtures.opp_goals).mean(), 2),
               round(recent_fixtures.clean_sheets.mean() * 100, 1),
               round(recent_fixtures.did_team_score.mean() * 100, 1),
               round(fixtures_df.points.mean(), 2)]
        x.add_row(row)

    with open('index.html', 'r') as file :
        filedata = file.read()

    filedata = filedata.replace('HTML_TEAMTABLE', x.get_html_string(sortby='Goals Per Game [5]', reversesort=True))
    filedata = filedata.replace('<table>', '<table class="styled-table">')

    with open('index.html', 'w') as file:
        file.write(filedata)

#=====================================

def printDifficulties():
    all_fixtures_df = get_fixture_data()
    team_df = get_global_info('teams')
    id_to_name = team_df.set_index('id')['name'].to_dict()

    x = PrettyTable()
    names = ["Team"]

    lookahead = [3, 5, 10]
    for number in lookahead:
        names.append("Difficulty Next {}".format(number))
    names.append("Remaining Difficulty")

    x.field_names = names

    for id, name in id_to_name.items():
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) | 
            (all_fixtures_df.team_a == id)) & (all_fixtures_df.finished == False)]
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['difficulty'] = np.where(fixtures_df.is_home_team == True,
                fixtures_df.team_h_difficulty, fixtures_df.team_a_difficulty)
        fixtures_df.sort_values(by=['event'])
        row = [name]
        for number in lookahead:
            row.append(round(fixtures_df.head(number).difficulty.mean(), 2))
        row.append(round(fixtures_df.difficulty.mean(), 2))
        x.add_row(row)

    with open('tpl_index.html', 'r') as file :
        filedata = file.read()

    filedata = filedata.replace('HTML_TABLE', x.get_html_string())
    filedata = filedata.replace('<table>', '<table class="styled-table">')

    with open('index.html', 'w') as file:
        file.write(filedata)
#    print(x.get_html_string())

#=====================================

def printPlayerMetrics():
    '''Create a shortlist using form, value, underlying attacking data and minutes.'''
    players_df = get_global_info('elements').copy()
    teams_df = get_global_info('teams')
    team_names = teams_df.set_index('id')['name'].to_dict()
    positions = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}

    numeric_columns = ['form', 'total_points', 'now_cost', 'minutes', 'starts',
                       'expected_goals', 'expected_assists']
    for column in numeric_columns:
        players_df[column] = pd.to_numeric(players_df[column], errors='coerce').fillna(0)

    players_df['team_name'] = players_df['team'].map(team_names)
    players_df['position'] = players_df['element_type'].map(positions)
    players_df['price'] = players_df['now_cost'] / 10
    players_df['points_per_million'] = np.where(
        players_df['price'] > 0, players_df['total_points'] / players_df['price'], 0)
    players_df['xgi_per_90'] = np.where(
        players_df['minutes'] > 0,
        (players_df['expected_goals'] + players_df['expected_assists']) * 90 / players_df['minutes'],
        0)
    players_df['minutes_per_start'] = np.where(
        players_df['starts'] > 0, players_df['minutes'] / players_df['starts'], 0)

    # A three-match minutes threshold avoids recommending one-match outliers.
    shortlist = players_df[players_df['minutes'] >= MIN_RECOMMENDATION_MINUTES]
    shortlist = shortlist.sort_values(
        ['element_type', 'form', 'xgi_per_90', 'points_per_million'],
        ascending=[True, False, False, False]).groupby('element_type', group_keys=False).head(5)

    table = PrettyTable()
    table.field_names = ['Player', 'Pos', 'Team', 'Price', 'Form', 'Points',
                         'Pts / £m', 'xGI / 90', 'Starts', 'Mins / Start']
    for _, player in shortlist.iterrows():
        table.add_row([
            player['web_name'], player['position'], player['team_name'],
            '£{:.1f}'.format(player['price']), round(player['form'], 1),
            int(player['total_points']), round(player['points_per_million'], 1),
            round(player['xgi_per_90'], 2), int(player['starts']),
            round(player['minutes_per_start'], 1)])

    with open('index.html', 'r') as file:
        filedata = file.read()

    filedata = filedata.replace('HTML_PLAYERTABLE', table.get_html_string())
    filedata = filedata.replace('<table>', '<table class="styled-table">')

    with open('index.html', 'w') as file:
        file.write(filedata)

#=====================================

def showBenchedPoints(mini_league_code):
    mini_league_list, names, teams = getMiniLeague(mini_league_code)

    table = PrettyTable()
    table.field_names = ["Name", "Team", "Benched Points", "Cost of Transfers", "Transfers", "Entry Number"]

    for idx, row in enumerate(mini_league_list):
        if idx % 100 == 0:
            logging.info('Processing player count {}'.format(idx))
        points, cost, transfers = getBenchedPoints(row)
        table.add_row(["Dummy", teams[idx], points, cost, transfers, row])

    print(table.get_string(sortby="Benched Points", reversesort=True))

#=====================================

def main():
    logging.basicConfig(level=logging.INFO)

#    mini_league_code = 1
#    examine606()
#    showBenchedPoints(mini_league_code)
    printDifficulties()
    displayTopPlayers()
    printPlayerMetrics()
    printTeamForm()

#=====================================

if __name__ == "__main__":
    # execute only if run as a script
    main()
