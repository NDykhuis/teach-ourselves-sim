import sys
from simsocial_crec import simulation, configuration, agent
from ast import literal_eval as evalsafe

# Load configuration
config = None
if len(sys.argv) > 1:
    filename = sys.argv[1]
    f = open(filename, 'r')
    params = evalsafe(f.read())
    simcfg = params[0]
    agentcfg = params[1]
    f.close()
    agent.initconfig(agentcfg)
    #simulation.setconfig(simcfg)
    config = simcfg

from time import strftime
dt = strftime("%Y-%m-%d_%H:%M:%S")
        
# Initialize simulation
sim = simulation(config)
sim.dt = dt
sim.setup()

# Run simulation
sim.run()

# Save configuration
from pprint import pprint as pp

cfgfile = "sim_" + dt + ".cfg"
f = open(cfgfile, "w")

agentcfg = agent.getconfig()
simcfg = sim.getconfig()
cfgtuple = (simcfg, agentcfg)

pp(cfgtuple, f)
f.close()

sim.savegraphs(dt)
