class recorder:
    def __init__(self, capacity):
        self.rec = {}
        self.t = {}
        self.capacity = capacity
        self.limits = {}
    
    def log(self, var, val):
        try:
            t = self.t[var]
        except KeyError:
            self.rec[var] = [0]*self.capacity
            self.t[var] = 0
            t = 0
        finally:
            self.rec[var][t] = val
            self.t[var] += 1
        
    def getrec(self, var):
        return self.rec[var]
        
    def getlastrec(self, var):
        try:                          return self.rec[var][self.t[var]-1]
        except KeyError, IndexError:  return 0
        
    def getlimits(self, var):
        try:              return self.limits[var]
        except KeyError:  return (None, None)

