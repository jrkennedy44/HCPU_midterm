#!/usr/bin/env python

"""
Manages jobs for specific programs to be launched in parallel on a cluster.
"""
import re
import os
import sys
import glob
import time

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepetUnit.commons.stat.Stat import Stat
from pyRepet.sql.RepetJobMySQL import Job
from pyRepet.launcher.programLauncher import programLauncher

#------------------------------------------------------------------------------

class Launcher:
    """
    Manages jobs for specific programs to be launched in parallel on a cluster.
    """
    
    def __init__( self, jobdb, query="", subject="", param="", cdir="",
                  tmpdir="", job_table="", queue="", groupid="", acro="X" ):
        """
        @param jobdb: RepetDB
        @type jobd: object
        @param query: directory containing files
        @type query: string
        @param subject: name of the file used as subject (if any)
        @type subject: string
        @param param: parameters to be passed to the command-line of the program
        @type param: string
        @param cdir: path to the current directory
        @type cdir: string
        @param tmpdir: path to the temporary directory
        @type tmpdir: string
        @param job_table: name of the table keeping track of the jobs
        @type job_table: string
        @param queue: name of the cluster queue under which the jobs will be launched
        @type queue: string
        @param groupid: identifier of the group under which all the jobs will be launched
        @type groupid: string
        @param acro: acronym
        @type acro: string
        """
        
        self.jobdb = jobdb
        self.query = query
        self.subject = subject
        self.parameter = param
        self.cdir = cdir
        self.tmpdir = tmpdir
        self.job_table = job_table
        self.groupid = groupid
        self.acronyme = acro
        
        self.queue, lResources = self.getQueueNameAndResources(queue)
        if lResources == []:
            #To have mem_free=1G:
            self.job = Job( tablename=self.job_table, queue=self.queue )
        else:
            self.job = Job( tablename=self.job_table, queue=self.queue, lResources=lResources )
            
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
        
        
    def cmd_start( self, inFileName ):
        """
        Command launching the program, thus specific of each program.
        """
        pass

    
    def cmd_test( self, job, newStatus, loop ):
        """
        Update the status of each job in the MySQL table.
        Used at the very beginning of each job ('running') and at the very end ('finished').
        Also used after retrieving the output value sent by the program to track 'error' if necessary.
        """
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
    
    
    def cmd_finish( self, inFileName ):
        """
        Command line to clean temporary files, thus specific of each program.
        """
        pass
    
    
    def beginRun( self ):
        """
        Check that everything is ok before launching a job.
        """
        if self.groupid == "":
            self.job.groupid = "%s_%s_%s" % ( self.query.rstrip("/").split("/")[-1],\
                                              self.acronyme,\
                                              self.subject.split("/")[-1] )
        else:
            self.job.groupid = self.groupid

        if self.jobdb.has_unfinished_job( self.job.tablename, self.job.groupid ):
            self.jobdb.wait_job_group( self.job.tablename, self.job.groupid )
            return
        
        self.jobdb.clean_job_group( self.job.tablename, self.job.groupid )
        
        string = "submitting job(s) with groupid '%s' (%s)" % ( self.job.groupid,  time.strftime("%Y-%m-%d %H:%M:%S") )
        print string; sys.stdout.flush()
        
        
    def run( self, pattern="*.fa", verbose=0 ):
        """
        Launch jobs in parallel on each file in the query directory.
        @param pattern: regular expression to find all files in the query directory on which the same job will be launched
        @type pattern: string
        """
        
        self.beginRun()
        
        minFreeGigaInTmpDir = 1
        
        lInFiles = glob.glob( self.query + "/" + pattern )
        lInFiles.sort()
        for inFileName in lInFiles:
            self._nbJobs += 1
            fileName = os.path.basename( inFileName )
            if verbose > 0:
                print "processing file '%s'" % ( inFileName )
                sys.stdout.flush()

            self.job.jobname = "%s%i" % ( self.acronyme, self._nbJobs )

            pid = str(os.getpid())
            now = time.localtime()
            pyFileName = self.cdir + "/ClusterLauncher_" + self.job.groupid + "_" +\
            self.job.jobname + "_" + str(now[0]) + "-" + str(now[1]) +\
            "-" + str(now[2]) + "_" + pid + ".py"
            pyFile = open( pyFileName, "w" )
            cmd = "#!/usr/bin/env python\n"
            cmd += "\n"
            cmd += "import os\n"
            cmd += "import sys\n"
            cmd += "import time\n"
            cmd += "\n"
            cmd += "print os.uname(); sys.stdout.flush()\n"
            cmd += "beginTime = time.time()\n"
            cmd += "print 'beginTime=%f' % ( beginTime )\n"
            cmd += "print \"work in dir '%s'\"\n" % ( self.tmpdir )
            cmd += "sys.stdout.flush()\n"
            cmd += "if not os.path.exists( \"%s\" ):\n" % ( self.tmpdir )
            cmd += "\tprint \"ERROR: temporary directory '%s' doesn't exist\"\n" % ( self.tmpdir )
            cmd += self.cmd_test( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "freeSpace = os.statvfs( \"%s\" )\n" % ( self.tmpdir )
            cmd += "if ( freeSpace.f_bavail * freeSpace.f_frsize ) / 1073741824.0 < %i:\n" % ( minFreeGigaInTmpDir ) # nb blocs * bloc size in bytes > 1 GigaByte ?
            cmd += "\tprint \"ERROR: less than %iGb in '%s'\"\n" % ( minFreeGigaInTmpDir, self.tmpdir )
            cmd += self.cmd_test( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "os.chdir( \"%s\" )\n" % ( self.tmpdir )
            cmd += "newDir = \"%s_%s_%s\"\n" % ( self.job.groupid, self.job.jobname, time.strftime("%Y%m%d-%H%M%S") )
            cmd += "if os.path.exists( newDir ):\n"
            cmd += "\tos.system( \"rm -r \" + newDir )\n"
            cmd += "os.mkdir( newDir )\n"
            cmd += "os.chdir( newDir )\n"
            cmd += self.cmd_test( self.job, "running", 0 )
            cmd += "if not os.path.exists( \"%s\" ):\n" % ( fileName )
            cmd += "\tos.symlink( \"%s\", \"%s\" )\n" % ( inFileName, fileName )
            if self.subject != "":
                cmd += "if not os.path.exists( \"%s\" ):\n" % ( os.path.basename(self.subject) )
                cmd += "\tos.symlink( \"%s\", \"%s\" )\n" % ( self.subject, os.path.basename(self.subject) )
            cmd += "\n"
            cmd += "print \"launch '%s'\"\n" % ( self.cmd_start( inFileName ) )
            cmd += "sys.stdout.flush()\n"
            cmd += "log = os.system ( \"%s\" )\n" % ( self.cmd_start( inFileName ) )
            cmd += "if log != 0:\n"
            cmd += "\tprint \"ERROR: job '%i' returned \" + str(log)\n" % ( self._nbJobs )
            cmd += "\tos.chdir( \"%s\" )\n" % ( self.tmpdir )
            cmd += "\tos.system( \"mv \" + newDir + \" %s\" )\n" % ( self.cdir )
            cmd += self.cmd_test( self.job, "error", 1 )
            cmd += "\tsys.exit(1)\n"
            cmd += "else:\n"
            cmd += "\tprint \"job '%i' finished successfully\"\n" % ( self._nbJobs )
            cmd += "\n"
            cmd += "if os.path.exists( \"%s\" ):\n" % ( fileName )
            cmd += "\tos.remove( \"%s\" )\n" % ( fileName )
            cmd += self.cmd_finish( inFileName )
            cmd += "\n"
            cmd += "os.chdir( \"..\" )\n"
            cmd += "os.system( \"rm -rf %s\" % ( newDir ) )\n"
            cmd += "\n"
            cmd += self.cmd_test( self.job, "finished", 0 )
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
            time.sleep( 0.5 )
            log = self.jobdb.submit_job( self.job, verbose )
            if log != 0:
                print "ERROR while submitting job to the cluster"
                sys.exit(1)
                
        self.endRun()
        
        
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
        cmd += self.cmd_test( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "freeSpace = os.statvfs( \"%s\" )\n" % ( self.tmpdir )
        cmd += "if ( freeSpace.f_bavail * freeSpace.f_frsize ) / 1073741824.0 < %i:\n" % ( minFreeGigaInTmpDir ) # nb blocs * bloc size in bytes > 1 GigaByte ?
        cmd += "\tprint \"ERROR: less than %iGb in '%s'\"\n" % ( minFreeGigaInTmpDir, self.tmpdir )
        cmd += self.cmd_test( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "os.chdir( \"" + self.tmpdir + "\" )\n"
        cmd += "newDir = \"%s_%s_%s\"\n" % ( self.job.groupid, self.job.jobname, time.strftime("%Y%m%d-%H%M%S") )
        cmd += "if os.path.exists( newDir ):\n"
        cmd += "\tos.system( \"rm -r \" + newDir )\n"
        cmd += "os.mkdir( newDir )\n"
        cmd += "os.chdir( newDir )\n"
        cmd += self.cmd_test( self.job, "running", 0 )
        cmd += cmd_start
        cmd += "if log != 0:\n"
        cmd += "\tprint \"ERROR: job returned \" + str(log)\n"
        cmd += "\tos.chdir( \"%s\" )\n" % ( self.tmpdir )
        cmd += "\tos.system( \"mv \" + newDir + \" %s\" )\n" % ( self.cdir )
        cmd += self.cmd_test( self.job, "error", 1 )
        cmd += "\tsys.exit(1)\n"
        cmd += "else:\n"
        cmd += "\tprint \"job finished successfully\"\n"
        cmd += cmd_finish
        cmd += "\n"
        cmd += "os.chdir( \"..\" )\n"
        cmd += "os.system( \"rm -rf %s\" % ( newDir ) )\n"
        cmd += "\n"
        cmd += self.cmd_test( self.job, "finished", 0 )
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
        log = self.jobdb.submit_job( self.job )
        if log != 0:
                print "ERROR while submitting job to the cluster"
                sys.exit(1)
                
                
    def endRun( self ):
        """
        Check that all the jobs are finished.
        """
        string = "waiting for %i job(s) with groupid '%s' (%s)" % ( self._nbJobs, self.job.groupid, time.strftime("%Y-%m-%d %H:%M:%S") )
        print string; sys.stdout.flush()
        self.jobdb.wait_job_group( self.job.tablename, self.job.groupid )
        if self._nbJobs > 1:
            string = "all jobs with groupid '%s' are finished (%s)" % ( self.job.groupid, time.strftime("%Y-%m-%d %H:%M:%S") )
            print string; sys.stdout.flush()
        statsExecutionTime = self.getStatsOfExecutionTime()
        if self._nbJobs > 1:
            print "execution time of all jobs (seconds): %f" % statsExecutionTime.getSum()
        print "execution time per job: %s" % statsExecutionTime.string()
        sys.stdout.flush()
        self.jobdb.clean_job_group( self.job.tablename, self.job.groupid )
        
        
    def clean( self, acronyme="", stdout=True, stderr=True ):
        """
        Remove the temporary data used to launch the jobs and keep track of them.
        @param acronyme: useful when using runSingleJob() several times with different acronymes but the same groupid
        @type: string
        """
        # remove the python files used to launch the jobs in parallel
        if acronyme == "":
            cmd = "find . -name \"ClusterLauncher*%s*.py\" -exec rm {} \;" % ( self.acronyme )
        else:
            cmd = "find . -name \"ClusterLauncher*%s*.py\" -exec rm {} \;" % ( acronyme )
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing python scripts used on cluster nodes"
            sys.exit(1)

        # remove the stdout of each individual jobs
        if stdout:
            if acronyme == "":
                cmd = "find . -name \"%s*.o*\" -exec rm {} \;" % ( self.acronyme )
            else:
                cmd = "find . -name \"%s*.o*\" -exec rm {} \;" % ( acronyme )
            log = os.system( cmd )
            if log != 0:
                print "ERROR while removing stdout from jobs"
                sys.exit(1)

        # remove the stderr of each individual jobs
        if stderr:
            if acronyme == "":
                cmd = "find . -name \"%s*.e*\" -exec rm {} \;" % ( self.acronyme )
            else:
                cmd = "find . -name \"%s*.e*\" -exec rm {} \;" % ( acronyme )
            log = os.system( cmd )
            if log != 0:
                print "ERROR while removing stderr from jobs"
                sys.exit(1)
                
                
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

#------------------------------------------------------------------------------

class BlasterLauncher( Launcher ):
    """
    Specific launcher for Blaster (pairwise alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Blaster"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -q %s" % ( fileName )
        cmd += " -s %s" % ( os.path.basename(self.subject) )
        cmd += " -B %s" % ( fileName )
        cmd += " %s" % ( self.parameter )
        return cmd
    
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if os.path.exists( \"%s.Nstretch.map\" ):\n" % ( fileName )
        cmd += "\tos.remove( \"%s.Nstretch.map\" )\n" % ( fileName )
        
        cmd += "if os.path.exists( \"%s_cut\" ):\n" % ( fileName )
        cmd += "\tos.remove( \"%s_cut\" )\n" % ( fileName )
        
        cmd += "if os.path.exists( \"%s.raw\" ):\n" % ( fileName )
        cmd += "\tos.remove( \"%s.raw\" )\n" % ( fileName )
        
        cmd += "if os.path.exists( \"%s.seq_treated\" ):\n" % ( fileName )
        cmd += "\tos.remove( \"%s.seq_treated\" )\n" % ( fileName )
        
        cmd += "if not os.path.exists( \"%s/%s.align\" ):\n" % ( self.cdir, fileName )
        cmd += "\tos.system( \"mv %s.align %s\" )\n" % ( fileName, self.cdir )
        
        cmd += "if not os.path.exists( \"%s/%s.param\" ):\n" % ( self.cdir, fileName )
        cmd += "\tos.system( \"mv %s.param %s\" )\n" % ( fileName, self.cdir )
        
        return cmd
    
#------------------------------------------------------------------------------

class MatcherLauncher( Launcher ):
    """
    Specific launcher for Matcher (match connection and filtering).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Matcher"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
        
    def cmd_start( self, inFileName ):
        prg = os.environ["REPET_PATH"] + "/bin/matcher"
        cmd = prg
        cmd += " -m %s" % ( inFileName )
        cmd += " %s" % ( self.parameter )
        return cmd
    
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        s = ".clean_match"
        if "-a" in self.parameter:
            s = ".match"
            
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + s + ".path\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + s + ".path " + self.cdir + "\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + s + ".map\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + s + ".map " + self.cdir + "\" )\n"
        
        if "-q" in self.parameter and "-s" in self.parameter:
            cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + s + ".tab\" ):\n"
            cmd += "\tos.system( \"mv " + fileName + s + ".tab " + self.cdir + "\" )\n"
            
        return cmd

#------------------------------------------------------------------------------

class RMLauncher( Launcher ):
    """
    Specific launcher for RepeatMasker (pairwise alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="RM"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = "RepeatMasker"
        cmd = prg
        cmd += " " + self.parameter
        cmd += " -dir ."
        cmd += " -pa 1 -gccalc -no_is -nolow"
        cmd += " -lib " + os.path.basename(self.subject)
        cmd += " " + fileName
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if not os.path.exists( \"" + fileName + ".cat\" ):\n"
        cmd += "\tprint \"RepeatMasker didn't find any match\"\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".cat\" ):\n"
        #cmd += "\tos.system( \"ProcessRepeats " + fileName + ".cat\" )\n"
        cmd += "\tos.system( \"" + os.environ["REPET_PATH"] + "/bin/RMcat2align.py -i " + fileName + ".cat\" )\n"
        cmd += "\tif not os.path.exists( \"" + self.cdir + "/" + fileName + ".cat.align\" ):\n"
        cmd += "\t\tos.system( \"mv " + fileName + ".cat.align " + self.cdir + "\" )\n"
        cmd += "\tif not os.path.exists( \"" + self.cdir + "/" + fileName + ".cat\" ):\n"
        cmd += "\t\tos.system( \"mv " + fileName + ".cat " + self.cdir + "\" )\n"
##        cmd += "\tos.remove( \"" + fileName + ".cat\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".stderr\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".stderr\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".tbl\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".tbl\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".ori.out\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".ori.out\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".masked\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".masked\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".out\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".out\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".log\" ):\n"
        cmd += "\tos.remove( \"" + fileName + ".log\" )\n"
        
        return cmd
    
#------------------------------------------------------------------------------

class RMSSRLauncher( Launcher ):
    """
    Specific launcher for RepeatMasker to detect SSRs.
    """
    
    def __init__(self,jobdb,query="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="RMSSR"):
        Launcher.__init__(self,jobdb,query,"",param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = "RepeatMasker"
        cmd = prg
        cmd += " " + self.parameter
        cmd += " -dir ."
        cmd += " -pa 1 -gccalc -no_is -int"
        cmd += " " + fileName
        return cmd

    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if not os.path.exists( \"" + fileName + ".cat\" ):\n"
        cmd += "\tprint \"RepeatMasker didn't find any match\"\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".cat\" ):\n"
        cmd += "\tos.system( \"" + os.environ["REPET_PATH"] + "/bin/RMcat2path.py -i " + fileName + ".cat\" )\n"
        cmd += "\tos.system( \"mv " + fileName + ".cat.path " + fileName + "." + self.acronyme + ".path\" )\n"
        cmd += "\tif not os.path.exists( \"" + self.cdir + "/" + fileName + "." + self.acronyme + ".path\" ):\n"
        cmd += "\t\tos.system( \"mv " + fileName + "." + self.acronyme + ".path " + self.cdir + "\" )\n"
        cmd += "\t\tos.system( \"mv " + fileName + ".cat " + self.cdir + "\" )\n"
##        cmd += "\tos.system( \"rm " + fileName + ".cat\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".stderr\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".stderr\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".tbl\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".tbl\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".out\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".out\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".masked\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".masked\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".log\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".log\" )\n"
        
        return cmd

#------------------------------------------------------------------------------

class CensorLauncher( Launcher ):
    """
    Specific launcher for Censor (pairwise alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="CEN"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = "censor"
        cmd = prg
        cmd += " %s" % ( fileName )
        cmd += " -debug"
        cmd += " -lib %s" % ( os.path.basename(self.subject) )
        if self.parameter != "":
            cmd += " %s" % ( self.parameter )
        cmd += " -bprm '-cpus 1'"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if not os.path.exists( \"" + fileName + ".map\" ):\n"
        cmd += "\tprint \"Censor didn't find any match\"\n"
        
        cmd += "elif os.path.exists( \"" + fileName + ".map\" ):\n"
        cmd += "\tos.system( \"" + os.environ["REPET_PATH"] + "/bin/CENmap2align.py -i " + fileName + ".map\" )\n"
        
        cmd += "\tif not os.path.exists( \"" + self.cdir + "/" + fileName + ".map\" ):\n"
        cmd += "\t\tos.system( \"mv " + fileName + ".map " + self.cdir + "\" )\n"
        
        cmd += "\tif not os.path.exists( \"" + self.cdir + "/" + fileName + ".map.align\" ):\n"
        cmd += "\t\tos.system( \"mv " + fileName + ".map.align " + self.cdir + "\" )\n"
        
        cmd += "\tos.system( \"rm censor.*.log\" )\n"
        
##        cmd += "if os.path.exists( \"" + fileName + ".map\" ):\n"
##        cmd += "\tos.system( \"rm " + fileName + ".map\" ) \n"
        
        cmd += "if os.path.exists( \"" + fileName + ".aln\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".aln\" ) \n"
        
        cmd += "if os.path.exists( \"" + fileName + ".idx\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".idx\" ) \n"
        
        cmd += "if os.path.exists( \"" + fileName + ".found\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".found\" ) \n"
        
        cmd += "if os.path.exists( \"" + fileName + ".masked\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".masked\" ) \n"
        
        cmd += "if os.path.exists( \"" + fileName + ".tab\" ):\n"
        cmd += "\tos.system( \"rm " + fileName + ".tab\" ) \n"
        
        return cmd

#------------------------------------------------------------------------------

class PalsLauncher( Launcher ):
    """
    Specific launcher for Pals (pairwise alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Pals"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = "pals"
        cmd = prg
        cmd += " -query %s" % ( fileName )
        cmd += " -target %s" % ( os.path.basename(self.subject) )
        cmd += " -out %s.%s.gff" % ( fileName, self.acronyme )
        if self.parameter != "":
            cmd += " %s" % ( self.parameter )
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + "."+ self.acronyme + ".gff\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + "."+ self.acronyme + ".gff " + self.cdir + "\" )\n"
        return cmd

#------------------------------------------------------------------------------

class TRFLauncher( Launcher ):
    """
    Specific launcher for TRF (micro-satellite detection).
    """
    
    def __init__(self,jobdb,query="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="TRF"):
        Launcher.__init__(self,jobdb,query,"",param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchTRF.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        cmd += " -c"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".TRF.set\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".TRF.set " + self.cdir + "\" )\n"
        return cmd
    
#------------------------------------------------------------------------------

class MrepsLauncher( Launcher ):
    """
    Specific launcher for Mreps (micro-satellite detection).
    """
    
    def __init__(self,jobdb,query="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Mreps"):
        Launcher.__init__(self,jobdb,query,"",param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchMreps.py"
        cmd = prg
        cmd += " -i " + fileName
        cmd += " -c"
        return cmd

    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".Mreps.set\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".Mreps.set " + self.cdir + "\" )\n"
        return cmd

#------------------------------------------------------------------------------

class MapLauncher( Launcher ):
    """
    Specific launcher for MAP (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Map"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):        
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchMap.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        cmd += " -o %s.fa_aln" % ( fileName )
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):        
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        return cmd

#------------------------------------------------------------------------------

class RefalignLauncher( Launcher ):
    """
    Specific launcher for Refalign (master-slave multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Refalign"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchRefalign.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        if self.parameter != "":
            cmd += " %s" % ( self.parameter )
        cmd += " -o %s.fa_aln" % ( fileName )
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        return cmd
    
#------------------------------------------------------------------------------

class MafftLauncher( Launcher ):
    """
    Specific launcher for Mafft (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Mafft"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchMafft.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        cmd += " -o %s.fa_aln" % ( fileName )
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        return cmd
    
#------------------------------------------------------------------------------

class TcoffeeLauncher( Launcher ):
    """
    Specific launcher for T-Coffee (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Tcoffee"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchTCoffee.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        cmd += " -o %s.fa_aln" % ( fileName )
        if self.parameter != "":
            cmd += " -P '%s'" % ( self.parameter)
        cmd += " -c"
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if os.path.exists( \"" + fileName.split(".fa")[0] + ".dnd\" ):\n"
        cmd += "\tos.system( \"rm -f " + fileName.split(".fa")[0] + ".dnd\" )\n"
        
        cmd += "if os.path.exists( \"" + fileName + ".fa_aln.html\" ):\n"
        cmd += "\tos.system( \"rm -f " + fileName + ".fa_aln.html\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        
        return cmd
    
#------------------------------------------------------------------------------

class MuscleLauncher( Launcher ):
    """
    Specific launcher for Muscle (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Muscle"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        pL = programLauncher( fileName )
        cmd = pL.launchMuscle( outFileName=inFileName+".fa_aln", run="no" )
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if os.path.exists( \"" + fileName + ".dnd\" ):\n"
        cmd += "\tos.system( \"rm -f " + fileName + ".dnd\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        
        return cmd
    
#------------------------------------------------------------------------------

class PrankLauncher( Launcher ):
    """
    Specific launcher for Prank (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Prank"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        prg = os.environ["REPET_PATH"] + "/bin/launchPrank.py"
        cmd = prg
        cmd += " -i %s" % ( fileName )
        cmd += " -o %s.fa_aln" % ( fileName )
        cmd += " -P '%s'" % ( self.parameter )
        cmd += " -c"
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "os.system( \"mv %s.fa_aln.2.fas %s.fa_aln\" )\n" % ( fileName, fileName )
        
        cmd += "if os.path.exists( \"" + fileName + ".fa_aln.1.fas\" ):\n"
        cmd += "\tos.system( \"rm -f " + fileName + ".fa_aln.1.fas\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        
        return cmd
    
#------------------------------------------------------------------------------

class ClustalwLauncher( Launcher ):
    """
    Specific launcher for Clustal-W (multiple alignment).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Clustalw"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        pL = programLauncher( fileName )
        cmd = pL.launchClustalw( outFileName=inFileName+".fa_aln", run="no" )
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = ""
        
        cmd += "if os.path.exists( \"" + fileName.split(".fa")[0] + ".dnd\" ):\n"
        cmd += "\tos.system( \"rm -f " + fileName.split(".fa")[0] + ".dnd\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + ".fa_aln\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + ".fa_aln " + self.cdir + "\" )\n"
        
        return cmd
    
#------------------------------------------------------------------------------

class LucyLauncher( Launcher ):
    """
    Deprecated.
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="Lucy"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        prg = os.environ["REPET_PATH"] + "/bin/lucy_tim.py"
        cmd = prg
        cmd += " -i " + inFileName
        cmd += " " + self.parameter
        return cmd
    
    def cmd_finish( self, inFileName ):
        family_dir = inFileName.split(".fa")[0]
        cmd = "os.system( \"cat " + family_dir +\
                     "/seqs_oriented.log >> Lucy_seqs_oriented.log\" )\n"
        cmd += "os.system( \"rm " + family_dir +\
                      "/seqs_oriented.log\" )\n"
        return cmd
    
#------------------------------------------------------------------------------

class HmmpfamLauncher ( Launcher ):
    """
    Specific launcher for HMMER (for HMM profils).
    """
    
    def __init__( self, jobDb, params ):
        self.jobdb = jobDb
        self.params = params
        self.query = params["query"]
        self.job_table = params["job_table"]
        self.queue = params["queue"]
        self.groupid = params["groupid"]
        self.job = Job( self.job_table, "?", "?", self.queue,"?", "?" )
        self.acronyme = "Hmmpfam"
        self.tmpdir = self.params["tmpDir"]
        self.cdir = self.params["cDir"]
        
    def cmd_start(self, inFileName):
        fileName = os.path.basename( inFileName )
        prg = "hmmpfam"
        cmd = prg
        cmd += " " + self.params["param"]
        cmd += " " + self.params["profilDB"]
        cmd += " " + fileName
        cmd += " > " + self.params["outputDir"] + "/" + fileName + ".hmmpfamOut"
        return cmd
    
    def cmd_finish ( self, inFileName ):
        cmd = ""
        return cmd
    
    
class HmmpfamAndParse2alignLauncher ( HmmpfamLauncher ):
    
    def cmd_finish (self, inFileName):
        fileName = os.path.basename( inFileName )
        cmd = ""
        cmd += "os.system( \"" + self.params["scriptToLaunch"] + " -i " + self.params["outputDir"] + "/" + fileName + ".hmmpfamOut -o " + self.params["outputDir"] + "/" + fileName + ".hmmpfamOut.align -c\" )\n"
        return cmd
    
#------------------------------------------------------------------------------

class PhyMlLauncher( Launcher ):
    """
    Specific launcher for PhyML (phylogeny).
    """
    
    def __init__(self,jobdb,query="",subject="",param="",cdir="",tmpdir="",job_table="",queue="",groupid="",acro="PhyMl"):
        Launcher.__init__(self,jobdb,query,subject,param,cdir,tmpdir,job_table,queue,groupid,acro)
        
    def cmd_start( self, inFileName ):
        fileName = os.path.basename( inFileName )
        cmd = os.environ["REPET_PATH"] + "/bin/launchPhyML.py"
        cmd += " -i %s" % ( fileName )
        cmd += " -c"
        cmd += " -v 1"
        return cmd
    
    def cmd_finish( self, inFileName ):
        fileName = os.path.basename( inFileName )
        
        cmd = ""
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + "_phyml.newick\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + "_phyml.newick " + self.cdir + "\" )\n"    
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + "_phyml_tree.txt\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + "_phyml_tree.txt " + self.cdir + "\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + "_phyml_lk.txt\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + "_phyml_lk.txt " + self.cdir + "\" )\n"
        
        cmd += "if not os.path.exists( \"" + self.cdir + "/" + fileName + "_phyml_stat.txt\" ):\n"
        cmd += "\tos.system( \"mv " + fileName + "_phyml_stat.txt " + self.cdir + "\" )\n"
        
        return cmd
