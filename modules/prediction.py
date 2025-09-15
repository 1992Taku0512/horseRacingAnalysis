import datetime
import random
import requests
import re
from io import StringIO
import pickle

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import numpy as np
import chainer
import chainer.links as L
import chainer.functions as F
from chainer import serializers
from linebot import LineBotApi
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage

import my_snipets

class makeRaceCardData:
    """
    出馬表データを取得するクラス
    """
    def __init__(self, date:datetime.date):
        self.date = date

    def makeRaceDateURLList(self) -> None:
        """
        対象日付の開催レース一覧ページのURLを生成する関数
        """
    
        #対象年月の開催カレンダーのURLを生成
        url = f"https://race.netkeiba.com/top/calendar.html?year={self.date.year}&month{self.date.month}"

        #カレンダーページのHTMLを取得
        headers = {'User-Agent': random.choice(my_snipets.makeUserAgents())}
        html = requests.get(url, headers=headers)
        html.encoding = "EUC-JP"

        #HTMLをsoupオブジェクトに変換
        soup = BeautifulSoup(html.text,"lxml")

        #開催日の一覧を取得し、開催日ページのURLを取得
        RaceCellBoxAll = soup.find_all("td",attrs={"class":"RaceCellBox"})
        
        for i in range(len(RaceCellBoxAll)):
            if RaceCellBoxAll[i].find("a") is not None:
                day = RaceCellBoxAll[i].find("span",attrs={"class":"Day"}).text
                if datetime.date(self.date.year, self.date.month, int(day)) == self.date:
                    self.tgtURL = (RaceCellBoxAll[i].find("a")["href"].replace("..","https://race.netkeiba.com/"))
                    break

        return

    def makeRaceURLList(self) -> None:
        """
        開催日ページのURLから、各レースのURLリストと発走日時のデータフレーム(発走日時昇順)を作成する関数
        """
        self.urlDF = pd.DataFrame()
        URLList = []
        datetimeList = []
        dateStr = self.tgtURL.split("=")[1]

        # Seleniumを使用してブラウザを起動し、対象URLにアクセス
        option = Options()
        option.add_argument('--headless')
        browser = webdriver.Chrome(options=option)
        browser.get(self.tgtURL)

        # ブラウザから必要な情報を取得
        RaceListDataItemAll = browser.find_elements(By.CLASS_NAME,"RaceList_DataItem")
        for item in RaceListDataItemAll:
            if len(item.find_element(By.CLASS_NAME,"RaceData").find_element(By.TAG_NAME,"span").text) > 0:
                timeStr = item.find_element(By.CLASS_NAME,"RaceData").find_element(By.TAG_NAME,"span").text
            else:
                timeStr = "23:59"

            URLList.append(item.find_element(By.TAG_NAME,"a").get_attribute("href"))
            datetimeList.append(datetime.datetime(int(dateStr[0:4]), int(dateStr[4:6]), int(dateStr[6:8]),int(timeStr[0:2]), int(timeStr[3:5])))

        # ブラウザを閉じる
        browser.quit()
        
        # データフレームに変換
        self.urlDF = pd.DataFrame({"URL": URLList,"datetime": datetimeList})
        self.urlDF.sort_values(by="datetime", inplace=True)
        self.urlDF.reset_index(drop=True, inplace=True)

        print(f"対象日付: {dateStr}" + "\n" + f"レース数: {len(self.urlDF)}")

        return
    
    def screpingRaceCardHTML(self,raceNo) -> str:
        """
        レースカードのHTMLをスクレイピングする関数
        `raceNo`: 対象日付のレース番号(0始まりの整数)
        """
        raceURL = self.urlDF["URL"][raceNo]
        raceID = re.sub(r"\D+", "", str(raceURL.split("/")[-1:]))
        option = Options()
        option.add_argument('--headless')
        browser = webdriver.Chrome(options=option)
        browser.get(raceURL)
        html = browser.page_source
        with open(f"../../../data/html/raceCard/{raceID}.txt","w") as f:
                f.write(html)
        browser.quit()

        print(f"[raceID:{raceID}]出馬表のHTMLをスクレイピングしました。")

        return raceID
    
    def makeRaceCardDataFrame(self, raceNo) -> pd.DataFrame:
        """
        レースカードのHTMLからDataFrameを作成する関数
        `raceID`: レースID
        """
        tgtRaceID = re.sub(r"\D+", "", str(self.urlDF["URL"][raceNo].split("/")[-1:]))

        with open(f"../../../data/html/raceCard/{tgtRaceID}.txt", "r") as f:
            html = f.read()

        returnDF = pd.read_html(StringIO(html))[0]

        # raceCardDFのカラム名を整形
        columnList = returnDF.columns.get_level_values(1)
        returnDF.columns = columnList
        
        # HTMLをsoupオブジェクトに変換
        soup = BeautifulSoup(html,"lxml")

        # raceCardDFにraceID/horseID/jockeyIDを追加
        horseIDList = []
        jockeyIDList = []
        HorseListAll = soup.find_all("tr",attrs={"class":"HorseList"})
        cnt = 0
        while cnt < len(returnDF):
            horseID = HorseListAll[cnt].find("span",attrs={"class":"HorseName"}).find("a")["href"].split("/")[-1]
            if HorseListAll[cnt].find("td",attrs={"class":"Jockey"}).find("a") != None:
                jockeyID = HorseListAll[cnt].find("td",attrs={"class":"Jockey"}).find("a")["href"].split("/")[-2]
            else:
                jockeyID = "00000"
            horseIDList.append(horseID)
            jockeyIDList.append(jockeyID)
            cnt += 1

        returnDF["raceID"] = tgtRaceID
        returnDF["horseID"] = horseIDList
        returnDF["jockeyID"] = jockeyIDList

        # レース名
        raceName = soup.find("h1", attrs={"class": "RaceName"}).text.strip()

        # レース情報
        raceInfoList = soup.find("div", attrs={"class": "RaceData01"}).text.split("/")
        
        #距離
        course_len = re.findall("\d+",raceInfoList[1].strip())[0]

        #レースタイプ
        if raceInfoList[1].strip().find("障") != -1:
            raceType = "障害"
        elif raceInfoList[1].strip().find("芝") != -1:
            raceType = "芝"
        elif raceInfoList[1].strip().find("ダ") != -1:
            raceType = "ダート"

        #天候
        try:
            weather = raceInfoList[2].strip().split(":")[1]
        except IndexError:
            weather = np.nan

        #馬場状態
        try:
            groundState = raceInfoList[3].strip().split(":")[1]
            if groundState == "稍":
                groundState = "稍重"
        except IndexError:
            groundState = np.nan

        returnDF["raceName"] = raceName
        returnDF["course_len"] = course_len
        returnDF["weather"] = weather
        returnDF["raceType"] = raceType
        returnDF["groundState"] = groundState
        returnDF["date"] = pd.to_datetime(f"{self.date.year}年{self.date.month}月{self.date.day}日",format="%Y年%m月%d日")

        return returnDF
    
class predLGBM:
    def __init__(self, modelName: str, scoringdf: pd.DataFrame, raceCardDF: pd.DataFrame):
        self.modelName = modelName
        self.scoringdf = scoringdf.copy()
        self.raceCardDF = raceCardDF.copy()

    def loadModel(self):
        with open(f"../../../models/lightGBM/{self.modelName}.pickle", "rb") as f:
            self.modelLGBM = pickle.load(f)

    def pred(self):
        self.socredData = self.modelLGBM.predict(self.scoringdf)
        self.raceCardDF["predLGBM"] = self.socredData
        return self.raceCardDF

class Mychain(chainer.Chain):
    def __init__(self):
        super().__init__(
            bn = L.BatchNormalization(24),
            l1 = L.Linear(None, 24),
            l2 = L.Linear(None, 12),
            l3 = L.Linear(None, 6),
            l4 = L.Linear(None, 2),
        )

    def __call__(self,x):
        h1 = F.relu(self.l1(self.bn(x)))
        h2 = F.relu(self.l2(h1))
        h3 = F.relu(self.l3(h2))
        output = self.l4(h3)

        return output
    
class predNN:
    def __init__(self, modelName: str , scoringDF: pd.DataFrame, raceCardDF: pd.DataFrame):
        self.modelName = modelName
        self.scoringDF = scoringDF.copy()
        self.raceCardDF = raceCardDF.copy()

    def loadModel(self):
        self.model = L.Classifier(Mychain())
        serializers.load_npz(f"../../../models/neuralNetwork/{self.modelName}.npz",self.model)

    def pred(self):
        forScoring_x = self.scoringDF.values
        forScoring_x = forScoring_x.astype(np.float32)
        socredDataNN = F.softmax(self.model.predictor(forScoring_x).data)[:,1].array
        self.raceCardDF["predNN"] = socredDataNN

        return self.raceCardDF

class predDelivery:
    def __init__(self, raceID: str, predDF: pd.DataFrame) -> None:
        self.raceID = raceID
        self.predDF = predDF.copy()
    
    def makeRaceInfoText(self) -> None:
        kaisu = self.raceID[6:8]
        kaisaibi = self.raceID[8:10]
        trackName = my_snipets.getTrackName(self.raceID)
        raceNo = self.raceID[10:]
        raceName = self.predDF["raceName"][0]
        raceType = self.predDF["raceType"][0]
        course_len = self.predDF["course_len"][0]
        weather = self.predDF["weather"][0]
        groundState = self.predDF["groundState"][0]
        self.raceInfoText = f"==========\n{int(kaisu)}回 {trackName} {int(kaisaibi)}日目" + "\n" + f"{int(raceNo)}R {raceName}\n" + f"{raceType}{course_len} 天気:{weather} 馬場:{groundState}\n=========="

    def makePredText(self, rank: int) -> None:
        self.predListLGBM = []
        self.predListNN = []
        raceCardDFLGBM=self.predDF[["馬名","オッズ更新","predLGBM"]].sort_values(by="predLGBM", ascending=False).head(rank).reset_index(drop=True)
        raceCardDFNN = self.predDF[["馬名","オッズ更新","predNN"]].sort_values(by="predNN", ascending=False).head(rank).reset_index(drop=True)
        for i in range(rank):
            textLGBM = raceCardDFLGBM["馬名"][i] + "/" + str(raceCardDFLGBM["オッズ更新"][i]) + "/" + str(raceCardDFLGBM["predLGBM"][i])
            textNN = self.predDF["馬名"][i] + "/" + str(raceCardDFNN["オッズ更新"][i]) + "/" + str(raceCardDFNN["predNN"][i])
            self.predListLGBM.append(textLGBM)
            self.predListNN.append(textNN)

        self.predTextLGBM = "【LGBM予測結果】==========\n馬名/単勝オッズ/予測値\n" + "\n".join(self.predListLGBM)
        self.predTextNN = "【DNN予測結果】==========\n馬名/単勝オッズ/予測値\n" + "\n".join(self.predListNN)

    def delivaryPredLine(self) -> None:
        text = self.raceInfoText + "\n\n" + self.predTextLGBM + "\n\n" + self.predTextNN

        CHANNEL_ACCESS_TOKEN = "iFSTH9Vagd7Ozy2YcYiH+xrjx+rmQL8xDWjZtAnIaT78vhIPhDdYQ0O7a1CSpuH2VxYeifzWNAdJWEgAkSHf2VNH9woaYVm2tB9HgWCFTRmfFZtDaJmTcUbZX0whj6/uQWUp9dquBfef24HYaWzejgdB04t89/1O/w1cDnyilFU="
        USER_ID = "U176770efe9b2a6d6bae891eb95ca0f45"

        configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            message = TextMessage(text=text)
            push_message_request = PushMessageRequest(to=USER_ID,messages=[message])
            messaging_api.push_message(push_message_request)