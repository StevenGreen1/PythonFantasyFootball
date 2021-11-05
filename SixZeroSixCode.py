import logging

from prettytable import PrettyTable

from MiniLeagues import *

def examine606():
    logging.basicConfig(level=logging.INFO)

    entry_ids = []
    names = []
    teams = []

    if False:
        full_league_code = 1
        entry_ids, names, teams = getMiniLeague(full_league_code)
    else:
        entry_ids = [1, 2, 3]
        names = ["Redacted", "Redacted", "Redacted"]
        teams = ["Team1", "Team2", "Team3"]

    table = PrettyTable()
    table.field_names = ["Name", "Team", "Benched Points", "Cost of Transfers", "Transfers", "Entry Number"]

    for idx, name in enumerate(names):
        points, cost, transfers = getBenchedPoints(entry_ids[idx])
        table.add_row([name, teams[idx], points, cost, transfers, entry_ids[idx]])

    print(table)
 
