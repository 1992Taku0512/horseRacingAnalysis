import os
import pandas as pd
from makeRawData import makeRaceData,makeHorseData

#カレントディレクトリを自身が格納されているフォルダパスに変更
os.chdir(os.path.dirname(__file__))

#レース結果のデータを作成
MRD = makeRaceData("201901","201912")
MRD.makeYMList()
MRD.makeRaceDateURLList()
MRD.makeRaceURLList()
MRD.screpingRaceHTML(skip=True)
MRD.makeRawDataRace(skip=True)

#horseIDListを作成
horseIDListPrep = []
for raceID in MRD.raceIDList:
    try:#競争中止とかで結果がない場合があるので例外処理
        raceResultsDF = pd.read_pickle(f"../../../data/rawData/raceResults/{raceID}.pickle")
        horseIDTmp = raceResultsDF["horseID"].unique()
        horseIDListPrep.extend(horseIDTmp)
    except FileNotFoundError:
        continue

horseIDList = pd.DataFrame(horseIDListPrep)[0].unique().tolist()
horseIDList.sort()

#馬の過去成績/血統データを作成
MHD = makeHorseData(horseIDList)
MHD.getHorseHTML(skipResult=True, skipPED=True)
MHD.makeHorseRawData(skipResult=True, skipPED=True)