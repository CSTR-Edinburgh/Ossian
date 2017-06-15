#!/usr/bin/python


import sys, os, re, math, string
from string import strip
from argparse import ArgumentParser

## Script to plot HTK format decision tree

## Oliver Watts
## s0676515@sms.ed.ac.uk

## Run the script with no arguments for some pointers.


def get_subtree(tree, start_node):
     
     """
     take tree_dict tree. return subtree whose root is start_node
     """
         
     plot_nodes = [start_node]
     finished=False
     while not finished:
         extra_nodes = []
         for node in plot_nodes:
             children = []
             if "yes_branch" in tree[node]:
                 children.append(tree[node]["yes_branch"])
             if "no_branch" in tree[node]:
                 children.append(tree[node]["no_branch"])
             for child in children:
                 if child not in extra_nodes and child not in plot_nodes:
                     extra_nodes.append(child)
         if extra_nodes == []:
             finished=True
         else:
             plot_nodes.extend(extra_nodes)
             
     sub_tree = {}
     for node in tree.keys():
         if node in plot_nodes:
             sub_tree[node] = tree[node]
             
     return sub_tree



## as parse_htsengine_treefile below but more general
def parse_treefile_general(treefile, get_questions=False):
    """Return list of sublists, one sublist for each state.
    Sublist entries are quadruples like:  
    (2765, 'C-Syl_er', 2912, 'dur_s2_2398'),
    ...
    i.e. (nodenumber, qname, lbranch_node_number, rbranch_node_number)
    ...
    where "nodenumbers" are strings, these are leafnode names
    
    order is no_branch, yes_branch
    """


    f = open(treefile, "r")
    file_data = f.readlines()
    f.close()
    
    file_data = [line.strip("\n") for line in file_data]
    data = [line for line in file_data if line[:2] != "QS"]  ## strip qwuestions 
    
    if get_questions:
        questions = [line for line in file_data if line[:2] == "QS"] 
        questions = [line.replace("{", "").replace("}", "") for line in questions]
        questions = [line.strip(" ") for line in questions]
        questions = [re.split("\s+", line) for line in questions]
        for line in questions:
            assert len(line) == 3,line # "Line does not contain 3 items: %s"%(" ".join(line))
        questions = dict([(line[1], line[2]) for line in questions])

    data = "\n".join(data)
    
    bracketed = re.findall("\{[^\}]*\}",data)
    
    #print bracketed
    #### bracketed should consist of name, tree, name, tree... -- sort it out
    if len(bracketed) % 2 != 0:
        print "bracketed should consist of name, tree, name, tree"
        sys.exit(1)
        
    data = []
    i=1
    for item in bracketed:
        #print item
        if i%2!=0.0: ## if i odd
            name = item
        else:
            tree = item
            data.append((name,tree))
        i+=1

    def strip_quotes(x):
        x = string.strip(x, '"') #("\_|-", "", x)          
        return  x     
            
    def to_num(x):
        if x[0] == "-" or x[0] == "0":
            return int(math.fabs(int(x)))
        else:
            return strip_quotes(x)
    #print data
    names_trees = []
    for (name, treestring) in data:
        
        #### tree
        treestring = treestring.strip("{} \n")

        treestring = re.split("\n", treestring)
        treestring = [line.strip(" \n") for line in treestring]        
        treestring = [re.split("\s+", line) for line in treestring]  

        tree = [(to_num(num), quest, to_num(left), to_num(right)) for (num, quest, left, right) in treestring]


        ### name
        treestring = name.strip("{} \n")

        names_trees.append((name, tree))
        
    ##print names_trees   
    if get_questions:
        return names_trees, questions                
    else:
        return names_trees                
    

def treelist_to_dict(treelist):
    """
    take list with entries
    (nodenumber, qname, lbranch_node_number, rbranch_node_number)
    return dict with dict entries
    nodenumber: {"question": qname, "no_branch": lb, "yes_branch": rb}
    """   
    treelist = [(node, {"question": qname, "no_branch": no_branch,\
               "yes_branch": yes_branch}) \
               for (node, qname, no_branch, yes_branch) in treelist]
    tree_dict = dict(treelist)
    return tree_dict
    
    

def add_plot_info_to_treedict(treedict, colour="leaf_nonleaf", text="question", shape="ellipses", highlight_indexes=None):

    salmon     = '#FF8877'
    piss       = '#DDFFBB'
    grape      = "#9900FF"
    blue       = "#3366CC"
    nice_green = "#339900"
    dark_blue  = "#000066"
    good_red   = "#CC0000"
    yolky      = "#FFCC00"


    for node in treedict.keys():

        ### 1) colour
        if colour == "leaf_nonleaf":  ## default
        
            if "no_branch" in treedict[node]:
                treedict[node]["colour"] = piss
            else:
                if highlight_indexes:
                    print treedict[node]
                    index = int(treedict[node]["leaf_name"].split("_")[-1])
                    if index in highlight_indexes:
                        treedict[node]["colour"] = blue
                    else:
                        treedict[node]["colour"] = salmon
                        
                else:
                    treedict[node]["colour"] = salmon
      #      elif colour == "question_macro_merge":
       #         if treedict[node]
        
        ### 2) text
        if text=="question":
        
            if "question" not in treedict[node]:
                treedict[node]["text"] = str(node)
            elif treedict[node]["question"] == "MERGE":
                treedict[node]["text"] = str(node)
            else:
                treedict[node]["text"] = treedict[node]["question"]
        
        
        elif text=="dominant_phone_and_question":
        
            dphone=treedict[node]["dominant_phone"]
            dpercent=treedict[node]["percent_dominance"]
            dom_info="%s (%s) -- "%(dphone, dpercent)
                        
            if "question" not in treedict[node]:
                treedict[node]["text"] = dom_info + str(node)
            elif treedict[node]["question"] == "MERGE":
                treedict[node]["text"] = dom_info + str(node)
            else:
                treedict[node]["text"] = dom_info + treedict[node]["question"]                
        
        
        ### 3) shape
        if shape=="ellipses":

            treedict[node]["shape"] = "ellipse"

    return treedict
    

    
def add_leaf_entries(tree):

    for node in tree.keys():
        print tree[node]
        for child in ["yes_branch", "no_branch"]:
            child = tree[node][child]
            if child not in tree:
                tree[child] = {"leaf_name": child}
    return tree

####### revised version --- take treedict that must already contain all info to be plotted:
####### {0, {'node_label': xxx, 'no_branch': xxx, 'yes_branch': xxx, 'colour': xxx, 'shape': xxx}}
def make_dot_file_simple_questions(dotfile, tree, macroroot="mcep"):
    """
    
    """

    ## All nodes should be dict keys (e.g. after percolating).
    ## Plot info (colour, shape, label) should already be in tree (e.g. from add_plot_info_to_treedict)
    ## However, add number to each node for graphviz definition: won't be visible in plot, numbers 
    ## not same as HTS node numbers; necessary because graphviz needs numbers also for leaf nodes

    i = 0    
    for node in tree.keys():
        tree[node]["graphviz_number"] = i
        i+=1
       
        
    
    ## Get transitions with y/n
    arc_list = []

    for node in tree.keys():
        if "yes_branch" in tree[node]:
            yes_node = tree[node]["yes_branch"]
            #print yes_node
            #print "........"
            ### new version -- map to graphviz numbers later
            #arc_list.append((tree[node]["graphviz_number"], tree[yes_node]["graphviz_number"], "Yes"))
            arc_list.append((node, yes_node, "Yes"))
      
        if "no_branch" in tree[node]:
            no_node = tree[node]["no_branch"]
            #arc_list.append((tree[node]["graphviz_number"], tree[no_node]["graphviz_number"], "No"))
            arc_list.append((node, no_node, "No"))
            
            


#     ## impose weights for hammock:
#     if hammock:
#         new_arc_list = []
#         for  (fro, to, label, weight) in arc_list:
#             if tree[fro]["text"] == tree[to]["text"]:
#                 new_arc_list.append((fro, to, label, 0)) ## small weight to hammock middle
#             else:
#                 new_arc_list.append((fro, to, label, 100))                
#         arc_list = new_arc_list
#         
    ### finally map to graphziv numbers:
    arc_list  =  [ (tree[fro]["graphviz_number"], tree[to]["graphviz_number"], label) \
                for (fro, to, label) in arc_list]

    ### write dot file
    header="""digraph G0 {\n size = "100.0,100.0"; \n  center = 1;  \
    \n ranksep = "0.4"; \n nodesep = "0.25";  \n """
    ##\n orientation = Landscape;
    

        
    f = open(dotfile, "w")
    f.write(header)  # dot header
    for node in tree.keys():
        number=tree[node]["graphviz_number"]    
        text  =tree[node]["text"]    
        shape =tree[node]["shape"]    
        colour=tree[node]["colour"]   

                
          
        f.write('%s [label = "%s" shape="%s" style="filled" color="%s"];\n'%(number,text,shape,colour))
    for (from_num,to_num, Y_N) in arc_list:
           # Y_N = "lab"
        f.write('%s -> { %s }  [arrowhead=none label="%s"] ;\n'%(from_num,to_num, Y_N))     

#     if hammock:
#         first_row =  [str(x) for x in first_row] 
#         first_row =  "{rank=same; " + " ".join(first_row) + "}\n"
#         f.write( first_row)  
#         second_row =  [str(x) for x in second_row] 
#         second_row =  "{rank=same; " + " ".join(second_row) + "}\n"
#         f.write( second_row)          
    f.write(" } ")  # dot footer                
    f.close()
          
          





def main_work():
  
    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-treefile', required=True, help="...")
    a.add_argument('-outdir', required=True, help="...")
    a.add_argument('-state', dest="state_to_draw", default=0, type=int, help="...")
    a.add_argument('-root', dest="start_node", default=0, type=int, help="...")
    a.add_argument('-highlight', dest="highlight_indexes",  help="...")

    opts = a.parse_args()



#            draw_hts_tree_simple.py treefile output_directory state_to_draw start_node
#            
#            State_to_draw:  we'll start numbering of states in the file at 0.
#            So, to plot the middle state of 5 emitting-state model (HTK "state 4"),
#            enter 2 here. If there is only one state's tree in file, this must be
#            0.
#            
#            To plot a sub tree, make start_node > 0; to plot whole tree, 
#            start_node is 0 (0 = root of tree)

    max_nodename_length = 20 

    if not os.path.isdir(opts.outdir):
        os.mkdir(opts.outdir)

    highlight_indexes = None
    if opts.highlight_indexes:
        highlight_indexes = [int(value) for value in opts.highlight_indexes.split(",")]


    ### 1) read trees
    print "Reading trees..."
        
    state_trees = parse_treefile_general(opts.treefile)
    (modelname,tree) = state_trees[opts.state_to_draw] ## take the one we want
    tree = treelist_to_dict(tree)

    for key in tree.keys():
        print "%s %s"%(key, tree[key]["question"])

    tree = add_leaf_entries(tree)

    ### add colour etc options here
    tree = add_plot_info_to_treedict(tree, highlight_indexes=highlight_indexes)     
     

    if opts.start_node != 0:
        tree = get_subtree(tree, opts.start_node)


    here = os.getcwd()
    ##for state_num in range(len(state_trees)):

        # filenames
        
    path,name = os.path.split(opts.treefile)
        
     

         
    #make_dot_file(dot, tree, max_nodename_length)

    dot  = os.path.join(opts.outdir, name+".state-%s.dot"%(opts.state_to_draw+2))
    ps   = os.path.join(opts.outdir, name+".state-%s.ps"%(opts.state_to_draw+2))
    svg  = os.path.join(opts.outdir, name+".state-%s.svg"%(opts.state_to_draw+2))
    #jpg  = os.path.join(opts.outdir, name+".state-%s.jpg"%(opts.state_to_draw+2))   
    png  = os.path.join(opts.outdir, name+".state-%s.png"%(opts.state_to_draw+2))        
    pdf  = os.path.join(opts.outdir, name+".state-%s.pdf"%(opts.state_to_draw+2))
    fig  = os.path.join(opts.outdir, name+".state-%s.fig"%(opts.state_to_draw+2)) 


    make_dot_file_simple_questions(dot, tree)
    os.system("cd " + opts.outdir)

    ### dot
    # possible formats:   canon cmap cmapx dia dot fig gd gd2 gif hpgl imap ismap 
    # jpeg jpg mif mp pcl pic plain plain-ext png ps ps2 svg svgz vrml vtx wbmp xdot


    ### dot - svg
    comm = "dot -Tsvg " + dot + " > " + svg
    print comm
    os.system(comm)    

    ### dot - png
    comm = "dot -Tpng " + dot + " > " + png
    print comm
    os.system(comm)
          
    ### dot - ps
    comm = "dot -Tps " + dot + " > " + ps
    print comm
    os.system(comm)      

    ### dot - pdf
    comm = "dot -Tpdf " + dot + " > " + pdf
    print comm
    os.system(comm) 

    ### dot - fig
    comm = "dot -Tfig " + dot + " > " + fig
    print comm
    os.system(comm) 
          
    # # #     
    # # # ### ps - pdf

    # # # #  comm = "ps2pdfwr -c \"<< /PageSize [842 595] >> setpagedevice\" -f " + ps + " " + pdf
    # # # comm = "ghostscript -dQUIET -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sPAPERSIZE=a0 -sOutputFile="+pdf+" "+ps
    # # # print comm
    # # # os.system(comm)    
    #     
    os.system("cd "+ here)






if __name__=="__main__":

    main_work()
