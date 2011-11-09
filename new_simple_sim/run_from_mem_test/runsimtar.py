import sys
import tarfile as tar

### Make sure that you only run this with trusted tarballs - it calls a lot of unprotected execs.

if len(sys.argv) < 2:
    print("Please pass the filename of a tar archived simulation to run")
    sys.exit()
    
tarfilename = sys.argv[1]

tfile = tar.open(tarfilename)

files = tfile.getnames()      # Or could be getmembers
filedict = {}
runfile = None
for filename in files:
    if filename == 'run.py':
        runfile = tfile.extractfile(filename)
    else:
        memfile = tfile.extractfile(filename)   # Extract the file as an in-memory file object
        filedict[filename] = memfile

for filename, memfile in filedict.iteritems():
    exec(

# make a tmp directory

# unzip the tar
#   We may be able to run without unzipping using the extractfile() operator

# find "run.py"

# run run.py, but specify to not log data. (maybe run.py does this automatically)
#  (run.py is auto-generated and just runs the main simulator py (specified in run.py). This lets us do things like run multiple sims at once)


# remove temporary files
