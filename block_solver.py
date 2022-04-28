from data_set import DataSet
from solution import Solution

def block_solve(data_set: DataSet) -> Solution:
    min_earliest = min(data_set.earliest)
    max_latest = max(data_set.latest)
    safety = data_set.safety_time
    
    distance = max_latest - min_earliest
    num_blocks = distance // safety
    blocks = [-1] * num_blocks
    
    for i in range(data_set.num_aircraft):
        target = data_set.target[i]
        earliest = data_set.earliest[i]
        latest = data_set.latest[i]
        
        b0 = int(round(target / safety))
        final_block = -1
        for k in range(0, num_blocks):
            b1 = b0 - k
            b2 = b0 + k
            
            if 0 <= b1 < num_blocks and blocks[b1] == -1:
                t1 = b1 * safety + min_earliest
                if earliest < t1 < latest:
                    final_block = b1
                    break
                
            if 0 <= b2 < num_blocks and blocks[b2] == -1:
                t2 = b2 * safety + min_earliest
                if earliest < t2 < latest:
                    final_block = b2
                    break
        
        if final_block >= 0:
            blocks[final_block] = i
        else:
            print("Airplane " + str(i) + " no spot")
    
    sol = Solution(data_set.num_aircraft)
    for i in range(num_blocks):
        plane = blocks[i]
        sol.arrival_times[plane] = min_earliest + i * safety
    
    return sol
    
    