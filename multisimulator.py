import sys
from simsocial_c import simulation, configuration, agent
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
        
# Initialize simulation
dt = strftime("%Y-%m-%d_%H:%M:%S")

# Run simulation
seeds = [341, 341, 67, 934, 123]
for seed in seeds:
    print "Simulating with seed", seed
    sim = simulation(config)
    sim.dt = dt+'_'+str(seed)
    sim.cfg.interactive = False
    sim.cfg.verbose = False
    sim.cfg.randseed = seed
    sim.setup()
    sim.run()
    # Grab data from sim
    print "Cumulative reward:", sim.rec.getlastrec('cumulative_reward')
    

# Save configuration
from time import strftime
from pprint import pprint as pp

cfgfile = "sim_" + dt + ".cfg"
f = open(cfgfile, "w")

agentcfg = agent.getconfig()
simcfg = sim.getconfig()
cfgtuple = (simcfg, agentcfg)

pp(cfgtuple, f)
f.close()

sim.savegraphs(dt)
