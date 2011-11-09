import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from operator import itemgetter
from socagents_rb import *
import threading
import time

class configuration:
    N = 30          # Number of agents
    connections = 4
    conhigh = 5     # default 5
    conlow = 2      # default 1
    nturns = 200
    reward = 20                 # nominally between 0 and 100
    agent.globalreward = 20           

    interactive = True          # Do we cmdpause for user input before and after sim?
    stepbystep = False          # Do we cmdpause after every time step?
    verbose = True

    # do 10 agents, shuffle 0, seed 29 to see reward effect

    SIMILARITY_GRAPH = 1        # Add friends by similarity, or random small-world graph?
    RND_CON = 1                 # Random number of connections
    SOC_CON = 0                 # num of connections based on social weight
    SHUFFLE = 10                # number of edges to shuffle on the similarity graph
    
    randseed = 1365
    
    agenttype = 'random'        # Also accepts 'high_low_mix', 'high_low_cross'
    
    graph_on_figure = { 'participation':2, 'correct':2, 'interest':False, 'reward':False, 'cumulative_reward':False }  # Value is what figure to plot it on
    graph_at_end = True         # Generate graphs only at the end of the sim

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


class simulation:
    def __init__(self, config=None):
        self.cfg = configuration()
        if config is not None:
            self.setconfig(config)
        agent.idc = 0
    
    def setconfig(self, config):
        for key,val in config.iteritems():
            setattr(configuration, str(key), val)
    
    def getconfig(self):
        d = configuration.__dict__
        types = (type(1), type(1.5), type(True), type("hi"))
        #kvs = {key:val for key, val in d.iteritems() if type(val) in types and key[0:2] != '__'}  # get all configuration variables from the class  # Python 2.7 req'd
        kvs = dict([(key,val) for key, val in d.iteritems() if type(val) in types and key[0:2] != '__'])
        return kvs
    
    def seed(self):
        random.seed(self.cfg.randseed)     # for agent generation 
        np.random.seed(self.cfg.randseed)  # for graph drawing

    def setup(self):
        cfg = self.cfg
        N = self.cfg.N
        
        rs = random.getstate()        # to restore afterward, if we want
        self.seed()
        
        if cfg.verbose: print "generating agents"
        
        # Totally random agents
        if cfg.agenttype == 'random':
            agents = [agent() for i in range(0,N)]
        elif cfg.agenttype == 'high_low_mix':
            # mix of "smart" and "dumb" agents
            agents = [betaagent(skillmd=0.85, intmd=0.8) for i in range(int(math.ceil(N/2.0)))]
            agents.extend([betaagent(skillmd=0.15, intmd=-0.8) for i in range(int(math.floor(N/2.0)))])
            #agents = [random.choice( (betaagent(skillmd=0.15, intmd=-0.8),betaagent(skillmd=0.85, intmd=0.8)) ) for i in range(N)]
        elif cfg.agenttype == 'high_low_cross':
            agents = [betaagent(skillmd=random.choice((0.15,0.85)), intmd=random.choice((-0.8,0.8)),wb=[1,1,1]) for i in range(N)]     # seed 64

        #agents = [gaussagent(skillmu=0.5, skillsd=0.2, intmu=0, intsd=0.4) for i in range(N)]

        self.agents = agents

        if cfg.verbose: print "generating graph"

        G=nx.Graph()
        
        def add_friend(x,y, w=None):
            if w==None:
                w = random.random()
            G.add_edge(x,y,weight=w)
            agents[x].nbrs += [agents[y],]
            agents[y].nbrs += [agents[x],]

        def unfriend(x,y):
            G.remove_edge(x,y)
            agents[x].nbrs.remove(agents[y])
            agents[y].nbrs.remove(agents[x])

        def inspect(i):
            a = agents[i]
            a.printself()

        # We're going to try to connect agents by similarity

        if cfg.SIMILARITY_GRAPH:
            if cfg.verbose: print "generating similarity connections"
            G.add_nodes_from(range(0,N))
            con = cfg.connections
            for i in range(N):        # Look at each agent
                t = [[0,0] for q in range(N)]
                for j in range(0,N):    # Compare to each other agent
                    t[j][0] = j
                    if i == j: continue
                    t[j][1] = agents[i].difference(agents[j])
                t = sorted(t, key=itemgetter(1))
                del t[0]    # delete i-i connection
                if cfg.RND_CON:   con = random.randint(cfg.conlow,cfg.conhigh)
                for j in range(0,con):
                    # connect agents i and t[j][0]
                    G.add_edge(i,t[j][0],weight=random.random())#1-t[j][1]**2)

            e = random.sample(G.edges(),cfg.SHUFFLE)
            G.remove_edges_from(e)
            for i in range(cfg.SHUFFLE):
                x=random.randint(0,N-1); y=random.randint(0,N-1)
                G.add_edge(x,y,weight=random.random())#1-agents[x].difference(agents[y])**2)

        else:
            G = nx.generators.random_graphs.watts_strogatz_graph(N,connections,0.25)
            for (x,y) in G.edges():
                G[x][y]['weight'] = random.random()

        if cfg.verbose: print "spring layout"
        self.Glayout = nx.spring_layout(G,weighted=False)
        colors = ['r' for node in G]
        
        self.G = G
        
        # give each agent a list of its neighbors
        for i in range(N):
            try:    agents[i].neighbors(list(itemgetter(*G.neighbors(i))(agents)),G[i])
            except TypeError as te:   
                    print "Error:",te
        
        if cfg.verbose: print "Initial layout"
        plt.ion()
        colors2 = range(len(G.edges()))
        wid = [d['weight']*5 for (x,y,d) in G.edges(data=True)]
        nx.draw(G,pos = self.Glayout,node_color=colors,font_color='w',width=wid) #edge_cmap=plt.cm.Blues, edge_color=colors2,
        plt.plot()
        #plt.show()
    
        if cfg.interactive: self.cmdpause()
    
    def run(self):
        cfg = self.cfg
        N = self.cfg.N
        agents = self.agents
        self.reward = cfg.reward
        self.rec = recorder(cfg.nturns)
        self.rec.limits['participation'] = (0,N)
        self.rec.limits['correct'] = (0,N)
        cmdpause = self.cmdpause
        simulation.pausenow = False
        
        class pausekey(threading.Thread):
            def __init__ (self):
                threading.Thread.__init__(self)
            def run(self):
                #global pausenow
                while True:
                    if simulation.pausenow: 
                        time.sleep(1); continue
                    k=raw_input()
                    if k=="p":
                        simulation.pausenow = True
                    if k=="k":
                        exit()
                        #raise SystemExit

        pauser = pausekey()
        pauser.daemon = True
        if not cfg.stepbystep:
            pauser.start()
        
        self.graphref = {}
        
        for t in range(cfg.nturns):
          try:
            for i in range(N):
                agents[i].play()
            for a in agents:
                if a.mymove:
                    if random.random() < a.skill:   # They got it right!
                        a.points = self.reward*a.mymove     #TODO: global + individual reward
                        a.correct = True
                    else:
                        a.points = 0
                        a.correct = False
                else:
                    a.points = 0
                    a.correct = None

            for a in agents:
                a.postprocess(a.points)
            
            if cfg.verbose: print "  t:",t#,"  part:",part[t],"  correct:",corr[t]
            
            self.logdata()
            if not cfg.graph_at_end:
                self.drawgraph()
                if not (t+1) % 5:
                    self.drawothergraphs()
            
            if simulation.pausenow or cfg.stepbystep:
                cmdpause()
                simulation.pausenow = False    
          except KeyboardInterrupt:
                cmdpause()
        
        # Simulation finished
        if configuration.graph_at_end:
            self.drawgraph()
            self.drawothergraphs()
        if cfg.interactive: cmdpause()

    
    def drawgraph(self):
        agents = self.agents
        G = self.G
        
        colors = [('b' if a.correct else 'r') if a.mymove else 'k' for a in agents]
        plt.figure(1)
        plt.clf()
        wid = [d['weight']**2*5 for (x,y,d) in G.edges(data=True)]
        nx.draw(G,pos = self.Glayout,node_color=colors, font_color='w',width=wid)#,edge_cmap=plt.cm.Blues,edge_color=ecolors)
        plt.draw()
        
    def drawothergraphs(self):
        for key, val in configuration.graph_on_figure.iteritems():
            if not val: continue
            record = self.rec.getrec(key)
            fig = plt.figure(val)
            if val not in self.graphref or not self.graphref[val]:
                plt.cla()
                #ax = fig.add_subplot(111)
                #ax.set_ylim(bottom=0)
                self.graphref[val] = True
            ax = fig.add_subplot(111)   
            #ax.plot(xrange(0,nturns,dpfreq), partav)
            ax.plot(smoothTriangle(record,5))
            (ymin, ymax) = self.rec.getlimits(key)
            if ymin is not None: ax.set_ylim(ymin = ymin)
            if ymax is not None: ax.set_ylim(ymax = ymax)
            #ax.set_ylim(bottom=0)
            #ax.set_ylim(0,self.N)  # it would be sooooper to set this
        #plt.ylim(ymin=0)
        for k in self.graphref: self.graphref[k] = False
        plt.draw()


    def logdata(self):
        # NEED TO DEVELOP CODE TO LOG RELEVANT DATA TO DATA STRUCTURE
        # includes participation, interest, % correct, reward per turn, cumulative reward
        part = 0
        correct = 0
        reward = 0
        for a in self.agents:
            part += a.mymove
            correct += (a.correct == True)
            reward += a.points
        self.rec.log('participation', part)
        self.rec.log('correct', correct)
        self.rec.log('reward', reward)
        self.rec.log('cumulative_reward', reward + self.rec.getlastrec('cumulative_reward'))
        
    def savegraphs(self, dt):
        graphs = configuration.graph_on_figure
        done = {}   # Keep track of which figures we've saved already so we don't get duplicates
        for data, fig in graphs.iteritems():
            if not fig or fig in done: continue
            picfile = "sim_" + dt + "_"+ data +".png"
            plt.figure(fig)
            plt.savefig(picfile, format="png")
            done[fig] = True
    
    
    
    def setreward(self,x):
        #global reward
        self.reward = x
        agent.globalreward = x
        for ag in self.agents:
            ag.newinfo = True

    def inspect(self, i):
        a = self.agents[i]
        a.printself()

    def cmdpause(self):
        inspect = self.inspect
        setreward = self.setreward
        cmd = " "
        while cmd != '':
            try:
                cmd = raw_input("Press ENTER to continue, or enter command: ")
                if cmd == 'step':
                    simulation.configuration.stepbystep = True
                elif cmd == 'nostep':
                    simulation.configuration.stepbystep = False
                else:
                    exec(cmd)
            except EOFError:
                print "END"
                exit()
                #raise SystemExit
            except Exception as strerror:
                print "Error in input:",strerror #,sys.exc_info()[0]
                pass


def smoothTriangle(data,degree,dropVals=False):
        """performs moving triangle smoothing with a variable degree."""
        """note that if dropVals is False, output length will be identical
        to input length, but with copies of data at the flanking regions"""
        triangle=np.array(range(degree)+[degree]+range(degree)[::-1], dtype=np.float)+1
        smoothed=[]
        for i in range(degree,len(data)-degree*2):
                point=data[i:i+len(triangle)]*triangle
                smoothed.append(sum(point)/sum(triangle))
        if dropVals: return smoothed
        smoothed=[smoothed[0]]*(degree+degree/2)+smoothed
        while len(smoothed)<len(data):smoothed.append(smoothed[-1])
        return smoothed
