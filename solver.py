from data_set import DataSet

class Solution:
    # Class representing a solution to the airplanes problem.
    
    def __init__(self, num_aircraft: int, data_set: DataSet):
        self.data_set = data_set
        self.arrival_times = [-1] * num_aircraft
        
    def __str__(self):
        out =  "Deviation   = {:d}\n".format(int(self.get_deviation()))
        out += "Is valid    = {:s}\n".format("Yes" if self.is_valid else "No")
        out += "ID    early    arrival  latest   target  diff\n"
        for i in range(len(self.arrival_times)):
            diff = self.arrival_times[i] - self.data_set.target[i]
            out += "{:<3d} : {:<6d} < {:<6d} < {:<6d} : {:<6d}  {:<3d}\n".format(i, \
                    self.data_set.earliest[i], self.arrival_times[i], \
                    self.data_set.latest[i], self.data_set.target[i], diff)
        return out


    def get_deviation(self) -> float:
        # Return average deviation from target times.
        sum_variance = 0
        for i in range(len(self.arrival_times)):
            sum_variance += abs(self.arrival_times[i] - self.data_set.target[i])
        return sum_variance / len(self.arrival_times)


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


def block_solve(data_set: DataSet) -> Solution:
    # Block solve algorithm distributes the entire time interval in blocks 
    # based on safety time. Planes are then assigned the closest empty block based
    # on their target time.
    min_earliest = min(data_set.earliest)
    max_latest = max(data_set.latest)
    interval = max_latest - min_earliest
    num_blocks = interval // data_set.safety_time
    # Equally distribute the remainder of dividing by safety time for more spacing.
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
    sol = Solution(data_set.num_aircraft, data_set)
    for i in range(num_blocks):
        if blocks[i] != -1:
            sol.arrival_times[blocks[i]] = int(round(min_earliest + i * spacing))
    return sol
