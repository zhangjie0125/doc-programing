import ftplib
import os
import socket
import sys
from subprocess import Popen, PIPE

HOST = '10.113.171.161'
PORT = 2121
USER = 'irteam'
PASSWD = 'irteam'

LOCAL_BASE_DIR = 'D:/Code/'
REMOTE_BASE_DIR = '/home1/irteam/Code/'

GIT_CMD='D:/Program Files/Git/bin/git.exe'
CONVERT_CMD='D:/Tools/dos2unix-7.3.2-win64/bin/dos2unix.exe'

class FtpClient:
    __host = ''
    __port = -1
    __user = ''
    __passwd = ''
    __isConnected = 0;
    __projectName = ''
    
    def __init__(self, host, port, user, passwd, projectName):
        self.__host = host
        self.__port = port
        self.__user = user
        self.__passwd = passwd
        self.__projectName = projectName
        
    def connect(self):
        if self.__isConnected == 0:
            self.ftp=ftplib.FTP()
        
            self.ftp.connect(self.__host, self.__port)
            print '*** Connected to host "%s"' % self.__host

            self.ftp.login(self.__user, self.__passwd)
            print '*** Logged in'
            
            self.__isConnected = 1
            
        return
        
    def upload(self, fullfilePath):
        if self.__isConnected == 1:
            filePath = os.path.dirname(fullfilePath)
            filename = os.path.basename(fullfilePath)
        
            remotePath = REMOTE_BASE_DIR + '/' + self.__projectName + '/' + filePath

            self.ftp.cwd(remotePath)
            print '*** Changed to "%s" folder' % remotePath
            
            isOpenFile = False
            unixFormatFullFilePath = ''
                
            try:
                localFullFilePath = os.path.join(LOCAL_BASE_DIR, self.__projectName, fullfilePath)
                localFullFilePath = os.path.normpath(localFullFilePath)
                
                #convert file format to unix
                unixFormatFullFilePath = self.__convertFileFormat(localFullFilePath)
                
                file_handler = open( unixFormatFullFilePath, "rb" )
                isOpenFile = True
                
                print '*** Prepare to upload "%s" in "%s"' % (fullfilePath, remotePath)
                self.ftp.storbinary('STOR %s' % filename, file_handler, 4096)
            finally:
                if isOpenFile:
                    file_handler.close()
                if unixFormatFullFilePath != '':
                    os.system('del %s' % unixFormatFullFilePath)

            print '*** Uploaded "%s" in "%s"' % (localFullFilePath, remotePath)

        
    def delete(self, fullfilePath):
        if self.__isConnected == 1:
            remotePath = REMOTE_BASE_DIR + '/' + self.__projectName

            self.ftp.cwd(remotePath)
            print '*** Changed to "%s" folder' % remotePath
            
            print '*** Prepare to delete "%s" in "%s"' % (fullfilePath, remotePath)
            self.ftp.delete(fullfilePath)
            
            print '*** Deleted "%s" in "%s"' % (fullfilePath, remotePath)

        
    def disconnect(self):
        if self.__isConnected == 1:
            self.ftp.quit()
            
    def __convertFileFormat(self, filePath):
        localFullFilePath = os.path.join(LOCAL_BASE_DIR, self.__projectName, filePath)
        localFullFilePath = os.path.normpath(localFullFilePath)
        newLocalFullFilePath = localFullFilePath + '.tempunixformat'
        
        cmd = '"%s" -k -n "%s" "%s"' % (CONVERT_CMD, localFullFilePath, newLocalFullFilePath)
        print '*** Execute convert command:%s' % (cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out = p.stdout.readlines()
        for line in out:
            line = line.strip()
            print '****** Output:%s' % line

        return newLocalFullFilePath
        

def getLocalModifiedFileList(projectName):
    list = []
    localDir = os.path.join(LOCAL_BASE_DIR, projectName)
    cmd = 'cd /d "%s" & "%s" status -s' % (localDir, GIT_CMD)
    print "cmd:%s" % cmd
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out = p.stdout.readlines()
    for line in out:
        line = line.strip()
        #ignore .cproject file
        if line.find('.cproject') != -1:
            continue
        list.append(line)
        
    print "Total modified %d files!" % len(list)
    index = 0
    for onefile in list:
        index = index + 1
        print '%3d: %s' % (index, onefile)
    return list
    
    
def processModifiedFileList(projectName, list):
    if (len(list) == 0):
        return
        
    print 'Begin to process modified files!'
    
    
    try:    
        #connect to linux ftp
        ftp = FtpClient(HOST, PORT, USER, PASSWD, projectName)
        ftp.connect()
        
        for fileInfo in list:
            array = fileInfo.split()
            operator = array[0]
            
            print 'process file info: %s' % fileInfo

            if operator == 'M' or operator == 'A':
                #Modified or add file
                filename = array[1]
                
                #upload this file
                ftp.upload(filename)
                    
            elif operator == 'D':
                #delete file
                filename = array[1]
                
                #delete file
                try:
                    ftp.delete(filename)
                except (ftplib.error_reply, ftplib.error_perm),e:
                    print '*** File "%s" is already deleted. Reason:%s' % (filename, e)

            elif operator == 'R':
                #rename file
                oldfilePath = array[1]
                newfilePath = array[3]
                
                #delete old file
                try:
                    ftp.delete(oldfilePath)
                except (ftplib.error_reply, ftplib.error_perm),e:
                    print '*** File "%s" is already deleted. Reason:%s' % (oldfilePath, e)
                
                #upload new file
                ftp.upload(newfilePath)

            elif operator == 'C' or operator == 'U':
                print "can not support %s command" % operator
                return
            else:
                #add new file
                filename = array[1]
                
                #upload this file
                ftp.upload(filename)

    except (socket.error, socket.gaierror), e:
        #ftp connect failed
        print 'ERROR: cannot reach "%s"' % HOST
        return
    except ftplib.error_reply:
        #ftp login failed
        print 'ERROR: login failed with "%s" and "%s"' % (USER, PASSWD)
        return
    except ftplib.error_perm:
        #ftp operator failed
        print 'Error: failed for ftp operator'
        return
    finally:
        ftp.disconnect()
    
    
    print 'Success to process modified files!'

def main(projectName):
    modifiedFileList = getLocalModifiedFileList(projectName)
    
    processModifiedFileList(projectName, modifiedFileList)
    
    
def usage():
    print 'usage: pyftp.py Project-Name'
    return

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        usage()
        sys.exit()
        
    main(sys.argv[1])