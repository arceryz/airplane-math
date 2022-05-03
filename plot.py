# Written by Timothy van der Valk. Modelling B.

# Collection of plotting functions for all possible data sets used in the model.
# Call desired plot_* functions and finally call plot_show to show all the 
# selected plots at once.

import matplotlib.pyplot as plt
import numpy as np
from solver import Solution


def plot_sol_deviation(sol: Solution):
    # Plot bar chart with deviation from target arrival time for each aircraft.

    n = sol.data_set.num_aircraft
    xlist = np.arange(n)
    ylist = []
    for i in range(n):
        ylist.append(sol.arrival_times[i] - sol.data_set.target[i]) 
        pass

    plt.figure("Deviation chart")
    plt.title("Deviation from target times of %d aircraft" % sol.data_set.num_aircraft)
    plt.xlabel("Plane ID")
    plt.ylabel("Deviation from target")

    plt.axhline(y=0, c="gray")
    plt.axhline(int(sol.get_deviation()), c="red")
    plt.bar(xlist, ylist, width=0.5)


def plot_sol_events(sol: Solution):
    # Plots the given runway allocation problem by target time and given time.

    xlist = sol.arrival_times
    xlist2 = sol.data_set.target
    ylist = [ 0 ] * len(xlist)

    plt.figure("Event chart")
    plt.title("Arrival and target times of %d aircraft" % sol.data_set.num_aircraft)
    plt.xlabel("Desired (red) and actual (blue) arrival times")

    plt.axhline(y=0, c="gray")
    plt.plot(xlist2, ylist, "r|", ms=60, mew=2)
    plt.plot(xlist, ylist, 'bo', ms=7)
    
    # Hide Y axis.
    plt.gca().get_yaxis().set_visible(False)


def plot_sol_intervals(sol: Solution):
    # Plots the given arrival intervals for all aircraft with target and given
    # arrival times. This is the largest plot.

    target_xlist = []
    target_ylist = []
    given_xlist = []
    
    xlist=[]
    ylist=[]
    n = sol.data_set.num_aircraft
    for i in range(n):
        xlist.append(sol.data_set.earliest[i])     
        xlist.append(sol.data_set.latest[i])     
        xlist.append(None)

        yval = i
        ylist.append(yval)
        ylist.append(yval)
        ylist.append(None)

        target_xlist.append(sol.data_set.target[i])
        target_ylist.append(yval)
        given_xlist.append(sol.arrival_times[i])

    # Plot three different things. Intervals, target and given.
    plt.figure("Interval chart")
    plt.title("Arrival windows and arrival times of %d aircraft" % n)
    plt.ylabel("Plane ID")
    plt.xlabel("Timespan")

    plt.plot(xlist, ylist, 'gray')
    plt.plot(target_xlist, target_ylist, 'r^')
    plt.plot(given_xlist, target_ylist, 'go', ms=5)

    # Place ID on Y axis for all planes 0, 1, 2, 3 etc.
    plt.yticks(np.arange(0, n))


def plot_show():
    # Show plots to the screen.
    plt.show()
