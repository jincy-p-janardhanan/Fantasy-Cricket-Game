import sqlite3
import sys
from GameWindow import *
from MessageDialog import *
from EvaluateDialog import *
from GetNameDialog import *
from Scoring import *

game_db = sqlite3.connect('cricket.db')
game_cursor = game_db.cursor()

class Game:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.MainWindow.showMaximized()
        try:
            self.new_selected = 0
            self.open_selected = 0
            self.exist_required= False
            self.team_name = ''
            self.team_details = None
            self.all_players = []
            self.team_players = []
            self.ui.msgDialog = QtWidgets.QDialog(self.MainWindow)
            self.ui.msgUi = Ui_MsgDialog()
            self.ui.evaluateDialog = QtWidgets.QDialog(self.MainWindow)
            self.ui.evaluateUi = Ui_Dialog()
            self.ui.getNameDialog = QtWidgets.QDialog(self.MainWindow)
            self.ui.getNameUi = Ui_GetNameDialog()
            self.ui.menu_Manage_Teams.triggered[QtWidgets.QAction].connect(self.manage)
            self.ui.BatRadio.toggled.connect(lambda: self.displayList(self.ui.AllPlayersList, self.all_players))
            self.ui.BwlRadio.toggled.connect(lambda: self.displayList(self.ui.AllPlayersList, self.all_players))
            self.ui.ArRadio.toggled.connect(lambda: self.displayList(self.ui.AllPlayersList, self.all_players))
            self.ui.WkRadio.toggled.connect(lambda: self.displayList(self.ui.AllPlayersList, self.all_players))
            self.ui.AllPlayersList.itemDoubleClicked.connect(self.addPlayers)
            self.ui.TeamPlayersList.itemDoubleClicked.connect(self.removePlayers)
        except Exception as e:
            self.exceptMsg(e, 'from method __init__')

        sys.exit(self.app.exec_())

    def manage(self,action):
        action_name = (action.text())
        if action_name == 'NEW Team':
            self.newTeam()
        elif action_name == 'OPEN Team':
            self.openTeam()
        elif action_name == 'SAVE Team':
            self.saveTeam()
        elif action_name == 'EVALUATE Team':
            self.evaluateTeam()

    def newTeam(self):
        self.disableWidgets()
        self.new_selected = 1
        self.exist_required = False
        self.getTeamName()
        
    def openTeam(self, team_name = None):
        self.disableWidgets()
        self.open_selected = 1
        self.exist_required = True
        if team_name == None:
            self.getTeamName()
        else:
            self.newOrOpenTeam(team_name)

    def saveTeam(self):
        try:
            value = self.ui.PointsUsedValueLbl.text()
            tables = ['Teams', 'Batsmen', 'Bowlers', 'AllRounders', 'WicketKeeper']
            team = [[[self.team_name, value]]]
            i = 0
            for g in self.team_players:
                group = []
                for p in g:
                    p = list(p)
                    p.insert(0, self.team_name)
                    group.append(p)
                    i+=1
                team.append(group)
            if i != 11:
                msg = """Uh..Oh! You might've forgot to add all the players for your team.
You need 11 players in your team to save it."""
                self.showMessage(msg)
                return
            if self.checkTeamExists(self.team_name):
                for t in tables:
                    query = "DELETE FROM "+ t +" WHERE Name = ? "
                    game_cursor.execute(query, (self.team_name,))
            i = 0
            for g in team:
                for p in g:
                    query = "INSERT INTO "+tables[i]+" VALUES (?,?)"
                    game_cursor.execute(query, (p[0], p[1]))
                    game_db.commit()
                i += 1
            self.openTeam(self.team_name)
        except Exception as e:
            self.exceptMsg(e, 'from method saveTeam')        

    def evaluateTeam(self):
        try:
            self.ui.evaluateUi.setupUi(self.ui.evaluateDialog)
            self.ui.evaluateUi.SelectCombo.activated.connect(self.getList)
            self.ui.evaluateUi.CalcScoreBtn.clicked.connect(self.getScores)
            self.getCombos()
            self.ui.evaluateDialog.show()
        except Exception as e:
            self.exceptMsg(e, 'from method evaluateTeam')
    
    def getTeamName(self):      #Opens the UI to enter team name
        self.ui.getNameUi.setupUi(self.ui.getNameDialog)
        self.ui.getNameUi.TeamNameLine.setFocus()
        self.ui.getNameUi.GetTeamNameButtons.accepted.connect(self.newOrOpenTeam)
        self.ui.getNameDialog.show()
        
    def disableWidgets(self):   #Disabeles required widgets
        self.ui.BatRadio.setEnabled(False)
        self.ui.BwlRadio.setEnabled(False)
        self.ui.ArRadio.setEnabled(False)
        self.ui.WkRadio.setEnabled(False)
        self.clearSelection()
        self.ui.PointsAvailValueLbl.setText('0')
        self.ui.PointsUsedValueLbl.setText('0')
        self.ui.TeamNameDisplayLbl.setText(' ')
        self.ui.AllPlayersList.setEnabled(False)
        self.ui.TeamPlayersList.setEnabled(False)

    def newOrOpenTeam(self, team_name = None):      #Performs appropriate action uponn recieving a team name
        try:
            if team_name == None:
                self.team_name = self.ui.getNameUi.TeamNameLine.text()
            else:
                self.team_name = team_name
            exists = self.checkTeamExists(self.team_name)
            if exists == self.exist_required:
                self.ui.TeamNameDisplayLbl.setText(self.team_name)
                self.enableWidgets()
                self.populateList(self.ui.AllPlayersList, self.all_players)
                if self.open_selected == 1:
                    self.populateList(self.ui.TeamPlayersList, self.team_name)
                    self.displayList(self.ui.TeamPlayersList, self.team_players)
                    self.getPlayerCounts(self.team_players)
                    self.getTeamPoints(self.team_players, self.ui.PointsUsedValueLbl)
                    self.ui.TeamPlayersList.setFocus()
                    for g in self.team_players:
                        for p in g:
                            self.updateLists(self.all_players,'', p[0])                           
                elif self.new_selected == 1:
                    self.new_selected = 0
                self.getTeamPoints(self.all_players, self.ui.PointsAvailValueLbl)
            else:
                if self.new_selected == 1:
                    msg = ("""Oh no! You've already created {} team.
    Create a new team or open {} team""".format(self.team_name,self.team_name))
                elif self.open_selected == 1:
                    msg = ("""Oh no! You might've forgot to create {} team.
    Enter a team you've already created or create a new team!!""".format(self.team_name))
                self.showMessage(msg)
        except Exception as e:
            self.exceptMsg(e, 'from method newOrOpenTeam')
        
    
    def checkTeamExists(self, team_name):       #Checks whether a team is already existing
        try:
            query = ['SELECT * FROM Teams WHERE Name = "'+team_name+'";']
            self.team_details = self.getQueryResult(query)
        except Exception as e:
            self.exceptMsg(e, 'from method checkTeamExists')
            return
        if self.team_details == [[]]:
            return False
        else:
            return True
        
    def enableWidgets(self):
        self.ui.BatRadio.setEnabled(True)
        self.ui.BwlRadio.setEnabled(True)
        self.ui.ArRadio.setEnabled(True)
        self.ui.WkRadio.setEnabled(True)
        self.ui.AllPlayersList.setEnabled(True)
        self.ui.TeamPlayersList.setEnabled(True)
        self.clearSelection()
        
    def showMessage(self, msg):         #Shows message from using message UI
        self.ui.msgUi.setupUi(self.ui.msgDialog)
        self.ui.msgUi.MessageLbl.setText(msg)
        self.ui.msgUi.OkButtonBox.setFocus()
        self.ui.msgDialog.show()

    def clearSelection(self):       #Clears selection of lists, radio buttons, teams, etc
        self.ui.RadioButtonGroup.setExclusive(False)
        self.ui.BatRadio.setChecked(False)
        self.ui.BwlRadio.setChecked(False)
        self.ui.ArRadio.setChecked(False)
        self.ui.WkRadio.setChecked(False)
        self.ui.RadioButtonGroup.setExclusive(True)
        self.ui.AllPlayersList.clear()
        self.ui.TeamPlayersList.clear()
        try:
            del self.all_players[0:10]
            del self.team_players[0:10]
        except:
            pass
        
    def exceptMsg(self, e, fn):
        msg = ("""We are sorry, something happened and we cannot create or open your team.
Please try again later or try changing the team name.
:(

Error: {} {}""".format(e, fn))
        self.showMessage(msg)        
        
    def populateList(self, list_name, team_name):
        try:
            if team_name == self.all_players:
                query = ['SELECT Player, CTG FROM Stats;']
            elif team_name == self.team_name:
                query = ['SELECT Batsman FROM Batsmen, Teams WHERE Teams.Name == Batsmen.Name AND Teams.Name = "'+team_name+'";',
                         'SELECT Bowler FROM Bowlers, Teams WHERE Teams.Name == Bowlers.Name AND Teams.Name = "'+team_name+'";',
                         'SELECT AR FROM AllRounders, Teams WHERE Teams.Name == AllRounders.Name AND Teams.Name = "'+team_name+'";',
                         'SELECT WK FROM WicketKeeper, Teams WHERE Teams.Name == WicketKeeper.Name AND Teams.Name = "'+team_name+'";']
                team_name = self.team_players
            result = self.getQueryResult(query)
            for r in result:
                team_name.append(r)
        except Exception as e:
            self.exceptMsg(e,'from method populateList')

    def getTeamPoints(self, team, lbl):
        try:
            points = getPoints(team)
            lbl.setText(str(points))
        except Exception as e:
            self.exceptMsg(e,'from method getPlayerStats')

    def getPlayerCounts(self, team):
        lbls = [self.ui.BatNoLbl, self.ui.BowNoLbl, self.ui.ArNoLbl, self.ui.WkNoLbl]
        i = 0
        for g in team:
            count = 0
            for p in g:
                count+=1
            lbls[i].setText(str(count))
            i+=1

    def displayList(self, list_name, team_name):
        try:
            list_name.clear()
            if list_name == self.ui.AllPlayersList:
                rb_group = [self.ui.BatRadio, self.ui.BwlRadio, self.ui.ArRadio, self.ui.WkRadio]
                checked_rb = None
                for rb in rb_group:
                    if rb.isChecked():
                        checked_rb = rb
                        break
                if checked_rb != None:
                    group = checked_rb.text()
                    if group == 'BOW':
                        group = 'BWL'
                    self.find(list_name, team_name, group)
            elif list_name == self.ui.TeamPlayersList:
                self.find(list_name, team_name)
        except Exception as e:
            self.exceptMsg(e,'from method displayList')             

    def find(self, list_name, team_name, group = ''):
        try:   
            for g in team_name:
                for p in g:
                    if group == '':
                        list_name.addItem(p[0])
                    elif group == p[1]:
                        if self.open_selected == 0:
                            list_name.addItem(p[0])
                        elif self.checkPlayerInTeam(p[0]) == 0:
                            list_name.addItem(p[0])
        except Exception as e:
            self.exceptMsg(e,'from method find')

    def getGroup(self, player):
        query = 'SELECT CTG FROM Stats Where Player = ?;'
        game_cursor.execute(query, (player,))
        group = []
        group.append(game_cursor.fetchone())
        if group[0][0] == 'BAT':
            group.append('batsmen')
            group.append(1)
        elif group[0][0] == 'BWL':
            group.append('bowlers')
            group.append(2)
        elif group[0][0] == 'AR':
            group.append('all- rounders')
            group.append(3)
        else:
            group.append('wicket keeper')
            group.append(4)
        return group

    def checkPlayerInTeam(self, player):
        for g in self.team_players:
            for p in g:
                if p[0] == player:
                    return 1
        return 0

    def addPlayers(self):
        try:
            if self.team_players == []:
                self.team_players = [ [], [], [], [] ]
            player = (self.ui.AllPlayersList.currentItem()).text()
            group = self.getGroup(player)
            group_count =  self.getGroupCount(group[0][0])
            if self.checkAddPermissible(group[0][0], group_count):
                no = 0
                for g in self.team_players:
                    no += 1
                    if no == group[2]:
                        g.append((player,))
                        break
                self.updateLists(self.all_players, self.ui.AllPlayersList)
                self.ui.TeamPlayersList.addItem(player)
            else:
                msg = """Oh no!
You can surely have more power in your team if your team has more members,
but you cannot add more than {} {}.""".format(group_count, group[1])
                self.showMessage(msg)
        except Exception as e:
            self.exceptMsg(e,'from method addPlayers')

    def removePlayers(self):
        try:
            player = (self.ui.TeamPlayersList.currentItem()).text()
            group = self.getGroup(player)
            p_details = (player, group[0][0])
            already_in_list = False
            for g in self.all_players:
                for p in g:
                    if p == p_details:
                        already_in_list = True
                        break
                if already_in_list == False:
                    g.append(p_details)
            self.updateLists(self.team_players, self.ui.TeamPlayersList)
        except Exception as e:
            self.exceptMsg(e,'from method removePlayers')

    def getGroupCount(self, group):
        if group == 'BAT':
            lbl = self.ui.BatNoLbl
        elif group == 'BWL':
            lbl = self.ui.BowNoLbl
        elif group == 'AR':
            lbl = self.ui.ArNoLbl
        else:
            lbl = self.ui.WkNoLbl
        return int(lbl.text())

    def checkAddPermissible(self, group, count):
        if (group == 'BAT' and count < 4) or ((group == 'BWL' or group == 'AR') and count < 3) or (group == 'WK' and count < 1):
            return True
        else:
            return False

    def updateLists(self, team, list_name = '', player = ''):
        if player == '':
            player = (list_name.currentItem()).text()
        for g in team:
            for p in g:
                if p[0] == player:
                    g.remove(p)
                    break
        if list_name != '':
            list_name.takeItem(list_name.currentRow())
        self.displayList(self.ui.AllPlayersList, self.all_players)
        self.getTeamPoints(self.all_players, self.ui.PointsAvailValueLbl)
        self.getTeamPoints(self.team_players, self.ui.PointsUsedValueLbl)
        self.getPlayerCounts(self.team_players)

    def getQueryResult(self, query):
        try:
            result=[]
            for q in query:
                game_cursor.execute(q)
                result.append(game_cursor.fetchall())
            return result
        except Exception as e:
            self.exceptMsg(e, 'from method getQueryResult')

##SETTINGS FOR EVALUATE DIALOG
            
    def getCombos(self):
        query = ['SELECT name FROM Teams', 'SELECT MatchID FROM AllMatches']
        result = self.getQueryResult(query)
        combo = [self.ui.evaluateUi.SelectCombo, self.ui.evaluateUi.MatchCombo]
        for c in combo:
            c.clear()
        i = 0
        for r in result:
            for item in r:
                combo[i].addItem(item[0])
            i+=1

    def getList(self):
        try:
            team_name = self.ui.evaluateUi.SelectCombo.currentText()
            list_name = self.ui.evaluateUi.PlayersList
            query = ['SELECT Batsman FROM Batsmen, Teams WHERE Teams.Name == Batsmen.Name AND Teams.Name = "'+team_name+'";',
                     'SELECT Bowler FROM Bowlers, Teams WHERE Teams.Name == Bowlers.Name AND Teams.Name = "'+team_name+'";',
                     'SELECT AR FROM AllRounders, Teams WHERE Teams.Name == AllRounders.Name AND Teams.Name = "'+team_name+'";',
                     'SELECT WK FROM WicketKeeper, Teams WHERE Teams.Name == WicketKeeper.Name AND Teams.Name = "'+team_name+'";']
            result  = self.getQueryResult(query)
            list_name.clear()
            for g in result:
                for p in g:
                    list_name.addItem(p[0])
        except Exception as e:
            self.exceptMsg(e, 'from method getList')

    def getScores(self):
        try:
            selected_match = self.ui.evaluateUi.MatchCombo.currentText()
            team_name = self.ui.evaluateUi.SelectCombo.currentText()
            list_name = self.ui.evaluateUi.ScoreList
            scores = getTeamScore(selected_match, team_name)
            list_name.clear()
            tot_score_text = ('Overall Score: {}'.format(scores[0]))
            self.ui.evaluateUi.ScoreLbl.setText(tot_score_text)
            scores.pop(0)
            for s in scores:
                list_name.addItem(str(s))
        except Exception as e:
            self.exceptMsg(e, 'from method getScores')
game1 = Game()
