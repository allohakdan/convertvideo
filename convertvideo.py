#!/usr/bin/python
# convertvideo.py
# [db] 2013.03.06 
#
# Converts videos on OSX using HandBreakCLI in parallel, optimizing for the number of cores
#
# INSTALLING:
# 1) Download HandBreak and HandBreakCLI - BOTH
# 2) Rename covertvideo.py to convertvideo.command
# 3) Use your favorite text editor to change the parameters NUM_IDLE_CORES and VIDEO_EXT
#
# USAGE:
# 1) Place all the videos you wish to convert into a single directory
# 2) Drop convertvideo.command into the directory containing the videos 
# 3) Double click convertvideo.command to execute
#
# TODO:
# Could be easily be converted to work on linux (just change the get_num_cores command)
#

NUM_IDLE_CORES = 1
handbrake_params = "--preset=\"Normal\""

# Copyright (c) 2013, Dan Brooks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import subprocess
import threading
import os
import time
import sys

def get_num_cores():
    if sys.platform == "linux" or sys.platform == "linux2":
        # LINUX
        output, err = call("nproc")
        if len(output) > 0 and len(output[0]) > 0:
            return int(output[0][0])
    else:
        # DARWIN
        output, err = call("sysctl -a")
        for l in output:
            if "machdep.cpu.core_count:" in l:
                return int(l[1])

class ProcessThread(threading.Thread):
    def set_target(self,path):
        self.path = path
    def run(self):
        print "Starting Thread for %s"%self.path
        output, _ = call('HandBrakeCLI -i "%s" -o "%s" %s'%(self.path,ofile,handbrake_params))
        print "Thread finished for %s"%self.path


def call(cmd):
    p = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = p.communicate()
    lines = out.split("\n")
    linesplits = list()
    for l in lines:
        linesplits.append(l.split())
    return linesplits, err

class Spinner():
    def __init__(self):
        self.__blip = "|"
    def spin(self):
        p = { "|": "/",
              "/": "-",
              "-": "\\",
              "\\": "|"}
        self.__blip = p[self.__blip]
        print "\b\b"+self.__blip,
        sys.stdout.flush()


if __name__ == "__main__":
    cores = get_num_cores() - NUM_IDLE_CORES
    location = os.path.dirname(os.path.abspath(__file__))
    print "Coverting video in %s"%location
    print "Using %d cores"%cores
    
    # Get files
    files =  os.listdir(location)
    files = filter(lambda x: x[-3:] == VIDEO_EXT,files)
    print "Found %d videos"%len(files)

    # Use full path
    files = [location+"/"+f for f in files]

    spinner = Spinner()
    threadlock = threading.Lock()
    threads = list() 
    for i in range(1,len(files)+1):
        with threadlock:
            while True:
                # Calculate number of working threads
                waitcount = 0
                for t in threads:
                    if t.is_alive():
                        waitcount+=1
                if waitcount < cores:
                    print ""
                    print "There are %d working threads. Adding Thread for video %d of %d (%s)"%(waitcount,i,len(files),files[i-1])
                    threads.append(ProcessThread())
                    threads[-1].set_target(files[i-1])
                    threads[-1].start()
                    break
                else:
                    time.sleep(1)
                    spinner.spin()

    print "Waiting for remaining threads to finish"
    for t in threads:
        while t.is_alive():
            time.sleep(1)
            spinner.spin()
    print "FINISHED!"
