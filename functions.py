import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_score, accuracy_score, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import time

def prepareForModelUse(populatedDataframe: DataFrame, index):
    
    # Uklanjanje nepotrebnih svojstava skupa podataka
    populatedDataframe.drop('sessionIndex', axis = 1, inplace = True)
    populatedDataframe.drop('rep', axis = 1, inplace = True)

    # Razdvajanje skupa podataka na 2 cjeline. Y oznacava skup podataka
    # koji sadrzi korisnike dok je X skup podataka kojega model strojnog
    # ucenja treba razvrstati (prepoznati) prema skupu Y
    X = populatedDataframe.iloc[:, 1:]
    Y = populatedDataframe['subject']

    # Priprema polja za skupove treniranja i testiranja. Pocetna inicijalizacija
    # je potrebna zbog zadrzavanja originalnog poredka subjekata
    X_train, X_test, y_train, y_test = [], [], [], []

    # Podijeli prethodne skupove podataka na skupove za treniranje modela 
    # strojnog ucenja i skupove za testiranje modela strojnog ucenja
    for subject in index:
        subjectData = populatedDataframe[populatedDataframe['subject'] == subject]
        trainData, testData = train_test_split(subjectData, test_size=0.2, random_state=42)
        
        X_train.append(trainData.iloc[:, 1:])
        y_train.extend(trainData['subject'])
        
        X_test.append(testData.iloc[:, 1:])
        y_test.extend(testData['subject'])

    # Dodavanje podataka u liste
    X_train = pd.concat(X_train, axis=0)
    X_test = pd.concat(X_test, axis=0)

    # Pretvorba popunjenih lista u 'DataFrame'
    y_train = pd.Series(y_train)
    y_test = pd.Series(y_test)

    # Normaliziranje skupova podataka kako bi predvidanje modela 
    # bilo sto preciznije
    scaler = MinMaxScaler()
    scaler.fit(X_train)
    X_train = scaler.transform(X_train)
    X_test = scaler.transform(X_test)
    return X_train, X_test, y_train, y_test

def useModel(trainDF_Y, trainDF_X, y_test, testDF_X, model: RandomForestClassifier):
    
    # Treniranje modela stojnog ucenja i mjerenje 
    # vremena potrebnog za isto
    startTime = time.time()
    model.fit(trainDF_X, trainDF_Y.values.ravel())
    endTime = time.time()
    trainingTime = endTime - startTime
    
    # Testiranje modela strojnog ucenja i mjerenje
    # vremena potrebnog za isto
    startTime = time.time()
    prediction = model.predict(testDF_X)
    endTime = time.time()
    testingTime = endTime - startTime
    
    # Izrada konfuzijske matrice klasifikacija modela. Sluzi nam za kasnije
    # izracunavanje konkretnih pokazatelja performansi modela strojnog ucenja
    confusionMatrix = confusion_matrix(y_test, prediction, labels = model.classes_)
    return confusionMatrix, prediction, trainingTime, testingTime

def calculateStatisticalData(confusionMatrix, y_test, prediction):
    
    # Izracun pokazatelja performansi modela strojnog ucenja
    truePositive = np.diag(confusionMatrix)
    falsePositive = confusionMatrix.sum(axis=0) - np.diag(confusionMatrix)
    falseNegative = confusionMatrix.sum(axis=1) - np.diag(confusionMatrix)
    trueNegative = confusionMatrix.sum() - (falsePositive + falseNegative + truePositive)
    falseAcceptanceRate = falsePositive / (falsePositive + trueNegative) * 100
    falseRejectionRate = falsePositive / (truePositive + falseNegative) * 100
    recall = truePositive / (truePositive + falseNegative) * 100
    precision = precision_score(y_test, prediction, average = 'weighted') * 100
    specificity = trueNegative / (trueNegative + falsePositive) * 100
    fMeassure = 2 * ((precision * recall) / (precision + recall))
    accuracy = accuracy_score(y_test, prediction) * 100
    
    statisticalData = dict()
    statisticalData['truePositive'] = truePositive
    statisticalData['falsePositive'] = falsePositive
    statisticalData['falseNegative'] = falseNegative
    statisticalData['trueNegative'] = trueNegative
    statisticalData['falseAcceptanceRate'] = falseAcceptanceRate
    statisticalData['falseRejectionRate'] = falseRejectionRate
    statisticalData['recall'] = recall
    statisticalData['precision'] = precision
    statisticalData['specificity'] = specificity
    statisticalData['fMeassure'] = fMeassure
    statisticalData['accuracy'] = accuracy
    
    return statisticalData

def plotStatisticalData(statisticalData: dict, index, confusionMatrix, model):
    
    # Iscrtavanje slozenih pokazatelja kako bi mogli usporediti performanse 
    # modela strojnog ucenja za pojedine subjekte iz skupa podataka
    # FAR
    falseAcceptanceValuesDF = pd.DataFrame(statisticalData.get("falseAcceptanceRate"), index = index)
    falseAcceptanceValuesDF.plot(kind = 'bar')
    plt.xticks(rotation=90)
    plt.title('Stopa pogrešnih klasifikacija po subjektima')
    plt.legend().remove()
    plt.savefig('stopaPogresnogPrihvacanja.png')

    # FRR
    falseRejectionValuesDF = pd.DataFrame(statisticalData.get("falseRejectionRate"), index = index)
    falseRejectionValuesDF.plot(kind = 'bar')
    plt.xticks(rotation=90)
    plt.title('Stopa pogrešnog odbijanja')
    plt.legend().remove()
    plt.savefig('stopaPogresnogOdbijanja.png')

    # Opoziv
    recallValuesDF = pd.DataFrame(list(statisticalData.get("recall")), index = index)
    recallValuesDF.plot(kind = 'bar')
    plt.xticks(rotation=90)
    plt.title('Opoziv po subjektima')
    plt.legend().remove()
    plt.savefig('opoziv.png')

    # Specificity
    specificityValuesDF = pd.DataFrame(statisticalData.get("specificity"), index = index)
    specificityValuesDF.plot(kind = 'bar')
    plt.xticks(rotation=90)
    plt.title('Specifičnost po subjektima')
    plt.legend().remove()
    plt.savefig('specificnost.png')

    # F-Mjera
    fMeassureValuesDF = pd.DataFrame(statisticalData.get("fMeassure"), index = index)
    fMeassureValuesDF.plot(kind = 'bar')
    plt.xticks(rotation=90)
    plt.title('F-Mjera po subjektima')
    plt.legend().remove()
    plt.savefig('fMjera.png')

    # Konfuzijska matrica
    disp = ConfusionMatrixDisplay(confusionMatrix, display_labels = model.classes_)
    fig, ax = plt.subplots(figsize = (20,20))
    disp.plot(ax = ax)
    plt.title('Konfuzijska matrica klasifikacija')
    plt.ylabel('Stvarne oznake')
    plt.xlabel('Predviđene oznake')
    plt.xticks(rotation = 90)
    plt.savefig('konfuzijskaMatrica.png')
    return

def saveToExcel(statisticalData: dict, trainingTime, testingTime, index):
    
    # Priprema statistickih podataka za ispis u Excel datoteku
    simpleStatisticsDataFrame = pd.DataFrame(index = ['Vrijeme treniranja', 'Vrijeme testiranja', 'Preciznost', 'Tocnost'])
    simpleStatisticsDataFrame["Iznos"] = [trainingTime, testingTime, statisticalData.get("accuracy"), statisticalData.get("precision")]
    classificationStatisticsDataFrame = pd.DataFrame(index = index)
    classificationStatisticsDataFrame['True Positive'] = statisticalData.get("truePositive")
    classificationStatisticsDataFrame['False Positive'] = statisticalData.get("falsePositive")
    classificationStatisticsDataFrame['False Negative'] = statisticalData.get("falseNegative")
    classificationStatisticsDataFrame['True Negative'] = statisticalData.get("trueNegative")
    classificationStatisticsDataFrame['Stopa pogrešnog prihvaćanja'] = statisticalData.get("falseAcceptanceRate")
    classificationStatisticsDataFrame['Stopa pogrešnog  odbijanja'] = statisticalData.get("falseRejectionRate")
    classificationStatisticsDataFrame['Opoziv'] = statisticalData.get("recall")
    classificationStatisticsDataFrame['Specifičnost'] = statisticalData.get("specificity")
    classificationStatisticsDataFrame['F-Mjera'] = statisticalData.get("fMeassure")
    
    # Kreiranje i ispis statistickih pokazatelja u Excel datoteku
    fileName = 'Statisticki podaci modela.xlsx'
    writer = pd.ExcelWriter(fileName, engine = 'xlsxwriter', engine_kwargs={'options':{'strings_to_formulas': False}})
    workbook = writer.book
    worksheet = workbook.add_worksheet("Statistika")
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 18)
    worksheet.set_column(3, 7, 10)
    worksheet.set_column(8, 11, 12)
    writer.sheets["Statistika"] = worksheet
    simpleStatisticsDataFrame.to_excel(writer, sheet_name = "Statistika", startrow = 0, startcol = 0)
    classificationStatisticsDataFrame.to_excel(writer, sheet_name = "Statistika", startrow = 0, startcol = 3)
    writer.close()
    return