#!/usr/bin/env python

# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


import glob
import stat
import shutil

from pyRepet.launcher.AbstractProgramLauncher import *
from pyRepet.sql.RepetJobMySQL import Job
from pyRepet.sql.RepetJobMySQL import RepetJob
from pyRepetUnit.commons.checker.CheckerException import CheckerException
from pyRepetUnit.commons.utils.FileUtils import FileUtils
from pyRepetUnit.commons.stat.Stat import Stat


GENERIC_IN_FILE = "zDUMMYz"


## Abstract class to launch a program in parallel on a cluster.
#
#
class AbstractClusterLauncher( object ):
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inputDir = ""            # path to the directory with input files
        self._queueName = ""           # name of the queue on the cluster
        self._groupId = ""             # identifier of the group of jobs (groupid)
        self._inputFileSuffix = "fa"   # suffix of the input files (default='fa')
        self._prgAcronym = ""          # acronym of the program to launch
        self._configFile = ""          # name of the configuration file (connect to MySQL)
        self._currentDir = os.getcwd() # path to the current directory
        self._tmpDir = ""              # path to the temporary directory
        self._jobTable = "jobs"        # name of the table recording the jobs
        self._catOutFiles = False      # concatenate output files of all jobs
        self._clean = False            # clean job file, job stdout, job table...
        self._verbose = 1              # verbosity level
        self.jobdb = None              # RepetJob instance
        self.job = Job()               # Job instance
        self._nbJobs = 0
        
        self._cmdLineGenericOptions = "hi:Q:g:S:a:C:d:j:Zcv:"
        self._cmdLineSpecificOptions = ""
        
        self._exeWrapper = "AbstractProgramLauncher.py"
        self._prgLauncher = AbstractProgramLauncher()
        
        # list of instances derived from AbstractProgramLauncher()
        # If several program are launched successively in the same job,
        # 'lPrgLaunchers' has to be filled before run().
        self.lPrgLaunchers = []
        
        
    def getGenericHelpAsString( self ):
        """
        Return the generic help as a string.
        """
        string = ""
        string += "usage: %s.py [options]" % ( type(self).__name__ )
        string += "\ngeneric options:"
        string += "\n     -h: this help"
        string += "\n     -i: directory with input files (absolute path)"
        string += "\n     -Q: needed resources on the cluster"
        string += "\n     -g: identifier of the group of jobs (groupid)"
        string += "\n     -S: suffix of the input files (default='fa')"
        string += "\n     -a: acronym of the program to be launched (default='%s')" % ( self.getAcronym() )
        string += "\n     -C: configuration file to connect to MySQL (absolute path or in current dir)"
        string += "\n     -d: temporary directory (absolute path, default=None)"
        string += "\n     -j: table recording the jobs (default='jobs')"
        string += "\n     -c: clean the temporary data"
        string += "\n     -v: verbosity level (default=0/1/2)"
        return string
    
    
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        pass
    
    
    def getHelpAsString( self ):
        """
        Return the help as a string.
        """
        string = self.getGenericHelpAsString()
        string += self.getSpecificHelpAsString()
        return string
    
    
    def setAGenericAttributeFromCmdLine( self, o, a="" ):
        """
        Set a generic attribute from the command-line arguments.
        """
        if o == "-h":
            print self.getHelpAsString()
            sys.exit(0)
        elif o == "-i":
            self.setInputDirectory( a )
        elif o == "-Q":
            self.setQueueName( a )
        elif o == "-g":
            self.setGroupIdentifier( a )
        elif o == "-S":
            self.setInputFileSuffix( a )
        elif o == "-a":
            self.setAcronym( a )
        elif o == "-C":
            self.setConfigFile( a )
        elif o == "-d":
            self.setTemporaryDirectory( a )
        elif o == "-j":
            self.setJobTableName( a )
        elif o == "-Z":
            self.setCatOutputFiles()
        elif o == "-c":
            self.setClean()
        elif o == "-v":
            self.setVerbosityLevel( a )
            
            
    def setASpecificAttributeFromCmdLine( self, o, a="" ):
        """
        Set the specific attributes from the command-line arguments.
        """
        self._prgLauncher.setASpecificAttributeFromCmdLine( o, a )
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line arguments.
        """
        try:
            opts, args = getopt.getopt( sys.argv[1:], "%s%s" % ( self._cmdLineGenericOptions, self._cmdLineSpecificOptions ) )
        except getopt.GetoptError, err:
            print str(err);
            print self.getHelpAsString()
            sys.exit(1)
        for o, a in opts:
            self.setAGenericAttributeFromCmdLine( o, a )
            self.setASpecificAttributeFromCmdLine( o, a )
            
            
    def setInputDirectory( self, arg ):
        self._inputDir = arg
        
    def setQueueName( self, arg ):
        self._queueName = arg
        
    def setGroupIdentifier( self, arg ):
        self._groupId = arg
        
    def setInputFileSuffix( self, arg ):
        self._inputFileSuffix = arg
        
    def setAcronym( self, arg ):
        self._prgAcronym = arg
        
    def setConfigFile( self, arg ):
        if os.path.dirname( arg ) == "":
            self._configFile = "%s/%s" % ( os.getcwd(), arg )
        else:
            self._configFile = arg
            
    def setCurrentDirectory( self ):
        self._currentDir = os.getcwd()
        
    def setTemporaryDirectory( self, arg ):
        self._tmpDir = arg
        
    def setJobTableName( self, arg ):
        self._jobTable = arg
    #TODO: boolean start method with 'is'    
    def setCatOutputFiles( self ):
        self._catOutFiles = True
    #TODO: boolean start method with 'is'    
    def setClean( self ):
        self._clean = True
        
    def setVerbosityLevel( self, arg ):
        self._verbose = int(arg)
        
    def setExecutableWrapper( self, arg ):
        self._exeWrapper = arg
    #TODO: Wrapper and Program are confusing    
    def setSingleProgramLauncher( self ):
        """
        Set the wrapper and program command-lines of the program launcher.
        Append the program launcher to 'self.lPrgLaunchers'.
        """
        self._prgLauncher.setWrapperCommandLine()
        self._prgLauncher.setProgramCommandLine()
        self.lPrgLaunchers.append( self._prgLauncher )
        
        
    def getInputDirectory( self ):
        return self._inputDir
        
    def getQueueName( self ):
        return self._queueName
        
    def getGroupIdentifier( self ):
        return self._groupId
        
    def getInputFileSuffix( self ):
        return self._inputFileSuffix
    
    def getAcronym( self ):
        return self._prgAcronym
        
    def getConfigFile( self ):
        return self._configFile
        
    def getCurrentDirectory( self ):
        return self._currentDir
        
    def getTemporaryDirectory( self ):
        return self._tmpDir
        
    def getJobTableName( self ):
        return self._jobTable
    
    def getCatOutputFiles( self ):
        return self._catOutFiles
    
    def getClean( self ):
        return self._clean
        
    def getVerbosityLevel( self ):
        return self._verbose
    
    def getWrapperName( self ):
        return self._prgLauncher.getWrapperName()
    
    def getProgramName( self ):
        return self._prgLauncher.getProgramName()
    
    def getPatternToConcatenate( self ):
        return self._prgLauncher.getOutputFile().replace( GENERIC_IN_FILE, "*" )
    
    def getProgramLauncherInstance( self ):
        pass
    
    
    def checkGenericAttributes( self ):
        """
        Check the generic attributes before running the program.
        """
        if self.getInputDirectory() == "":
            message = "ERROR: missing input directory"
            raise CheckerException(message)
        if not os.path.exists( self.getInputDirectory() ):
            message = "ERROR: input directory '%s' doesn't exist" % ( self.getInputDirectory() )
            raise CheckerException(message)
        if self.getGroupIdentifier() == "":
            message = "ERROR: missing group identifier"
            raise CheckerException(message)
        if self.getAcronym() == "":
            message = "ERROR: missing program acronym"
            raise CheckerException(message)
        if self.getConfigFile() == "":
            message = "ERROR: missing config file to access MySQL"
            raise CheckerException(message)
        if not os.path.exists( self.getConfigFile() ):
            message = "ERROR: config file '%s' doesn't exist" % ( self.getConfigFile() )
            raise CheckerException(message)   
        if self.getTemporaryDirectory() == "":
            self.setTemporaryDirectory(self._currentDir)
            
            
    def checkSpecificAttributes( self ):
        """
        Check the specific attributes of each program launcher.
        """
        self._prgLauncher.checkSpecificAttributes()
        
        
    def checkProgramAvailability( self ):
        """
        Check that all required programs are in the user's PATH.
        """
        if len(self.lPrgLaunchers) == 1:
            for name in [ self.getWrapperName(), self.getProgramName() ]:
                if not CheckerUtils.isExecutableInUserPath( name ):
                    print "ERROR: '%s' not in your PATH" % ( name )
                    sys.exit(1)
        elif len(self.lPrgLaunchers) > 1:
            for pL in self.lPrgLaunchers:
                for name in [ pL.getWrapperName(), pL.getProgramName() ]:
                    if not CheckerUtils.isExecutableInUserPath( name ):
                        print "ERROR: '%s' not in your PATH" % ( name )
                        sys.exit(1)
                        
                        
    def getProgramCommandLineAsString( self ):
        """
        Return the command-line to launch in each job.
        Specified in each wrapper.
        """
        pass
    
    
    def getListFilesToKeep( self ):
        """
        Return the list of files to keep at the end of each job.
        Specified in each wrapper.
        """
        pass
    
    
    def getListFilesToRemove( self ):
        """
        Return the list of files to remove at the end of each job.
        Specified in each wrapper.
        """
        pass
    
    
    def getJobFileNameAsString( self, count ):
        """
        Return the name of the job file as a string.
        @param count: job number (e.g. '1') or '*'
        @type count: integer or string
        """
        jobFile = "ClusterLauncher"
        jobFile += "_groupid%s" % ( self.getGroupIdentifier() )
        if count != "*":
            jobFile += "_job%i" % ( count )
            jobFile += "_time%s" % ( time.strftime("%Y-%m-%d-%H-%M-%S") )
        else:
            jobFile += "_job*"
            jobFile += "_time%s-*" % ( time.strftime("%Y-%m") )
        jobFile += ".py"
        return jobFile
    
    
    def getCmdUpdateJobStatusAsString( self, newStatus ):
        """
        Return the command to update the job status in the table.
        """
        prg = os.environ["REPET_PATH"] + "/bin/srptChangeJobStatus.py"
        cmd = prg
        cmd += " -t %s" % ( self.job.tablename )
        if str(self.job.jobid).isdigit():
            cmd += " -j %s" % ( self.job.jobname )
        else:
            cmd += " -j %s" % ( self.job.jobid )
        cmd += " -g %s" % ( self.job.groupid )
        if self.job.queue != "":
            cmd += " -q %s" % ( self.job.queue )
        cmd += " -s %s" % ( newStatus )
        cmd += " -c %s" % ( self.getConfigFile() )
        cmd += " -v %i" % ( self._verbose )
        return "os.system( \"%s\" )\n" % ( cmd )
    
    
    def getCmdToLaunchWrapper( self, fileName, genericCmd, exeWrapper ):
        """
        Return the launching command as a string.
        Launch the wrapper, retrieve its exit status, update status if error.
        """
        specificCmd = genericCmd.replace( GENERIC_IN_FILE, fileName )
        cmd = ""
        cmd += "print \"LAUNCH: %s\"\n" % ( specificCmd )
        cmd += "sys.stdout.flush()\n"
        cmd += "exitStatus = os.system ( \"%s\" )\n" % ( specificCmd )
        cmd += "if exitStatus != 0:\n"
        cmd += "\tprint \"ERROR: wrapper '%s'" % ( exeWrapper )
        cmd += " returned exit status '%i'\" % ( exitStatus )\n"
        cmd += "\tos.chdir( \"%s\" )\n" % ( self.getTemporaryDirectory() )
        cmd += "\tshutil.move( newDir, '%s' )\n" % ( self.getCurrentDirectory() )
        cmd += "\t%s" % ( self.getCmdUpdateJobStatusAsString( "error" ) )
        cmd += "\tsys.exit(1)\n"
        return cmd
    
    
    def getCmdToKeepFiles( self, fileName, lFilesToKeep ):
        """
        Return the commands to keep the output files.
        """
        cmd = ""
        for f in lFilesToKeep:
            f = f.replace( GENERIC_IN_FILE, fileName )
            cmd += "if not os.path.exists( \"%s\" ):\n" % ( f )
            cmd += "\tprint \"ERROR: output file '%s' doesn't exist\"\n" % ( f )
            cmd += "\t%s" % ( self.getCmdUpdateJobStatusAsString( "error" ) )
            cmd += "\tsys.exit(1)\n"
            cmd += "if not os.path.exists( \"%s/%s\" ):\n" \
                   % ( self._currentDir, f )
            cmd += "\tshutil.copy( \"%s\", \"%s/%s\" )\n" % ( f, self.getCurrentDirectory(), f )
        return cmd
    
    
    def getCmdToRemoveFiles( self, fileName, lFilesToRemove ):
        """
        Return the commands to remove the temporary files.
        """
        cmd = ""
        if lFilesToRemove != []:
            for f in lFilesToRemove:
                f = f.replace( GENERIC_IN_FILE, fileName )
                cmd += "if os.path.exists( \"%s\" ):\n" % ( f )
                cmd += "\tos.remove( \"%s\" )\n" % ( f )
        return cmd
    
    
    def getJobCommandsAsString( self, fileName, jobName, minFreeGigaInTmpDir=1 ):
        """
        Return all the job commands as a string.
        """
        cmd = "#!/usr/bin/env python\n"
        cmd += "\n"
        cmd += "import os\n"
        cmd += "import sys\n"
        cmd += "import shutil\n"
        cmd += "import time\n"
        cmd += "\n"
        cmd += "print \"system:\", os.uname()\n"
        cmd += "beginTime = time.time()\n"
        cmd += "print 'beginTime=%f' % ( beginTime )\n"
        cmd += "\n"
        cmd += self.getCmdUpdateJobStatusAsString( "running" )
        cmd += "\n"
        cmd += "if not os.path.exists( \"%s\" ):\n" % ( self.getTemporaryDirectory() )
        cmd += "\tprint \"ERROR: working dir '%s' doesn't exist\"\n" % ( \
            self.getTemporaryDirectory() )
        cmd += "\t%s" % ( self.getCmdUpdateJobStatusAsString( "error" ) )
        cmd += "\tsys.exit(1)\n"
        cmd += "freeSpace = os.statvfs( \"%s\" )\n" % ( self.getTemporaryDirectory() )
        cmd += "if ( freeSpace.f_bavail * freeSpace.f_frsize ) / 1073741824.0 < %i:\n" % ( minFreeGigaInTmpDir ) # nb blocs * bloc size in bytes > 1 GigaByte ?
        cmd += "\tprint \"ERROR: less than %iGb in '%s'\"\n" % ( minFreeGigaInTmpDir, self.getTemporaryDirectory() )
        cmd += "\t%s" % ( self.getCmdUpdateJobStatusAsString( "error" ) )
        cmd += "\tsys.exit(1)\n"
        cmd += "print \"working dir: %s\"\n" % ( self.getTemporaryDirectory() )
        cmd += "sys.stdout.flush()\n"
        cmd += "os.chdir( \"%s\" )\n" % ( self.getTemporaryDirectory() )
        cmd += "\n"
        cmd += "newDir = \"%s_%s_%s\"\n" % ( self.getGroupIdentifier(), jobName, time.strftime("%Y%m%d-%H%M%S") )
        cmd += "if os.path.exists( newDir ):\n"
        cmd += "\tshutil.rmtree( newDir )\n"
        cmd += "os.mkdir( newDir )\n"
        cmd += "os.chdir( newDir )\n"
        cmd += "\n"
        cmd += "if not os.path.exists( \"%s\" ):\n" % ( fileName )
        cmd += "\tos.symlink( \"%s/%s\", \"%s\" )\n" % \
               ( self._inputDir, fileName, fileName )
        cmd += "\n"
        
        for pL in self.lPrgLaunchers:
            cmd += self.getCmdToLaunchWrapper( \
                fileName, \
                pL.getWrapperCommandLine(), \
                "%s.py" % ( type(pL).__name__ ) )
            cmd += "\n"
            cmd += self.getCmdToKeepFiles( fileName, pL.getListFilesToKeep() )
            cmd += "\n"
            cmd += self.getCmdToRemoveFiles( fileName, \
                                             pL.getListFilesToRemove() )
            
        cmd += "if os.path.exists( \"%s\" ):\n" % ( fileName )
        cmd += "\tos.remove( \"%s\" )\n" % ( fileName )
        cmd += "os.chdir( \"..\" )\n"
        cmd += "shutil.rmtree( newDir )\n"
        cmd += self.getCmdUpdateJobStatusAsString( "finished" )
        cmd += "\n"
        cmd += "endTime = time.time()\n"
        cmd += "print 'endTime=%f' % ( endTime)\n"
        cmd += "print 'executionTime=%f' % ( endTime - beginTime )\n"
        cmd += "print \"system:\", os.uname()\n"
        cmd += "sys.exit(0)\n"
        return cmd
    
    
    def initializeJob( self, fileName, count ):
        """
        Initialize the job (jobname, command, launcher).
        """
        self.job.jobname = "%s%i" % ( self.getAcronym(), count )
        
        cmd = self.getJobCommandsAsString( fileName, count )
        self.job.command = cmd
        
        jobFile = "%s/%s" % ( self.getCurrentDirectory(), \
                              self.getJobFileNameAsString( count ) )
        jobFileHandler = open( jobFile, "w" )
        jobFileHandler.write( cmd )
        jobFileHandler.close()
        os.chmod( jobFile, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC )
        self.job.launcher = jobFile
        
        
    def getStatsOfExecutionTime( self ):
        """
        Return a Stat object about the execution time of each job as a
        float expressed in seconds since the epoch, in UTC.
        """
        stat = Stat()
        pattern = "%s/%s*.o*" % ( self.getCurrentDirectory(), \
                                  self.getAcronym() )
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
    
    
    def removeAllJobFiles( self ):
        """
        Remove all job files.
        """
        pattern = "%s/%s" % ( self.getCurrentDirectory(), \
                              self.getJobFileNameAsString( "*" ) )
        lJobFiles = glob.glob( pattern )
        for f in lJobFiles:
            os.remove( f )
            
            
    def removeAllJobStdouts( self ):
        """
        Remove all job stdout.
        """
        pattern = "%s/%s*.o*" % ( self.getCurrentDirectory(), \
                                  self.getAcronym() )
        lJobFiles = glob.glob( pattern )
        for f in lJobFiles:
            os.remove( f )
            
            
    def removeAllJobStderrs( self ):
        """
        Remove all job stderr.
        """
        pattern = "%s/%s*.e*" % ( self.getCurrentDirectory(), \
                                  self.getAcronym() )
        lJobFiles = glob.glob( pattern )
        for f in lJobFiles:
            os.remove( f )
            
            
    def processOutputFile( self, tmpFile, outFile ):
        """
        Process the output file if necessary.
        """
        shutil.copyfile( tmpFile, outFile )
        
        
    def catOutputFiles( self ):
        """
        Concatenate output files from all jobs.
        """
        string = "concatenate output files from jobs..."
        print string; sys.stdout.flush()
        tmpFile = "%s.tmp" % ( self._prgLauncher.getOutputFile().replace( GENERIC_IN_FILE, self._groupId ) )
        if os.path.exists( tmpFile ):
            os.remove( tmpFile )
        lJobFiles = glob.glob( self.getPatternToConcatenate() )
        lJobFiles.sort()
        FileUtils.catFilesFromList( lJobFiles, tmpFile )
        if self.getClean():
            FileUtils.removeFilesFromList( lJobFiles )
        outFile = tmpFile[:-4]
        if os.path.exists( outFile ):
            os.remove( outFile )
        self.processOutputFile( tmpFile, outFile )
        if self.getClean():
            os.remove( tmpFile )
            
            
    def start( self ):
        """
        Useful commands before running the program (check, open database connector...).
        """
        try:
            self.checkGenericAttributes()
        except CheckerException, msg:
            print msg
            print self.getHelpAsString()
            sys.exit(1)
            
        if self.lPrgLaunchers == []:
            self.setSingleProgramLauncher()
        for pL in self.lPrgLaunchers:
            if pL.getWrapperCommandLine() == "":
                string = "ERROR: wrapper command is empty !"
                print string
                sys.exit(1)
            if pL.getProgramCommandLine() == "":
                string = "ERROR: program command is empty !"
                print string
                sys.exit(1)
        self.checkProgramAvailability()
        
        try:
            self.checkSpecificAttributes()
        except CheckerException, msg:
            print msg
            print self.getHelpAsString()
            sys.exit(1)
        
        if self.getVerbosityLevel() > 0:
            string = "START %s" % ( type(self).__name__ )
            print string
        self.job.tablename = self.getJobTableName()
        self.job.groupid = self.getGroupIdentifier()
        tokens = self.getQueueName().replace("'","").split(" ")
        self.job.setQueue( tokens[0] )
        if len(tokens) > 1:
            lResources = tokens[1:]
            self.job.lResources = lResources
        if self.getVerbosityLevel() > 0:
            print "groupid: %s" % ( self.getGroupIdentifier() )
        self.jobdb = RepetJob( cfgFileName=self.getConfigFile() )
        if self.jobdb.has_unfinished_job( self.job.tablename, \
                                          self.job.groupid ):
            self.jobdb.wait_job_group( self.job.tablename, self.job.groupid )
            return
        self.jobdb.clean_job_group( self.job.tablename, self.job.groupid )
        sys.stdout.flush()
        
        
    def end( self ):
        """
        Useful commands after the program was run (clean, close database connector...).
        """
        self.jobdb.close()
        
        if self.getVerbosityLevel() > 0:
            string = "END %s" % ( type(self).__name__ )
            print string
        sys.stdout.flush()
        
        
    def run( self ):
        """
        Launch jobs in parallel on each file in the query directory.
        """
        self.start()
        
        lInFiles = glob.glob( "%s/*.%s" % ( self._inputDir, self._inputFileSuffix ) )
        self._nbJobs = len(lInFiles)
        if self._verbose > 0:
            string = "submitting %i jobs" % ( self._nbJobs )
            string += " with groupid '%s'" % ( self.job.groupid )
            string += " (%s)" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
            print string; sys.stdout.flush()
            
        count = 0
        for inFile in lInFiles:
            count += 1
            fileName = os.path.basename( inFile )
            if self._verbose > 1:
                print "processing file '%s' # %i..." % ( fileName, count )
                sys.stdout.flush()
                
            self.initializeJob( fileName, count )
            
            time.sleep( 0.5 )
            exitStatus = self.jobdb.submit_job( job=self.job, verbose=self._verbose-1 )
            if exitStatus != 0:
                print "ERROR while submitting job '%i' to the cluster"  % ( \
                    count )
                sys.exit(1)
                
        string = "waiting for %i jobs" % ( self._nbJobs )
        string += " with groupid '%s'" % ( self.job.groupid )
        string += " (%s)" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
        print string; sys.stdout.flush()
        self.jobdb.wait_job_group( self.job.tablename, self.job.groupid )
        if self._nbJobs > 1:
            string = "all jobs with groupid '%s'" % ( self.job.groupid )
            string += " are finished (%s)" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
            print string; sys.stdout.flush()
        statsExecutionTime = self.getStatsOfExecutionTime()
        if self._nbJobs > 1:
            print "execution time of all jobs (seconds): %f" % statsExecutionTime.getSum()
        print "execution time per job: %s" % statsExecutionTime.string()
        sys.stdout.flush()
        self.jobdb.clean_job_group( self.job.tablename, self.job.groupid )
        
        if self.getClean():
            self.removeAllJobFiles()
            self.removeAllJobStdouts()
            self.removeAllJobStderrs()
            
        if self.getCatOutputFiles():
            self.catOutputFiles()
            
        self.end()
