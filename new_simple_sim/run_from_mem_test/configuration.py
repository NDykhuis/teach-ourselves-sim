# Check if agent class has been defined already
try: 
    agent
except NameError:
    from agents import agent

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

    SIMILARITY_GRAPH = 1        # Add friends by similarity, or random small-world graph?
    RND_CON = 1                 # Random number of connections
    SOC_CON = 0                 # num of connections based on social weight
    SHUFFLE = 10                # number of edges to shuffle on the similarity graph
    
    randseed = 1365
    
    agenttype = 'random'        # Also accepts 'high_low_mix', 'high_low_cross'
    
    # Key is what variable, value is what figure to plot it on
    graph_on_figure = { 'participation':2, 'correct':2, 'interest':False, 'reward':False, 'cumulative_reward':False }  
    graph_only_at_end = False         # Generate graphs only at the end of the sim
    
    outputdata = False              # Outputs all events in the simulation run
    outputagents = False            # Outputs parameters of all the agents
    agentfile = 'agents_'+agenttype+str(randseed)+'.dat'

