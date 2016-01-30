#!/usr/bin/env python
import os
import sys
from subprocess import Popen, PIPE

REMOTE_BASE_DIR = '/home1/irteam/Code/'


def main(projectName):

    remoteDir = REMOTE_BASE_DIR + projectName
    cmd = 'cd "%s" && git status -s' % (remoteDir)
    print "cmd:%s" % cmd
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out = p.stdout.readlines()
    for line in out:
        line = line.strip()
        print 'process file info:%s' % line
        array = line.split()
        operator = array[0]
        if operator == 'M' or operator == 'D':
            #Modified or add file
            filename = array[1]
            
            cmd = 'cd "%s" && git checkout "%s"' % (remoteDir, filename)
            print '*** command:%s' % cmd
            os.system(cmd)

        elif operator == 'C' or operator == 'U' or operator == 'A' or operator == 'R':
            print "can not support %s command" % operator
            return
        else:
            #add new file
            filename = array[1]
            
            cmd = 'cd "%s" && rm "%s"' % (remoteDir, filename)
            print '*** command:%s' % cmd
            os.system(cmd)

def usage():
    print 'usage: pyrestore.py Project-Name'
    return

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        usage()
        sys.exit()
        
    main(sys.argv[1])