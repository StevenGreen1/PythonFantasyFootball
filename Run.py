import requests, json, argparse, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable

parser = argparse.ArgumentParser()
parser.add_argument('-f','--file', help='File to save data to or to load', default='data.json', required=False)
parser.add_argument('-r','--refresh', help='Get data from api', action='store_true')

args = parser.parse_args()

url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

base_url = 'https://fantasy.premierleague.com/api/'

#=====================================

def get_season_history(player_id):
    '''get all past season info for a given player_id'''
    
    # send GET request to
    # https://fantasy.premierleague.com/api/element-summary/{PID}/
    r = requests.get(base_url + 'element-summary/' + str(player_id) + '/').json()
    
    # extract 'history_past' data from response into dataframe
    df = pd.json_normalize(r['history_past'])
    
    return df

#=====================================

def get_gameweek_history(player_id, elements = 'history'):
    '''get all gameweek info for a given player_id'''
    
    # send GET request to
    # https://fantasy.premierleague.com/api/element-summary/{PID}/
    r = requests.get(base_url + 'element-summary/' + str(player_id) + '/').json()

    # extract 'history' data from response into dataframe
    df = pd.json_normalize(r[elements])
    
    return df

#=====================================

def get_fixture_data():
    '''get all gameweek info for a given player_id'''

    # send GET request to
    # https://fantasy.premierleague.com/api/element-summary/{PID}/
    r = requests.get(base_url + 'fixtures/').json()

    df = pd.json_normalize(r)

    return df

#=====================================

def get_team_info():
    r = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    df = pd.json_normalize(r['teams'])
    return df

#=====================================

def main():
    r = requests.get(url)
    json_obj = r.json()

    elements_df = pd.DataFrame(json_obj['elements'])
    elements_df = elements_df.sort_values(by='total_points', ascending=False).head(10)

    printDifficulties()

    for iter, row in elements_df.iterrows():
        name = row['second_name']
        scores = get_gameweek_history(row['id'])['total_points'].to_list()
        gwk = get_gameweek_history(row['id'])['round'].to_list()
        moving_avg = movingaverage(scores, 3)
#        plt.plot(gwk, scores, label = name)
        plt.plot(gwk[1:-1], moving_avg, '--', label = name)
#        print("{} -> Avg {}".format(scores, moving_avg))

    plt.legend(loc="upper left")
    plt.title('Running Average Player Form')
    plt.xlabel('Gameweek')
    plt.ylabel('Running Average Points Scores')
    plt.show()

#=====================================

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'valid')

#=====================================

def printDifficulties():
    all_fixtures_df = get_fixture_data()
    team_df = get_team_info()
    id_to_name = team_df.set_index('id')['name'].to_dict()
 
    x = PrettyTable()
    x.field_names = ["Team", "Difficult", "Difficult 5", "Difficulty 10"]
 
    for id in id_to_name.keys():
        name = id_to_name[id]
        fixtures_df = all_fixtures_df[((all_fixtures_df.team_h == id) | (all_fixtures_df.team_a == id)) & (all_fixtures_df.finished == False)]
        fixtures_df['is_home_team'] = np.where(fixtures_df.team_h == id, True, False)
        fixtures_df['difficulty'] = np.where(fixtures_df.is_home_team == True, fixtures_df.team_h_difficulty, fixtures_df.team_a_difficulty)
        fixtures_df.sort_values(by=['event'])
 
        x.add_row([name, fixtures_df.difficulty.mean(), fixtures_df.head(5).difficulty.mean(), fixtures_df.head(10).difficulty.mean()])
    print(x)

#=====================================

if __name__ == "__main__":
    # execute only if run as a script
    main()
