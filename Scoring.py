import sqlite3
game_db = sqlite3.connect('cricket.db')
game_cursor = game_db.cursor()

def getPoints(team):
    points = 0
    for g in team:
        for p in g:
            points += getVal(p[0])
    return points

def getVal(player):
    query = 'SELECT Value FROM Stats WHERE Player = ?'
    game_cursor.execute(query, (player,))
    val =  game_cursor.fetchone()
    return val[0]

def getTeamScore(match, team):
    q = 'SELECT Scored, Faced, Fours, Sixes, Bowled, Maiden, Given, Wkts, Catches, Stumping, RO FROM Match, Teams, '
    query = [ q + ' Batsmen WHERE Match.Player = Batsmen.Batsman AND Teams.Name = Batsmen.Name AND Match.MatchID = ? AND Teams.Name = ?',
             q + ' Bowlers WHERE Match.Player = Bowlers.Bowler AND Teams.Name = Bowlers.Name AND Match.MatchID = ? AND Teams.Name = ?',
             q + ' AllRounders WHERE Match.Player = AllRounders.AR AND Teams.Name = AllRounders.Name AND Match.MatchID = ? AND Teams.Name = ?',
             q + ' WicketKeeper WHERE Match.Player = WicketKeeper.WK AND Teams.Name = WicketKeeper.Name AND Match.MatchID = ? AND Teams.Name = ?']
    players = []
    for q in query:
        game_cursor.execute(q, (match, team))
        result = game_cursor.fetchall()
        for r in result:
            players.append(r)
    team_score = 0
    player_score = []
    for p in players:
        s = getPlayerScore(p)
        team_score += s
        player_score.append(s)
    player_score.insert(0,team_score)
    return player_score

def getPlayerScore(p):
    runs = p[0]
    faced = p[1]
    fours = p[2]
    sixes = p[3]
    bowled = p[4]
    maiden = p[5]
    given = p[6]
    wkts = p[7]
    catches = p[8]
    stumping = p[9]
    ro = p[10]
    score = runs/2 +fours + sixes * 2 + maiden * 4 + 10 * (wkts + catches + stumping + ro)
    if faced > 0:
        strike_rate = runs/faced * 100
    else:
        strike_rate = 0
    if bowled > 0:
        eco_rate = 6 * given/bowled
    else:
        eco_rate = 0
    if strike_rate > 100:
        score += 4
    elif strike_rate >= 80:
        score += 2
    if eco_rate < 2:
        score += 10
    elif eco_rate < 3.5:
        score += 7
    elif eco_rate < 4.5:
        score += 4
    if runs > 100:
        score += 10
    elif runs > 50:
        score += 5
    if wkts >= 5:
        score+=10
    elif wkts >= 3:
        score+=5

    return int(score)
    
