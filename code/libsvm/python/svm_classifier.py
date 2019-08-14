from svmutil import *
import csv
class_=4

def filetolist(filename):
    data=[]
    lines=open(filename).readlines()
    for line in lines:
        line=line.strip('\r\n')
        data.append(float(line))
    return data

def precision_recall(c,p_label,test_label):
    FP = 0
    FN = 0
    TP = 0
    for i in range(len(p_label)):
        if test_label[i]==c:

            if p_label[i]==c:
                TP += 1
            else:
                FN+=1
        elif test_label[i]!=c and p_label[i]==c:
            FP+=1
    return float(TP)/(TP+FP),float(TP)/(TP+FN),TP+FN


train_label, train_feature = svm_read_problem("../../../data/input/train2.txt")

test_label, test_feature = svm_read_problem("../../../data/input/test2.txt")
train = svm_problem(train_label, train_feature)
param = svm_parameter('-c 8 -g 0.5')
trained_model = svm_train(train, param)
svm_save_model('../../../result/role.model', trained_model)
model = svm_load_model('../../../result/role.model')
#p_label=filetolist('../tools/test1.txt.predict')

p_label,  p_acc, p_vals = svm_predict(test_label, test_feature, model)
for c in range(class_):
    precision,recall,num=precision_recall(float(c),p_label,test_label)
    print c,precision,recall,num

