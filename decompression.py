import subprocess
import tempfile
import shutil
import os

# derived from a gpt solution in the main packagedump file.
# cleaned code up considerably and standardized.


class utilityoptions:
    def __init__(self, 
                 command:str,
                 extenstion:str, 
                 outputoption:str=None, 
                 otheroption:str=None, 
                 redirect:bool=False,
                 package:str=None):
        
        self.Command = command
        self.Extension = extenstion
        self.OuputOption = outputoption
        self.OtherOption = otheroption
        self.Redirect = redirect
        self.Package = package
        

# Compression utilities
ZCK_CMD = "unzck"
ZST_CMD = "unzstd"
GZ_CMD = "gunzip"  # handled by Python gzip module

# refereence this for extension
# https://chatgpt.com/c/68700c47-b2bc-800a-a4f7-1e949082fe7e
# define the subprocess calls here
# fucking z always had eyes on MY FUCKING PROJECTS.
extensions = {

                'gz': utilityoptions( GZ_CMD,'gz',None,'-c', True, 'gzip'),
                'zck': utilityoptions(ZCK_CMD, 'zck',None,'-c',True,'zcunk'),
                'zst': utilityoptions(ZST_CMD, 'zst','-o',"-f",False,'zstd')
            }



def decompress_to_temp(file_path:str):
    uto = None

    for ext in extensions:

        if file_path.endswith(ext):
            uto = extensions[ext]
            break
    
    if uto is None:
        raise ValueError(f"Compression Format Unknown\nPlease implement a handler for this file: {file_path}")

    if not shutil.which(uto.Command):
        raise ValueError(f"Compression command not available, install {uto.Package}")
    
    temp = tempfile.NamedTemporaryFile(delete=False)

    cmd = [uto.Command, f"\"{file_path}\""]

    if uto.OtherOption:
        cmd.append(uto.OtherOption)
    
    if uto.OuputOption:
        cmd.append(uto.OuputOption)
        cmd.append(f"\"{temp.name}\"")

    if uto.Redirect:
        cmd.append(">")
        cmd.append(f"\"{temp.name}\"")

    shcmd = " ".join(cmd)

    result = subprocess.run(shcmd,shell=True)

    if result.returncode != 0:
        raise OSError("decompression command failed.")

    if os.path.exists(temp.name):
        return temp.name
    else:
        raise OSError("for some reason the file does not exist")


if (__name__=="__main__"):
    
    projectpath = os.path.dirname(__file__)
    testdatapath = os.path.join(projectpath,'unittestdata')

    for dirname, dirnams, filenames in os.walk(testdatapath):

        for f in filenames:
            print(f"decompressing test: {f}")
            fname = decompress_to_temp(os.path.join(dirname, f))
            print(fname)


    

