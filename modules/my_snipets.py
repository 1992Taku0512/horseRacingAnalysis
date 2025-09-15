def makeUserAgents():
    """
    USER_AGENTSのリストを返す関数
    Returns:
        list: USER_AGENTSのリスト
    """
    returnList = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 OPR/85.0.4341.72",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 OPR/85.0.4341.72",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Vivaldi/5.3.2679.55",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Vivaldi/5.3.2679.55",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Brave/1.40.107",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Brave/1.40.107",
    ]

    return returnList

def getHorseResultsColumns():
    """
    馬の過去成績のリストを返す関数
    """
    returnList = ['日付', '開催', '天 気', 'R', 'レース名', '映 像', '頭 数', '枠 番', '馬 番', 'オ ッ ズ',
       '人 気', '着 順', '騎手', '斤 量', '距離', '馬 場', '馬場 指数', 'タイム', '着差', 'ﾀｲﾑ 指数',
       '通過', 'ペース', '上り', '馬体重', '厩舎 ｺﾒﾝﾄ', '備考', '勝ち馬 (2着馬)', '賞金']
    
    return returnList

def getTrackName(raceID: str) -> str:
    """
    raceIDから開催競馬場名を取得する関数
    """
    if raceID[4:6] == "01":
        trackName = "札幌"
    elif raceID[4:6] == "02":
        trackName = "函館"
    elif raceID[4:6] == "03":
        trackName = "福島"
    elif raceID[4:6] == "04":
        trackName = "新潟"
    elif raceID[4:6] == "05":
        trackName = "東京"
    elif raceID[4:6] == "06":
        trackName = "中山"
    elif raceID[4:6] == "07":
        trackName = "中京"
    elif raceID[4:6] == "08":
        trackName = "京都"
    elif raceID[4:6] == "09":
        trackName = "阪神"
    elif raceID[4:6] == "10":
        trackName = "小倉"

    return trackName