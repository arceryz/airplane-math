# Modelling B python main.

from solver import * 
from plot import *

data_set = DataSet("data_large.xlsx")
sol = block_solve(data_set) 
print(sol)

plot_sol_deviation(sol)
plot_sol_events(sol)
plot_sol_intervals(sol)
plot_show()

data_set = DataSet("data_small.xlsx")
sol = block_solve(data_set) 
print(sol)
