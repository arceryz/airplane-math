from pulp import *
from data_set import DataSet
from solver import *
from plot import *
large_data = DataSet("data_large.xlsx")
small_data = DataSet("data_small.xlsx")


#Pulp
prob : LpProblem = LpProblem('ArrivalTimes', LpMinimize)

#Lists
planearrivallist = []
left_deviations = []
right_deviations = []
left_right_bool = []

#Variables and constants for-loop
for i in range(small_data.num_aircraft):
    left_deviations.append(LpVariable('l'+ str(i), 0, 10000, LpInteger ))
    right_deviations.append(LpVariable('r'+ str(i), 0, 10000, LpInteger ))
    left_right_bool.append(LpVariable('lr' + str(i), 0, 1, LpBinary))
    
#Constraints for-loop
for i in range(small_data.num_aircraft):
    prob.addConstraint(small_data.target[i] + right_deviations[i] <= small_data.latest[i])
    prob.addConstraint(small_data.target[i] - left_deviations[i] >= small_data.earliest[i])
    prob.addConstraint(left_deviations[i] <= 10**9 * left_right_bool[i])
    prob.addConstraint(right_deviations[i] <= 10**9 * (1 - left_right_bool[i]))




prob.setObjective(sum(left_deviations) + sum(right_deviations))

status = prob.solve()


for i in range(small_data.num_aircraft):
    planearrivallist.append(int(value(right_deviations[i]) + value(small_data.target[i]) - value(left_deviations[i])))

# for i in planearrivallist:
#     print(value(i))
    
    
    
    
    
solution_small = Solution(10, small_data)
solution_small.arrival_times = planearrivallist
print(solution_small)
plot_sol_deviation(solution_small)
plot_sol_events(solution_small)
plot_sol_intervals(solution_small)
plot_show()