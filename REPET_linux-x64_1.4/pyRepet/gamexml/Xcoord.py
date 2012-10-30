from pyRepet.coord.Match import *
from pyRepet.coord.Path import *
from pyRepet.coord.Set import *
from pyRepet.coord.Map import *
from pyRepet.coord.Range import *

class Xmap(Map):
    def get_name(self):
        return self.name.replace("|","/")
    
    def add_span(self,doc,set):
        result_span=doc.createElement('result_span')

        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.seqname)
        sp1=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.start)))
        sp1.appendChild(start1)
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(end1)
        result_span.appendChild(relship1)     

        relship2=doc.createElement('seq_relationship')
        relship2.setAttribute('type','subject')
        relship2.setAttribute('seq',self.get_name()+'::'+str(self.get_id()))
        sp2=doc.createElement('span')
        start2=doc.createElement('start')
        start2.appendChild(doc.createTextNode("-1"))
        sp2.appendChild(start2)
        end2=doc.createElement('end')
        end2.appendChild(doc.createTextNode("-1"))
        sp2.appendChild(end2)
        relship2.appendChild(sp2)
        result_span.appendChild(relship2)

        score=doc.createElement('score')
        score.appendChild(doc.createTextNode("-1"))
        result_span.appendChild(score)

        set.appendChild(result_span)

class Xset(Set):
    def get_name(self):
        return self.name.replace("|","/")

    def add_span(self,doc,set):
        result_span=doc.createElement('result_span')

        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.seqname)
        sp1=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.start)))
        sp1.appendChild(start1)
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(end1)
        result_span.appendChild(relship1)     

        relship2=doc.createElement('seq_relationship')
        relship2.setAttribute('type','subject')
        relship2.setAttribute('seq',self.get_name()+'::'+str(self.get_id()))
        sp2=doc.createElement('span')
        start2=doc.createElement('start')
        start2.appendChild(doc.createTextNode("-1"))
        sp2.appendChild(start2)
        end2=doc.createElement('end')
        end2.appendChild(doc.createTextNode("-1"))
        sp2.appendChild(end2)
        relship2.appendChild(sp2)
        result_span.appendChild(relship2)

        score=doc.createElement('score')
        score.appendChild(doc.createTextNode("-1"))
        result_span.appendChild(score)
        
        set.appendChild(result_span)

class Xpath(Path):
    def get_name(self):
        return self.range_subject.seqname.split("|")[-1]
    
    def add_span(self,doc,set):
        #print span
        result_span=doc.createElement('result_span')
        set.appendChild(result_span)
        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.range_query.seqname)
        relship2=doc.createElement('seq_relationship')
        relship2.setAttribute('type','subject')
        relship2.setAttribute('seq',self.get_name()+'::'+str(self.get_id()))
        score=doc.createElement('score')
        result_span.appendChild(relship1)
        result_span.appendChild(relship2)
        score.appendChild(doc.createTextNode(str(self.identity)))
        result_span.appendChild(score)
        sp1=doc.createElement('span')
        sp2=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.range_query.start)))
        start2=doc.createElement('start')
        start2.appendChild(doc.createTextNode(str(self.range_subject.start)))
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.range_query.end)))
        end2=doc.createElement('end')
        end2.appendChild(doc.createTextNode(str(self.range_subject.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(start1)
        sp1.appendChild(end1)
        relship2.appendChild(sp2)
        sp2.appendChild(start2)
        sp2.appendChild(end2)
        
class Xmatch(Match):    
    def get_name(self):
        return self.range_subject.seqname.split("|")[-1]

    def add_span(self,doc,set):
        #print span
        result_span=doc.createElement('result_span')
        set.appendChild(result_span)
        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.range_query.seqname)
        relship2=doc.createElement('seq_relationship')
        relship2.setAttribute('type','subject')
        relship2.setAttribute('seq',self.get_name()+'::'+str(self.get_id()))
        score=doc.createElement('score')
        result_span.appendChild(relship1)
        result_span.appendChild(relship2)
        score.appendChild(doc.createTextNode(str(self.identity)))
        result_span.appendChild(score)
        sp1=doc.createElement('span')
        sp2=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.range_query.start)))
        start2=doc.createElement('start')
        start2.appendChild(doc.createTextNode(str(self.range_subject.start)))
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.range_query.end)))
        end2=doc.createElement('end')
        end2.appendChild(doc.createTextNode(str(self.range_subject.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(start1)
        sp1.appendChild(end1)
        relship2.appendChild(sp2)
        sp2.appendChild(start2)
        sp2.appendChild(end2)

class Xalign(Match):    
    def get_name(self):
        return self.range_subject.seqname.split("|")[-1]

    def set_align(self,alq,als):
        self.alignQ=alq
        self.alignS=als
        count=0
        count_id=0
        for i in xrange(len(alq)):
            if alq[i]!="-" and als[i]!="-":
                count+=1
                if alq[i]==als[i]:
                    count_id+=1
        if count==0:
            self.identity=0.0
        else:
            self.identity=(float(count_id)/count)*100
        
    def add_span(self,doc,set):
        #print span
        result_span=doc.createElement('result_span')
        set.appendChild(result_span)
        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.range_query.seqname)
        alq=doc.createElement('alignment')
        alq.appendChild(doc.createTextNode(self.alignQ))
        relship1.appendChild(alq)
        relship2=doc.createElement('seq_relationship')
        relship2.setAttribute('type','subject')
        relship2.setAttribute('seq',self.get_name()+'::'+str(self.get_id()))
        als=doc.createElement('alignment')
        als.appendChild(doc.createTextNode(self.alignS))
        relship2.appendChild(als)
        score=doc.createElement('score')
        result_span.appendChild(relship1)
        result_span.appendChild(relship2)
        score.appendChild(doc.createTextNode(str(self.identity)))
        result_span.appendChild(score)
        sp1=doc.createElement('span')
        sp2=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.range_query.start)))
        start2=doc.createElement('start')
        start2.appendChild(doc.createTextNode(str(self.range_subject.start)))
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.range_query.end)))
        end2=doc.createElement('end')
        end2.appendChild(doc.createTextNode(str(self.range_subject.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(start1)
        sp1.appendChild(end1)
        relship2.appendChild(sp2)
        sp2.appendChild(start2)
        sp2.appendChild(end2)

class Xrange(Range):
    def get_name(self):
        return self.name.split("|")[-1]

    def add_span(self,doc,set):
        result_span=doc.createElement('result_span')
        set.appendChild(result_span)
        relship=doc.createElement('seq_relationship')
        relship.setAttribute('type','query')
        relship.setAttribute('seq',self.seqname)
        sp=doc.createElement('span')
        start=doc.createElement('start')
        end=doc.createElement('end')
        start.appendChild(doc.createTextNode(str(self.start)))
        end.appendChild(doc.createTextNode(str(self.end)))
        sp.appendChild(start)
        sp.appendChild(end)
        relship.appendChild(sp)
        result_span.appendChild(relship)
        score=doc.createElement('score')
        score.appendChild(doc.createTextNode(str(self.score)))
        result_span.appendChild(score)

class Xannot(Path):
    def get_name(self):
        return self.range_subject.seqname.split("|")[-1]
    
    def add_span(self,doc,set):
        #print span
        result_span=doc.createElement('feature_span')
        set.appendChild(result_span)
        
        type=doc.createElement('type')
        type.appendChild(doc.createTextNode("exon"))
        result_span.appendChild(type)
        
        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.range_query.seqname)
        sp1=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.range_query.start)))
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.range_query.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(start1)
        sp1.appendChild(end1)
        result_span.appendChild(relship1)

class XsetAnnot(Set):
    def get_name(self):
        return self.name.split("|")[-1]
    
    def add_span(self,doc,set):
        #print span
        result_span=doc.createElement('feature_span')
        set.appendChild(result_span)
        
        type=doc.createElement('type')
        type.appendChild(doc.createTextNode("exon"))
        result_span.appendChild(type)
        
        relship1=doc.createElement('seq_relationship')
        relship1.setAttribute('type','query')
        relship1.setAttribute('seq',self.seqname)
        sp1=doc.createElement('span')
        start1=doc.createElement('start')
        start1.appendChild(doc.createTextNode(str(self.start)))
        end1=doc.createElement('end')
        end1.appendChild(doc.createTextNode(str(self.end)))
        relship1.appendChild(sp1)
        sp1.appendChild(start1)
        sp1.appendChild(end1)
        result_span.appendChild(relship1)
