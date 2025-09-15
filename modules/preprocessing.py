import datetime
import pickle

import pandas as pd
import numpy as np

class preprocessingRaceCard:
    """
    出馬表のデータの前処理を実施し、スコアリング用データを作成するクラス
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def raceCardPreprocess(self) -> None:
        """
        出馬表データに対して、前処理を実行するメソッド
        """
        # カラム名の整形
        newColumns = []
        for col in self.df.columns:
            newColumns.append(col.replace(" ",""))
        self.df.columns = newColumns

        #性齢 → Sex/Age
        self.df["Sex"] = self.df["性齢"].astype(str).str[:1]
        self.df["Age"] = self.df["性齢"].str.extract(r'(\d+)').astype(int)

        #馬体重(増減) → Weight/WeightVariation
        try:
            self.df["Weight"] = self.df["馬体重(増減)"].str.split("(",expand=True)[0].astype(int)
            self.df["WeightVariation"] = self.df["馬体重(増減)"].str.split("(",expand=True)[1].str[:-1].astype(int)
        except AttributeError:
            self.df["Weight"] = np.nan
            self.df["WeightVariation"] = np.nan

        #カラムの変数型の成型
        self.df["course_len"] = self.df["course_len"].astype(int)

        return

    def makedataHorseResults(self) -> None:
        """
        出馬表に存在する全ての馬の過去成績のデータを縦結合する
        """

        self.horseResults = pd.DataFrame()
        horseIDList = self.df["horseID"].tolist()
        cnt = 1
        for horseID in horseIDList:
            print("\r" + "(" + str(cnt) + "/" + str(len(horseIDList)) + ")",end="")

            dftmp = pd.read_pickle(f"../../../data/rawData/horse/{horseID}.pickle")

            indexdf = []
            for i in range(len(dftmp)):
                indexdf.append(horseID)

            dftmp.index = indexdf
            self.horseResults = pd.concat([self.horseResults,dftmp])
            cnt += 1
        
        # カラム名の整形
        newColumns = []
        for col in self.horseResults.columns:
            newColumns.append(col.replace(" ",""))
        self.horseResults.columns = newColumns

        return
    
    def horseResultsPreprocess(self) -> None:
        """
        過去成績のデータを前処理する関数
        """
        self.horseResults["Rank_y"] = self.horseResults["着順"].astype(str).str.strip("()降再")
        self.horseResults = self.horseResults[self.horseResults["Rank_y"].astype(str).str.contains("\d")]
        self.horseResults["Rank_y"] = self.horseResults["Rank_y"].astype(float)
        self.horseResults["Rank_Y"] = self.horseResults["Rank_y"].astype(int)

        #変数の型を修正
        self.horseResults["date"] = pd.to_datetime(self.horseResults["日付"])

        #不要変数の削除
        self.horseResults.drop(columns=["着順","日付"], inplace=True)

        return
    
    def makeVarFromHorseResults(self) -> None:
        """
        馬の過去成績から変数を作成し、出馬表データに付与し、スコアリング用データを作成するメソッド
        作成変数===================  
        pre1Rank  :前1走の順位  
        pre2Rank  :前2走の順位  
        pre3Rank  :前3走の順位  
        pre4Rank  :前4走の順位  
        pre5Rank  :前5走の順位  
        preAllRank:過去すべての順位の平均  
        pre1Term  :前1走から今回までの期間(日)  
        pre2Term  :前2走から前1走までの期間(日)  
        pre3Term  :前3走から前2走までの期間(日)  
        pre4Term  :前4走から前3走までの期間(日)  
        pre5Term  :前5走から前4走までの期間(日)
        """

        self.forScoringDF = self.df.copy()
        #過去の順位系の変数作成===================================================================================================
        #pre1Rank,pre2Rank,pre3Rank,preAllRankMean
        #馬結果テーブルを中央の結果のみにする
        forPreRank = self.horseResults[self.horseResults['開催'].str.contains("札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉")]

        #レース結果テーブルと馬結果テーブルを結合(Rank,date,)
        forPreRank2 = self.df.merge(forPreRank[["Rank_y","date"]], left_on = "horseID", right_index = True, how = "left")

        #対象レースより過去の日付の結果のみに絞る
        forPreRank2 = forPreRank2[forPreRank2["date_x"] > forPreRank2["date_y"]]
        #レースID,horseIDをキーに連番をふる(何個前のレースかの番号)
        forPreRank2["no"] = forPreRank2.groupby(["raceID","horseID"]).cumcount()

        #過去レースの順位テーブルを作成
        for i in range(5):
            preRankTmp = pd.DataFrame()
            preRankTmp = forPreRank2[forPreRank2["no"] == i][["raceID","horseID","Rank_y"]]
            preRankTmp.rename(columns={'Rank_y': f'pre{str(i + 1)}Rank'},inplace=True)
            self.forScoringDF = self.forScoringDF.merge(preRankTmp, left_on=["raceID","horseID"],right_on=["raceID","horseID"],how="left")

        preAllRankMean = forPreRank2.groupby(["raceID","horseID"]).mean("Rank_y")
        preAllRankMean.rename(columns={"Rank_y":"preAllRankMean"},inplace=True)
        self.forScoringDF = self.forScoringDF.merge(preAllRankMean["preAllRankMean"],left_on=["raceID","horseID"],right_index=True,how="left")
        #過去実績のない馬に対する処理を追加する必要あり

        #過去のレース間日数系の変数作成============================================================================================
        #pre1Term,pre2Term,pre3Term
        #レース結果テーブルと馬結果テーブルを結合(Rank,date,)
        forPreTerm = self.df.merge(self.horseResults[["Rank_y","date"]], left_on = "horseID", right_index = True, how = "left")
        #対象レースより過去の日付の結果のみに絞る
        forPreTerm = forPreTerm[forPreTerm["date_x"] > forPreTerm["date_y"]]
        #レースID,horseIDをキーに連番をふる(何個前のレースかの番号)
        forPreTerm["no"] = forPreTerm.groupby(["raceID","horseID"]).cumcount()

        #過去のレース間の日数を算出
        preTermFin = pd.DataFrame()
        termColumnsList = ["raceID","horseID"]
        for i in range(5):
            preTermTmp = forPreTerm[forPreTerm["no"] == i][["raceID","horseID","date_x","date_y"]]
            preTermTmp.rename(columns={"date_y":f"pre{str(i + 1)}date"},inplace=True)

            if i == 0 :
                preTermFin = preTermTmp
                preTermFin.rename(columns={"date_x":"pre0date"},inplace=True)
            else:
                preTermFin = preTermFin.merge(preTermTmp[["raceID","horseID",f"pre{str(i + 1)}date"]],left_on=["raceID","horseID"],right_on=["raceID","horseID"],how="left")

            preTermFin[f"pre{str(i + 1)}Term"] = preTermFin[f"pre{str(i)}date"] - preTermFin[f"pre{str(i + 1)}date"]
            preTermFin[f"pre{str(i + 1)}Term"] = preTermFin[f"pre{str(i + 1)}Term"] / datetime.timedelta(days=1)
            termColumnsList.append(f"pre{str(i + 1)}Term")

        #dftmpにレース間日数情報を結合
        self.forScoringDF = self.forScoringDF.merge(preTermFin[termColumnsList],left_on=["raceID","horseID"],right_on=["raceID","horseID"],how="left")

        return
    
    def forScoringDFPreprocess(self) -> pd.DataFrame:
        """
        スコアリング用データの前処理をするメソッド
        """
        #カラム名の成形
        self.forScoringDF = self.forScoringDF.rename(columns={"枠":"枠番","オッズ更新":"単勝","予想オッズ":"単勝"})

        #必要なカラムだけ残す
        self.forScoringDF = self.forScoringDF[[
            '枠番',
            '馬番', 
            '斤量',
            '単勝',
            '人気',
            'course_len',
            'weather',
            'raceType',
            'groundState',
            'Sex',
            'Age',
            'Weight',
            'WeightVariation',
            'pre1Rank',
            'pre2Rank',
            'pre3Rank',
            'pre4Rank',
            'pre5Rank',
            'preAllRankMean',
            'pre1Term',
            'pre2Term',
            'pre3Term',
            'pre4Term',
            'pre5Term']]
        
        #labelEncoding
        categorical_features = ["weather","raceType","groundState","Sex"]
        for col in categorical_features:
            with open(f"../../../data/labelencoder/{col}_labelEncoder.pickle","rb") as f:
                LE = pickle.load(f)

            LE.classes_ = np.append(LE.classes_,np.nan)
            self.forScoringDF[col] = LE.transform(self.forScoringDF[col])
            self.forScoringDF[col] = self.forScoringDF[col].astype("category")
        
        #欠損値補完
        self.forScoringDF = self.forScoringDF.fillna({
            "枠番":-1,
            "馬番":-1,
            "Weight":-1,
            "WeightVariation":-1,
            "pre1Rank":-1,
            "pre2Rank":-1,
            "pre3Rank":-1,
            "pre4Rank":-1,
            "pre5Rank":-1,
            "preAllRankMean":-1,
            "pre1Term":-1,
            "pre2Term":-1,
            "pre3Term":-1,
            "pre4Term":-1,
            "pre5Term":-1})
        
        return self.forScoringDF