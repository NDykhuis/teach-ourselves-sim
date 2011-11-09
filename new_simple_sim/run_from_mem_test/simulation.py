import matplotlib.pyplot as plt
from operator import itemgetter
import numpy as np
import threading
import time
from time import strftime
import networkx as nx
import os

# For our files, check if they've already been imported
try:                configuration
except NameError:   from configuration import configuration
try:                recorder
except NameError:   from recorder import recorder
try:                agent
except NameError:   from agents import *

# Class that handles pausing the simulation
class pausekey(threading.Thread):
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            if simulation.pausenow: time.sleep(1); continue
            k=raw_input()
            if k=="p":    simulation.pausenow = True
            if k=="k":    exit()


class simulation:
    def __init__(self, config=None):
        self.cfg = configuration()  # init default configuration
        if config is not None:
            self.setconfig(config)  # set configuration from file
        agent.idc = 0               # initialize agent id counter
        
    def setup(self):        # creates agents and social network
        cfg = self.cfg
        N = self.cfg.N
        
        rs = random.getstate()        # to restore afterward, if we want
        self.seed()

        if cfg.agenttype == 'random':
            agents = [agent() for i in range(0,N)]
        self.agents = agents
        
        self.create_graph()
        G = self.G
        colors = ['r' for node in G]

        if cfg.verbose: print "Initial layout"
        plt.ion()
        colors2 = range(len(G.edges()))
        wid = [d['weight']*5 for (x,y,d) in G.edges(data=True)]
        nx.draw(G,pos = self.Glayout,node_color=colors,font_color='w',width=wid) #edge_cmap=plt.cm.Blues, edge_color=colors2,
        plt.plot()
    
        if cfg.outputdata:
            if not self.dt:
                self.dt = strftime("%Y-%m-%d_%H:%M:%S")
            self.datafilename = 'data_'+self.dt+'.dat'
            self.datafile = open(self.datafilename,'w')  # for simple dumping of raw data
            self.datafile.write("(\n")

        if cfg.interactive: self.cmdpause()
                
    def run(self):          # iterates through timesteps, calling play() on each agent, postprocess(), and gathering statistics
        cfg = self.cfg
        N = self.cfg.N
        agents = self.agents
        self.reward = cfg.reward
        self.rec = recorder(cfg.nturns)
        self.rec.limits['participation'] = (0,N)
        self.rec.limits['correct'] = (0,N)
        cmdpause = self.cmdpause
        simulation.pausenow = False

        # Start the pause listener
        pauser = pausekey()
        pauser.daemon = True
        if not cfg.stepbystep:
            pauser.start()

        self.graphref = {}      # Used in drawothergraphs

        for t in range(cfg.nturns):
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
            
            self.logdata(t)
            if not cfg.graph_only_at_end:
                self.drawgraph()
                if not (t+1) % 5:
                    self.drawothergraphs()
            
            if simulation.pausenow or cfg.stepbystep:
                cmdpause()
                simulation.pausenow = False    


    def save_results(self): # saves graphs of the run and all python scripts in a tar  
                        # this should pass a list of files up to the simulator, and the simulator can take care of zipping them.
        cfg = self.cfg

        returnfiles = [os.path.basename(__file__), "agents.py", "agentcfg.py", "configuration.py", "recorder.py"]
        
        # Simulation finished
        if cfg.outputagents:
            self.dumpagents()
            returnfiles.append(self.cfg.agentfile)
        if cfg.outputdata: 
            self.datafile.write(')')
            self.datafile.close()
            returnfiles.append(self.datafilename)
        if configuration.graph_only_at_end:
            self.drawgraph()
            self.drawothergraphs()

        if cfg.interactive: self.cmdpause()
        
        graphfiles =  self.savegraphs(self.dt) 
        if graphfiles:
            returnfiles.extend(graphfiles)
    
        # Save graph to [somegraphfilename].png
        return returnfiles
        
        
        
        
        
        
        
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

    def create_graph(self):
        cfg = self.cfg; N = self.cfg.N
        agents = self.agents
        
        # Generate graph
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

    def setreward(self,x):
        #global reward
        self.reward = x
        agent.globalreward = x

    def cmdpause(self): # Pause and ask for a command
        #inspect = self.inspect
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
                
    def drawgraph(self):
        agents = self.agents
        G = self.G
        
        colors = [('b' if a.correct else 'r') if a.mymove else 'k' for a in agents]
        plt.figure(1)
        plt.clf()
        #wid = [d['weight']**2*5 for (x,y,d) in G.edges(data=True)]
        #nx.draw(G,pos = self.Glayout,node_color=colors, font_color='w',width=wid)#,edge_cmap=plt.cm.Blues,edge_color=ecolors)
        nx.draw(G,pos = self.Glayout,node_color=colors, font_color='w')
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
            ax.plot(smoothTriangle(record,3))
            (ymin, ymax) = self.rec.getlimits(key)
            if ymin is not None: ax.set_ylim(ymin = ymin)
            if ymax is not None: ax.set_ylim(ymax = ymax)
            #ax.set_ylim(bottom=0)
            #ax.set_ylim(0,self.N)  # it would be sooooper to set this
        #plt.ylim(ymin=0)
        for k in self.graphref: self.graphref[k] = False
        plt.draw()


    def logdata(self, timestep):
        part = 0
        correct = 0
        reward = 0
        for a in self.agents:
            part += a.mymove
            correct += (a.correct == True)
            reward += a.points
            
            #[t, mymove, correct, points, numfriends, numfriendspart, success]

            numnbr = len(a.nbrs)
            nbrmoves = [nbr.correct for nbr in a.nbrs if nbr.correct is not None]
            nbrpart = len(nbrmoves)#float(sum(nbr.mymove for nbr in a.nbrs))
            nbrcorr = sum(nbrmoves)
            #if nbrpart:
            #    pctfriends = nbrpart/numfriends
            #else:  pctfriends = -1
        
            # Simple data recording for future use
            if self.cfg.outputdata:
                dataline = (timestep, a.aid, a.mymove, a.correct, a.points, numnbr, nbrpart, nbrcorr)
                self.datafile.write(str(dataline)+',\n')
            
        self.rec.log('participation', part)
        self.rec.log('correct', correct)
        self.rec.log('reward', reward)
        self.rec.log('cumulative_reward', reward + self.rec.getlastrec('cumulative_reward'))
        


    def savegraphs(self, dt):
        graphs = configuration.graph_on_figure
        graphfiles = []
        done = {}   # Keep track of which figures we've saved already so we don't get duplicates
        for data, fig in graphs.iteritems():
            if not fig or fig in done: continue
            picfile = "sim_" + dt + "_"+ data +".png"
            plt.figure(fig)
            plt.savefig(picfile, format="png")
            done[fig] = True
            graphfiles.append(picfile)
        return graphfiles
    
    def dumpagents(self):
        # (aid, skill, interest, E, I, S, (friends))
        #afile = open('agents_'+self.dt+'.dat')
        afile = open(self.cfg.agentfile, 'w')
        afile.write('(')
        for a in self.agents:
            nbrtuple = tuple([n.aid for n in a.nbrs])
            agentuple = \
                (a.aid, round(a.skill,3), round(a.interest,3), round(a.weights[0],3), round(a.weights[1],3), round(a.weights[2],3), nbrtuple)
            afile.write(str(agentuple)+',\n')
        afile.write(')')
        afile.close()

# from http://www.swharden.com/blog/2010-06-20-smoothing-window-data-averaging-in-python-moving-triangle-tecnique/
def smoothTriangle(data,degree,dropVals=False):
    """performs moving triangle smoothing with a variable degree."""
    """note that if dropVals is False, output length will be identical
    to input length, but with copies of data at the flanking regions"""
    triangle=np.array(range(degree)+[degree]+range(degree)[::-1])+1
    smoothed=[]
    for i in range(degree,len(data)-degree*2):
            point=data[i:i+len(triangle)]*triangle
            smoothed.append(sum(point)/sum(triangle))
    if dropVals: return smoothed
    smoothed=[smoothed[0]]*(degree+degree/2)+smoothed
    while len(smoothed)<len(data):smoothed.append(smoothed[-1])
    return smoothed
