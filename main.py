# Modelling B python main.

from solver import * 
from plot import *

data_set = DataSet("data_large.xlsx")
load_cplex()
sol = ILP_solve_leftright(data_set)
sol.write_report("report.txt")

print(sol)
plot_sol_deviation(sol)
plot_show()
