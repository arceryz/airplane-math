class Solution:
    
    def __init__(self, n_planes: int):
        self.n_planes = n_planes
        self.arrival_times = [-1] * n_planes
        
    def __str__(self):
        return str(self.arrival_times)