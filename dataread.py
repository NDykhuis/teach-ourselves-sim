from ast import literal_eval as evalsafe
import sys
from matplotlib import pyplot as plt

datafilename = sys.argv[1]
datafile = open(datafilename, 'r')
print "Reading data"
data = evalsafe(datafile.read())
datafile.close()

#data = evalsafe(strdata)

# filename format:  data_2011-10-06_19:20:30.csv
# filename format:  sim_2011-10-06_19:21:53.cfg

print "Reading configuration"
cfgfilename = 'sim_'+datafilename[5:-4]+'.cfg'
cfgfile = open(cfgfilename, 'r')
params = evalsafe(cfgfile.read())
simcfg = params[0]
agentcfg = params[1]
cfgfile.close()


# Rearrange data
print "Rearranging data"

agentdata = {}
for agentid in range(simcfg['N']):
    # dataline = (timestep, a.aid, a.mymove, a.correct, a.points, numnbr, nbrpart, nbrcorr)
    atuples = [line for line in data if line[1]==agentid]
    adata = {}
    adata['tuples'] = atuples
    adata['move'] = [line[2] for line in atuples]
    adata['correct'] = [line[3] for line in atuples]
    adata['points'] = [line[4] for line in atuples]
    numnbr = atuples[1][5];                     adata['numnbr'] = numnbr
    nbrpart = [line[6] for line in atuples];    adata['nbrpart'] = nbrpart
    nbrcorr = [line[7] for line in atuples];    adata['nbrcorr'] = nbrcorr
    if numnbr: 
        adata['pctnbr'] = [npart/numnbr for npart in nbrpart]
        adata['pctcorr'] = [ncorr/numnbr for ncorr in nbrcorr]
    else:      
        adata['pctnbr'] = [0 for i in xrange(len(nbrpart))]
        adata['pctcorr'] = [0 for i in xrange(len(nbrpart))]
    
    # Use slice operator to get a sliding window!
    
    agentdata[agentid] = adata

try:
    if simcfg['outputagents']:
        print "Reading agents"
        # (aid, skill, interest, E, I, S, (friends))
        afile = open(simcfg['agentfile'],'r')
        agentuples = evalsafe(afile.read())
        for a in agentuples:
            ag = agentdata[a[0]]
            ag['skill'] = a[1]
            ag['interest'] = a[2]
            ag['E'] = a[3]
            ag['I'] = a[4]
            ag['S'] = a[5]
            ag['friends'] = a[6]
except NameError, KeyError:
    agents = None

    
plt.ion()
def plot(aid, dvalue):
    plt.plot(agentdata[aid][dvalue])
    plt.show()
def inspect(aid):
    print '(aid, skill, interest, E, I, S, (friends))'
    atuple = [a for a in agentuples if a[0] == aid][0]
    printuple = [round(v,2) for v in atuple[1:-1]]
    printuple.append(atuple[-1])
    print printuple
    
# Make a terminal    
cmd = " "
while cmd != 'exit':
    try:
        cmd = raw_input(">>> ")
        exec(cmd)
    except EOFError:
        print "END"
        exit()
    except Exception as strerror:
        print "Error in input:",strerror #,sys.exc_info()[0]
        pass

