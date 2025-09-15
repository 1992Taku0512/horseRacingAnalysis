import datetime
import time
import os

import pandas as pd

from makeRawData import makeHorseData
from preprocessing import preprocessingRaceCard
from prediction import makeRaceCardData, predLGBM, predNN, predDelivery

# カレントディレクトリを自身が格納されているフォルダパスに変更
os.chdir(os.path.dirname(__file__))

# 予測対象日の設定
tgtyear = 2025
tgtmonth = 9
tgtday = 15

# 対象日付のレース一覧を取得
mRCD = makeRaceCardData(datetime.date(tgtyear, tgtmonth, tgtday))
mRCD.makeRaceDateURLList()
mRCD.makeRaceURLList()

# レース開催日時の3分前に処理を開始するためのリストを作成
runtimeList = []
for tgt in mRCD.urlDF["datetime"]:
    runtime = tgt + datetime.timedelta(minutes=-3)
    runtimeList.append(runtime)

# 予測処理を実行
for idx, runtime in enumerate(runtimeList):
    returnflg = 0
    while returnflg == 0:
        now = datetime.datetime.now()
        if now.hour == runtime.hour and now.minute == runtime.minute :
            raceID = mRCD.screpingRaceCardHTML(raceNo=idx)
            raceCardDF = mRCD.makeRaceCardDataFrame(raceNo=idx)

            MHD = makeHorseData(raceCardDF["horseID"].tolist())
            MHD.getHorseHTML(skipResult=False)
            MHD.makeHorseRawData()

            pRC = preprocessingRaceCard(raceCardDF)
            pRC.raceCardPreprocess()
            pRC.makedataHorseResults()
            pRC.horseResultsPreprocess()
            pRC.makeVarFromHorseResults()
            forScoringDF = pRC.forScoringDFPreprocess()

            # lightGBMによる予測
            pLGBM = predLGBM("LGBM_1", forScoringDF, raceCardDF)
            pLGBM.loadModel()
            raceCardDF = pLGBM.pred()

            # NNによる予測
            pNN = predNN("NN_1", forScoringDF, raceCardDF)
            pNN.loadModel()
            raceCardDF = pNN.pred()

            pDeli = predDelivery(raceID, raceCardDF)
            pDeli.makeRaceInfoText()
            pDeli.makePredText(5)
            pDeli.delivaryPredLine()
            returnflg = 1
        else:
            time.sleep(30)