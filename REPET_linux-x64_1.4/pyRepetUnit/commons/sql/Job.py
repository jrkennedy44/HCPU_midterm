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

## Job informations to launch a command on a cluster.
#
class Job( object ):
    
    ## Constructor
    #
    #   @param tablename table name to record the jobs
    #   @param jobid the job identifier
    #   @param jobname the job name
    #   @param groupid the group identifier to record related job series 
    #   @param queue queue name of the batch job manager
    #   @param command command launched
    #   @param node cluster node name where the execution takes place
    #   @param launcherFile file name launched as job
    #   @param lResources resources (memory, time...) but need to conform to SGE/PBS syntax !
    #
    def __init__( self, tablename="", jobid=0, jobname="", groupid="", queue="", \
                  command="", launcherFile="", node="", lResources="mem_free=1G", parallelEnvironment="" ):
        self.tablename = tablename
        if str(jobid).isdigit():
            self.jobid = int(jobid)
            self.jobname = jobname
        else:
            self.jobname = jobid
            self.jobid = 0
        self.jobid = jobid
        self.groupid = groupid
        self.setQueue( queue )
        self.command = command
        self.launcher = launcherFile
        self.node = node
        self.lResources = lResources
        self.parallelEnvironment = parallelEnvironment
        
        
    def setQueue( self, queue ):
        self.queue = ""
        if queue != "none":
            self.queue = queue
    
    def __eq__(self, o):
        if self.tablename == o.tablename and self.jobid == o.jobid and self.jobname == o.jobname and self.groupid == o.groupid and self.queue == o.queue and self.command == o.command and self.launcher == o.launcher and self.node == o.node and self.lResources == o.lResources and self.parallelEnvironment == o.parallelEnvironment:
            return True
        return False
