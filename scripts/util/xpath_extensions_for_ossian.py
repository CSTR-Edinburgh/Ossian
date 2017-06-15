#!/usr/bin/env python
# -*- coding: utf-8 -*-
## This file is part of the Ossian text-to-speech toolkit: 
##   http://homepages.inf.ed.ac.uk/owatts/ossian/html/overview.html 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi
## April 2015 

import sys
import lxml
from lxml import etree
from lxml.etree import * 

## See here for adding new functions to lxml's xpath: http://lxml.de/3.2/extensions.html


## This is based on a function sent by Antti -- Oliver turned it into an xpath extension:
def simple_count(context, child, ancestor, count):
    print context, child, ancestor, count
    assert count in ['preceding', 'following', 'sum'], count
    ancestor = context.context_node.xpath('./ancestor::'+ancestor)
    target = context.context_node.xpath('./ancestor-or-self::'+child)
    
    if ancestor and target:
        #print "ok"
        siblings = ancestor[0].xpath('./descendant::'+child)
        if count == 'sum':
            return float(len(siblings))
        pos = 0
        for node in siblings:
            if node == target[0]:
                if count=='preceding':
                    #print node.get('text'), pos,
                    return float(pos)
                else:
                    return float(len(siblings)-pos)
            pos+=1
    else:
        return 0.0  ## standard xpath default value


### The same function broken down into 3 specialised functions with more 
## descriptive names and simpler interfaces:
def count_Xs_since_start_Y(context, X, Y):
    
    ancestor = context.context_node.xpath('./ancestor::'+Y)
    target = context.context_node.xpath('./ancestor-or-self::'+X)
    
    answer = 0.0  ## standard xpath default value
    if ancestor and target:
        siblings = ancestor[0].xpath('./descendant::'+X)
        for (pos, node) in enumerate(siblings):
            if node == target[0]:
                answer = float(pos+1)  ## osw: count from 1 (matches behaviour of count_Xs_till_end_Y)
    return answer


def count_Xs_till_end_Y(context, X, Y):
    
    ancestor = context.context_node.xpath('./ancestor::'+Y)
    target = context.context_node.xpath('./ancestor-or-self::'+X)
    
    answer = 0.0  ## standard xpath default value
    if ancestor and target:
        siblings = ancestor[0].xpath('./descendant::'+X)
        pos = 0
        for (pos, node) in enumerate(siblings):
            if node == target[0]:
                answer = float(len(siblings)-pos)
    return answer

def count_Xs_in_Y(context, X, Y):
    
    ancestor = context.context_node.xpath('./ancestor::'+Y)
    target = context.context_node.xpath('./ancestor-or-self::'+X)
    
    answer = 0.0  ## standard xpath default value
    if ancestor and target:
        siblings = ancestor[0].xpath('./descendant::'+X)
        answer = float(len(siblings))
    return answer



## register the functions.
## TODO: specify some non-default namespace?
ns = etree.FunctionNamespace(None)
ns['simple_count'] = simple_count
ns['count_Xs_since_start_Y'] = count_Xs_since_start_Y
ns['count_Xs_till_end_Y'] = count_Xs_till_end_Y
ns['count_Xs_in_Y'] = count_Xs_in_Y


    
