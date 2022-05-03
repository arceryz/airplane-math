from pulp import *

# Define the variables with respective upper/lower bounds.
plain = LpVariable('plain', 0, 1000, LpInteger)
mexican = LpVariable('mexican', 0, 1000, LpInteger)

# Create the problem and set whether we should maximize or minimize objective.
prob: LpProblem = LpProblem('Potato', LpMaximize)

# Add constraints that limit the optimisation process.
prob.addConstraint(2*plain + 4*mexican <= 345)
prob.addConstraint(4*plain + 5*mexican <= 480)
prob.addConstraint(4*plain + 2*mexican <= 330)

# Set the expression that should be maximized/minimized.
# Maximize/minimize based on the problem.
prob.setObjective(2*plain + 1.5*mexican)

# Sovlve the problem. The results can be read from the LpVariables.
status = prob.solve()
print(value(plain), value(mexican))
print(2*value(plain) + 1.5*value(mexican))