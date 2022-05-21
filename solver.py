# Written by Timothy van der Valk and Simon Deuten.
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
# Solve the problem using pulp with left/right deviation technique without a
# Y decision variable, which is proven to be unnecessary. 
#
# 3) ILP_solve_deviation_bound
# Solve the problem using pulp with deviation neighborhood technique. The given
# time is bounded by the deviation which is then minimized.
#
# 4) ILP_solve_leftright_y
# Same as 2) but the unnecessary Y variable is included for completeness.


from data_set import *
import time
import pulp


g_solver = None


class Solution:
    # Class representing a solution to the airplanes problem.
    
    def __init__(self, data_set: DataSet):
        self.technique = "Unknown technique"
        self.solving_time = 0.0
        self.data_set = data_set
        self.arrival_times = [-1] * data_set.num_aircraft
        

    def __str__(self):
        out = ""
        out += "===== SOLUTION REPORT =====\n"
        out += "Technique    = {:s}\n".format(self.technique)
        out += "Backend      = {:s}\n".format("Default" if g_solver == None else "CPLEX")
        out += "Solving time = {:.2f}s\n".format(self.solving_time)
        out += "Deviation    = {:d}\n".format(int(self.get_deviation()))
        out += "Objective    = {:d}\n".format(int(self.get_objective()))
        out += "Safety time  = {:d}\n".format(self.data_set.safety_time)
        out += "Is valid     = {:s}\n".format("Yes" if self.is_valid else "No")
        out += "ID    early    arrival  latest   target  diff\n"
        for i in range(len(self.arrival_times)):
            diff = self.arrival_times[i] - self.data_set.target[i]
            out += "{:<3d} : {:<6d} < {:<6d} < {:<6d} : {:<6d}  {:<3d}\n".format(i, \
                    self.data_set.earliest[i], self.arrival_times[i], \
                    self.data_set.latest[i], self.data_set.target[i], diff)
        return out


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
                if abs(arrival - other) > self.data_set.safety_time:
                    return False
        return True


def load_cplex():
    # Load the cplex solver and set a time limit.
    global g_solver
    g_solver = pulp.CPLEX_PY()


def block_solve(data_set: DataSet) -> Solution:
    start_time = time.time()

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
    sol.technique = "Block Assign"
    sol.solving_time = time.time() - start_time
    for i in range(num_blocks):
        if blocks[i] != -1:
            sol.arrival_times[blocks[i]] = int(round(min_earliest + i * spacing))
    return sol


def ILP_solve_leftright(data_set: DataSet) -> Solution:
    start_time = time.time()

    # Solve ILP using the left/right deviations technique without removal of
    # y decision constraint.
    prob = pulp.LpProblem("airplane_ilp", pulp.LpMinimize)      
   
    a_vars = []
    b_vars = []
    y_vars = []
    k_lists = []
    overlap_lists = []
    M = 1000000

    # Define all variables
    for i in range(data_set.num_aircraft):
        a_vars.append(pulp.LpVariable("a_"+str(i), 0, M, pulp.LpInteger))
        b_vars.append(pulp.LpVariable("b_"+str(i), 0, M, pulp.LpInteger))
        y_vars.append(pulp.LpVariable("y_"+str(i), 0, M, pulp.LpInteger))

        overlap = data_set.get_overlaps(i)
        overlap_lists.append(overlap) 
        k_vars = []
        for j in range(len(overlap)):
            k_vars.append(pulp.LpVariable("k_"+str(i)+"_"+str(j), 0, 1, pulp.LpBinary)) 
        k_lists.append(k_vars)

    # Define all constraints.
    for i in range(data_set.num_aircraft):
        a = a_vars[i]
        b = b_vars[i]
        y = y_vars[i]
        e = data_set.earliest[i]
        l = data_set.latest[i]
        t = data_set.target[i]
        s = data_set.safety_time
        overlap = overlap_lists[i]

        # Boundary constraint.
        prob.addConstraint(t - a >= e)
        prob.addConstraint(t + b <= l)

        # Choice constraint.
        # Removing these constraints has no influence on the outcome, but they
        # help nudge the solver in the right direction and thus increase solving
        # speed. Solutions where a > 0 and b > 0 are no longer considered.
        prob.addConstraint(a <= M * y)
        prob.addConstraint(b <= M * (1 - y))

        # Plane-relative constraints. Based on the decision for kj, disable one
        # constraint by making it trivial. The decision kj determines whether
        # we should align left or right of plane j.
        for ii in range(len(overlap)):
            j = overlap[ii]
            aj = a_vars[j]
            bj = b_vars[j]
            tj = data_set.target[j]
            kj = k_lists[i][ii]
            prob.addConstraint(t - a + b <= tj - aj + bj - s + M * kj)
            prob.addConstraint(t - a + b >= tj - aj + bj + s - M * (1 - kj))
        pass

    prob.setObjective(sum(a_vars) + sum(b_vars))
    prob.solve(g_solver)

    sol = Solution(data_set)
    sol.solving_time = time.time() - start_time
    sol.technique = "ILP LeftRight"

    for i in range(data_set.num_aircraft):
        a = int(pulp.value(a_vars[i]))
        b = int(pulp.value(b_vars[i]))
        y = int(pulp.value(y_vars[i]))
        t = data_set.target[i]
        arr = t - a + b
        sol.arrival_times[i] = arr
        print("plane {:d}: a={:d} b={:d}, dev={:d}, overlaps={:d}".format(i, a, b, abs(t - arr), len(overlap_lists[i])))
        
    return sol


def ILP_solve_deviation_bound(data_set: DataSet) -> Solution:
    start_time = time.time()

    # Solve ILP using the deviation neighborhood technique.
    # About 3x as slow as our leftright technique.
    prob = pulp.LpProblem("airplane_ilp", pulp.LpMinimize)      
   
    s = data_set.safety_time
    g_vars = []
    d_vars = []
    k_lists = []
    overlap_lists = []
    M = 1000000

    # Define all variables
    for i in range(data_set.num_aircraft):
        g_vars.append(pulp.LpVariable("g_"+str(i), 0, M, pulp.LpInteger))
        d_vars.append(pulp.LpVariable("d_"+str(i), 0, M, pulp.LpInteger))

        overlap = data_set.get_overlaps(i)
        overlap_lists.append(overlap) 
        k_vars = []
        for j in range(len(overlap)):
            k_vars.append(pulp.LpVariable("k_"+str(i)+"_"+str(j), 0, 1, pulp.LpBinary)) 
        k_lists.append(k_vars)

    # Define all constraints.
    for i in range(data_set.num_aircraft):
        g = g_vars[i]
        d = d_vars[i]
        e = data_set.earliest[i]
        l = data_set.latest[i]
        t = data_set.target[i]
        overlap = overlap_lists[i]

        # Boundary constraint.
        prob.addConstraint(g >= e)
        prob.addConstraint(g <= l)

        # Deviation constraint. From this constraint we have an upper bound
        # for the deviation around target given by d, which we can then minimize.
        prob.addConstraint(g >= t - d)
        prob.addConstraint(g <= t + d)

        # Plane safety constraints.
        k_vars = k_lists[i]
        for ii in range(len(overlap)):
            j = overlap[ii]
            gj = g_vars[j]
            kj = k_vars[ii]

            prob.addConstraint(g <= gj - s + M * kj)
            prob.addConstraint(g >= gj + s - M * (1 - kj))
        pass

    prob.setObjective(sum(d_vars))
    prob.solve(g_solver)

    sol = Solution(data_set)
    sol.solving_time = time.time() - start_time
    sol.technique = "ILP Deviation neighborhood"

    for i in range(data_set.num_aircraft):
        g = int(pulp.value(g_vars[i]))
        d = int(pulp.value(d_vars[i]))
        t = data_set.target[i]
        sol.arrival_times[i] = g
        print("plane {:d}: g={:d} d={:d}, dev={:d}, overlaps={:d}".format(i, g, d, abs(t - g), len(overlap_lists[i])))
       
    return sol
