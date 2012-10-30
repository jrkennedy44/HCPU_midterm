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


import os
import time
import datetime
import sys
from pyRepetUnit.commons.sql.Job import Job 
from pyRepetUnit.commons.sql.DbMySql import DbMySql

## Methods for Job persistence 
#
class RepetJob( DbMySql ):
    
    ## Create a job table
    #
    # @param tablename new table name
    #
    def createJobTable( self, tablename ):
        self.dropTable( tablename )
        sqlCmd = "CREATE TABLE %s" % ( tablename )
        sqlCmd += " ( jobid INT UNSIGNED"
        sqlCmd += ", jobname VARCHAR(255)"
        sqlCmd += ", groupid VARCHAR(255)"
        sqlCmd += ", command TEXT"
        sqlCmd += ", launcher VARCHAR(1024)"
        sqlCmd += ", queue VARCHAR(255)"
        sqlCmd += ", status VARCHAR(255)"
        sqlCmd += ", time DATETIME"
        sqlCmd += ", node VARCHAR(255) )"
        self.execute( sqlCmd )
        
        self.updateInfoTable( tablename, "job table" )
        sqlCmd = "CREATE INDEX igroupid ON " + tablename + " ( groupid(10) )"
        self.execute( sqlCmd )
        
        
    ## Record a job
    #
    # @param job Job instance with the job informations
    #
    def recordJob( self, job ):
        self.removeJob( job )
        sqlCmd = "INSERT INTO %s" % ( job.tablename )
        sqlCmd += " VALUES ("
        sqlCmd += " \"%s\"," % ( job.jobid )
        sqlCmd += " \"%s\"," % ( job.jobname )
        sqlCmd += " \"%s\"," % ( job.groupid )
        sqlCmd += " \"%s\"," % ( job.command.replace("\"","\'") )
        sqlCmd += " \"%s\"," % ( job.launcher )
        sqlCmd += " \"%s\"," % ( job.queue )
        sqlCmd += " \"waiting\","
        sqlCmd += " \"%s\"," % ( time.strftime( "%Y-%m-%d %H:%M:%S" ) )
        sqlCmd += " \"?\" );"
        self.execute( sqlCmd )
        
        
    ## Remove a job from the job table
    #
    #  @param job: job instance to remove
    #
    def removeJob( self, job ):
        qry = "DELETE FROM %s" % ( job.tablename )
        qry += " WHERE groupid='%s'" % ( job.groupid )
        qry += " AND jobname='%s'" % ( job.jobname )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
            
            
    ## Set the jobid of a job with the id of SGE
    #
    # @param job job instance
    # @param jobid integer
    #
    def setJobIdFromSge( self, job, jobid ):
        qry = "UPDATE %s" % ( job.tablename )
        qry += " SET jobid='%i'" % ( int(jobid) )
        qry += " WHERE jobname='%s'" % ( job.jobname )
        qry += " AND groupid='%s'" % ( job.groupid )
        qry += " AND queue='%s';" % ( job.queue )
        self.execute( qry )
        
        
    ## Get a job status
    #
    # @param job: a Job instance with the job informations
    #
    def getJobStatus( self, job ):
        if job.jobid != 0 and job.jobname == "":
            job.jobname = job.jobid
            job.jobid = 0
        qry = "SELECT status FROM %s" % ( job.tablename )
        qry += " WHERE groupid='%s'" % ( job.groupid )
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
    
    
    ## Change a job status
    #
    # @param job: a Job instance with the job informations
    # @param status: the new status (waiting,finished,error)
    # @param method: db or file
    #
    def changeJobStatus( self, job, status, method ):
        sqlCmd = "UPDATE %s" % ( job.tablename )
        sqlCmd += " SET status='%s'" % ( status )
        sqlCmd += ",node='%s'" % ( job.node )
        sqlCmd += " WHERE groupid='%s'" % ( job.groupid )
        sqlCmd += " AND jobname='%s'" % ( job.jobname )
        sqlCmd += " AND queue='%s';" % ( job.queue )
        self.execute( sqlCmd )
        
        
    ## Get the number of jobs belonging to the desired groupid with the desired status.
    #
    # @param tablename string table name to record the jobs   
    # @param groupid string a group identifier to record related job series 
    # @param status string job status (waiting, running, finished, error)
    # @return int
    #
    def getCountStatus( self, tablename, groupid, status ):
        qry = "SELECT count(jobname) FROM %s" % ( tablename )
        qry += " WHERE groupid='%s'" % ( groupid )
        qry += " AND status='%s';" % ( status )
        self.execute( qry )
        res = self.fetchall()
        return int( res[0][0] )
        
        
    ## Clean all job from a job group
    #
    # @param tablename table name to record the jobs
    # @param groupid: a group identifier to record related job series
    #
    def cleanJobGroup( self, tablename, groupid ):
        if self.doesTableExist( tablename ):
            qry = "DELETE FROM %s WHERE groupid='%s';" % ( tablename, groupid )
            self.execute( qry )
            
            
    ## Check if there is unfinished job from a job group.
    #
    # @param tablename string table name to record the jobs
    # @param groupid string a group identifier to record related job series 
    #        
    def hasUnfinishedJob( self, tablename, groupid ):
        if not self.doesTableExist( tablename ):
            return False
        qry = "SELECT * FROM %s" % ( tablename )
        qry += " WHERE groupid='%s'" % ( groupid )
        qry += " and status!='finished';" 
        self.execute( qry )
        res = self.fetchall()
        if len(res) == 0:
            return False
        return True
    
         
    ## Check if a job is still handled by SGE
    #
    # @param jobid string job identifier
    # @param jobname string job name
    #  
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
    
    
    ## Wait job finished status from a job group.
    #  Job are re-launched if error (max. 3 times)
    #
    # @param tableName string table name to record the jobs
    # @param groupid string a group identifier to record related job series
    # @param checkInterval integer time laps in seconds between two checks (default = 5)
    # @param maxRelaunch integer max nb of times a job in error is relaunch before exiting (default = 3)
    # @param exitIfTooManyErrors boolean exit if a job is still in error above maxRelaunch (default = True)
    # @param timeOutPerJob integer max nb of seconds after which one tests if a job is still in SGE or not (default = 60*60=1h)
    #
    def waitJobGroup( self, tableName, groupid, checkInterval=5, maxRelaunch=3, exitIfTooManyErrors=True, timeOutPerJob=60*60 ):
        dJob2Err = {}
        
        # retrieve the total number of jobs belonging to the desired groupid
        qry = "SELECT count(jobname) FROM %s WHERE groupid='%s';" % ( tableName, groupid )
        self.execute( qry )
        totalNbJobs = int( self.fetchall()[0][0] )
        
        nbTimeOuts = 0
        
        while True:
            time.sleep( checkInterval )
            # retrieve the finished jobs and stop if all jobs are finished
            nbFinishedJobs = self.getCountStatus( tableName, groupid, "finished" )
            if nbFinishedJobs == totalNbJobs:
                break

            # retrieve the jobs in error and relaunch them if they are in error (max. 3 times)
            qry = "SELECT * FROM %s" % ( tableName )
            qry += " WHERE groupid='%s'" % ( groupid )
            qry += " AND status ='error';"
            self.execute( qry )
            lJobsInError = self.fetchall()
#            if lJobsInError != "":   # 0:jobid, 1:groupid, 2:cmd, 3:launcher, 4:queue, 5:status, 6:time, 7:node      
#                raise Exception
            for job in lJobsInError:
                if not dJob2Err.has_key( job[1] ):
                    dJob2Err[ job[1] ] = 1
                if dJob2Err[ job[1] ] < maxRelaunch:
                    cmd = "job '%s' in error, re-submitting (%i)" % ( job[1], dJob2Err[ job[1] ] )
                    print cmd; sys.stdout.flush()
                    newJob = Job( tablename=tableName,
                                  jobname=job[1],
                                  groupid=job[2],
                                  command=job[3],
                                  launcherFile=job[4],
                                  queue=job[5] )
                    #TODO: rename
                    self.submitJob( newJob )
                    dJob2Err[ job[1] ] += 1
                else:
                    dJob2Err[ job[1] ] += 1
                    cmd = "job '%s' in permanent error (>%i)" % ( job[1], maxRelaunch )
                    cmd += "\ngroupid = %s" % ( groupid )
                    cmd += "\nnb of jobs = %i" % ( totalNbJobs )
                    cmd += "\nnb of finished jobs = %i" % ( self.getCountStatus( tableName, groupid, "finished" ) )
                    cmd += "\nnb of waiting jobs = %i" % ( self.getCountStatus( tableName, groupid, "waiting" ) )
                    cmd += "\nnb of running jobs = %i" % ( self.getCountStatus( tableName, groupid, "running" ) )
                    cmd += "\nnb of jobs in error = %i" % ( self.getCountStatus( tableName, groupid, "error" ) )
                    print cmd; sys.stdout.flush()
                    if exitIfTooManyErrors:
                        self.cleanJobGroup( tableName, groupid )
                        sys.exit(1)
                    else:
                        checkInterval = 60
                        
            # retrieve the date and time at which the oldest, still-running job was submitted
            sql = "SELECT jobid,jobname,time FROM %s WHERE groupid='%s' AND status='running' ORDER BY time DESC LIMIT 1" % ( tableName, groupid )
            self.execute( sql )
            res = self.fetchall()
            if len(res) > 0:
                jobid = res[0][0]
                jobname = res[0][1]
                dateTimeOldestJob = res[0][2]
                dateTimeCurrent = datetime.datetime.now()
                # delta is time between (i) first job launched of the given groupid and still in running and (ii) current time 
                delta = dateTimeCurrent - dateTimeOldestJob
                # check if delta is in an interval:  0 => delta > 1h | 1h => delta > 2h | 2h => delta > 3h (timeOutPerJob = 1h)  
                if delta.seconds >= nbTimeOuts * timeOutPerJob and delta.seconds < (nbTimeOuts+1) * timeOutPerJob:
                    continue
                # delta outside the interval: go to next interval (time out) 
                if delta.seconds >= (nbTimeOuts+1) * timeOutPerJob:
                    nbTimeOuts += 1
                    # Job with 'running' status should be in qstat. Because status in DB is set at 'running' by the job launched.
                    if not self.isJobStillHandledBySge( jobid, jobname ):
                        # But if not, let time for the status update (in DB), if the job finished between the query execution and now.
                        time.sleep( 5 )
                    # If no update at 'finished', exit
                    #TODO: check status in DB
                    if not self.isJobStillHandledBySge( jobid, jobname ):
                        msg = "ERROR: job '%s', supposedly still running, is not handled by SGE anymore" % ( jobid )
                        msg += "\nit was launched the %s (> %.2f hours ago)" % ( dateTimeOldestJob, timeOutPerJob/3600.0 )
                        msg += "\nthis problem can be due to:"
                        msg += "\n* memory shortage, in that case, decrease the size of your jobs;"
                        msg += "\n* timeout, in that case, decrease the size of your jobs;"
                        msg += "\n* node failure, in that case, relaunch the program or see your admin system."
                        sys.stderr.write( "%s\n" % msg )
                        sys.stderr.flush()
                        self.cleanJobGroup( tableName, groupid )
                        sys.exit(1)
                        
                        
    ## Submit a job to a queue and record it in job table.
    #
    # @param job a job instance
    # @param maxNbWaitingJobs integer max nb of waiting jobs before submitting a new one (default = 10000)
    # @param checkInterval integer time laps in seconds between two checks (default = 30)
    # @param verbose integer (default = 0)
    #               
    def submitJob( self, job, verbose=0, maxNbWaitingJobs=10000, checkInterval=30 ):
        if os.environ.get( "REPET_QUEUE" ) not in "SGE":
            print "ERROR: environment variable REPET_QUEUE should be 'SGE'"
            return 1
        
        if not self.doesTableExist( job.tablename ):
            self.createJobTable( job.tablename )
        else:
            lFields = self.getFieldListFromTable( job.tablename )
            if len(lFields) == 8:
                self.dropTable( job.tablename )
                self.createJobTable( job.tablename )
                
        if self.getJobStatus( job ) in [ "waiting", "running", "finished" ]:
            msg = "WARNING: job '%s' was already submitted" % ( job.jobname )
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            self.cleanJobGroup( job.tablename, job.groupid )
            sys.exit(1)
            
        while self.getCountStatus( job.tablename, job.groupid, "waiting" ) > maxNbWaitingJobs:
            time.sleep( checkInterval )
            
        self.recordJob( job )
        
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
            if job.parallelEnvironment != "":
                cmd += " -pe " + job.parallelEnvironment
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
                        
    #TODO: to remove ?
    ## Submit a array job to a queue and record it in job table.
    #
    # @param job a job instance
    # @param maxNbWaitingJobs integer max nb of waiting jobs before submitting a new one (default = 10000)
    # @param checkInterval integer time laps in seconds between two checks (default = 30)
    # @param verbose integer (default = 0)
    #               
    def submitArrayJob( self, nbJob, job, verbose=0, maxNbWaitingJobs=10000, checkInterval=30 ):
        if os.environ.get( "REPET_QUEUE" ) not in "SGE":
            print "ERROR: environment variable REPET_QUEUE should be 'SGE'"
            return 1
        
        if not self.doesTableExist( job.tablename ):
            self.createJobTable( job.tablename )
        else:
            lFields = self.getFieldListFromTable( job.tablename )
            if len(lFields) == 8:
                self.dropTable( job.tablename )
                self.createJobTable( job.tablename )
                
        if self.getJobStatus( job ) in [ "waiting", "running", "finished" ]:
            msg = "WARNING: job '%s' was already submitted" % ( job.jobname )
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            self.cleanJobGroup( job.tablename, job.groupid )
            sys.exit(1)
            
        while self.getCountStatus( job.tablename, job.groupid, "waiting" ) > maxNbWaitingJobs:
            time.sleep( checkInterval )
            
        self.recordJob( job )
        
        cmd = "echo 'sh %s' | " % ( job.launcher )
        prg = "qsub"
        cmd += prg
        cmd += " -V"
        cmd += " -t 1-%s" % ( nbJob )
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
            if job.parallelEnvironment != "":
                cmd += " -pe " + job.parallelEnvironment
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
            jobid = jobidFileHandler.readline().split(" ")[2]
            if verbose > 0:
                print "job '%i %s' submitted" % ( jobid, job.jobname )
                sys.stdout.flush()
            job.jobid = jobid
            jobidFileHandler.close()
            
            jobid, nbJob = self._getJobidAndNbJob(jobid)
            self.setJobIdFromSge( job, jobid )
            os.remove( "jobid.stdout" )
        return returnStatus
        
        
    ## Get the list of nodes where jobs of one group were executed
    #
    # @param tablename string table name where jobs are recored   
    # @param groupid string a group identifier of job series 
    # @return lNodes list of nodes names
    #
    def getNodesListByGroupId( self, tableName, groupId ):
        qry = "SELECT node FROM %s" % tableName
        qry += " WHERE groupid='%s'" % groupId
        self.execute( qry )
        res = self.fetchall()
        lNodes = []
        for resTuple in res:
            lNodes.append(resTuple[0])
        return lNodes
    
    def _getJobidAndNbJob(self, jobid) :
        tab = []
        tab = jobid.split(".")
        jobid = tab[0]
        tab = tab[1].split(":")
        nbJob = tab[0]
        return jobid, nbJob
