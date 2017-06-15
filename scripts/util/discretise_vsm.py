#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import sys
from naive.naive_util import *


def discretise_vsm(infile, outfile, method, nbins):

    data = readlist(infile)
    data = [re.split("\s+", line) for line in data]

    for line in data:
        assert len(line) == len(data[0])

    ## gather data per dimension:
    dimension_data = {}
    for line in data:
        for (i, item) in enumerate(line):            
            if i not in dimension_data:
                dimension_data[i] = []
            dimension_data[i].append(item)

    ## train disc per dimensions:
    discretised_data = {}
    for (dim, datalist) in dimension_data.items():
        if dim == 0:
            discretised_data[dim] = dimension_data[dim]
        else:
            disc = Discretiser()
            disc.train(datalist, number_bins=int(nbins), method=method)
            discretised_data[dim] = [str(disc.bin(value)) for value in datalist]


    #print discretised_data.keys()

    ## write data out:
    m = len(data)
    n = len(data[0])


    outdata = []
    for line in range(m):
        outline = []
        #print range(len(data[0]))
        for col in range(n):
            #print line
            #print col
            outline.append(discretised_data[col][line])
        outline = " ".join(outline)
        outdata.append(outline)
    writelist(outdata, outfile, uni=True)

                    
class Discretiser:
    """
    Objects of this class assign any real number to a numbered bin.
    
    Instance methods handle training and application of a Discretiser.
                        
    """
    ##def __init__(self):  ## values, field_name,

        
    def train(self, values, number_bins=50, method="uniform"):
        """
         Methods of discretisation: uniform
                       standard_set -- (name from Breiman et al. 1993 section 2.4.1) put boundaries between 
                               each consecutive pair of values
                               -- ignore number_bins in this case        
        """
        assert method in ["uniform","standard_set"],"Unknown method of discretisation"  ## add , "quantiles"

        values = [float(value) for value in values]



        self.bins = []


        if method=="uniform":
                                 
            maxi = max(values)
            mini = min(values) 
            step = (maxi-mini) / float(number_bins)
                
            lower_edge = float("-inf") ## platform-specific behaviour pre-python 3?
            upper_edge = mini + step   
            
            for k in range(1, number_bins):
                self.bins.append((lower_edge, upper_edge, k))
                lower_edge = upper_edge
                upper_edge = upper_edge + step 
 
            ## final bin        
            k = number_bins
            upper_edge = float("inf")
            self.bins.append((lower_edge, upper_edge, k))

        elif method=="standard_set":
            
            # Get sorted types
            values = list(set(values))
            if len(values) > 1000:
                sys.exit("Using standard set for discretisation gives %s bins!"%(len(values)))
            values.sort()

            lower_edge = float("-inf") ## platform-specific behaviour pre-python 3?
            for i in range(1,len(values)):

                ## diff in val between last and this one
                diff = values[i] - values[i-1]
                upper_edge = values[i] - (0.5 * (diff))
                self.bins.append((lower_edge, upper_edge, i))
                lower_edge=upper_edge
            ## final bin        
            i = len(values)
            upper_edge = float("inf")                
            self.bins.append((lower_edge, upper_edge, i))

        elif method=="quantiles":
            sys.exit("NOT IMPLEMENTED ")
        else:
            sys.exit("unknown disc method")
        """   ### NOT IMPLEMENTED ------------
        
            for j in range(n):   

                ## find bins over indexes:  
                bin_edges=[]       
                step=m / float(number_bins)
                binedge= step
                for k in range(number_bins-1):
                    binedge+= step
                    bin_edges.append(binedge)  
                
                ## discretise:               
                vals=feats[:,j]
                vals = vals.tolist()
                vals_order = zip(vals, range(len(vals)))
                vals_order.sort()
                order = [order for (val, order) in vals_order]
                order_rank = zip(order, range(len(order)))
                order_rank.sort()
                rank=[r for (o,r) in order_rank]
                
                for i in range(m):
                    disc_feats[i,j] = bin(rank[i], bin_edges)        
        """  



    def save(self, fname):
        string_rep = ["%s %s %s"%(lower_edge, upper_edge, bin_number) for \
                    (lower_edge, upper_edge, bin_number) in self.bins]
        (disc_direc, junk) = os.path.split(fname)            
        if not os.path.isdir(disc_direc):
            os.makedirs(disc_direc)
        writelist(string_rep, fname)    

    def load(self, fname):
        string_rep = readlist(fname)   
        data = [line.split(" ") for line in string_rep]
        data = [(float(lower_edge), float(upper_edge), int(bin_number)) for \
                    (lower_edge, upper_edge, bin_number) in data]
#        (direc, attribute) = os.path.split(fname)            
        self.bins = data 
#        self.attribute = attribute           
                    
                    
    def bin(self, value):
              
        value = float(value)
        for (lower_edge, upper_edge, bin_number) in self.bins:   
            if (value > lower_edge) and (value <= upper_edge):
                return bin_number
        sys.exit("No bin found -- something is wrong with the bin-set")


    def process(self, utt):
        #nodes = [el for el in utt.iterdescendants()] + [utt]
        for node in utt.all_nodes():
            if self.attribute in node.keys():
                binned = self.bin(node.get(self.attribute))
                node.set(self.attribute + "_bin", str(binned))  
            ## Discretise padding attributes:
            if self.attribute + "_PADDING" in node.keys():
                binned = self.bin(node.get(self.attribute  + "_PADDING" ))
                node.set(self.attribute + "_bin_PADDING", str(binned)) 

    def get_questions(self):
        """
        Return question names and values (values as Python lists, not formatted as HTK itemlists)
        """
        
        questions = []
        qnames = []  ## only used for finding duplicate names

        ## First get "single bin" questions:            
        for (lower_edge, upper_edge, bin_number) in self.bins[1:-1]:
            question_name = '%s_between_%.3f_and_%.3f'%(self.field_name, lower_edge, upper_edge) 
            question_values = [bin_number]
            
            ## Take care that there are no duplicate names by adjusting precision:
            if (question_name) in qnames:
                i = 4 ## starting value was 3
                while question_name in qnames:
                    format_string = '%%s_between_%%.%sf_and_%%.%sf'%(i, i)
                    question_name = format_string%(self.field_name, lower_edge, upper_edge) 
                    i += 1
                    
            questions.append((question_name, question_values))
            qnames.append(question_name)
            
        ## ... then get range questions:
        for (lower_edge, upper_edge, bin_number) in self.bins[:-1]:
            question_name = '%s_<=%.3f'%(self.field_name, upper_edge) 
            question_values = range(1, bin_number + 1)
            
            ## Take care that there are no duplicate names by adjusting precision:            
            if question_name in qnames:
                i = 4 ## starting value was 3
                while question_name in qnames:
                    format_string = '%%s_<=%%.%sf'%(i)
                    question_name = format_string%(self.field_name, upper_edge) 
                    i += 1            
                    
            questions.append((question_name, question_values))
            qnames.append(question_name)
            
        return questions
        



if __name__=="__main__":

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Usage: ......  "
        sys.exit(1)

    # e.g. 

    try:

        infile = sys.argv[1]
        outfile = sys.argv[2]
        method = sys.argv[3]
        nbins = sys.argv[4]

    except:
        usage()

    print infile
    #################################################

    discretise_vsm(infile, outfile, method, nbins)

