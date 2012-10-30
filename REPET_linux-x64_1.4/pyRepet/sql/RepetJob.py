import os
import sys
import time
import datetime
import MySQLdb

from pyRepet.sql.RepetDBMySQL import RepetDB


class Job:
    """
    Job informations to launch a command on a cluster
    """
    
    def __init__( self, tablename="", jobid=0, jobname="", groupid="", queue="", \
                  command="", launcherFile="", node="", lResources="mem_free=1G" ):
        """
        Constructor.
        @param tablename: table name to record the jobs
        @type tablename: string
        @param jobid: identifier given by SGE on submission
        @type jobid: integer
        @param jobname: name
        @type jobname: string
        @param groupid: a group identifier to record related job series 
        @type groupid: string
        @param queue: queue name of the batch job manager
        @type queue: string
        @param command: command launched
        @type command: string
        @param node: cluster node name where the execution takes place
        @type node: string
        @param lResources: resources (memory, time...) but need to conform to SGE/PBS syntax !
        @type lResources: list of strings
        """
        self.tablename = tablename
        if str(jobid).isdigit():
            self.jobid = int(jobid)
            self.jobname = jobname
        else:
            self.jobname = jobid
            self.jobid = 0
        self.groupid = groupid
        self.setQueue( queue )
        self.command = command
        self.launcher = launcherFile
        self.node = node
        self.lResources = lResources
        
    def setQueue( self, queue ):
        self.queue = ""
        if queue != "none":
            self.queue = queue
            
            
class RepetJob( RepetDB ):
    """
    Connector to manage jobs launched in parallel, their features being recorded
    in a MySQL database.
    """
    
    def create_job_table( self, tablename ):
        """
        Create a job table.
        @param tablename: new table name
        @type tablename: string
        """
        self.remove_if_exist( tablename )
        qry = "CREATE TABLE %s (jobid INT UNSIGNED, jobname VARCHAR(255), groupid VARCHAR(255), command TEXT, launcher VARCHAR(1024), queue VARCHAR(255), status VARCHAR(255), time DATETIME, node VARCHAR(255))" % ( tablename )
        self.execute( qry )
        self.update_info_table( tablename, "job table" )
        sqlCmd = "CREATE INDEX igroupid ON %s ( groupid(10) )" % ( tablename )
        self.execute( sqlCmd )
        
        
    def record_job( self, job ):
        """
        Record a job.
        @param job: a L{Job<Job>} instance with the job informations
        @type job: L{Job<Job>} instance
        """
        self.remove_job( job )
        qry = "INSERT INTO %s" % ( job.tablename )
        qry += " VALUES ("
        qry += " \"%s\"," % ( job.jobid )
        qry += " \"%s\"," % ( job.jobname )
        qry += " \"%s\"," % ( job.groupid )
        qry += " \"%s\"," % ( job.command.replace("\"","\'") )
        qry += " \"%s\"," % ( job.launcher )
        qry += " \"%s\"," % ( job.queue )
        qry += " \"waiting\","
        qry += " \"%s\"," % ( time.strftime( "%Y-%m-%d %H:%M:%S" ) )
        qry += " \"?\" );"
        self.execute( qry )
        while self.get_job_status(job) == "unknown":
            msg = "ERROR while recording job"
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            sys.exit(1)
            
            
    def setJobIdFromSge( self, job, jobid ):
        qry = "UPDATE %s" % ( job.tablename )
        qry += " SET jobid='%i'" % ( int(jobid) )
        qry += " WHERE jobname='%s'" % ( job.jobname )
        qry += " AND groupid='%s'" % ( job.groupid )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
        
        
    def remove_job( self, job ):
        """
        Remove a job from the job table.
        @param job: a job
        @type job: RepetJobMySQL
        """
        qry = "DELETE FROM %s" % ( job.tablename )
        qry += " WHERE groupid='%s'" % ( job.groupid )
#        if job.jobid != 0:
#            qry += " AND jobid='%i'" % ( job.jobid )
        qry += " AND jobname='%s'" % ( job.jobname )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
        
        
    def change_job_status( self, job, status, method ):
        """
        Change a job status.
        @param job: a L{Job<Job>} instance with the job informations
        @type job: L{Job<Job>} instance
        @param status: the new status (waiting,finished,error)
        @type status: string
        """
        qry = "UPDATE %s" % ( job.tablename )
        qry += " SET status='%s'" % ( status )
        qry += " WHERE groupid='%s'" % ( job.groupid )
#        if job.jobid != 0:
#            qry += " AND jobid='%i'" % ( job.jobid )
        qry += " AND jobname='%s'" % ( job.jobname )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
        
        
    def get_job_status( self, job ):
        """
        Get a job status.
        @param job: a L{Job<Job>} instance with the job informations
        @type job: L{Job<Job>} instance
        """
        if job.jobid != 0 and job.jobname == "":
            job.jobname = job.jobid
            job.jobid = 0
        qry = "SELECT status FROM %s" % ( job.tablename )
        qry += " WHERE groupid='%s'" % ( job.groupid )
#        if job.jobid != 0:
#            qry += " AND jobid='%i'" % ( job.jobid )
        qry += " AND jobname='%s'" % ( job.jobname )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
        res = self.fetchall()
        if len(res) > 1:
            msg = "ERROR while getting job status: non-unique jobs"
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            sys.exit(1)
        if res == None or len(res) == 0:
            return "unknown"
        return res[0][0]
    
    
    def getCountStatus( self, tablename, groupid, status ):
        """
        Get the number of jobs belonging to the desired groupid with the desired status.
        @param tablename: table name to record the jobs
        @type tablename: string
        @param groupid: a group identifier to record related job series 
        @type groupid: string
        @param status: job status (waiting, running, finished, error)
        @type status: string
        @return: number of jobs belonging to the desired groupid with the desired status
        @rtype: integer
        """
        qry = "SELECT count(jobname) FROM %s" % ( tablename )
        qry += " WHERE groupid='%s'" % ( groupid )
        qry += " AND status='%s';" % ( status )
        self.execute( qry )
        res = self.fetchall()
        if len(res) == 0:
            return 0
        else:
            return int( res[0][0] )
        
        
    def clean_job_group( self, tablename, groupid ):
        """
        Clean all job from a job group.
        @param tablename: table name to record the jobs
        @type tablename: string
        @param groupid: a group identifier to record related job series 
        @type groupid: string
        """
        if self.exist( tablename ):
            qry = "DELETE FROM %s WHERE groupid='%s';" % ( tablename, groupid )
            self.execute( qry )
            
            
    def has_unfinished_job( self, tablename, groupid ):
        """
        Check if there is unfinished job from a job group.
        @param tablename: table name to record the jobs
        @type tablename: string
        @param groupid: a group identifier to record related job series 
        @type groupid: string
        """
        if not self.exist( tablename ):
            return False
        qry = "SELECT * FROM %s" % ( tablename )
        qry += " WHERE groupid='%s'" % ( groupid )
        qry += " and status!='finished';" 
        self.execute( qry )
        res = self.fetchall()
        if len(res) == 0:
            return False
        return True
    
    
    def isJobStillHandledBySge( self, jobid, jobname ):
        isJobInQstat = False
        qstatFile = "qstat_stdout"
        cmd = "qstat > %s" % ( qstatFile )
        returnStatus = os.system( cmd )
        if returnStatus != 0:
            msg = "ERROR while launching 'qstat'"
            sys.stderr.write( "%s\n" % msg )
            sys.exit(1)
        qstatFileHandler = open( qstatFile, "r" )
        lLines = qstatFileHandler.readlines()
        for line in lLines:
            tokens = line.split()
            if len(tokens) > 3 and tokens[0] == str(jobid) and tokens[2] == jobname[0:len(tokens[2])]:
                isJobInQstat = True
                break
        qstatFileHandler.close()
        os.remove( qstatFile )
        return isJobInQstat
    
    
    def wait_job_group( self, tablename, groupid, checkInterval=5, maxRelaunch=3, exitIfTooManyErrors=True, timeOutPerJob=60*60 ):
        """
        Wait job finished status from a job group.
        @note: job are re-launched if error (max. 3 times)
        @param tablename: table name to record the jobs
        @type tablename: string
        @param groupid: a group identifier to record related job series 
        @type groupid: string
        @param checkInterval: time laps in seconds between two checks
        @type checkInterval: integer (default=5)
        @param maxRelaunch: max nb of times a job in error is relaunch before exiting
        @type maxRelaunch: integer (default=3)
        @param exitIfTooManyErrors: exit if a job is still in error above maxRelaunch
        @type exitIfTooManyErrors: boolean (default=True)
        @param timeOutPerJob: max nb of seconds after which one tests if a job is still in SGE or not
        @type timeOutPerJob: integer (default=60*60=1h)
        """
        
        dJob2Err = {}
        
        # retrieve the total number of jobs belonging to the desired groupid
        qry = "SELECT count(jobname) FROM %s WHERE groupid='%s';" % ( tablename, groupid )
        self.execute( qry )
        totalNbJobs = int( self.fetchall()[0][0] )
        
        nbTimeOuts = 0
        
        while True:
            time.sleep( checkInterval )
            
            # retrieve the finished jobs and stop if all jobs are finished
            nbFinishedJobs = self.getCountStatus( tablename, groupid, "finished" )
            if nbFinishedJobs == totalNbJobs:
                break
            
            # retrieve the jobs in error and relaunch them if they are in error (max. 3 times)
            qry = "SELECT * FROM %s" % ( tablename )
            qry += " WHERE groupid='%s'" % ( groupid )
            qry += " AND status='error';"
            self.execute( qry )
            lJobsInError = self.fetchall()   # 0:jobid, 1:jobname, 2:groupid, ...
            for job in lJobsInError:
                if not dJob2Err.has_key( job[1] ):
                    dJob2Err[ job[1] ] = 1
                if dJob2Err[ job[1] ] < maxRelaunch:
                    cmd = "job '%s' in error, re-submitting (%i)" % ( job[1], dJob2Err[ job[1] ] )
                    print cmd; sys.stdout.flush()
                    newJob = Job( tablename=tablename,
                                  jobname=job[1],
                                  groupid=job[2],
                                  command=job[3],
                                  launcherFile=job[4],
                                  queue=job[5] )
                    self.submit_job( newJob )
                    dJob2Err[ job[1] ] += 1
                else:
                    dJob2Err[ job[1] ] += 1
                    msg = "job '%s' in permanent error (>%i)" % ( job[1], maxRelaunch )
                    msg += "\ngroupid = %s" % ( groupid )
                    msg += "\nnb of jobs = %i" % ( totalNbJobs )
                    msg += "\nnb of finished jobs = %i" % ( self.getCountStatus( tablename, groupid, "finished" ) )
                    msg += "\nnb of waiting jobs = %i" % ( self.getCountStatus( tablename, groupid, "waiting" ) )
                    msg += "\nnb of running jobs = %i" % ( self.getCountStatus( tablename, groupid, "running" ) )
                    msg += "\nnb of jobs in error = %i" % ( self.getCountStatus( tablename, groupid, "error" ) )
                    sys.stderr.write( "%s\n" % msg )
                    sys.stderr.flush()
                    if exitIfTooManyErrors:
                        self.clean_job_group( tablename, groupid )
                        sys.exit(1)
                    else:
                        checkInterval = 60
                        
            # retrieve the date and time at which the oldest, still-running job was submitted
            sql = "SELECT jobid,jobname,time FROM %s WHERE groupid='%s' AND status='running' ORDER BY time DESC LIMIT 1" % ( tablename, groupid )
            self.execute( sql )
            res = self.fetchall()
            if len(res) > 0:
                jobid = res[0][0]
                jobname = res[0][1]
                dateTimeOldestJob = res[0][2]
                dateTimeCurrent = datetime.datetime.now()
                delta = dateTimeCurrent - dateTimeOldestJob
                if delta.seconds >= nbTimeOuts * timeOutPerJob and delta.seconds < (nbTimeOuts+1) * timeOutPerJob:
                    continue
                if delta.seconds >= (nbTimeOuts+1) * timeOutPerJob:
                    nbTimeOuts += 1
                    if not self.isJobStillHandledBySge( jobid, jobname ):
                        time.sleep( 5 )
                    if not self.isJobStillHandledBySge( jobid, jobname ):
                        msg = "ERROR: job '%s', supposedly still running, is not handled by SGE anymore" % ( jobid )
                        msg += "\nit was launched the %s (> %.2f hours ago)" % ( dateTimeOldestJob, timeOutPerJob/3600.0 )
                        msg += "\nthis problem can be due to:"
                        msg += "\n* memory shortage, in that case, decrease the size of your jobs;"
                        msg += "\n* timeout, in that case, decrease the size of your jobs;"
                        msg += "\n* node failure, in that case, relaunch the program or see your admin system."
                        sys.stderr.write( "%s\n" % msg )
                        sys.stderr.flush()
                        self.clean_job_group( tablename, groupid )
                        sys.exit(1)
                        
                        
    def submit_job( self, job, verbose=0, maxNbWaitingJobs=10000, checkInterval=30 ):
        """
        Submit a job to a queue and record it in job table.
        @param job: a L{Job<Job>} instance with the job informations
        @type job: L{Job<Job>} instance
        @param maxNbWaitingJobs: max nb of waiting jobs before submitting a new one
        @type maxNbWaitingJobs: integer (default=10000)
        @param checkInterval: time laps in seconds between two checks
        @type checkInterval: integer (default=30)
        """
        
        if os.environ.get( "REPET_QUEUE" ) not in [ "SGE", "PBS" ]:
            print "ERROR: environment variable REPET_QUEUE should be 'SGE' or 'PBS'"
            return 1
        
        if not self.exist( job.tablename ):
            self.create_job_table( job.tablename )
        else:
            lFields = self.getFieldListFromTable( job.tablename )
            if len(lFields) == 8:
                self.remove_if_exist( job.tablename )
                self.create_job_table( job.tablename )
                
        if self.get_job_status( job ) in [ "waiting", "running", "finished" ]:
            msg = "WARNING: job '%s' was already submitted" % ( job.jobname )
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            self.clean_job_group( job.tablename, job.groupid )
            sys.exit(1)
            
        while self.getCountStatus( job.tablename, job.groupid, "waiting" ) > maxNbWaitingJobs:
            time.sleep( checkInterval )
            
        self.record_job( job )
        
        cmd = "echo '%s' | " % ( job.launcher )
        prg = "qsub"
        cmd += prg
        cmd += " -V"
        cmd += " -N %s" % ( job.jobname )
        if job.queue != "":
            cmd += " -q %s" % ( job.queue )
        if os.environ.get( "REPET_QUEUE" ) == "SGE":
            cmd += " -cwd"
            if job.lResources != []:
                cmd += " -l \""
                for resource in job.lResources:
                    cmd += resource
                cmd += "\""
        elif os.environ.get( "REPET_QUEUE" ) == "PBS":
            if job.lResources != []:
                cmd += " -l \""
                for resource in job.lResources:
                    cmd += resource.replace("mem_free","mem")
                cmd += "\""
        cmd += " > jobid.stdout"
        
        returnStatus = os.system( cmd )
        if returnStatus == 0:
            jobidFileHandler = open( "jobid.stdout", "r" )
            jobid = int(jobidFileHandler.readline().split(" ")[2])
            if verbose > 0:
                print "job '%i %s' submitted" % ( jobid, job.jobname )
                sys.stdout.flush()
            job.jobid = jobid
            jobidFileHandler.close()
            self.setJobIdFromSge( job, jobid )
            os.remove( "jobid.stdout" )
        return returnStatus
