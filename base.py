from dateutil.parser import parse
import pandas as pd
import re
import datetime
from seaborn import distplot
from numpy import nan
from matplotlib import pyplot as plt
from matplotlib.dates import date2num

class task:
    '''The task class represents all data for a given task. It does not contain any information
    regarding a task's relationship to other tasks (e.g. Predecessors, start dates, etc)
    '''
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

    def distplot(self,figsize = (12,6)):
        '''Method to give a graphical depiction of the task duration distribution'''
        #Find the 
        ycdf = [0]
        xvalues =[0]
        xstep = 0.5
        while ycdf[-1] < .99:
            xvalues.append(xvalues[-1] + xstep)
            ycdf.append(self.dist.cdf(xvalues[-1]))
        ypdf = [self.dist.pdf(xval) for xval in xvalues]

        fig,ax = plt.subplots(1,2,figsize = figsize)
        ax[0].fill_between(xvalues,ypdf,alpha = 0.7)
        ax[0].grid()
        ax[1].fill_between(xvalues,ycdf,alpha = 0.7)
        ax[1].grid()

    def mean_duration(self):
        '''Method to return the mean of the task duration (if a scipy.stats object has been provided)'''
        if self.dist is None:
            return self.duration
        else:
            return self.dist.mean()

class project:
    def __init__(self,startdate = None):
        if startdate == None:
            self.startdate = pd.Timestamp(datetime.datetime.today())
        elif type(startdate) == str:
            self.startdate = pd.Timestamp(parse(startdate))
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
        if there is more than one tasks without predecessors
        '''
        zeropredlist = []
        for task in self.taskdir.values():
            if task.predecessors == None:
                zeropredlist.append(task.id)
        if len(zeropredlist) != 1:
            raise ValueError
        else:
            self.startid = zeropredlist[0]
   
    def findend(self):
        '''Method to find the end task of the project tasks.
        Needs an exception raised if it doesn't find end.'''
        for task in self.taskdir.values():
            test = self.children[task.id]
            if "EndofProject" in test:
                self.endid = task.id
            
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
        #Create the children map
        self.children = self.familytree()
        #Set the end variable
        self.findend()

    def readdf(self,df):
        '''Reads a Dataframe'''
        for i in range(df.shape[0]):
            taskseries = df.iloc[i,:]
            self.taskdir[taskseries['TaskID']] = task(taskseries['TaskID'],taskseries['Task'],taskseries['Duration'],taskseries['Predecessors'])
            self.linksdf.loc[taskseries['TaskID'],'EarlyStart'] = self.startdate
            self.linksdf.loc[taskseries['TaskID'],'EarlyFinish'] = self.startdate + datetime.timedelta(days = int(taskseries['Duration']))
            self.taskdf.loc[taskseries['TaskID'],:] = [taskseries['Task'],taskseries['Duration'],taskseries['Predecessors']]
            self.durations = self.taskdf['Duration'].copy()

        #Set the start variable
        self.findstart()
        #Create the children map
        self.children = self.familytree()
        #Set the end variable
        self.findend()
        
    def _reset_linksdf(self):
        '''Internal Method used to reset the taskdf after running as simulation, before running forwardprop.'''
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

    def familytree(self):
        family_dir = {}
        for onetask in self.taskdir.values():
            family_dir[onetask.id] = self.findChildren(onetask.id)
        return family_dir
            
    def findParents(self,taskID):
        '''Method to find the direct parents of a given task'''
        
        return self.taskdir[taskID].predecessors
        
           
    def forwardprop2(self,taskID = None,backprop = True):
        '''Method to run the forward propagation of the Gantt chart to determine the project length
        Arguments:
        taskID, integer: taskID to start forwardprop at, defaults to projects .startid attribute if None
        backprop, boolean: Do not run backprop if critical path is not needed.
        '''
        if taskID is None:
            taskID = self.startid

        #Reset the linksdf 
        self._reset_linksdf()
        
        kids = self.children[taskID]

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
                    self.forwardprop2(child,backprop)
        
        #Gives the option to exit the method before backprop for speed if critical path is not needed.
        if backprop == True:
            self.start_backwardprop()
        else:
            return None

    def start_backwardprop(self):
        '''Method to kick off the backward propagation from the end task'''
        self.linksdf.loc[:,'LateFinish'] = self.linksdf.loc[self.endid,'EarlyFinish'] #Set the late start and late finish 
        self.linksdf.loc[:,'LateStart'] = self.linksdf.loc[self.endid,'EarlyStart']   # In anticipation of calling backprop
        self.backwardprop(self.endid)
        return None

    def backwardprop(self,taskID):
        '''Method to run the backwards propagation of the Gantt chart to determine the critical path'''

        #Get the parents
        parents = self.findParents(taskID)
        #templfd = self.linksdf.loc[taskID,'LateStart']
        if parents is None: #If no parents are found, then the backward prop is complete, kick out of method.
            return None
        else:
            for parent in parents:
                templsd = self.linksdf.loc[taskID,'LateStart']
                if templsd <= self.linksdf.loc[parent,'LateFinish']:
                    self.linksdf.loc[parent,'LateFinish'] = templsd # Shift the finish date
                    durdays = int(self.durations[parent])
                    self.linksdf.loc[parent,'LateStart'] = templsd - datetime.timedelta(days = durdays)
                    self.backwardprop(parent)

    def add_dist(self,taskID,scipy_object):
        '''Accessor method to add a scipy.stats object to a task to run stochastic simulation'''
        self.taskdir[taskID].set_scipy(scipy_object)

    def sample(self):
        '''Method to simulate the project once with stochastic values for tasks'''
        for task in self.taskdir.values():
            self.durations[task.id] = task.random_duration()
            self.taskdf.loc[task.id,'Duration'] = self.durations[task.id]

    def mean(self,backprop = True):
        '''Method to give the mean of the tasks'''
        for task in self.taskdir.values():
            self.durations[task.id] = task.mean_duration()
            self.taskdf.loc[task.id,'Duration'] = task.mean_duration()
        
    def summarytable(self):
        return pd.merge(self.taskdf,self.linksdf,left_index = True, right_index = True)

    def distplot(self,taskID,figsize = None):
        self.taskdir[taskID].distplot(figsize)

    def Gantt(self,fontsize = 16):

        fig,ax = plt.subplots(figsize = (20,10))

        for i,task in enumerate(self.taskdir.values()):
            y = i*10
            x = self.linksdf.loc[task.id,'EarlyStart']
            start = date2num(self.linksdf.loc[task.id,'EarlyStart'])
            finish = date2num(self.linksdf.loc[task.id,'EarlyFinish'])
            ax.barh(y,width = (finish - start),height = 8,left = start, color = 'blue')
            ax.text(finish,y,task.task,ha = 'right',color = 'black',fontsize = 16)
            
        ax.set_xlim([date2num(self.linksdf['EarlyStart'].min()),date2num(self.linksdf['EarlyFinish'].max())])
        ax.xaxis_date()

        ax.set_ylim([0,10 * len(self.taskdir)+10])
        ax.invert_yaxis()
        ax.yaxis.set_ticks([])

    def critical_path(self):
        '''Finds the critical path'''
        cplist= [self.startid]
        return self.critical_path_recursive(self.startid,cplist)

    def critical_path_recursive(self,taskID,cplist):
        '''Internal method called by critical path'''
        tempdf = self.linksdf
        indexlist = tempdf.index
        #Remove any tasks that start *before* taskid
        temp = tempdf.loc[taskID,"LateFinish"]
        temp2df = tempdf.query("LateStart >= @temp")
        for i in temp2df.index:
            if i == taskID:
                continue
            elif tempdf.loc[i,"LateStart"] == tempdf.loc[i,"LateFinish"]:
                #Found the end of the project
                return cplist
            elif tempdf.loc[i,"LateStart"] == tempdf.loc[taskID,"LateFinish"]:
                cplist.append(i)
                cplist = self.critical_path_recursive(i,cplist)
            else:
                continue
        return None
        
def simulate(project,nsamp = 10,backprop = True):
    '''Function to simulate a project to create a distribution
    Arguments:
    project, base.project class: project class to simulate
    nsamp, int: Number of simulations to run
    backprop, boolean: True, runs backprop, False does not run backpop
    '''
    results = []
    for i in range(nsamp):
        project.sample()  #Populate the distributions attribute with random variables
        project._reset_linksdf()
        project.forwardprop2(project.startid, backprop) #Run the distributions
        results.append(distResults(project.summarytable()))  #Create a list of distResults class
    return results


class distResults:
    def __init__(self,resultsdf):
        self.resultsdf = resultsdf
    
    def duration(self):
        return self.resultsdf['EarlyFinish'].max() - self.resultsdf['EarlyStart'].min()

    def finish_date(self,taskID):
        '''Method to return finish date of a task in the project'''
        return self.resultsdf.loc[taskID,'EarlyFinish'].date()

    def endtask(self):
        '''Method to identify endtask.'''
        tempdf = self.resultsdf
        return tempdf.query("Duration == 0")['EarlyFinish'].sort_values().index[-1]

    def starttask(self):
        '''Method to identify the starttask'''
        tempdf = self.resultsdf
        return tempdf.query("Duration == 0")['EarlyStart'].sort_values().index[0]

    def critical_path(self):
        '''Finds the critical path'''

        #Find the startdate
        taskID = self.starttask()
        cplist = [taskID]
        return self.critical_path_recursive(taskID,cplist)
    
    def critical_path_recursive(self,taskID,cplist):
        '''Internal method called by critical path'''
        
        tempdf = self.resultsdf
        indexlist = tempdf.index
        #Remove any tasks that start *before* taskid
        temp = tempdf.loc[taskID,"LateFinish"]
        temp2df = tempdf.query("LateStart >= @temp")
        for i in temp2df.index:
            if i == taskID:
                continue
            elif tempdf.loc[i,"LateStart"] == tempdf.loc[i,"LateFinish"]:
                return cplist
            elif tempdf.loc[i,"LateStart"] == tempdf.loc[taskID,"LateFinish"]:
                cplist.append(i)
                cplist  = self.critical_path_recursive(i,cplist)
            else:
                continue
        return None
