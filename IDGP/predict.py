# python packages
import random
import time
import operator
import evalGP_main as evalGP
# only for strongly typed GP
import gp_restrict
import numpy as np
# deap package
from deap import base, creator, tools, gp
from strongGPDataType import Int1, Int2, Int3, Img, Region, Vector, Vector1
from saveFile import saveAllResults
import feature_function as fe_fs
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score
from sklearn import preprocessing
import pandas as pd


randomSeeds = 42
dataSetName = 'selectdwi'

x_train = np.load(dataSetName + '_train_data.npy')
y_train = np.load(dataSetName + '_train_label.npy')
x_test = np.load(dataSetName + '_test_data.npy')
y_test = np.load(dataSetName + '_test_label.npy')



print(x_train.shape,y_train.shape, x_test.shape, y_test.shape)

# parameters:
population = 300
generation = 300
cxProb = 0.8
mutProb = 0.19
elitismProb = 0.01
totalRuns = 1
initialMinDepth = 2
initialMaxDepth = 6
maxDepth = 8

bound1, bound2 = x_train[1, :, :].shape
##GP

pset = gp.PrimitiveSetTyped('MAIN', [Img], Vector, prefix='Image')
#Feature concatenation
pset.addPrimitive(fe_fs.root_con, [Vector1, Vector1], Vector1, name='FeaCon')
pset.addPrimitive(fe_fs.root_con, [Vector, Vector], Vector1, name='FeaCon2')
pset.addPrimitive(fe_fs.root_con, [Vector, Vector, Vector], Vector1, name='FeaCon3')
# Global feature extraction
pset.addPrimitive(fe_fs.all_dif, [Img], Vector, name='Global_DIF')
pset.addPrimitive(fe_fs.all_histogram, [Img], Vector, name='Global_Histogram')
pset.addPrimitive(fe_fs.global_hog, [Img], Vector, name='Global_HOG')
pset.addPrimitive(fe_fs.all_lbp, [Img], Vector, name='Global_uLBP')
pset.addPrimitive(fe_fs.all_sift, [Img], Vector, name='Global_SIFT')
# Local feature extraction
pset.addPrimitive(fe_fs.all_dif, [Region], Vector, name='Local_DIF')
pset.addPrimitive(fe_fs.all_histogram, [Region], Vector, name='Local_Histogram')
pset.addPrimitive(fe_fs.local_hog, [Region], Vector, name='Local_HOG')
pset.addPrimitive(fe_fs.all_lbp, [Region], Vector, name='Local_uLBP')
pset.addPrimitive(fe_fs.all_sift, [Region], Vector, name='Local_SIFT')
# Region detection operators
pset.addPrimitive(fe_fs.regionS, [Img, Int1, Int2, Int3], Region, name='Region_S')
pset.addPrimitive(fe_fs.regionR, [Img, Int1, Int2, Int3, Int3], Region, name='Region_R')
# Terminals
pset.renameArguments(ARG0='Grey')

pset.addEphemeralConstant('X', lambda: random.randint(0, bound1 - 20), Int1)
pset.addEphemeralConstant('Y', lambda: random.randint(0, bound2 - 20), Int2)
pset.addEphemeralConstant('Size', lambda: random.randint(20, 51), Int3)

#fitnesse evaluaiton
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("expr", gp_restrict.genHalfAndHalfMD, pset=pset, min_=initialMinDepth, max_=initialMaxDepth)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)
toolbox.register("mapp", map)

def evalTrain(individual):
    # print(individual)
    func = toolbox.compile(expr=individual)
    train_tf = []
    for i in range(0, len(y_train)):
        train_tf.append(np.asarray(func(x_train[i, :, :])))
    min_max_scaler = preprocessing.MinMaxScaler()
    train_norm = min_max_scaler.fit_transform(np.asarray(train_tf))

    # print(train_norm.shape)
    lsvm = LinearSVC(max_iter=10000)
    accuracy = round(100 * cross_val_score(lsvm, train_norm, y_train, cv=3).mean(), 2)
    return accuracy,


# genetic operator
toolbox.register("evaluate", evalTrain)
toolbox.register("select", tools.selTournament, tournsize=5)
toolbox.register("selectElitism", tools.selBest)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp_restrict.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=maxDepth))
toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=maxDepth))



def evalTest(individual):
    func = toolbox.compile(expr=individual)
    train_tf = []
    test_tf = []
    for i in range(0, len(y_train)):
        train_tf.append(np.asarray(func(x_train[i, :, :])))
    for j in range(0, len(y_test)):
        test_tf.append(np.asarray(func(x_test[j, :, :])))
    train_tf = np.asarray(train_tf)
    test_tf = np.asarray(test_tf)
    min_max_scaler = preprocessing.MinMaxScaler()
    train_norm = min_max_scaler.fit_transform(np.asarray(train_tf))
    test_norm = min_max_scaler.transform(np.asarray(test_tf))
    lsvm= LinearSVC(max_iter=10000)
    lsvm.fit(train_norm, y_train)
    score = lsvm.decision_function(test_norm)
    prediction = lsvm.predict(test_norm)
    accuracy = round(100*lsvm.score(test_norm, y_test),2)
    return score, prediction, y_test, accuracy

if __name__ == "__main__":
    txtpath = '42Final_Result_sonselectdwi.txt'
    with open(txtpath, 'r') as f:
        lines = f.readlines()
        info = lines[-1]
        info = info[:-1]
    beginTime = time.process_time()


    score, prediction, testL, testResults = evalTest(info)
    testTime = time.process_time() - beginTime

    testcsv = pd.DataFrame({
        'testL':testL,
        'IDGP_axdwi_roi':prediction,
        'score':score,
        'testtime':testTime
    })
    testcsv.to_csv('IDGP_axdwi_roi_pre.csv')
    print(testResults)
    print(score)
    print(prediction)
    print(testL)
    print(testTime)
