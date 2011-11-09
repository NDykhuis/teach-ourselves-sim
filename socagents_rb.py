import math
#from decisionmaker import *

# The most complex decision-making agents available.
# Features:
#   Dynamic, weighted friend connections
#   Prospect-theory external reward
#   Affect and momentum
#   The worst performance of any of the agent models!


def prospectV(x,p,alpha=0.88,lamb=2.25,gamma=0.61,delta=0.69, scale=0.05):
    if x > 0:
        return (prospectwp(p,gamma)*(scale*x)**alpha)
    else:
        return (prospectwn(p,delta)*-lamb*((-scale*x)**alpha))

def prospectwp(p, gamma = 0.61):
    return p**gamma/(p**gamma+(1.0-p)**gamma)**(1.0/gamma)

def prospectwn(p, delta = 0.69):
    return prospectwp(p,delta)
    
def sigmoid(x, scale = 1.0):    # Function = 0.96 at x = scale
    scaler = 4/(scale)
    return (2/(1+math.exp(-x*scaler))-1)
    

class agent(object):
    idc = 0     # BAD WAY TO DO A COUNTER
    
    # put in default parameters here
    globalreward = 0
    reward = 0
    
    stochasticchoice = True # Agents choose stochastically based on relative weights of options (rather than greedily)
    stochasticrange = 0.25  # Tightness of threshold on sigmoid function (f(x) = 0.96 at x = stochasticrange)
    momentum = True         # Agents tend to keep doing the same thing as long as they're happy with it
    idealperf = False       # Agents interest decays when material is too easy or too hard
    socialint = False       # Interest is influenced by friends
    
    learning = True         # do the agents' skills increase over time with playing the game?
    learningrate = 0.005
    
    hlearn = 0.1            # Rate at which agent's history changes
    
    reps = 0.05             # Rationality epsilon - how frequenly agent randomly re-considers
    
    idealp = 0.85           # Ideal performance level for a student.
    
    @staticmethod
    def initconfig(cfgdict):
        for key,val in cfgdict.iteritems():
            setattr(agent,str(key), val)
            #vars(agent)[str(key)] = val
    
    @staticmethod
    def getconfig():
        #t = type(agent.__init__)
        d = agent.__dict__
        #kvs = {key:val for key, val in d.iteritems() if type(val) != t and key[0:2] != '__'}  # get all static variables that I defined
        types = (type(1), type(1.5), type(True))
        kvs = dict([(key,val) for key, val in d.iteritems() if type(val) in types and key[0:2] != '__'])
        del kvs['idc']
        return kvs
        
    
    def __init__(self, base=True):
        self.aid = agent.idc; agent.idc += 1
        
        self.mymove = None
        self.lastmove = None
        self.correct = False
        self.hperf = 1
        self.hoperf = 0
        self.hpart = 0.5
        self.hpay = 0
        self.effortreq = 0.1
        self.newinfo = False
        
        if base:    # if we're instantiating a stand-alone agent (not a derived class)
            self.skill = random.random()   # 0 to 1, odds of succeeding when it participates
            self.interest = 2*random.random()-1    # -1 to 1, intrinsic interest in the activity
            self.intmot = self.interest
            self.affect = self.interest
            self.weights = [0,0,0]
            for i in (0,1,2):   # extrinsic, intrinsic, and social reward
                self.weights[i] = random.random()
            self.weights = [w / sum(self.weights) for w in self.weights]    # normalize
        pass

    def play(self):
        # decide rational-utility vs. affect-momentum
        #   calculate expected utility for both options
        #   OR pick same move
        self.mymove = random.choice([True, False])
        if random.random()**2 > self.affect or not self.momentum or self.newinfo:
            # Calculate U(part) - U(not) and check if > 0
            #ext = prospectV(self.reward, self.hperf, alpha=0.5, lamb=5, scale=0.01*self.weights[0]) - self.effortreq
            ext = (prospectV(self.globalreward + self.reward, self.hperf, alpha=0.5, lamb=5, scale=0.01*self.weights[0]) - prospectV(-(self.globalreward + self.reward), 1-self.hperf, alpha=0.5, lamb=5, scale=0.01*self.weights[0]))/2
            inter = prospectV(self.interest, self.hperf, alpha=0.5, lamb=1.5, scale = self.weights[1])
            # how much participation, performance, relative performance
            soc = prospectV(((prospectwp(self.hpart)-prospectwn(1-self.hpart)) + (self.hperf-self.hoperf) - (self.hoperf-self.hperf)**2)/3, 1, alpha=0.5, lamb=1.5, scale = self.weights[2])
            
            # pick (ext + inter + soc) from normal cdf or sigmoid to determine probability of participating.
            # 0 = 50/50
            judgment = ext + inter + soc
            prob = (sigmoid(judgment, scale=agent.stochasticrange)+1)/2  # prob from 0 to 1
            #prob = prob**2
            if agent.stochasticchoice:
                self.mymove = random.random() < prob
            else:
                self.mymove = judgment > 0 
            self.prob = prob; self.external = ext; self.internal = inter; self.social = soc
            if self.mymove != self.lastmove:
                self.affect = 0
            self.newinfo = False
        else:
            self.mymove = True #self.mymove
            self.prob = self.affect
            
                
        self.expectext = self.hperf * (self.globalreward+self.reward) * self.mymove
        
        #self.mymove = random.choice([True, False])  # Temporary
        return self.mymove

    def postprocess(self, points):
        # update history
        # update affect/interest
        afeps = 0.75
        
        if self.affect >= 0 or self.mymove:
            samefriends = sum(n.mymove==self.mymove for n in self.nbrs)
            if samefriends:
                friendinterest = sum(n.interest for n in self.nbrs if n.mymove == self.mymove)/samefriends
            else: friendinterest = sum(n.interest for n in self.nbrs) / len(self.nbrs)
            
            # External = prospect(reward) where reward = reward, or reward - expectation, or some combination
            # Internal = interest - (hperf - idealp)^2 - external + (friendavg - myinternal)    # external could also be a scaling factor
            # Social = combination of my perf, avg perf, friend perf
            
            
            external = prospectV(0.5*(points - self.expectext)+0.5*points, 1, alpha=0.5, lamb=5, scale=0.01*self.weights[0]) - self.effortreq
            internal = (self.interest - (self.hperf - self.idealp)**2 + self.weights[2]*(friendinterest - self.interest))*(1/2**external)*self.weights[1]
            # how much participation, performance, relative performance
            social = prospectV(((prospectwp(self.hpart)-prospectwn(1-self.hpart))/2 + (self.hperf-self.hoperf) - (self.hoperf-self.hperf)**2)/3, 1, alpha=0.5, lamb=1.5, scale = self.weights[2])
            
            self.affect = afeps*self.affect + (1-afeps)*(external + internal + social)
            self.external = external; self.internal = internal; self.social = social
        else:
            self.affect = afeps*self.affect + (1-afeps)*(self.internal)  # This is a bad way to do it - should be that bigger changes in affect have a bigger impact. Affect should change immediately upon learning that the reward is now -100
            
        # State interest decays to trait interest?
        
        if self.learning and self.mymove:
            #if points > 0:  # we got it right
            self.skill += self.learningrate*(1-self.skill)
        
        if self.mymove: 
            self.hpay = self.hlearn*(points) + (1-self.hlearn)*self.hpay
            self.hpay = max(self.hpay,0)    # A hack, for negative pays
            self.hperf = self.hlearn*self.correct + (1-self.hlearn)*self.hperf   # should change less drastically
        
        if self.nbrs and len(self.nbrs):
            # Historical participation is a weighted average based on connection strength
            sumw = sum(self.node[n.aid]['weight'] for n in self.nbrs)
            #normw = [self.node[n.aid]['weight']/sumw for n in self.nbrs]
            self.hpart = (1-self.hlearn)*self.hpart + \
                self.hlearn*(sum(n.mymove*self.node[n.aid]['weight']/sumw for n in self.nbrs))
        
        nbrpart = float(sum(nbr.correct is not None for nbr in self.nbrs))
        if nbrpart:     # prevent div by zero errors
            self.hoperf = self.hlearn*(sum([nbr.correct is not None and nbr.correct for nbr in self.nbrs])/ \
                     nbrpart) + (1-self.hlearn)*self.hoperf
        
        for n in self.nbrs:
            self.node[n.aid]['weight'] = self.node[n.aid]['weight']*(1-0.01)+0.01*(self.mymove==n.mymove)
        
        self.lastmove = self.mymove
        pass

    def printself(self):
        print "skill:",self.skill," interest:",self.interest
        print "ext:",self.weights[0]," int:",self.weights[1]," soc:",self.weights[2]
        if self.mymove is not None:
            stat = "right" if self.mymove and self.correct else ("wrong" if self.mymove else "none")
            print "prob:",self.prob," affect:", self.affect
            print "ext:",self.external," int:",self.internal," soc:",self.social," ",stat
        print "hpay:",self.hpay," hpart:",self.hpart," hperf:",self.hperf," hoperf:",self.hoperf
        #print "play:",self.playpay," not:",self.nonepay
        pass

    def difference(self, other):        # Used in estimating difference between two students for social network formation
        diff = 0
        diff += (self.skill-other.skill)**2 + ((self.interest-other.interest)/2)**2  # not dividing by two weights interest too heavily
        diff += sum([(self.weights[i]-other.weights[i])**2 for i in (0,1,2)])/6.0
        # diff += socweights?
        return diff
        pass

    def neighbors(self, nbrs, node):    # Add neighbors to an agent
        self.nbrs = nbrs
        self.node = node
        try: len(nbrs)  # see if nbrs is a list, or single item
        except (AttributeError, TypeError):
            self.nbrs = [self.nbrs]



def restrict(var,sm,lg):
    return min(lg, max(sm, var))

class unifagent(agent):
    def __init__(self, skilllo=0, skillhi=1, intlo=-1, inthi=1, wlo=[0,0,0], whi=[1,1,1]):
        super(unifagent,self).__init__(False)
        self.skill = random.uniform(skilllo,skillhi)   # 0 to 1, odds of succeeding when it participates
        self.interest = random.uniform(intlo, inthi)   # -1 to 1, intrinsic interest in the activity
        self.weights = [0,0,0]
        for i in (0,1,2):   # extrinsic, intrinsic, and social reward
            self.weights[i] = random.uniform(wlo[i],whi[i])
        self.weights = [w / sum(self.weights) for w in self.weights]    # normalize
        self.socweights = [1] #[random.random()]
        self.Q = [0,0]  # Q-learning table - expected reward for each action
        # need to also init place in the graph / neighbors

class gaussagent(agent):
    def __init__(self, skillmu=0.5, skillsd=0.2, intmu=0, intsd=0.4, wmu=[0.5,0.5,0.5], wsd=[0.2,0.2,0.2]):
        super(gaussagent,self).__init__(False)
        self.skill = restrict(random.gauss(skillmu, skillsd),0,1)   # 0 to 1, odds of succeeding when it participates
        self.interest = restrict(random.gauss(intmu, intsd),-1,1)   # -1 to 1, intrinsic interest in the activity
        self.weights = [0,0,0]
        for i in (0,1,2):   # extrinsic, intrinsic, and social reward
            self.weights[i] = restrict(random.gauss(wmu[i],wsd[i]),0,1)
        self.weights = [w / sum(self.weights) for w in self.weights]    # normalize
        self.socweights = [1] #[random.random()]
        self.Q = [0,0]  # Q-learning table - expected reward for each action

from betarand import betarand
class betaagent(agent):
    def __init__(self, skillmd=0.5, skillb=8, intmd=0, intb=8, wmd=[0.5,0.5,0.5], wb=[3,3,3]):
        super(betaagent,self).__init__(False)
        self.skill = betarand(skillmd, skillb)           # 0 to 1, odds of succeeding when it participates
        self.interest = 2*betarand(intmd/2+0.5, intb)-1  # -1 to 1, intrinsic interest in the activity
        self.intmot = self.interest
        self.affect = self.interest
        self.weights = [0,0,0]
        for i in (0,1,2):   # extrinsic, intrinsic, and social reward
            self.weights[i] = betarand(wmd[i],wb[i])
        self.weights[0]*=2
        self.weights = [w / sum(self.weights) for w in self.weights]    # normalize
        self.socweights = [1] #[random.random()]
        self.Q = [0,0]  # Q-learning table - expected reward for each action

