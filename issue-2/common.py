import os
import subprocess
import re
def recursive_find(address, approvedlist, cond_function = os.path.isfile, find_parent_folder = False):
    filelist = os.listdir(address)
    for i in range(0, len(filelist)):
        filelist[i] = os.path.join(address, filelist[i])

    for filename in filelist:
        if os.path.isdir(filename):
            recursive_find(filename, approvedlist, cond_function, find_parent_folder)
    
    for filename in filelist:
        if cond_function(filename):
            if find_parent_folder:
                approvedlist.append(address)
                break
            else:
                approvedlist.append(filename)
def RunExe(arg_list, stderr_file, stdout_file,log:list, env_vars=None):
    # print(str(arg_list))
    out_text = ""
    for a in arg_list:
        has_ws = False
        for ch in a:
            if ch.isspace():
                has_ws = True
                break
        if has_ws:
            out_text += "\"{}\" ".format(a)
        else:
            out_text += "{} ".format(a)
    print(out_text)

    curr_env = os.environ.copy()
    if env_vars is not None:
        if type(env_vars) == dict:
            for key, v in env_vars.items():
                if key in curr_env:
                    curr_env[key] += ":{}".format(v)
                else:
                    curr_env[key] = v

    proc = subprocess.run(arg_list, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=curr_env)
    _error = proc.stderr
    if len(stderr_file) != 0:
        WriteStringToFile(stderr_file, _error.decode("ascii"))
        # print( _error.decode("ascii"))
    _output = proc.stdout
    if len(stdout_file) != 0:
        WriteStringToFile(stdout_file, _output.decode("ascii"))
    log.extend(re.split("\n",  _error.decode("ascii")))
    return proc.returncode
def WriteStringToFile(file_name, content, append = False):
    if append:
        text_file = open(file_name, "a")
    else:
        text_file = open(file_name, "w")
    n = text_file.write(content)
    text_file.close()
