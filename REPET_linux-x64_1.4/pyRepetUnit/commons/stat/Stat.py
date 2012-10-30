#from pyRepet.util.Stat import Stat
import math

class Stat(object):

    def __init__(self, lValues = []):
        self.reset()
        if lValues != []:
            self.fill(lValues)
    
    def __eq__(self, o):
        self._lValues.sort()
        o._lValues.sort()
        return self._lValues == o._lValues and self._sum == o._sum and self._sumOfSquares == o._sumOfSquares \
            and self._n == self._n and self._min == o._min and self._max == o._max
            
    def getValuesList(self):
        return self._lValues
    
    def getSum(self):
        return self._sum
    
    def getSumOfSquares(self):
        return self._sumOfSquares
    
    def getValuesNumber(self):
        return self._n
    
    def getMin(self):
        return self._min
    
    def getMax(self):
        return self._max

    ## Reset all attributes
    #
    def reset(self):
        self._lValues = []
        self._sum = 0.0
        self._sumOfSquares = 0.0
        self._n = 0
        self._max = 0.0
        self._min = 0.0

    ## Add a value to Stat instance list and update attributes
    #
    # @param v float value to add
    #    
    def add(self, v):
        self._lValues.append( float(v) )
        self._sum += float(v)
        self._sumOfSquares += float(v) * float(v)
        self._n = self._n + 1
        if v > self._max:
            self._max = float(v)
        if self._n == 1:
            self._min = float(v)
        elif v < self._min:
            self._min = float(v)
         
    ## Add a list of values to Stat instance list and update attributes
    #
    # @param lValues list of float list to add
    #    
    def fill(self, lValues):
        for v in lValues:
            self.add(v)
    
    ## Get the arithmetic mean of the Stat instance list
    #
    # @return float
    #
    def mean(self):
        if self._n == 0:
            return 0
        else:
            return self._sum / float(self._n)
    
    ## Get the variance of the sample
    # @note we consider a sample, not a population. So for calculation, we use n-1
    #
    # @return float
    #
    def var(self):
        if self._n < 2 or self.mean() == 0.0:
            return 0
        else:
            return self._sumOfSquares / float(self._n - 1) - self._n / float(self._n - 1) * self.mean() * self.mean()

    ## Get the standard deviation of the sample
    #
    # @return float
    #
    def sd(self):
        return math.sqrt( self.var() )

    ## Get the coefficient of variation of the sample
    #
    # @return float
    #
    def cv(self):
        if self._n < 2 or self.mean() == 0.0:
            return 0
        else:
            return self.sd() / self.mean()

    ## Get the median of the sample
    #
    # @return number or "NA" (Not available)
    #
    def median( self ):
        if len(self._lValues) == 0:
            return "NA"
        if len(self._lValues) == 1:
            return self._lValues[0]
        self._lValues.sort()
        m = int( math.ceil( len(self._lValues) / 2.0 ) )
        if len(self._lValues) % 2:
            return self._lValues[m-1]
        else:
            return ( self._lValues[m-1] + self._lValues[m] ) / 2.0
        
    ## Get the kurtosis (measure of whether the data are peaked or flat relative to a normal distribution, 'coef d'aplatissement ' in french)).
    #  k = 0 -> completely flat
    #  k = 3 -> same as normal distribution
    #  k >> 3 -> peak
    #
    # @return float 
    #
    def kurtosis(self):
        numerator = 0
        for i in self._lValues:
            numerator += math.pow( i - self.mean(), 4 )
        return numerator / float(self._n - 1) * self.sd() 

    ## Prepare a string with calculations on your values
    #
    # @return string 
    #
    def string(self):
        msg = ""
        msg += "n=%d" % ( self._n )
        msg += " mean=%5.3f" % ( self.mean() )
        msg += " var=%5.3f" % ( self.var() )
        msg += " sd=%5.3f" % ( self.sd() )
        msg += " min=%5.3f" % ( self.getMin() )
        median = self.median()
        if median == "NA":
            msg += " med=%s" % (median)
        else:
            msg += " med=%5.3f" % (median)
        msg += " max=%5.3f" % ( self.getMax() )
        return msg
    
    ## Print descriptive statistics
    #
    def view(self):
        print self.string()

    ## Ascending sorted list of values
    #
    # @return list
    #
    def sort( self ):
        v = []
        v.extend( self._lValues )
        v.sort()
        return v
    
    ## Give the quantile corresponding to the chosen percentage
    #
    # @return number 
    #
    def quantile( self, percentage ):
        if self._n == 0:
            return 0
        else:
            return self.sort()[int(self._n * percentage)]
        
    ## Prepare a string with quantile values
    #
    # @return string
    #    
    def stringQuantiles( self ):
        return "n=%d min=%5.3f Q1=%5.3f median=%5.3f Q3=%5.3f max=%5.3f" % \
               (self._n, self.getMin(), self.quantile(0.25), self.quantile(0.5), self.quantile(0.75), self.getMax())

    ## Print quantiles string
    #
    def viewQuantiles( self ):
        print self.stringQuantiles()