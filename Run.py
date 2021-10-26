import requests, json, sys, math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype

base_url = 'https://fantasy.premierleague.com/api/'

#=====================================
# element options for an individual players:
# history - previous weeks in this season
# history_past - previous seasons data

def get_player_history(player_id, elements = 'history'):
    '''get all gameweek info for a given player_id'''
    r = requests.get(base_url + 'element-summary/' + str(player_id) + '/').json()
    df = pd.json_normalize(r[elements])
    return df

#=====================================

def get_fixture_data():
    '''get all gameweek info for a given player_id'''
    r = requests.get(base_url + 'fixtures/').json()
    df = pd.json_normalize(r)
    return df

#=====================================
# element options for global data:
# teams = individual team data
# elements = all player data

def get_global_info(elements = 'teams'):
    '''get all team data'''
    r = requests.get(base_url + 'bootstrap-static/').json()
    df = pd.json_normalize(r[elements])
    return df

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

        for idx, element in elements_df.iterrows():
            name = element['second_name']
            scores = get_player_history(element['id'])['total_points'].to_list()
            gwk = get_player_history(element['id'])['round'].to_list()
            moving_avg = movingaverage(scores, 3)
            axs[row, col].plot(gwk[1:-1], moving_avg, '-', label = name)

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

def printDifficulties():
    all_fixtures_df = get_fixture_data()
    team_df = get_global_info('teams')
    id_to_name = team_df.set_index('id')['name'].to_dict()

    x = PrettyTable()
    names = ["Team", "Remaining Difficulty"]

    lookahead = [3, 5, 10]
    for number in lookahead:
        names.append("Difficulty Next {}".format(number))

    x.field_names = names

    for id, name in id_to_name.items():
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) | (all_fixtures_df.team_a == id)) & (all_fixtures_df.finished == False)]
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['difficulty'] = np.where(fixtures_df.is_home_team == True, fixtures_df.team_h_difficulty, fixtures_df.team_a_difficulty)
        fixtures_df.sort_values(by=['event'])
        row = [name, round(fixtures_df.difficulty.mean(), 2)]
        for number in lookahead:
            row.append(round(fixtures_df.head(number).difficulty.mean(), 2))
        x.add_row(row)
    print(x)

    with open('tpl_index.html', 'r') as file :
        filedata = file.read()

    filedata = filedata.replace('HTML_TABLE', x.get_html_string())

    with open('index.html', 'w') as file:
        file.write(filedata)
#    print(x.get_html_string())

#=====================================

def main():
    printDifficulties()
    displayTopPlayers()

#=====================================

if __name__ == "__main__":
    # execute only if run as a script
    main()
