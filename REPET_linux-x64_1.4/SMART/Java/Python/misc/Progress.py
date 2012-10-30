#
# Copyright INRA-URGI 2009-2010
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
# 
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
#
import sys
import time

class Progress(object):
    """Show the progress of a process"""

    def __init__(self, aim, message = "Progress", verbosity = 0):
        self.aim = aim
        self.progress = 0
        self.message = message
        self.length = -1
        self.verbosity = verbosity
        self.maxMessageSize = 50
        self.barSize = 80
        self.startTime = time.time()
        self.elapsed = 0
        if len(self.message) > self.maxMessageSize:
            self.message = self.message[0:self.maxMessageSize-3] + "..."
        self.show()


    def inc(self):
        self.progress += 1
        self.show()
        
        
    def getPrintableElapsedTime(self, time):
        timeHou = int(time) / 3600
        timeMin = int(time) / 60 - 60 * timeHou
        timeSec = int(time) % 60
        if timeHou > 0:
            return "%3dh %2dm" % (timeHou, timeMin)
        if timeMin > 0:
            return "%2dm %2ds" % (timeMin, timeSec)
        return "%2ds" % (timeSec)


    def show(self):
        if not self.verbosity:
            return
        if self.aim == 0:
            return
        messageSize = len(self.message)
        length = int(self.progress / float(self.aim) * self.barSize)
        elapsed = int(time.time() - self.startTime)
        if (length > self.length) or (elapsed > self.elapsed + 10):
            self.length = length
            self.elapsed = elapsed            
            string = "%s%s[%s%s] %d/%d" % (self.message, " " * max(0, self.maxMessageSize - messageSize), "=" * self.length, " " * (self.barSize - self.length), self.progress, self.aim)
            if elapsed > 5:
                done = float(self.progress) / self.aim
                total = elapsed / done
                remaining = total - elapsed
                string += " ETA: %s " % (self.getPrintableElapsedTime(remaining))
            string += "\r"
            sys.stdout.write(string)
            sys.stdout.flush()


    def done(self):
        if self.verbosity:
            messageSize = len(self.message)
            elapsed = time.time() - self.startTime
            print "%s%s[%s] %d completed in %s " % (self.message, " " * max(0, self.maxMessageSize - messageSize), "=" * self.barSize, self.aim, self.getPrintableElapsedTime(elapsed))
