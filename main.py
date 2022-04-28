from solver import *

data_set = DataSet("data_large.xlsx")
sol = block_solve(data_set) 
print(sol)

data_set = DataSet("data_small.xlsx")
sol = block_solve(data_set) 
print(sol)
