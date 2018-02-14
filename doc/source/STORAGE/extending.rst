
Extending Ossian with your own recipes and processors
=====================================================

Note on the recipes included here
---------------------------------


None of the recipes mentioned is intended to be in any way definitive -- for a given 
recipe, there are probably lots of different imaginable alternative pipelines of 
processors that will produce the same result. 

One major possible area of variation is processor granularity -- rather than, e.g. the 
separate segment_adder, silence_adder and endsilence_adder processors in demo05, it 
would be straightforward to write a single processor that performs the functions of all 
three. There has been a lot of indecision about a reasonable level of granularity during 
development. Trade-off between making elements so specific that they can’t be 
reconfigured, and making a recipe so long with so many elements that it can’t be 
understood. Personal taste; also depends on your role as to what level of granularity 
is a good one. If you just want to run existing recipes on new data, ....



 
