import requests, json, argparse, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

def get_gameweek_history(player_id):
    '''get all gameweek info for a given player_id'''
    
    # send GET request to
    # https://fantasy.premierleague.com/api/element-summary/{PID}/
    r = requests.get(base_url + 'element-summary/' + str(player_id) + '/').json()
    
    # extract 'history' data from response into dataframe
    df = pd.json_normalize(r['history'])
    
    return df

#=====================================

def main():
    r = requests.get(url)
    json_obj = r.json()

    elements_df = pd.DataFrame(json_obj['elements'])

    #cols = ['id','second_name','team','element_type','selected_by_percent','now_cost','minutes','transfers_in','value_season','total_points','dreamteam_count','points_per_game','event_points']
    cols = ['id', 'second_name', 'team','selected_by_percent','now_cost','transfers_in','total_points','points_per_game']

    drop = []
    for col in elements_df.columns:
        if col not in cols:
            drop.append(col)

    elements_df = elements_df.drop(columns=drop)
    elements_df = elements_df.sort_values(by='total_points', ascending=False).head(3)

    for iter, row in elements_df.iterrows():
        name = row['second_name']
        scores = get_gameweek_history(row['id'])['total_points'].to_list()
        moving_avg = movingaverage(scores, 3)
        plt.plot(scores, label = name)
        plt.plot(moving_avg, label = name)
        print("{} -> Avg {}".format(scores, moving_avg))

    plt.legend(loc="upper left")
    plt.show()

#=====================================

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'valid')

#=====================================

if __name__ == "__main__":
    # execute only if run as a script
    main()
