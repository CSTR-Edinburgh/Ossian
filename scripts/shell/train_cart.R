### R script


## Command line arguments
# trailingOnly=TRUE means that only arguments after --args are returned
args = commandArgs(trailingOnly = TRUE)
print("Script train_cart.R called with arguments:")
print(args)


data_fn = args[1]
outfile = args[2]


library(rpart)


my_data <- read.csv(file=data_fn,head=TRUE,sep=",")
## my_data$break_type <- as.factor(my_data$break_type) ## <-- make sure predictee is category
summary(my_data) 


my_control=rpart.control(minsplit=1, minbucket=1, xval=10, cp=0.0)
my_rpart <- rpart(response~., data=my_data, control=my_control   )

### tree before pruning:
print(my_rpart)
printcp(my_rpart)

## find smallest model with cp with 1SE of cross validation error:
min_error = min(my_rpart$cptable[,"xerror"])
min_error_std = min(my_rpart$cptable[,"xstd"])
thresh = min_error + min_error_std
for (i in seq(nrow(my_rpart$cptable))) {   
   print(my_rpart$cptable[i,"xerror"])
   if (my_rpart$cptable[i,"xerror"] < thresh) {
      best_cp=my_rpart$cptable[i,"CP"]
      break
      }
   } 
print(best_cp)
my_rpart <- prune(my_rpart, cp=best_cp)
print(my_rpart)

save(my_rpart, file=outfile)
