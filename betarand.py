from scipy.stats import beta
import numpy as np
import random

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
    a,b = getbeta(mode,beta)
    return random.betavariate(a,b)

def plotbeta(a,b):
    import matplotlib.pyplot as plt
    x = np.arange(0,200)/200.0
    y = beta.pdf(x,a,b)

    print "max:",np.argmax(y)/200.0

    #plt.ion()
    plt.plot(x,y)
    plt.show()

