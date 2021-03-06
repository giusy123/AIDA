import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import numpy as np

np.random.seed(12)
from tensorflow import set_random_seed

set_random_seed(12)
from Preprocessing import Preprocessing as prep
from sklearn.preprocessing import StandardScaler, scale, MinMaxScaler, Normalizer, normalize
from keras import optimizers
from Models import Models
from keras import callbacks
from keras.utils import np_utils
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score
from keras.models import Model
import seaborn as sns
from keras.models import load_model
from sklearn import svm
import pickle
import time




def preprocessing(train, test, p):
    train, test = p.preprocessingOneHot(train, test)
    train, test = p.preprocessinLabel(train, test)
    # final_train, final_test = dfTrain.align(dfTest, join='inner', axis=1)  # inner join
    missing_cols = set(train.columns) - set(test.columns)
    for c in missing_cols:
       # print("not found:", c)
        test[c] = 0
        # Ensure the order of column in the test set is in the same order than in train set
    test = test[train.columns]

    missing_cols = set(test.columns) - set(train.columns)
    for c in missing_cols:
        #print("not found2:", c)
        train[c] = 0
        # Ensure the order of column in the test set is in the same order than in train set
    train = train[test.columns]

    return train, test


def scaler(train, test, listContent):
    scaler = StandardScaler()
    # print(train[listContent])
    frames = [train[listContent], test[listContent]]

    dfc = pd.concat(frames)
    # print(len(dfc.columns))
    # oppure su dfc?
    scaler.fit(train[listContent].values)  # Remember to only fit scaler to training data
    train[listContent] = scaler.transform(train[listContent])
    test[listContent] = scaler.transform(test[listContent])
    return train, test


def scaleSimple(Y_train, Y_test):
    Y_train=scale(Y_train)
    Y_test=scale(Y_test)
    return Y_train, Y_test



def printPlotLoss(history, d):
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs = range(1, len(loss) + 1)
    plt.plot(epochs, loss, 'b', label='Training loss')
    plt.plot(epochs, val_loss, 'r', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()
    plt.savefig("plotLoss" + str(d) + ".png")
    plt.close()
    # plt.show()


def printPlotAccuracy(history, d):
    acc = history.history['acc']
    val_acc = history.history['val_acc']
    epochs = range(1, len(acc) + 1)
    plt.plot(epochs, acc, 'b', label='Training acc')
    plt.plot(epochs, val_acc, 'r', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()
    plt.savefig("plotAccuracy" + str(d) + ".png")
    plt.close()
    # plt.show()



def main():
    pd.set_option('display.expand_frame_repr', False)
    PREPROCESSING = 0
    N_CLASSES = 2
    VALIDATION_SPLIT=.1
    LABELS=["Attacks","Normal"]
    LOAD_MODEL=1
    LOAD_CLASSIFIER=1
    path = 'KDDTrain+aggregateOneCls10Features'
    pathTest = 'KDDTest+aggregateOneCls10Features'
    testpath='KDDTest+'
    pathModels = 'models/'
    pathDataset = 'datasets/'
    train = pd.read_csv(pathDataset+path + ".csv")
    test = pd.read_csv(pathDataset+pathTest + ".csv")
    pathOutputTrain = pathDataset+path + 'Numeric.csv'
    pathOutputTest = pathDataset+pathTest + 'Numeric.csv'


    listNumerical10=[
                     ' src_bytes', ' dst_bytes', ' diff_srv_rate', ' same_srv_rate', ' dst_host_srv_count', ' dst_host_same_srv_rate',
                     ' dst_host_diff_srv_rate',' dst_host_serror_rate']





    prp = prep(train, test)

    tic_preprocessing=time.time()

    if (PREPROCESSING == 1):
        train, test = preprocessing(train, test, prp)
        train, test = scaler(train, test, listNumerical10)
        train.to_csv(pathOutputTrain, index=False)  # X is an array
        test.to_csv(pathOutputTest, index=False)


    else:
        train = pd.read_csv(pathDataset+path + 'Numeric.csv')
        test = pd.read_csv(pathDataset+pathTest + 'Numeric.csv')


    clsT, clsTest = prp.getCls()
    train_normal = train[(train[clsT] == 1)]
    print("train normal:", train_normal.shape)

    train_anormal = train[(train[clsT] == 0)]
    test_normal = test[(test[clsTest] == 1)]
    test_anormal = test[(test[clsTest] == 0)]

    train_XN, train_YN, test_XN, test_YN = prp.getXY(train_normal, test_normal)

    train_XA, train_YA, test_XA, test_YA = prp.getXY(train_anormal, test_anormal)
    train_X, train_Y, test_X, test_Y = prp.getXY(train, test)

    toc_preprocessing=time.time()
    time_preprocessing=toc_preprocessing-tic_preprocessing

    print('Train data shape normal', train_XN.shape)
    print('Train target shape normal', train_YN.shape)
    print('Test data shape normal', test_XN.shape)
    print('Test target shape normal', test_YN.shape)

    print('Train data shape anormal', train_XA.shape)
    print('Train target shape anormal', train_YA.shape)
    print('Test data shape anormal', test_XA.shape)
    print('Test target shape anormal', test_YA.shape)

    # convert class vectors to binary class matrices fo softmax
    print(train_Y.head())
    train_Y2 = np_utils.to_categorical(train_Y, N_CLASSES)
    print("Target train shape after", train_Y2.shape)
    test_Y2 = np_utils.to_categorical(test_Y, N_CLASSES)
    print("Target test shape after", test_Y2.shape)


    callbacks_list = [
        callbacks.EarlyStopping(monitor='val_loss', min_delta=0.0001, patience=6, restore_best_weights=True),
    ]

    m = Models(N_CLASSES)

    if (LOAD_MODEL==0):
        tic_autoencoder=time.time()
        print('Autoencoder only normal')
        # parametri per autoencoder
        p1 = {
            'first_layer': 60,
            'second_layer': 30,
            'third_layer': 10,
            'four_layer': 40,
            'five_layer': 20,
            'six_layer': 10,
            'batch_size': 64,
            'epochs': 150,
            'optimizer': optimizers.Adam,
            'kernel_initializer': 'glorot_uniform',
            'losses': 'mse',
            'first_activation': 'tanh',
            'second_activation': 'tanh',
            'third_activation': 'tanh'}

        autoencoder = m.deepAutoEncoder(train_XN, p1)
        autoencoder.summary()

        history = autoencoder.fit(train_XN, train_XN,
                                   validation_split=VALIDATION_SPLIT,
                                   batch_size=p1['batch_size'],
                                   epochs=p1['epochs'], shuffle=True,
                                   callbacks=callbacks_list,
                                   verbose=1)

        printPlotAccuracy(history, 'autoencoder')
        printPlotLoss(history, 'autoencoder')

        toc_autoencoder=time.time()
        time_autoencoder=toc_autoencoder-tic_autoencoder
        autoencoder.save(pathModels+'autoencoderNormal.h5')
    else:
        print("Load autoencoder from disk")
        autoencoder=load_model(pathModels+'autoencoderNormal.h5')
       # autoencoder.summary()



    train_XS, test_XS = scaleSimple(train_X, test_X)



    print("Using softmax classifier:")
    if (LOAD_CLASSIFIER == 0):
        tic_classifier=time.time()
        # parameters for final model
        p2 = {
            'batch_size': 64,
            'epochs': 150,
            'optimizer': optimizers.Adam,
            'kernel_initializer': 'glorot_uniform',
            'losses': 'binary_crossentropy',
            'first_activation': 'tanh',
            'second_activation': 'tanh',
            'third_activation': 'tanh'}

        model=m.baselineModel(train_XS, p2)

        history2 = model.fit(train_XS, train_Y2,
                             validation_split=VALIDATION_SPLIT,
                             batch_size=p2['batch_size'],
                             epochs=p2['epochs'], shuffle=False,
                             callbacks=callbacks_list, #class_weight=class_weight,
                             verbose=1)

        toc_classifier=time.time()
        time_classifier=toc_classifier-tic_classifier

        printPlotAccuracy(history2, 'finalModel1')
        printPlotLoss(history2, 'finalModel1')
        model.save(pathModels+'modelsoftmax.h5')
    else:
        print("Load softmax from disk")
        model = load_model(pathModels+'modelsoftmax.h5')




    ################# mse train  ###########################

    #train predictions

    predictionsT = autoencoder.predict(train_X)
    mseT = np.mean(np.power(train_X - predictionsT, 2), axis=1)
    error_dfT = pd.DataFrame({'reconstruction_error': mseT})
    error_dfT['true_class'] = train_Y[clsT]






    ################# mse test #################################

    #test predictions
    tic_prediction_autoencoder = time.time()
    predictions = autoencoder.predict(test_X)
    mse = np.mean(np.power(test_X - predictions, 2), axis=1)
    toc_prediction_autoencoder = time.time()
    time_prediction_autoencoder1 = toc_prediction_autoencoder - tic_prediction_autoencoder
    error_df = pd.DataFrame({'reconstruction_error': mse})
    error_df['true_class'] = test_Y[clsTest]

    ###################classifier prediction ################
    tic_prediction_classifier=time.time()
    predictions = model.predict(test_XS)
    toc_prediction_classifier=time.time()
    time_prediction_classifier=toc_prediction_classifier-tic_prediction_classifier
    predictionsT=model.predict(train_XS)

    ############# create confusion matrix ######################

    # Predicting the Training set results
    y_predT = np.argmax(predictionsT, axis=1)
    cm = confusion_matrix(train_Y, y_predT)
    acc = accuracy_score(train_Y, y_predT, normalize=True)
    print('Softmax on training set')
    print(cm)
    print(acc)
    #Add prediction at dataframe with error reconstruction
    error_dfT['predict_softmax'] = y_predT
    pathOutputError = pathDataset+'ErrorTraining.csv'
    error_dfT.to_csv(pathOutputError, index=False)

    # Predicting the Test set results

    y_pred = np.argmax(predictions, axis=1)
    print(y_pred)
    cm = confusion_matrix(test_Y, y_pred)
    acc = accuracy_score(test_Y, y_pred, normalize=True)
    print(cm)
    print(acc)
    print('Softmax on test set')
    # Add prediction at dataframe with error reconstruction
    error_df['predict_softmax'] = y_pred
    #error_df['prob']=prob
    pathOutputError = pathDataset+'ErrorTest'
    error_df.to_csv(pathOutputError+testpath+'.csv', index=False)







#########################################Phase after classification##############################





    threshold = 0.0005

    tic_prediction_anomaly1=time.time()
    y_predA = [0 if (e > threshold) else 1  for e in error_df.reconstruction_error.values]
    toc_prediction_anomaly1=time.time()
    time_prediction_anomaly1=toc_prediction_anomaly1-tic_prediction_anomaly1
    conf_matrix = confusion_matrix(error_df.true_class, y_predA)
    plt.figure(figsize=(12, 12))
    sns.heatmap(conf_matrix, xticklabels=LABELS, yticklabels=LABELS, annot=True, fmt="d");
    plt.title("Confusion matrix All")
    plt.ylabel('True class')
    plt.xlabel('Predicted class')
    plt.savefig("first matrix")
    plt.show()
    plt.close()

    tic_prediction_anomaly2 = time.time()
    # take to dataframe only prediction equals to 1
    error_OnlyNormal = error_df[error_df['predict_softmax'] == 1]

    y_predNormal = [0 if (e > threshold) else 1 for e in error_OnlyNormal.reconstruction_error.values]
    toc_prediction_anomaly2 = time.time()
    time_prediction_anomaly2 = toc_prediction_anomaly2 - tic_prediction_anomaly2
    conf_matrix2 = confusion_matrix(error_OnlyNormal.true_class, y_predNormal)
    print(conf_matrix2)
    plt.figure(figsize=(12, 12))
    sns.heatmap(conf_matrix2, xticklabels=LABELS, yticklabels=LABELS, annot=True, fmt="d");
    plt.title("Confusion matrix Normal")
    plt.ylabel('True class')
    plt.xlabel('Predicted class')
    plt.savefig("second matrix")
    plt.show()

    if(PREPROCESSING==1):
        print("Time for preprocessing %s " % time_preprocessing)
    if(LOAD_MODEL==0):
     print("Time for train autoencoder %s " % time_autoencoder)
    if(LOAD_CLASSIFIER==0):
     print("Time for train classifier %s " % time_classifier)

    print("Time for anomaly prediction %s " % (time_prediction_autoencoder1+time_prediction_anomaly1))
    print("Time for classifier prediction %s " % time_prediction_classifier)
    print("Time for 2 phase prediction %s " % (time_prediction_classifier+time_prediction_autoencoder1+time_prediction_anomaly2))


if __name__ == "__main__":
    main()