import os
import re
import sys
import time
import glob
from pyRepetUnit.commons.sql.Job import Job
from pyRepetUnit.commons.stat.Stat import Stat
from pyRepet.launcher.Launcher import Launcher
from repet_tools.CleanClusterNodesAfterRepet import CleanClusterNodesAfterRepet

class Launcher(Launcher):
    
    def __init__( self, jobdb, query="", subject="", param="", cdir="",
                  tmpdir="", job_table="", queue="", groupid="", acro="X" ):

        self.jobdb = jobdb
        self.query = query
        self.subject = subject
        self.parameter = param
        self.cdir = cdir
        self.tmpdir = tmpdir
        self.jobTable = job_table
        self.groupid = groupid
        self.acronyme = acro
        
        self.queue, lResources = self.getQueueNameAndResources(queue)
        if lResources == []:
            #To have mem_free=1G:
            self.job = Job( tablename=self.jobTable, queue=self.queue )
        else:
            self.job = Job( tablename=self.jobTable, queue=self.queue, lResources=lResources )
            
        self._nbJobs = 0
        
    def getQueueNameAndResources(self, configQueue):
        tokens = configQueue.replace("'","").split(" ")
        queueName = ""
        lResources = []
        if tokens[0] != "":
            if re.match(".*\.q", tokens[0]):
                queueName = tokens[0]
                lResources = tokens[1:]
            else:
                lResources = tokens
        return queueName, lResources

    def createGroupidIfItNotExist(self):
        if self.groupid == "":
            self.job.groupid = "%s_%s_%s" % (self.query.rstrip("/").split("/")[-1], self.acronyme, 
                self.subject.split("/")[-1])
        else:
            self.job.groupid = self.groupid

    def beginRun( self ):
        self.createGroupidIfItNotExist()

        if self.jobdb.hasUnfinishedJob(self.job.tablename, self.job.groupid):
            self.jobdb.waitJobGroup(self.job.tablename, self.job.groupid)
        else:
            self.jobdb.cleanJobGroup( self.job.tablename, self.job.groupid )

    def runSingleJob( self, cmd_start, cmd_finish="" ):
        """
        Launch one job in parallel.
        @param cmd_start: command-line for the job to be launched
        @type cmd_start: string
        @param cmd_finish: command to retrieve result files and remove temporary files
        @type cmd_finish: string
        @warning: the jobname has to be defined outside from this method
        """
        self._nbJobs = 1
        pid = str(os.getpid())
        now = time.localtime()
        pyFileName = self.cdir + "/ClusterLauncher_" + self.job.groupid + "_" +\
                     self.job.jobname + "_" + str(now[0]) + "-" + str(now[1]) +\
                     "-" + str(now[2]) + "_" + pid + ".py"
        
        pyFile = open( pyFileName, "w" )
        minFreeGigaInTmpDir = 1
        cmd = "#!/usr/bin/env python\n"
        cmd += "\n"
        cmd += "import os\n"
        cmd += "import sys\n"
        cmd += "import time\n"
        cmd += "import shutil\n"
        cmd += "\n"
        cmd += "print os.uname()\n"
        cmd += "beginTime = time.time()\n"
        cmd += "print 'beginTime=%f' % ( beginTime )\n"
        cmd += "print \"work in dir '%s'\"\n" % ( self.tmpdir )
        cmd += "sys.stdout.flush()\n"
        cmd += "if not os.path.exists( \"%s\" ):\n" % ( self.tmpdir )
        cmd += "\tprint \"ERROR: temporary directory '%s' doesn't exist\"\n" % ( self.tmpdir )
        cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "freeSpace = os.statvfs( \"%s\" )\n" % ( self.tmpdir )
        cmd += "if ( freeSpace.f_bavail * freeSpace.f_frsize ) / 1073741824.0 < %i:\n" % ( minFreeGigaInTmpDir ) # nb blocs * bloc size in bytes > 1 GigaByte ?
        cmd += "\tprint \"ERROR: less than %iGb in '%s'\"\n" % ( minFreeGigaInTmpDir, self.tmpdir )
        cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "os.chdir( \"" + self.tmpdir + "\" )\n"
        cmd += "newDir = \"%s_%s_%s\"\n" % ( self.job.groupid, self.job.jobname, time.strftime("%Y%m%d-%H%M%S") )
        cmd += "if os.path.exists( newDir ):\n"
        cmd += "\tos.system( \"rm -r \" + newDir )\n"
        cmd += "os.mkdir( newDir )\n"
        cmd += "os.chdir( newDir )\n"
        cmd += self.writeSrptChangeJobStatusCmd( self.job, "running", 0 )
        cmd += cmd_start
        cmd += "if log != 0:\n"
        cmd += "\tprint \"ERROR: job returned \" + str(log)\n"
        cmd += "\tos.chdir( \"%s\" )\n" % ( self.tmpdir )
        cmd += "\tos.system( \"mv \" + newDir + \" %s\" )\n" % ( self.cdir )
        cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "else:\n"
        cmd += "\tprint \"job finished successfully\"\n"
        cmd += cmd_finish
        cmd += "\n"
        cmd += "os.chdir( \"..\" )\n"
        cmd += "os.system( \"rm -rf %s\" % ( newDir ) )\n"
        cmd += "\n"
        cmd += self.writeSrptChangeJobStatusCmd( self.job, "finished", 0 )
        cmd += "\n"
        cmd += "endTime = time.time()\n"
        cmd += "print 'endTime=%f' % ( endTime)\n"
        cmd += "print 'executionTime=%f' % ( endTime - beginTime )\n"
        cmd += "print os.uname()\n"
        pyFile.write( cmd )
        pyFile.close()
        os.system( "chmod go-rwx " + pyFileName )
        os.system( "chmod u+x " + pyFileName )
        
        self.job.command = pyFileName
        self.job.launcher = pyFileName
        
        string = "submitting job(s) with groupid '%s' (%s)" % ( self.job.groupid,  time.strftime("%Y-%m-%d %H:%M:%S") )
        print string
        sys.stdout.flush()
        log = self.jobdb.submitJob( self.job )
        if log != 0:
            print "ERROR while submitting job to the cluster"
            sys.exit(1)
    
    #TODO: to remove ?
    def runArrayJob( self, directory, lCmdStart, lCmdFinish=[] ):
        """
        Launch one job in parallel with SGE array.
        @param cmd_start: command-line for the job to be launched
        @type cmd_start: string
        @param cmd_finish: command to retrieve result files and remove temporary files
        @type cmd_finish: string
        @warning: the jobname has to be defined outside from this method
        """
        self._nbJobs = 0
        jobId = 0
        
        directoryShell = directory
        directoryPythonScripts = "%s/%s" % (directory, self.job.groupid)
        os.mkdir(directoryPythonScripts)
        
        for thisCmdStart in lCmdStart:
            cmdStart = thisCmdStart
            if lCmdFinish != [] or lCmdFinish[self._nbJobs] != '':
                cmdFinish = lCmdFinish[self._nbJobs]
            else:
                cmdFinish = ''
            self._nbJobs = self._nbJobs + 1
                
            pyFileName = "%s/launchJob_%s.py" % (directoryPythonScripts, self._nbJobs)
            pyFile = open(pyFileName, "w")
            minFreeGigaInTmpDir = 1
            
            cmd = "#!/usr/bin/env python\n"
            cmd += "\n"
            cmd += "import os\n"
            cmd += "import sys\n"
            cmd += "import time\n"
            cmd += "import shutil\n"
            cmd += "\n"
            cmd += "print os.uname()\n"
            cmd += "beginTime = time.time()\n"
            cmd += "print 'beginTime=%f' % ( beginTime )\n"
            cmd += "print \"work in dir '%s'\"\n" % ( self.tmpdir )
            cmd += "sys.stdout.flush()\n"
            cmd += "if not os.path.exists( \"%s\" ):\n" % ( self.tmpdir )
            cmd += "\tprint \"ERROR: temporary directory '%s' doesn't exist\"\n" % ( self.tmpdir )
            cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "freeSpace = os.statvfs( \"%s\" )\n" % ( self.tmpdir )
            cmd += "if ( freeSpace.f_bavail * freeSpace.f_frsize ) / 1073741824.0 < %i:\n" % ( minFreeGigaInTmpDir ) # nb blocs * bloc size in bytes > 1 GigaByte ?
            cmd += "\tprint \"ERROR: less than %iGb in '%s'\"\n" % ( minFreeGigaInTmpDir, self.tmpdir )
            cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "os.chdir( \"" + self.tmpdir + "\" )\n"
            cmd += "newDir = \"%s_%s_%s\"\n" % ( self.job.groupid, self.job.jobname, time.strftime("%Y%m%d-%H%M%S") )
            cmd += "if os.path.exists( newDir ):\n"
            cmd += "\tos.system( \"rm -r \" + newDir )\n"
            cmd += "os.mkdir( newDir )\n"
            cmd += "os.chdir( newDir )\n"
            cmd += self.writeSrptChangeJobStatusCmd( self.job, "running", 0 )
            cmd += cmdStart
            cmd += "if log != 0:\n"
            cmd += "\tprint \"ERROR: job returned \" + str(log)\n"
            cmd += "\tos.chdir( \"%s\" )\n" % ( self.tmpdir )
            cmd += "\tos.system( \"mv \" + newDir + \" %s\" )\n" % ( self.cdir )
            cmd += self.writeSrptChangeJobStatusCmd( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "else:\n"
            cmd += "\tprint \"job finished successfully\"\n"
            cmd += cmdFinish
            cmd += "\n"
            cmd += "os.chdir( \"..\" )\n"
            cmd += "os.system( \"rm -rf %s\" % ( newDir ) )\n"
            cmd += "\n"
            cmd += self.writeSrptChangeJobStatusCmd( self.job, "finished", 0 )
            cmd += "\n"
            cmd += "endTime = time.time()\n"
            cmd += "print 'endTime=%f' % ( endTime)\n"
            cmd += "print 'executionTime=%f' % ( endTime - beginTime )\n"
            
            pyFile.write(cmd)
            pyFile.close()
            os.system("chmod go-rwx " + pyFileName)
            os.system("chmod u+x " + pyFileName)
            
        scriptName = '%s.sh' % (self.groupid)
        self.createLauncherRunSingleJobSGEArray(scriptName, directoryShell, directoryPythonScripts, jobId)
        os.system("chmod go-rwx " + directoryShell + scriptName)
        os.system("chmod u+x " + directoryShell + scriptName)
        self.job.launcher = scriptName
        
        string = "submitting job(s) with groupid '%s' (%s)" % ( self.job.groupid,  time.strftime("%Y-%m-%d %H:%M:%S") )
        print string; sys.stdout.flush()
        log = self.jobdb.submitArrayJob( self._nbJobs, self.job )
        if log != 0:
                print "ERROR while submitting job to the cluster"
        
#        self.cleanRunArrayjob(lWorkingDir)
    
    def createLauncherRunSingleJobSGEArray(self, scriptName, directoryScript, directoryPython, maxJobId):
        shTemplate = "#!/bin/sh\n#$ -S /bin/sh\n"
        launcherFileName = '%s/%s' % (directoryScript, scriptName)
        launcherFile = open(launcherFileName, 'w')
        launcherFile.write(shTemplate)
        launcherFile.write("\n")
        launcherFile.write("python %s/launchJob_$SGE_TASK_ID.py\n" % (directoryPython))
        launcherFile.close()
        
    def writeSrptChangeJobStatusCmd( self, job, newStatus, loop ):
        if loop == 0:
            cmd_test = "os.system( \""
        elif loop == 1:
            cmd_test = "\tos.system( \""
        cmd_test += os.environ["REPET_PATH"] + "/bin/srptChangeJobStatus.py"
        cmd_test += " -t " + job.tablename
        if str(job.jobid).isdigit():
            cmd_test += " -j " + job.jobname
        else:
            cmd_test += " -j " + job.jobid
        cmd_test += " -g " + job.groupid
        if job.queue != "":
            cmd_test += " -q " + job.queue
        cmd_test += " -s " + newStatus
        if self.jobdb.host != "":
            cmd_test += " -H " + self.jobdb.host
        if self.jobdb.user != "":
            cmd_test += " -U " + self.jobdb.user
        if self.jobdb.passwd != "":
            cmd_test += " -P " + self.jobdb.passwd
        cmd_test += " -D " + self.jobdb.dbname
        cmd_test += " -T %i" % ( self.jobdb.port )
        cmd_test += " -v %i" % ( 1 )
        cmd_test += "\" )\n"
        return cmd_test
    
    def endRun( self, cleanNodes = False ):
        string = "waiting for %i job(s) with groupid '%s' (%s)" % ( self._nbJobs, self.job.groupid, time.strftime("%Y-%m-%d %H:%M:%S") )
        print string; sys.stdout.flush()
        self.jobdb.waitJobGroup( self.job.tablename, self.job.groupid )
        if self._nbJobs > 1:
            string = "all jobs with groupid '%s' are finished (%s)" % ( self.job.groupid, time.strftime("%Y-%m-%d %H:%M:%S") )
            print string; sys.stdout.flush()

        if cleanNodes:
            self.cleanNodes()
            
        statsExecutionTime = self.getStatsOfExecutionTime()
        if self._nbJobs > 1:
            print "execution time of all jobs (seconds): %f" % statsExecutionTime.getSum()
        print "execution time per job: %s" % statsExecutionTime.string()
        sys.stdout.flush()
        self.jobdb.cleanJobGroup( self.job.tablename, self.job.groupid )
        
    def getStatsOfExecutionTime( self, acronyme="" ):
        stat = Stat()
        if acronyme == "":
            pattern = "%s*.o*" % self.acronyme
        else:
            pattern = "%s*.o*" % acronyme
        lJobFiles = glob.glob( pattern )
        for f in lJobFiles:
            fH = open( f, "r" )
            while True:
                line = fH.readline()
                if line == "":
                    break
                if "executionTime" in line:
                    stat.add( float(line[:-1].split("=")[1] ) )
                    break
            fH.close()
        return stat     

    def clean( self, acronyme = "", stdout = True, stderr = True ):
        lFileToRemove = []
        if acronyme == "":
            acronyme = self.acronyme  
        pattern = "ClusterLauncher*%s*.py" % ( acronyme )
        lFileToRemove.extend(glob.glob( pattern ))
        if stdout:
            pattern = "%s*.o*" % ( acronyme )
            lFileToRemove.extend(glob.glob( pattern ))        
        if stderr:
            pattern = "%s*.e*" % ( acronyme )
            lFileToRemove.extend(glob.glob( pattern ))                   
        
        for file in lFileToRemove:
            os.remove(file)
    
    #TODO: handle of nodesMustBeCleaned => class attribute ?
    def runLauncherForMultipleJobs(self, acronymPrefix, lCmdsTuples, cleanMustBeDone = True, nodesMustBeCleaned = False):
        self.beginRun()
        count = 0
        for cmdsTuple in lCmdsTuples:
            count += 1
            self.acronyme = "%s_%s" % (acronymPrefix, count)
            self.job.jobname = self.acronyme
            self.runSingleJob(cmdsTuple[0], cmdsTuple[1])
        self.acronyme = acronymPrefix
        self.endRun(nodesMustBeCleaned)
        if cleanMustBeDone:
            self.clean("%s_" % acronymPrefix)
        self.jobdb.close()

    def prepareCommands(self, lCmds, lCmdStart = [], lCmdFinish = []):
        cmd_start = ""
        for cmd in lCmdStart:
            cmd_start += "%s\n" % (cmd)
        for cmd in lCmds:
            cmd_start += "%s\n" % (cmd)
        cmd_finish = ""
        for cmd in lCmdFinish:
            cmd_finish += "%s\n" % (cmd)
        return (cmd_start,  cmd_finish)
    
    def getSystemCommand(self, prg, lArgs):
        systemCmd = "log = os.system( \"" + prg 
        for arg in lArgs:
            systemCmd += " " + arg
        systemCmd += "\" )"
        return systemCmd

    def cleanNodes(self):
        iCleanClusterNodeAfterRepet = CleanClusterNodesAfterRepet()
        iCleanClusterNodeAfterRepet.setLNodes(self.jobdb.getNodesListByGroupId(self.jobTable, self.groupid))
        iCleanClusterNodeAfterRepet.setTempDirectory(self.tmpdir)
        iCleanClusterNodeAfterRepet.setPattern("%s*" % self.groupid)
        iCleanClusterNodeAfterRepet.run()
