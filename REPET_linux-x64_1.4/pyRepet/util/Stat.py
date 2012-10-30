import math

#------------------------------------------------------------------------------

class Stat:

    def __init__( self, lValues=[] ):
        self.reset()
        if lValues != []:
            self.fill( lValues )

    def reset( self ):
        self.values = []
        self.sum = 0.0
        self.sum2 = 0.0
        self.n = 0
        self.max = 0.0
        self.min = 0.0

    def add( self, v ):
        self.values.append( float(v) )
        self.sum = self.sum + float(v)
        self.sum2 = self.sum2 + float(v) * float(v)
        self.n = self.n + 1
        if v > self.max:
            self.max = float(v)
        if self.n == 1:
            self.min = float(v)
        elif v < self.min:
            self.min = float(v)
            
    def fill( self, lValues ):
        for v in lValues:
            self.add( v )
            
    def getSum( self ):
        """Get the sum of all values of the sample."""
        if self.sum == 0.0 and len(self.values) > 0:
            for v in self.values:
                self.sum += float(v)
        return self.sum
    
    def mean( self ):
        """Get the arithmetic mean of the sample."""
        if self.n == 0:
            return 0
        else:
            return self.sum / float(self.n)

    def var( self ):
        """Get the variance of the sample."""
        if self.n < 2 or self.mean() == 0.0:
            return 0
        else:
            return (self.sum2)/(self.n-1) - (self.n)/(self.n-1)*(self.mean())*(self.mean())

    def cv( self ):
        """Get the coefficient of variation of the sample."""
        if self.n < 2 or self.mean() == 0.0:
            return 0
        else:
            return self.sd() / self.mean()

    def sd( self ):
        """Get the standard deviation."""
        return math.sqrt( self.var() )

    def median( self ):
        """Get the median."""
        if len(self.values) == 0:
            return "NA"
        if len(self.values) == 1:
            return self.values[0]
        self.values.sort()
        m = int( math.ceil( len(self.values) / 2.0 ) )
        if len(self.values) % 2:
            return self.values[m-1]
        else:
            return ( self.values[m-1] + self.values[m] ) / 2.0

    def kurtosis( self ):
        """
        Get the kurtosis (measure of whether the data are peaked or flat relative to a normal distribution, 'coef d'aplatissement ' in french)).
        k = 0 -> completely flat
        k = 3 -> same as normal distribution
        k >> 3 -> peak
        """
        numerator = 0
        for i in self.values:
            numerator += math.pow( i - self.mean(), 4 )
        return numerator / ( (self.n - 1) * self.sd() )

    def string( self ):
        msg = ""
        msg += "n=%d" % ( self.n )
        msg += " mean=%5.3f" % ( self.mean() )
        msg += " var=%5.3f" % ( self.var() )
        msg += " sd=%5.3f" % ( self.sd() )
        msg += " min=%5.3f" % ( self.min )
        median = self.median()
        if median == "NA":
            msg += " med=%s" % ( median )
        else:
            msg += " med=%5.3f" % ( median )
        msg += " max=%5.3f" % ( self.max )
        return msg

    def view( self ):
        """Print descriptive statistics."""
        print self.string()

    def sort( self ):
        v = []
        v.extend( self.values )
        v.sort()
        return v

    def quantile( self, perc ):
        if self.n == 0:
            return 0
        else:
            return self.sort()[int(self.n*perc)]

    def stringQuantiles( self ):
        return "n=%d min=%5.3f Q1=%5.3f median=%5.3f Q3=%5.3f max=%5.3f" % \
               (self.n,self.min,self.quantile(0.25),self.quantile(0.5),self.quantile(0.75),self.max)

    def viewQuantiles( self ):
	print self.stringQuantiles()

    def __eq__( self, o ):
        self.values.sort()
        o.values.sort()
        if self.values == o.values:
            return True
        else:
            return False

#------------------------------------------------------------------------------

class Quantile( Stat ):

    def __init__( self ):
        self.reset()

    def reset( self ):
        Stat.reset( self )
        self.values = []

    def add( self, v ):
        Stat.add( self, v )
        self.values.append( v )

    def sort( self ):
        v = []
        v.extend( self.values )
        v.sort()
        return v

    def string( self ):
         return "n=%d min=%5.3f Q1=%5.3f median=%5.3f Q3=%5.3f max=%5.3f" % \
               (self.n,self.min,self.quantile(0.25),self.quantile(0.5),self.quantile(0.75),self.max)
     
    def quantile( self, perc ):
        if self.n == 0:
            return 0
        else:
            return self.sort()[int(self.n*perc)]
