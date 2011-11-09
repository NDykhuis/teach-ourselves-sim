import sys
from ast import literal_eval as evalsafe
import tarfile
import os
from time import strftime
from pprint import pprint as pp

from simulation import simulation, configuration, agent

saveconfig = False

def run(saveresults, config=None):
    dt = strftime("%Y-%m-%d_%H:%M:%S")

    # Initialize simulation
    sim = simulation(config)
    sim.dt = dt
    sim.setup()

    # Run simulation
    sim.run()

    if saveresults:     # Do not run this section on simulation replay

        # Save configuration
        if saveconfig:
            cfgfile = "sim_" + dt + ".cfg"
            f = open(cfgfile, "w")

            agentcfg = agent.getconfig()
            simcfg = sim.getconfig()
            cfgtuple = (simcfg, agentcfg)

            pp(cfgtuple, f)
            f.close()

        # Generate run.py
        runfile = open("run.py", "w")
        runstr = "import "+os.path.basename(__file__)[0:-3]+" as sim\n"
        runstr += "sim.run(saveresults=False)\n"
        runfile.write(runstr)
        runfile.close()

        # Compile a list of files to be zipped up
        filelist = []
        if saveconfig:
            filelist.append(cfgfile)
        simfiles = sim.save_results()
        filelist.extend(simfiles)
        filelist.append("run.py")
        filelist.append(os.path.basename(__file__))

        # Zip up the archive
        tarfilename = "sim_"+dt+".tar.gz"
        tar = tarfile.open(tarfilename, "w:gz")
        for filename in filelist:
            tar.add(filename)
        tar.close()
        print "Zipped results to "+tarfilename
        
        # Remove all of the data files?

if __name__ == '__main__':
    print "Running simulation"
    
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

    run(saveresults=True, config = config)
    
    print "End of simulation"
