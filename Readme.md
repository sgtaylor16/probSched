# Introduction

This packages is to facilitate analyzing projects stochastically rather than as a single point. Given a Gannt chart, a scipy.stats distribution can be assigned to a task's duration. The package can then assign tasks duration sampled from their respective random durations.

# Input File

A project is created by reading in a .csv file that has the following format:

|TaskID|   Task   |Duration|Predecessors|
|------|----------|--------|------------|
|  1   |   Start  |  0     |   []       |
|  2   |   Task 1 |  10    |   [1]      |
|  3   |   Task 2 |  20    |   [1]      |
|  4   |  Task 3  |  25    |   [2-3]    |
|  5   |  Task 4  |  15    |    [4]     |

The __TaskID__ column is a unique integer for a given task. It is not required that the taskID's be ordered in anyway. The __Task__ column is a title or description of the task. The task value does not need to be unique. The __Duration__ column is the duration of the task in a given time unit (usually days). The __Predecessors__ column sets what the predecessor tasks of the task are. The TaskID's of the predecessor task are enclosed in square brackets. If a task has more than one predecessor then enclose all of the predecessor ID's separated by dashes (or spaces). Don't use commas as that messes up the comma parsing when reading in the .csv file. 

There are two additional requirements. All tasks must be descendants of a single task of zero duration (Task 1 in the example above). Also, their must be a final task with zero duration that is a descendant of all tasks.

The text file is read in with the following code:

```python
from probSched import base
my_project = base.project("6/1/2020")  #The Datestring in the project argument sets the project start date.
my_project.readTaskTable("MyCSVfile.csv") #Argument is a string path to the .csv file.
```

# Adding Distributions

Reading in the .csv file puts only single point values for the durations of each task. Distributions can be given instead of single point values by assigning [scipy.stats](https://docs.scipy.org/doc/scipy/reference/stats.html) object to a task. The scipy.stats object is assigned to the project task with the .add_dist() method as follows:

```python
from scipy.stats import norm #Using a normal distribution from the scipy.stats package
my_distribution = norm(loc = 40, scale = 10) #This line creates a normal distribution with mean=40 and standard deviation=10. See scipy for more information on this object.
my_project.add_dist(2,my_distribution)  #adds the my_distribution object to TaskID 2
```

# The Project Class

The workhorse of the probSched package is the project class. Manipulating the attributes and invoking the methods of the project class are the main ways to ...

## summarytable()



