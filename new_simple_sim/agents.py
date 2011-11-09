import math
import random

from agentcfg import agentcfg

class agent(object):
    idc = 0     # BAD WAY TO DO A COUNTER

    globalreward = 0
    reward = 0

    def __init__(self):
        self.aid = agent.idc; agent.idc += 1

        self.mymove = None      # My move: participate (T) or not (F)
        self.lastmove = None    # Move from last turn
        self.correct = False    # Did I get the last problem correct?

        # In absence of a derived class, instantiate a random agent
        self.skill = random.random()   # 0 to 1, odds of succeeding when it participates
        self.interest = 2*random.random()-1    # -1 to 1, intrinsic interest in the activity

        self.weights = [1,1,1]  # Weights all equal = no effect
        # for i in (0,1,2):   # extrinsic, intrinsic, and social reward
        #     self.weights[i] = random.random()
        # self.weights = [w / sum(self.weights) for w in self.weights]    # normalize
        
        self.cfg = agentcfg()

    def play(self, t, reward_func):
        cfg = self.cfg
        #external_reward = reward_func(t)
        #expected_reward = external_reward * self.skill
        external_reward = self.reward + agent.globalreward  #reward_func( self.reward + agent.globalreward )
        expected_reward = external_reward*0.1*self.skill    #reward_func( external_reward ) * self.skill
        #print external_reward, "*", self.skill, "=", expected_reward
        social_influence = 0.0
        # take out social influence, see if participation rapidly drops
        #if t > 0: # determine neighbors' actions in previous round
        #    for nbr in self.nbrs:
        #        if nbr.mymove:
        #            social_influence += 1.0
        #        else:
        #            social_influence -= 1.0

        social_influence /= len(self.nbrs)
        # social_influence now a value between -1 and 1. 1 iff all neighbors participated last round, -1 iff all neighbors didn't participate
        #print social_influence, "+", self.interest, "+", expected_reward, "=", social_influence + self.interest + expected_reward

        evaluation = self.weights[0]*expected_reward + self.weights[1]*self.interest + self.weights[2]*social_influence
        if cfg.stochasticchoice:
            self.mymove = sigmoid(evaluation,width=2) > random.random()
        else:
            self.mymove = evaluation > 0
        return self.mymove
        
    def postprocess(self, points):
        cfg = self.cfg
        # update history, learning, etc.

        if cfg.learning and self.mymove:
            #if points > 0:  # do we learn only when we get it right?
            # With below eqn, skill exponentially approaches 1
            # Is this what we want?
            self.skill += cfg.learningrate*(1-self.skill)
        
        # Here, estimate average recent payment, average friend participation
        
        if self.nbrs and len(self.nbrs):
            nbrpart = sum(n.mymove for n in self.nbrs)  # num of friends participating
        
        self.lastmove = self.mymove

        
        
        
        
    @staticmethod
    def setconfig(config):
        for key,val in config.iteritems():
            setattr(agentcfg, str(key), val)
    
    @staticmethod
    def getconfig():
        d = agentcfg.__dict__
        types = (type(1), type(1.5), type(True), type("hi"))
        #kvs = {key:val for key, val in d.iteritems() if type(val) in types and key[0:2] != '__'}  # get all configuration variables from the class  # Python 2.7 req'd
        kvs = dict([(key,val) for key, val in d.iteritems() if type(val) in types and key[0:2] != '__'])
        return kvs

    def difference(self, other):        # Used in estimating difference between two students for social network formation
        diff = 0
        diff += (self.skill-other.skill)**2 + ((self.interest-other.interest)/2)**2  # not dividing by 2 weights interest too heavily
        diff += sum([(self.weights[i]-other.weights[i])**2 for i in (0,1,2)])/6.0
        # Should we weight social more heavily here?
        return diff

    def neighbors(self, nbrs, node):    # Add neighbors to an agent
        self.nbrs = nbrs
        self.node = node
        try: len(nbrs)  # see if nbrs is a list, or single item
        except (AttributeError, TypeError):
            self.nbrs = [self.nbrs]

    def printself(self):
        print "skill:",self.skill," interest:",self.interest
        print "ext:",self.weights[0]," int:",self.weights[1]," soc:",self.weights[2]
        if self.mymove is not None:
            stat = "right" if self.mymove and self.correct else ("wrong" if self.mymove else "none")
            print "prob:",self.prob," affect:", self.affect
            print "ext:",self.external," int:",self.internal," soc:",self.social," ",stat
        #print "hpay:",self.hpay," hpart:",self.hpart," hperf:",self.hperf," hoperf:",self.hoperf
        
        

import math

# This is a sigmoid function, with a y range of (0,1), where sigmoid(width) = threshold
def sigmoid(x, width=4, threshold=0.99, yrange=(0,1)):
    s = math.log(1/threshold-1)/(-width)
    return 1/(1+math.exp(-s*x))*(yrange[1]-yrange[0])-yrange[0]


        
### OTHER MODELS OF AGENT ###
        
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

class gaussagent(agent):
    def __init__(self, skillmu=0.5, skillsd=0.2, intmu=0, intsd=0.4, wmu=[0.5,0.5,0.5], wsd=[0.2,0.2,0.2]):
        super(gaussagent,self).__init__(False)
        self.skill = restrict(random.gauss(skillmu, skillsd),0,1)   # 0 to 1, odds of succeeding when it participates
        self.interest = restrict(random.gauss(intmu, intsd),-1,1)   # -1 to 1, intrinsic interest in the activity
        self.weights = [0,0,0]
        for i in (0,1,2):   # extrinsic, intrinsic, and social reward
            self.weights[i] = restrict(random.gauss(wmu[i],wsd[i]),0,1)
        self.weights = [w / sum(self.weights) for w in self.weights]    # normalize

#from betarand import betarand
# Functions to pick from beta distributions
def calcalph(m,b):
    return ((b-2)*m+1)/(1-m)

def getbeta(m,b):
    if m > 0.5:
        a = calcalph(1-m,b)
        a,b = b,a
    else:
        a = calcalph(m,b)
    return a,b

def betarand(mode,beta=8):  
    # mode is location of peak, beta is tightness of peak
    a,b = getbeta(mode,beta)
    return random.betavariate(a,b)

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
