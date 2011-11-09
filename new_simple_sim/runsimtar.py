import os
import sys
import tarfile as tar

### Make sure that you only run this with trusted tarballs - it calls unprotected exec.

if len(sys.argv) < 2:
    print("Please pass the filename of a tar archived simulation to run")
    sys.exit()
    
tarfilename = sys.argv[1]

tfile = tar.open(tarfilename)

base = tarfilename[0:-7]

# make a tmp directory
temppath = base+"_temp"
os.mkdir(temppath)

# unzip the tar
#   We may be able to run without unzipping using the extractfile() operator
tfile.extractall(path=temppath)
tfile.close()

# find "run.py"
os.chdir(temppath)

try:
    execfile("run.py")
except Exception as e:
    print "There was an exception in execution:"
    print e
else:
    print "Simulation complete"
    
# run run.py, but specify to not log data. (maybe run.py does this automatically)
#  (run.py is auto-generated and just runs the main simulator py (specified in run.py). This lets us do things like run multiple sims at once)

raw_input("Press ENTER to end program and clean up temp files")

# remove temporary files
os.chdir("..")
#os.rmdir(temppath)
