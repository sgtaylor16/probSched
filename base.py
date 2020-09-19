from dateutil.parser import parse
import pandas as pd
import re
import datetime
from seaborn import distplot
from numpy import nan

class task:
    def __init__(self,id,task,dur,preds,scipy_object=None):
        '''initiator method
        Arguments:
        id: int, unique number for the task
        dur: float, number of days for the task
        preds: list of id's of predacessor tasks
        Issues:
        -predecessors must be given as a string, not a list.
        '''
        self.id = int(id)
        self.task = task
        self.duration = float(dur)
        self.dist = scipy_object
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

    def random_duration(self):
        '''Method to return a random value from the tasks duration distrubution (if a scipy.stats object has 
        been provided)'''
        if self.dist is None:
            return self.duration
        else:
            return self.dist.rvs(size = 1)[0]

    def set_scipy(self,scipy_object):
        '''Accessor method to set the dist attribute to a scipy.stats object'''
        self.dist = scipy_object

    def show_dist(self,size = 1000):
        '''Method to give a graphical depiction of the task duration distribution'''
        distplot(self.dist.rvs(size=size))
        
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
        self.taskdf = pd.DataFrame(columns = ['Task','Duration','Predecessors'])
        self.durations = None
        
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
            self.taskdf.loc[taskseries['TaskID'],:] = [taskseries['Task'],taskseries['Duration'],taskseries['Predecessors']]
            self.durations = self.taskdf['Duration'].copy()
        
        #Set the start variable
        self.findstart()

            #Clean this up
    
    def initialize_linksdf(self):
        self.linksdf = pd.DataFrame(columns = ['EarlyStart','EarlyFinish','LateStart','LateFinish'])
        
    def _reset_linksdf(self):
        for row in self.linksdf.index:
            self.linksdf.loc[row,'EarlyStart'] = self.startdate
            durdays = int(self.durations[row])
            self.linksdf.loc[row,'EarlyFinish'] = self.startdate + datetime.timedelta(days = durdays)
        self.linksdf['LateStart'] = float('NaN')
        self.linksdf['LateFinish'] = float('NaN')

    def findChildren(self,taskID):
        '''Method to find the direct children of a given task'''
        children = []
        for onetask in self.taskdir.values(): # You have found the task itself
            if onetask.id == taskID:
                continue
            elif onetask.predecessors is None: 
                continue
            else:
                for i in onetask.predecessors:
                    if i == taskID:
                        children.append(onetask.id)
        #If no children were found return a set with the string "EndofProject"
        if len(children) == 0:
            children.append("EndofProject")
        return children
            
    def findParents(self,taskID):
        '''Method to find the direct parents of a given task'''
        
        return self.taskdir[taskID].predecessors
        
    def forwardprop(self,taskID = None):
        '''Method to run the forward propagation of the Gantt chart to determine the project length'''
        #Get the children
        if taskID is None:
            taskID = self.startid

        kids = self.findChildren(taskID)
        if len(kids) == 0: #If no children are found, then you are at completion. Kick out of the function.
            self.linksdf.loc[:,'LateFinish'] = self.linksdf.loc[taskID,'EarlyFinish'] #Set the late start adn late finish 
            self.linksdf.loc[:,'LateStart'] = self.linksdf.loc[taskID,'EarlyStart']   # In anticipation of calling backprop
            for parent in self.findParents(taskID):
                self.backwardprop(taskID)
        else:
            for child in kids:
               tempesd = self.linksdf.loc[taskID,'EarlyFinish']
               if tempesd >= self.linksdf.loc[child,'EarlyStart']:
                   self.linksdf.loc[child,'EarlyStart'] = tempesd  #Shift the start date
                   durdays = int(self.durations[child])
                   self.linksdf.loc[child,'EarlyFinish'] = tempesd + datetime.timedelta(days =durdays)
                   self.forwardprop(child)
        
    def forwardprop2(self,taskID = None):
        '''Method to run the forward propagation of the Gantt chart to determine the project length'''
        if taskID is None:
            taskID = self.startid

        kids = self.findChildren(taskID)

        for child in kids:
            if child == "EndofProject":
                tempesd = self.linksdf.loc[taskID,'EarlyFinish']
                if tempesd > self.linksdf.loc[taskID,'EarlyStart']:
                    self.linksdf.loc[child,'EarlyStart'] = tempesd #Shft the start date
                    durdays = int(self.durations[child])
                    self.linksdf.loc[child,'EarlyFinish'] = tempesd + datetime.timedelta(days = durdays)
            else:
                tempesd = self.linksdf.loc[taskID,'EarlyFinish']
                if tempesd >= self.linksdf.loc[child,'EarlyStart']:
                    self.linksdf.loc[child,'EarlyStart'] = tempesd #Shift the start date
                    durdays = int(self.durations[child])
                    self.linksdf.loc[child,'EarlyFinish'] = tempesd + datetime.timedelta(days = durdays)
                    self.forwardprop2(child)

        return "Done"

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
                    durdays = int(self.durations[parent])
                    self.linksdf.loc[parent,'LateStart'] = templfd - datetime.timedelta(days = durdays)
                    self.backwardprop(parent)

    def add_dist(self,taskID,scipy_object):
        '''Accessor method to add a scipy.stats object to a task to run stochastic simulation'''
        self.taskdir[taskID].set_scipy(scipy_object)

    def sample(self):
        '''Method to simulate the project once with stochastic values for tasks'''
        for task in self.taskdir.values():
            self.durations[task.id] = task.random_duration()
            self.taskdf.loc[task.id,'Duration'] = self.durations[task.id]

    def summarytable(self):
        return pd.merge(self.taskdf,self.linksdf,left_index = True, right_index = True)


def simulate(project,nsamp = 10):
    '''Function to simulate a project to create a distribution
    Arguments:
    project, base.project class: project class to simulate
    nsamp, int: Number of simulations to run
    '''
    results = []
    for i in range(nsamp):
        project.sample()  #Populate the distributions attribute with random variables
        project._reset_linksdf()
        project.forwardprop2(project.startid) #Run the distributions
        results.append(project.summarytable())
    return results

class distResults:
    def __init__(self,resultsdf):
        self.resultsdf = resultsdf
    
    def duration(self):
        return self.resultsdf['EarlyFinish'].max() - self.resultsdf['EarlyStart'].min()
