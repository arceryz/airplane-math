# Written by Timothy van der Valk, Simon Deuten, Frank van der Top, Shae Williams.
# 
# Includes block and PuLP optimized solver algorithms for solving the airplane
# runway problem.
# There are 4 solvers in this file.
#
# 1) block_solve: 
# Block solver assigns all airplanes to an unoccupied block closest to their
# preference. This algorithm is fast but suboptimal.
#
# 2) ILP_solve_leftright
# Solve the problem using pulp with left/right deviation technique.
# Seems to be much faster than technique 3.
#
# 3) ILP_solve_deviation_bound
# Solve the problem using pulp with deviation neighborhood technique. The given
# time is bounded by the deviation which is then minimized.


from data_set import *
import time
import pulp


g_solver = None


class Solution:
    # Class representing a solution to the airplanes problem.
    
    def __init__(self, data_set: DataSet):
        self.data_set = data_set
        self.arrival_times = [-1] * data_set.num_aircraft
        

    def __str__(self):
        out = ""
        out += "===== SOLUTION REPORT =====\n"
        out += "Backend      = {:s}\n".format("Default" if g_solver == None else "CPLEX")
        out += "Deviation    = {:d}\n".format(int(self.get_deviation()))
        out += "Objective    = {:d}\n".format(int(self.get_objective()))
        out += "Base safety time  = {:d}\n".format(self.data_set.safety_time)
        out += "Perfect arrival count = {:d}\n".format(int(self.count_0_deviations()))
        out += "Is valid     = {:s}\n".format("Yes" if self.is_valid() else "No")
        out += "ID    early    arrival  latest   target  diff  safety time\n"
        for i in range(len(self.arrival_times)):
            diff = self.arrival_times[i] - self.data_set.target[i]
            out += "{:<3d} : {:<6d} < {:<6d} < {:<6d} : {:<6d}  {:<3d}  {:<6d}\n".format(i, \
                    self.data_set.earliest[i], self.arrival_times[i], \
                    self.data_set.latest[i], self.data_set.target[i], diff, self.data_set.safety_times[i])
        return out
    
    def count_0_deviations(self):
        count = 0
        for i in range(len(self.arrival_times)):
            if self.arrival_times[i] - self.data_set.target[i] == 0:
                count += 1
        return count

    def write_report(self, file: str):
        # Write report to given file.
        f = open(file, "w")
        f.write(str(self))
        f.close()
        print("Report written to {:s}".format(file))


    def get_deviation(self) -> float:
        # Return average deviation from target times.
        sum_variance = 0
        for i in range(len(self.arrival_times)):
            sum_variance += abs(self.arrival_times[i] - self.data_set.target[i])
        return sum_variance / len(self.arrival_times)


    def get_objective(self) -> float:
        # Return objective of optimisation problems. Sum of deviations.
        sum_variance = 0
        for i in range(len(self.arrival_times)):
            sum_variance += abs(self.arrival_times[i] - self.data_set.target[i])
        return sum_variance


    def is_valid(self) -> bool:
        # Return whether solution satisfies all constraints.
        for i in range(len(self.arrival_times)):
            arrival = self.arrival_times[i]
            earliest = self.data_set.earliest[i]
            latest = self.data_set.latest[i]
            if arrival < earliest or arrival > latest:
                return False

            # Validate safety constraint.
            for k in range(len(self.arrival_times)):
                other = self.arrival_times[k]
                if abs(arrival - other) < self.data_set.safety_times[k] and k != i:
                    print("VIOLATION {:d} and {:d}".format(arrival, other))
                    return False
        return True


def load_cplex():
    # Load the cplex solver and set a time limit.
    global g_solver
    g_solver = pulp.CPLEX_PY()


def block_solve(data_set: DataSet) -> Solution:
    # Block solve algorithm distributes the entire time interval in blocks 
    # based on safety time. Planes are then assigned the closest empty block based
    # on their target time.
    min_earliest = min(data_set.earliest)
    max_latest = max(data_set.latest)
    interval = max_latest - min_earliest
    num_blocks = interval // data_set.safety_time
     
    # Equally distribute the remainder of dividing by safety time for more spacing.
    # This ensures that the entire interval is used to its full potential.
    spacing = data_set.safety_time + 0 * (interval - num_blocks * data_set.safety_time) / num_blocks
    blocks = [-1] * num_blocks
   
    # Iterate all aircraft to find the nearest suitable block for them to land.
    for i in range(data_set.num_aircraft):
        target = data_set.target[i]
        earliest = data_set.earliest[i]
        latest = data_set.latest[i]
        
        # The nearest block is the first to search. From there with each iteration
        # we consider b0 - k and b0 + k until one is empty.
        b0 = int(round((target - min_earliest) / spacing))
        final_block = -1
        for k in range(0, num_blocks):
            b1 = max(b0 - k, 0)
            b2 = min(b0 + k, num_blocks - 1)
            t1 = b1 * spacing + min_earliest
            t2 = b2 * spacing + min_earliest
            if blocks[b1] == -1 and earliest <= t1 <= latest:
                final_block = b1
                break
            elif blocks[b2] == -1 and earliest <= t2 <= latest:
                final_block = b2
                break
        
        if final_block >= 0:
            blocks[final_block] = i
        else: 
            # No block for this plane.
            pass
    
    # Assign all nonempty blocks to the solution.
    sol = Solution(data_set)
    for i in range(num_blocks):
        if blocks[i] != -1:
            sol.arrival_times[blocks[i]] = int(round(min_earliest + i * spacing))
    return sol

def ILP_solve_leftright_extended(data: DataSet) -> Solution:
    
    # Solve ILP using the left/right deviations technique without removal of
    # y decision constraint.
    prob = pulp.LpProblem("airplane_ilp", pulp.LpMinimize)      
    a_vars = []
    b_vars = []
    y_vars = []
    k_matrix = []
    M = 1000000

    for i in range(data.num_aircraft):
        a_vars.append(pulp.LpVariable("a_"+str(i), 0, M, pulp.LpInteger))
        b_vars.append(pulp.LpVariable("b_"+str(i), 0, M, pulp.LpInteger))
        y_vars.append(pulp.LpVariable("y_"+str(i), 0, 1, pulp.LpInteger))

        row = []
        for j in range(data.num_aircraft):
            row.append(pulp.LpVariable("k_"+str(i)+"_"+str(j), 0, 1, pulp.LpInteger))
        k_matrix.append(row)
     
    for i in range(data.num_aircraft):
        g = data.target[i] - a_vars[i] + b_vars[i]
        prob.addConstraint(g >= data.earliest[i])
        prob.addConstraint(g <= data.latest[i])
        prob.addConstraint(a_vars[i] <= M * y_vars[i])
        prob.addConstraint(b_vars[i] <= M * (1 - y_vars[i]))

        for j in range(data.num_aircraft):
            if i == j:
                continue
            gj = data.target[j] - a_vars[j] + b_vars[j]
            prob.addConstraint(g <= gj - data.safety_times[i] + M * k_matrix[i][j])
            prob.addConstraint(g >= gj + data.safety_times[i] - M * (1 - k_matrix[i][j]))
            prob.addConstraint(k_matrix[i][j] + k_matrix[j][i] == 1)
        pass

    prob.setObjective(sum(a_vars) + sum(b_vars))
    prob.solve(g_solver)

    sol = Solution(data) 
    for i in range(data.num_aircraft):
        g = int(data.target[i] - pulp.value(a_vars[i]) + pulp.value(b_vars[i]))
        sol.arrival_times[i] = g
    
    return sol
