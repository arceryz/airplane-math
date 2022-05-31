# Modelling B python main.

from solver import * 
from plot import *

data_set = DataSet("data_small.xlsx")
load_cplex()
sol = ILP_solve_leftright_extended(data_set)
sol.write_report("report.txt")

print(sol)
plot_sol_deviation(sol)
plot_show()
