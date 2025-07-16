import subprocess
import tempfile
import json
import os

def getInstalledPackagesJson()-> list[dict]:
    cmd = ["dnf", "repoquery", "--installed",  "--qf", "{\"epoch\":\"%{EPOCH}\",\"name\":\"%{NAME}\",\"version\":\"%{VERSION}\",\"release\":\"%{RELEASE}\",\"arch\":\"%{ARCH}\",\"repo\":\"%{repoid}\"}\\n"]

    fname = tempfile.mktemp()

    f = open(fname,'wb')

    res = subprocess.run(cmd, stdout=f)    


    f.close()

    if res.returncode!=0:
        os.remove(tempfile)
        raise OSError("dnf repoquery command returned an error")
    
    f = open(fname,'rb')

    jstrings = f.readlines()

    f.close()
    os.remove(fname)

    jstring ="["+ (','.join ([i.decode() for i in jstrings])) + "]"

    obj = json.loads(jstring)

    return obj

if __name__=="__main__":
    j = getInstalledPackagesJson()
    print(j)