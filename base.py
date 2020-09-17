from dateutil.parser import parse
import pandas as pd
import re
import datetime

class task:
    def __init__(self,id,task,dur,preds):
        '''initiator method
        Arguments:
        id: int, unique number for the task
        dur: float, number of days for the task
        preds: list of id's of predacessor tasks
        '''
        self.id = int(id)
        self.task = task
        self.duration = float(dur)
        numbers = re.findall('[0-9]{1,}',preds)
        if len(numbers) > 0:
            self.predecessors = [int(i) for i in numbers]
        else:
            self.predecessors = None

    def show(self):
        '''Method to display task properties'''
        tempframe = pd.Series()
        tempframe["id"] = self.id
        tempframe["Task"] = self.task
        tempframe['Duration'] = self.duration
        tempframe["Predecessors"] = self.predecessors
        return tempframe

class project:
    def __init__(self,startdate = None):
        if startdate == None:
            startdate = datetime.datetime.today()
        elif type(startdate) == str:
            self.startdate = parse(startdate)
        else:
            raise ValueError
        self.taskdir = {}
        self.linksdf = pd.DataFrame(columns = ['EarlyStart','EarlyFinish','LateStart','LateFinish'])
        
    def addTask(self,task_ob):
        self.taskdir[task_ob.id] = task_ob
        self.linksdf.loc[task_ob.id,'EarlyStart'] = self.startdate
        self.linksdf.loc[task_ob.id,'EarlyFinish'] = self.startdate

    def findstart(self):
        '''Method to find the root start task of the project tasks. Raises an exception 
        if there is more than one taks without predecessors
        '''
        zeropredlist = []
        for task in self.taskdir.values():
            if task.predecessors == None:
                zeropredlist.append(task.id)
        if len(zeropredlist) != 1:
            raise ValueError
        else:
            self.startid = zeropredlist[0]
   
    def showtask(self,id):
        '''Method to show task data for a given task'''
        self.taskdir[id].show()
     
    def readTaskTable(self,path):
        '''Reads a .csv file and creates the task objects from that file'''
        data = pd.read_csv(path)
        for i in range(data.shape[0]):
            taskseries = data.iloc[i,:]
            self.taskdir[taskseries['TaskID']] = task(taskseries['TaskID'],taskseries['Task'],taskseries['Duration'],taskseries['Predecessors'])
            self.linksdf.loc[taskseries['TaskID'],'EarlyStart'] = self.startdate
            self.linksdf.loc[taskseries['TaskID'],'EarlyFinish'] = self.startdate + datetime.timedelta(days = int(taskseries['Duration']))
    
    def showTaskTable(self):
        '''Method to show a table of the project's tasks'''
        mycolumns = ['TaskID','Task','Duration','Predecessors']
        outdf = pd.DataFrame(columns = mycolumns)
        for task in self.taskdir.values():
            columnlist = [task.id,task.task,task.duration,task.predecessors]
            tempdf = pd.DataFrame(index = mycolumns, data = columnlist).T
            outdf = pd.concat([outdf,tempdf],axis=0)
        return outdf
    
    def findChildren(self,taskID):
        '''Method to find the direct children of a given task'''
        children = []
        for onetask in self.taskdir.values():
            if onetask.id == taskID:
                continue
            elif onetask.predecessors is None:
                continue
            else:
                for i in onetask.predecessors:
                    if i == taskID:
                        children.append(onetask.id)
        return children
            
    def findParents(self,taskID):
        '''Method to find the direct parents of a given task'''
        
        return self.taskdir[taskID].predecessors

    def feedforward(self):
        self.taskdir[self.startid].esd = self.startdate
        self.taskdir[self.startid].efd = self.startdate + datetime.timedelta(days = self.taskdir[self.startid].duration)
        
    def forwardprop(self,taskID):
        '''Method to run the forward propagation of the Gantt chart to determine the project length'''
        #Get the children
        kids = self.findChildren(taskID)
        if len(kids) == 0: #If no children are found, then you are at completion. Kick out of the function.
            self.linksdf.loc[:,'LateFinish'] = self.linksdf.loc[taskID,'EarlyFinish']
            self.linksdf.loc[:,'LateStart'] = self.linksdf.loc[taskID,'EarlyStart']
            for parent in self.findParents(taskID):
                self.backwardprop(taskID)
        else:
            for child in kids:
               tempesd = self.linksdf.loc[taskID,'EarlyFinish']
               if tempesd > self.linksdf.loc[child,'EarlyStart']:
                   self.linksdf.loc[child,'EarlyStart'] = tempesd  #Shift the start date
                   self.linksdf.loc[child,'EarlyFinish'] = tempesd + datetime.timedelta(days = self.taskdir[child].duration)
               self.forwardprop(child)

    def backwardprop(self,taskID):
        '''Method to run the backwards propagation of the Gantt chart to determine the critical path'''

        #Get the parents
        parents = self.findParents(taskID)

        if parents is None: #If no parents are found, then the backward prop is complete, kick out of method.
            return None
        else:
            for parent in parents:
                templfd = self.linksdf.loc[taskID,'LateStart']
                if templfd <= self.linksdf.loc[parent,'LateFinish']:
                    self.linksdf.loc[parent,'LateFinish'] = templfd # Shift the finish date
                    self.linksdf.loc[parent,'LateStart'] = templfd - datetime.timedelta(days = self.taskdir[parent].duration)
                self.backwardprop(parent)

