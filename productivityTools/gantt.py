# %%
""" # Creating a GANTT chart from a CSV file """

# %%
""" 
First, we define a function that helps me running this code in jupyter notebook as well as python. 
Taken from https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
"""

# %%

def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


# %%
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from dateutil.relativedelta import relativedelta
import argparse
import pandas as pd
from pathlib import Path

homedir=str(Path.home())

# %%
def read_tasks_from_csv(file_path):
    """     
    function that parses the CSV file containing the info. An example of a file can be found
    in the same folder: tasks.csv
    """
    df = pd.read_csv(file_path)
    df.drop(df[df['delete'] == '#'].index, inplace=True)            # remove rows that have been explicitly deleted with
                                                                    # the sign # in the CSV
    for i, row in df.iterrows():
        df.at[i,'start'] = datetime.strptime(row['start'], '%Y-%m-%d')
        df.at[i,'end'] = datetime.strptime(row['end'], '%Y-%m-%d')
        df.at[i,'people_responsible'] = row['people_responsible'].split(',')
        df.at[i,'is_milestone'] = bool(int(row['is_milestone']))
    return df

def create_gantt_chart(tasks,months):
    """
    function that makes use of horizontal bar charts from matplotlib to build the GANTT
    The result can be exported as a pop up plot or saved as a figure.
    In this example, the figure is saved in PNG format in the wallpapers folder in Pictures, in order 
    to be used as background in your computer
    """
    # general setup for the plot
    plt.rcParams['figure.constrained_layout.use'] = True
    plt.rcParams['figure.figsize'] = 16, 9
    plt.rcParams["axes.edgecolor"] = "black"
    plt.rcParams["axes.linewidth"] = 1
    #plt.rcParams["figure.facecolor"] = "yellow"
    #plt.rcParams["axes.facecolor"] = "blue"

    fig, ax = plt.subplots() 
    xfmt = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(xfmt)
    ax.yaxis.tick_right()
    ax.set_xticks(tasks['end'])
  
    current_date = datetime.now().date()
    max_end = current_date+relativedelta(months=months)

    # Set the labels and ticks for y-axis
    labels = tasks['name']
    ax.set_yticks(range(5, len(labels) * 10 + 5, 10))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(current_date, max_end)
    ax.set_xlabel('End date')
    ax.set_title('Projects Schedule')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.xticks(rotation=90)
    ax.grid(True)

    # Plot the bars for each task and milestone
    for i, task in tasks.iterrows():
    
        edgecolor = 'black'
        if task['type'] == 'CALL':
            color = 'red'
        elif task['type'] == 'TEACH':
            color = 'blue'
        elif task['type'] == 'IRIS-CC':
            color = 'brown'
        elif task['type'] == 'RESEARCH':
            color = 'green'
        else:
            color = 'brown'

        start = task['start'].date()
        if task['start'].date() < current_date and task['end'].date() > current_date:
            # Tasca ja començada
            start = current_date
        elif task['is_milestone']:
            print('found milestone for task:',task)
            color = 'black'
        
        # some warnings
        if task['end'].date() == current_date + relativedelta(days=1):
            print ('WARNING: task ',task,' ends TOMORROW!!')
        elif task['end'].date() == current_date:
            print ('WARNING: task ',task,' ends TODAY!!')

        duration = task['end'].date() - start

        # plot each horizontal bar and the label       
        ax.barh(i * 10 + 5, duration, left=start, height=8, align='center', edgecolor=edgecolor, color=color, alpha=0.8)
        people = ', '.join(task['people_responsible'])
        ax.text(start, i * 10 + 5, people, ha='right', va='center')

    fig.savefig(homedir+'/Pictures/Wallpapers/gantt.png') # convenient to have it as wallpaper
    #plt.show()

# %%
"""  parse arguments """

# %%
parser = argparse.ArgumentParser(description='Generate Gantt chart from CSV file') # Crear un objecte ArgumentParser
parser.add_argument('-c','--csvfile', type=str, help='Path to the CSV file. Default is tasks.csv',default="tasks.csv") # Afegir l'argument per al camí del fitxer CSV
parser.add_argument('-m','--months', type=int, help='Number of months to visualize',default=2) # Afegir l'argument per al camí del fitxer CSV

if is_notebook():
    args = parser.parse_args(args=[]) 
else:
    args = parser.parse_args() 
csv_file_path = args.csvfile 
months = args.months

# %%
""" read the file and build the gantt """

# %%
tasks = read_tasks_from_csv(csv_file_path)
if is_notebook():
    print(tasks)
create_gantt_chart(tasks,months)
