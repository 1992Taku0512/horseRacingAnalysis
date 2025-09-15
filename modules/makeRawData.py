import my_snipets
import random
import os
import requests
import time
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import re

import datetime
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from tqdm import tqdm

class makeHorseData:
    """
    馬データを作成するクラス  
    -`horseIDList`=>取得対象となるhorseIDのリスト

    ***
        - `getHorseHTML`:`horseIDList`の中にある馬の過去成績と血統表のHTMLを取得し、txtファイルとして保存するメソッド
            - `skipResult:bool` => 過去成績のHTML取得をスキップするかどうか
            - `skipPED:bool` => 血統表のHTML取得をスキップするかどうか  

    ***
        - `makeHorseRawData(関数)`:`horseIDList`の中にある馬の過去成績と血統表のRawデータを作成し、pickleファイルとして保存するメソッド
            - `skipResult:bool` => 過去成績のRawデータ作成をスキップするかどうか
            - `skipPED:bool` =>血統表のRawデータ作成をスキップするかどうか  
    """
    def __init__(self, horseIDList:list):
        self.horseIDList = horseIDList
        print(f"{len(self.horseIDList)}頭の馬の過去成績/血統情報データを作成します。")
    
    def getHorseHTML(self, skipResult=False,skipPED=True):
        with tqdm(self.horseIDList) as urlPbar:
            urlPbar.set_description("getHorseHTML")

            #browserの設定
            service = Service()
            service.creation_flags = 0x08000000  
            option = Options()
            option.add_argument('--headless')
            browser = webdriver.Chrome(options=option,service=service)

            for horseID in urlPbar:
                urlPbar.set_postfix({"horseID":horseID})
                #馬の過去成績のHTML取得=====================================================
                if skipResult == False or os.path.isfile(f"../../../data/html/horse/{horseID}.txt") == False :
                    urlPbar.set_postfix({"horseID":horseID + "(過去成績)"})

                    browser.get("https://db.netkeiba.com/horse/" + horseID)
                    html = browser.page_source
                    with open(f"../../../data/html/horse/{horseID}.txt","w",encoding="utf-8") as f:
                        f.write(html)

                #馬の血統表情報のHTML取得===================================================
                if skipPED == False or os.path.isfile(f"../../../data/html/ped/{horseID}.txt") == False :
                    urlPbar.set_postfix({"horseID":horseID + "(血統情報)"})

                    browser.get("https://db.netkeiba.com/horse/ped/" + horseID)
                    html2 = browser.page_source
                    with open(f"../../../data/html/ped/{horseID}.txt","w",encoding="utf-8") as f:
                        f.write(html2)

            browser.quit()
        return

    def makeHorseRawData(self,skipResult=False,skipPED=True):
        """
        ファイルリスト内のHTMLから馬の過去成績のRawデータを作成する関数  
        """
        columns = ["F","FF","FFF","FFFF","FFFFF","FFFFM","FFFM","FFFMF","FFFMM","FFM","FFMF","FFMFF","FFMFM","FFMM","FFMMF","FFMMM","FM","FMF","FMFF","FMFFF","FMFFM","FMFM","FMFMF","FMFMM","FMM","FMMF","FMMFF","FMMFM","FMMM","FMMMF","FMMMM",
                   "M","MF","MFF","MFFF","MFFFF","MFFFM","MFFM","MFFMF","MFFMM","MFM","MFMF","MFMFF","MFMFM","MFMM","MFMMF","MFMMM","MM","MMF","MMFF","MMFFF","MMFFM","MMFM","MMFMF","MMFMM","MMM","MMMF","MMMFF","MMMFM","MMMM","MMMMF","MMMMM"]

        with tqdm(self.horseIDList) as urlPbar:
            urlPbar.set_description("makeHorseRawData")
            for horseID in urlPbar:
                #馬の過去成績のrawデータを作成================================================            
                if skipResult == False or os.path.isfile(f"../../../data/rawData/horse/{horseID}.pickle") == False:
                    urlPbar.set_postfix({"horseID":horseID + "(過去成績)"})

                    # htmlが格納されたファイルを開く
                    with open(f"../../../data/html/horse/{horseID}.txt","r",encoding="utf-8") as f:
                        html = f.read()

                    #htmlから過去戦績のデータを抽出
                    contents = pd.read_html(StringIO(html))
                    if len(contents) < 3 :
                        horseResults = pd.DataFrame(columns=my_snipets.getHorseResultsColumns())
                    elif contents[2].columns[0] == "日付":
                        horseResults = contents[2]
                    else:
                        horseResults = contents[3]
                    
                    #データフレームをpickle形式で保存
                    horseResults.to_pickle(f"../../../data/rawData/horse/{horseID}.pickle")

                if skipPED == False or os.path.isfile(f"../../../data/rawData/ped/{horseID}.pickle") == False:
                    urlPbar.set_postfix({"horseID":horseID + "(血統情報)"})

                    with open(f"../../../data/html/ped/{horseID}.txt","r",encoding="utf-8") as f: #ファイルを開く
                        html = f.read()       

                    soup = BeautifulSoup(html,"html.parser") #htmlをsoupオブジェクトへ

                    contents = soup.find("table",attrs={"summary":"5代血統表"}).find_all("a",attrs={"href":re.compile(r"/horse/\d+")}) #血統表の馬名の部分を抽出

                    pedHorseNameList = []
                    for text in contents:
                        text2 = str(text.text)
                        text3 = text2.split("\n")[0]
                        pedHorseNameList.append(text3)

                    PEDFinDF = pd.DataFrame(pedHorseNameList).T
                    for i in range(len(columns)):
                        PEDFinDF.rename(columns={int(f"{i}"):f"{columns[i]}"},inplace=True)
                    PEDFinDF.rename(index={0:str(horseID)},inplace=True)

                    PEDFinDF.to_pickle(f"../../../data/rawData/ped/{horseID}.pickle")
        print(f"{len(self.horseIDList)}頭の馬の過去成績/血統表データを作成しました。")
             
        return
    
class makeRaceData:
    """
    レース結果に関するデータを作成するクラス  
    - `startYM(str)`=>取得開始年月(yyyymm)  
    - `endYM(str)`=>取得終了年月(yyyymm)  

    ***
        - `makeYMList`:`self.startYM`～`self.endYM`までの(year,month)のリスト(`self.YMList`)を作成するメソッド

    ***
        - `makeRaceDateURLList`:`self.YMList`に含まれる年月のレース開催日のリスト(`self.raceDateURLList`)を作成するメソッド

    ***
        - `makeRaceURLList`:`self.raceDateURLList`に含まれる開催日ページのURLから、レースIDのリスト(`self.raceIDList`)を作成するメソッド

    ***
        - `screpingRaceHTML`:`self.raceIDList`に含まれるレースの結果ページのHTMLをスクレイピングしてtxtで保存するメソッド
            - `skip:bool`=>すでに処理済みのレースに関する処理をスキップするかどうか

    ***
        - `makeRawDataRace`:`self.raceIDList`に含まれるレースのデータフレームを作成し、pickleで保存するメソッド
            - `skip:bool`=>すでに処理済みのレースに関する処理をスキップするかどうか   
    """

    def __init__(self, startYM:str, endYM:str):
        self.startYM = startYM
        self.endYM = endYM
        print(f"{self.startYM[0:4]}/{self.startYM[4:6]}～{self.endYM[0:4]}/{self.endYM[4:6]}のレース情報のデータを作成します。")

    def makeYMList(self):
        """
        `self.startYM`～`self.endYM`までの(year,month)のリスト(`self.YMList`)を作成するメソッド
        """
        self.YMList = []

        start = datetime.date(int(self.startYM[0:4]),int(self.startYM[4:]),1)
        end = datetime.date(int(self.endYM[0:4]),int(self.endYM[4:]),1)
        diff = monthmod(start,end)

        for i in tqdm(range(0,diff[0].months + 1),desc="makeYMList"):
            tgt = start + relativedelta(months=i)
            tgtYM = (str(tgt.year),str(tgt.month).zfill(2))
            self.YMList.append(tgtYM)


    def makeRaceDateURLList(self):
        """
        `self.YMList`に含まれる年月のレース開催日のリスト(`self.raceDateURLList`)を作成するメソッド
        """
        self.raceDateURLList = []
        for year , month in tqdm(self.YMList,desc="makeRaceDateURLList"):
            #対象年月の開催カレンダーのURLを生成
            url = f"https://race.netkeiba.com/top/calendar.html?year={year}&month={month}"
            #カレンダーページのHTMLを取得
            headers = {'User-Agent': random.choice(my_snipets.makeUserAgents())}
            html = requests.get(url, headers=headers)
            html.encoding = "EUC-JP"

            #HTMLをsoupオブジェクトに変換
            soup = BeautifulSoup(html.text,features="lxml")

            #開催日の一覧を取得し、開催日ページのURLを取得
            RaceCellBoxAll = soup.find_all("td",attrs={"class":"RaceCellBox"})
            
            for i in range(len(RaceCellBoxAll)):
                if RaceCellBoxAll[i].find("a") is not None:
                    self.raceDateURLList.append(RaceCellBoxAll[i].find("a")["href"].replace("..","https://race.netkeiba.com/"))

            time.sleep(2)

    def makeRaceURLList(self):
        """
        `self.raceDateURLList`に含まれる開催日ページのURLから、レースIDのリスト(`self.raceIDList`)を作成するメソッド
        """

        self.raceIDList = []

        with tqdm(self.raceDateURLList) as urlPbar:
            urlPbar.set_description(desc="makeRaceURLList")

            #browserの設定
            service = Service()
            service.creation_flags = 0x08000000  
            option = Options()
            option.add_argument('--headless')
            browser = webdriver.Chrome(options=option,service=service)

            for tgtURL in urlPbar:
                dateStr = tgtURL.split("=")[1]
                urlPbar.set_postfix({"date":dateStr[0:4]+"/"+dateStr[4:6]+"/"+dateStr[6:8]})

                # Seleniumを使用してブラウザを起動し、対象URLにアクセス
                browser.get(tgtURL)

                # ブラウザから必要な情報を取得
                RaceListDataItemAll = browser.find_elements(By.CLASS_NAME,"RaceList_DataItem")
                for item in RaceListDataItemAll:
                    raceURL = item.find_element(By.TAG_NAME,"a").get_attribute("href")
                    self.raceIDList.append(re.sub(r"\D+", "", str(raceURL.split("/")[-1:])))

            # ブラウザを閉じる
            browser.quit()

    def screpingRaceHTML(self,skip:bool=True):
        """
        `self.raceIDList`に含まれるレースの結果ページのHTMLをスクレイピングしてtxtで保存するメソッド
            - `skip:bool`=>すでに処理済みのレースに関する処理をスキップするかどうか
        """
        with tqdm(self.raceIDList) as urlPbar:
            urlPbar.set_description("screpingRaceHTML")

            #browserの設定
            service = Service()
            service.creation_flags = 0x08000000  
            option = Options()
            option.add_argument('--headless')
            browser = webdriver.Chrome(options=option,service=service)

            for raceID in urlPbar:
                urlPbar.set_postfix({"raceID":raceID})
                if skip == False or os.path.isfile(f"../../../data/html/race/{raceID}.txt") == False:
                    url = "https://db.netkeiba.com/race/" + raceID
                    # Seleniumを使用してブラウザを起動し、対象URLにアクセス
                    browser.get(url)
                    html = browser.page_source

                    with open(f"../../../data/html/race/{raceID}.txt","w") as f:
                        f.write(html)

                    time.sleep(1)
            # ブラウザを閉じる
            browser.quit()

    def makeRawDataRace(self,skip:bool = True):
        """
        `self.raceIDList`に含まれるレースのデータフレームを作成し、pickleで保存するメソッド
            - `skip:bool`=>すでに処理済みのレースに関する処理をスキップするかどうか   
        """
        with tqdm(self.raceIDList) as urlPbar:
            urlPbar.set_description("makeRawDataRace")               
            for raceID in urlPbar:
                if skip == False or os.path.isfile(f"../../../data/rawData/raceResults/{raceID}.pickle") == False or os.path.isfile(f"../../../data/rawData/raceInfos/{raceID}.pickle") == False or os.path.isfile(f"../../../data/rawData/return/{raceID}.pickle") == False:
                    urlPbar.set_postfix({"raceID":raceID})
                    #共通処理======================================================================================================================
                    with open(f"../../../data/html/race/{raceID}.txt","r") as f:
                        html = f.read()

                    soup = BeautifulSoup(html,features="lxml") #htmlをsoupオブジェクトへ
                    
                    #receResultsに関する処理=======================================================================================================
                    if skip == False or os.path.isfile(f"../../../data/rawData/raceResults/{raceID}.pickle") == False:
                        raceResults = pd.DataFrame() #最終出力データセットの定義
                        try:
                            dfRace = pd.read_html(StringIO(str(soup("table")[0])))[0]
                        except IndexError :
                            print(f"raceID:{raceID}の処理をスキップします。")
                            continue

                        dfRace["raceID"] = raceID

                        horseIDList = []
                        horseAList = soup.find("table",attrs={"summary":"レース結果"}).find_all("a",attrs={"href":re.compile("^/horse")})
                        for a in horseAList:
                            horseID = re.findall("\d+",a["href"])
                            horseIDList.append(horseID[0])
                            
                        dfRace["horseID"] = horseIDList

                        jockeyIDList = []
                        jockeyAList = soup.find("table",attrs={"summary":"レース結果"}).find_all("a",attrs={"href":re.compile("^/jockey")})
                        for a in jockeyAList:
                            jockeyID = re.findall("\d+",a["href"])
                            jockeyIDList.append(jockeyID[0])

                        dfRace["jockeyID"] = jockeyIDList

                        raceResults = pd.concat([raceResults,dfRace])

                        raceResults.to_pickle(f"../../../data/rawData/raceResults/{raceID}.pickle")

                    #receInfosに関する処理==========================================================================================================
                    if skip == False or os.path.isfile(f"../../../data/rawData/raceInfos/{raceID}.pickle") == False:
                        raceInfos = pd.DataFrame() #最終出力データセットの定義
                        text = soup.find("div",attrs={"class" : "data_intro"}).find_all("p")[0].text + soup.find("div",attrs={"class" : "data_intro"}).find_all("p")[1].text
                        info = re.findall("\w+",text)

                        infoDict = {}
                        infoDict["raceID"] = raceID
                        infoDict["raceName"] = soup.find("div",attrs={"class" : "data_intro"}).find_all("h1")[0].text
                        for text in info:
                            if text in ["芝","ダート"]:
                                infoDict["raceType"] = text
                            if "障" in text:
                                infoDict["raceType"] = "障害"
                            if "m" in text:
                                infoDict["course_len"] = re.findall("\d+",text)[0]
                            if text in ["良","稍重","重","不良"]:
                                infoDict["groundState"] = text
                            if text in ["曇","晴","雨","小雨","小雪","雪"]:
                                infoDict["weather"] = text
                            if "年" in text :
                                infoDict["date"] = text

                        raceInfos = pd.DataFrame(infoDict,index=[0])
                        #raceInfos = pd.concat([raceInfos, dfInfo], ignore_index=True)

                        raceInfos.to_pickle(f"../../../data/rawData/raceInfos/{raceID}.pickle")
                    
                    #returnTableに関する処理========================================================================================================
                    #同着の時にイレギュラーパターンがあるからそれを処理する機能の追加必須
                    if skip == False or os.path.isfile(f"../../../data/rawData/return/{raceID}.pickle") == False:
                        table1 = pd.read_html(StringIO(str(soup("table")[1]).replace("<br/>","or")))[0]
                        table2 = pd.read_html(StringIO(str(soup("table")[2]).replace("<br/>","or")))[0]
                        returnTable = pd.concat([table1,table2])
                        returnTable.reset_index(drop=True,inplace=True)
                        
                        betList = returnTable[0].unique()
                        for betting in betList:
                            tgt = returnTable[returnTable[0] == betting]
                            if "or" in tgt[1].to_string(index=False):        
                                for i in [1,2,3]:
                                    tgtstring = tgt[i].to_string(index=False)
                                    tgtlist = tgtstring.split("or")
                                    tgtdf = pd.DataFrame(tgtlist)
                                    tgtdf.rename(columns={0:i},inplace=True)
                                    if i == 1:
                                        returnFin = tgtdf
                                    else:
                                        returnFin = pd.merge(returnFin,tgtdf,left_index=True, right_index=True,how="left")

                                    returnFin[0] = betting

                                    returnTable = returnTable[returnTable[0] != betting]
                                    returnTable = pd.concat([returnTable,returnFin])

                        returnTable.reset_index(drop=True,inplace=True)
                        returnTable.rename(columns={0:"betting",1:"results",2:"payout",3:"popularity"},inplace=True)

                        returnTable["payout"] = returnTable["payout"].apply(lambda x: int(str(x).replace(",", "")))
                        returnTable["payoutRate"] = returnTable["payout"] / 100
                        returnTable["raceID"] = raceID


                        returnTable.to_pickle(f"../../../data/rawData/return/{raceID}.pickle")
        print(f"{self.startYM[0:4]}/{self.startYM[4:6]}～{self.endYM[0:4]}/{self.endYM[4:6]}のレース情報のデータを作成しました")
