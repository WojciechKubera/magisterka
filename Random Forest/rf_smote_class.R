install.packages("keras")
install.packages("tensorflow")
install_keras()
install_tensorflow()
install.packages("ggplot2")
install.packages("caret")
install.packages("mtools")
install.packages('e1071', dependencies=TRUE)
install.packages("devtools")
devtools::install_github("RomeroBarata/bimba")

library(bimba)
library(caret)
library("ggplot2")
library(keras)
library(tensorflow)
library(randomForest)
set.seed(42)
tfe_enable_eager_execution(device_policy = "silent")
tf$executing_eagerly()
methods <- read.csv("C:\\studia_mag_zdobycze\\semestr 2 - mój\\magisterka\\class_results.csv")
# methods <- read.csv("C:\\studia_mag_zdobycze\\semestr 2 - mój\\magisterka\\metryki_data_class.csv")


recognized_smell = "blob"
# recognized_smell = "data class"
categories <- unique(methods$record_smell)
number_of_categories = length(categories)

#odzielenie zapachów jeden sample moze być dwoma róznymi zapachami
methods = methods[methods$record_smell == recognized_smell,]

methods$is_smell <- with(methods, ifelse(record_severity != "none",0, 1))
# methods$is_smell <- with(methods, ifelse(Severity != 0,0, 1))
# balance sets
majority_class_len <- nrow(methods[methods$is_smell == 1,])
minority_class_dataset = data.matrix(methods[methods$is_smell == 0,])
minority_class_len <- nrow(minority_class_dataset)


# Shuffle
rows <- sample(nrow(methods))
methods <- methods[rows, ]
number_of_rows <- nrow(methods)
split_point <- round(0.7 * number_of_rows)

prep_train <- data.frame(methods[1:split_point, ])
prep_test <- data.frame(methods[split_point:number_of_rows, ])




prep_train$is_smell <- as.factor(prep_train$is_smell)

somte_methods <- SMOTE(prep_train[c(19:23,26:50,63)], perc_min = 50, k = 2)

round_df <- function(x, digits) {
  # round all numeric variables
  # x: data frame 
  # digits: number of digits to round
  numeric_columns <- sapply(x, mode) == 'numeric'
  x[numeric_columns] <-  round(x[numeric_columns], digits)
  x
}
rd_m<-round_df(somte_methods[c(1:30)],0)
joined <-cbind(rd_m, somte_methods[c(31)])


majority_class_dataset = data.matrix(joined[joined$is_smell == 1,])
majority_class_len <- nrow(methods[joined$is_smell == 1,])
minority_class_dataset = data.matrix(joined[joined$is_smell == 0,])
minority_class_len <- nrow(joined)


# for (i in 1:(majority_class_len - minority_class_len)) {
#   print(i)
#   prep_train[nrow(prep_train) + 1,] = minority_class_dataset[sample(1:nrow(minority_class_dataset), 1),]
# }



# metrics <- normalize(data.matrix(methods_all[21:45]))
joined$is_smell <- as.numeric(as.character(joined$is_smell))
metrics_train <- data.matrix(joined[c(1:30)])
metrics_test <- data.matrix(prep_test[c(19:23,26:50)])


labels_train <- data.matrix(joined$is_smell)
labels_test <- data.matrix(prep_test$is_smell)
# class(labels_train)<- "numeric"
# class(labels_test)<- "numeric"

labels_train <- to_categorical(data.matrix(joined$is_smell)) #do softmaxa (units = 2)
labels_test <- to_categorical(data.matrix(prep_test$is_smell)) #do softmaxa (units = 2)


x_train <- metrics_train
y_train <- labels_train

x_test <- metrics_test
y_test <- labels_test


mcc <- function(tpi,tni,fpi,fni){
  tp = as.numeric(tpi)
  tn = as.numeric(tni)
  fp = as.numeric(fpi)
  fn = as.numeric(fni)
  return (((tp*tn)-(fp*fn))/sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)))
}
draw_confusion_matrix <- function(cm) {
  
  layout(matrix(c(1,1,2)))
  par(mar=c(2,2,2,2))
  plot(c(100, 345), c(300, 450), type = "n", xlab="", ylab="", xaxt='n', yaxt='n')
  title('CONFUSION MATRIX', cex.main=2)
  
  # create the matrix 
  rect(150, 430, 240, 370, col='#3F97D0')
  text(195, 435, 'Class1', cex=1.2)
  rect(250, 430, 340, 370, col='#F7AD50')
  text(295, 435, 'Class2', cex=1.2)
  text(125, 370, 'Predicted', cex=1.3, srt=90, font=2)
  text(245, 450, 'Actual', cex=1.3, font=2)
  rect(150, 305, 240, 365, col='#F7AD50')
  rect(250, 305, 340, 365, col='#3F97D0')
  text(140, 400, 'Class1', cex=1.2, srt=90)
  text(140, 335, 'Class2', cex=1.2, srt=90)
  
  # add in the cm results 
  res <- as.numeric(cm$table)
  text(195, 400, res[1], cex=1.6, font=2, col='white')
  text(195, 335, res[2], cex=1.6, font=2, col='white')
  text(295, 400, res[3], cex=1.6, font=2, col='white')
  text(295, 335, res[4], cex=1.6, font=2, col='white')
  
  # add in the specifics 
  plot(c(100, 0), c(100, 0), type = "n", xlab="", ylab="", main = "DETAILS", xaxt='n', yaxt='n')
  text(10, 85, names(cm$byClass[1]), cex=1.2, font=2)
  text(10, 70, round(as.numeric(cm$byClass[1]), 3), cex=1.2)
  text(30, 85, names(cm$byClass[2]), cex=1.2, font=2)
  text(30, 70, round(as.numeric(cm$byClass[2]), 3), cex=1.2)
  text(50, 85, names(cm$byClass[5]), cex=1.2, font=2)
  text(50, 70, round(as.numeric(cm$byClass[5]), 3), cex=1.2)
  text(70, 85, names(cm$byClass[6]), cex=1.2, font=2)
  text(70, 70, round(as.numeric(cm$byClass[6]), 3), cex=1.2)
  text(90, 85, names(cm$byClass[7]), cex=1.2, font=2)
  text(90, 70, round(as.numeric(cm$byClass[7]), 3), cex=1.2)
  
  # add in the accuracy information 
  text(25, 35, names(cm$overall[1]), cex=1.5, font=2)
  text(25, 20, round(as.numeric(cm$overall[1]), 3), cex=1.4)
  text(45, 35, names(cm$overall[2]), cex=1.5, font=2)
  text(45, 20, round(as.numeric(cm$overall[2]), 3), cex=1.4)
  text(65, 35, "Mcc", cex=1.5, font=2)
  text(65, 20, round(as.numeric(mcc(res[1], res[4],res[2], res[3])),3), cex=1.4)
}  


prep_train$is_smell = as.factor(prep_train$is_smell)

rf <- randomForest(is_smell~.,data=prep_train[c(19:23, 26:50, 63)], ntree=100)

print(rf)
floor(sqrt(ncol(prep_train[c(19:23, 26:50)]) - 1))

mtry <- tuneRF(prep_train[c(19:23, 26:50)],prep_train$is_smell, ntreeTry=100,
               stepFactor=1.5,improve=0.01, trace=TRUE, plot=TRUE)
best.m <- mtry[mtry[, 2] == min(mtry[, 2]), 1]
print(mtry)
print(best.m)

rf <-randomForest(is_smell~.,data=prep_train[c(19:23, 26:50, 63)], mtry=best.m, importance=TRUE,ntree=100)
print(rf)
#Evaluate variable importance
importance(rf)
jpeg(sprintf("%s_randomforest_importance.jpeg",recognized_smell), width = 500, height = 500)
varImpPlot(rf)
dev.off()



prep_test$prediction <- predict(rf, newdata=prep_test[c(19:23, 26:50)])
prep_test$prediction_correct <- with(prep_test, ifelse(is_smell == prediction,TRUE, FALSE))

correct_predictions = subset(prep_test, prep_test$prediction == prep_test$is_smell)
incorrect_predictions = subset(prep_test, prep_test$prediction != prep_test$is_smell)
tp <- nrow(subset(correct_predictions, correct_predictions$prediction == 0))
tn <- nrow(subset(correct_predictions, correct_predictions$prediction == 1))
fp <- nrow(subset(incorrect_predictions, incorrect_predictions$prediction ==0))
fn <- nrow(subset(incorrect_predictions, incorrect_predictions$prediction == 1))

validation <- prep_test[prep_test$record_smell == recognized_smell,]

cm <- confusionMatrix(table(prep_test$prediction, prep_test$is_smell), positive = NULL, dnn = c("Prediction", "Reference"))
print(cm)

print(mcc(tp,tn,fp,fn))

capture.output(cm, file = sprintf("%s_randomforest.csv",recognized_smell))

jpeg(sprintf("%s_randomforest.jpeg",recognized_smell), width = 500, height = 500)
draw_confusion_matrix(cm)
dev.off()

