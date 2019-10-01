from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import constant
import env
import os
import re
import requests

from bs4 import BeautifulSoup, element
from tqdm import tqdm

url = os.getenv('SWIM_DB_URL')
engine = create_engine(url, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

meet_link_ptn = re.compile(r"code=[0-9]{7}$") # <a href="../../swims/ViewResult?h=V1000&amp;code=0119605"
meet_caption_ptn = re.compile(r"(.+)　（(.+)） (.水路)") # 茨城:第42回県高等学校春季　（取手ｸﾞﾘｰﾝｽﾎﾟｰﾂｾﾝﾀｰ） 長水路
event_link_ptn = re.compile(r"&code=(\d{7})&sex=(\d)&event=(\d)&distance=(\d)") # "/swims/ViewResult?h=V1100&code=0919601&sex=1&event=5&distance=4"


def get_html(url):
    req = requests.get(url)
    req.encoding = "cp932"
    return req.text

class Meet(Base):
    __tablename__ = 'meets'
    id = Column(Integer, primary_key=True)                      # 連番で振られるid
    meetid = Column(String, unique = True, nullable = False)    # 7桁の大会ID 0119721など0で始まることもある
    name = Column(String, nullable = False)                     # 大会名
    place = Column(String, nullable = False)                    # 会場
    pool = Column(String, nullable = False)                     # 短水路or長水路
    start = Column(String, nullable = False)                    # 大会開始日 2019/09/24 で表す
    end = Column(String, nullable = False)                      # 大会終了日
    area = Column(Integer, nullable = False)                    # 地域(整数)
    year = Column(Integer, nullable = False)                    # 開催年
    code = Column(Integer, nullable = False)                    # 下三桁

    def __init__(self, meet_id):
        self.meetid = meet_id
        self.area = int(meet_id[:2])
        self.year = int(meet_id[2:4])
        self.code = int(meet_id[-2:])   # 下三桁
        html = get_html("http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + meet_id)
        soup = BeautifulSoup(html, "lxml")
        caption = soup.find("div", class_ = "headder").find_all("td", class_ = "p14b")
        date = caption[0].string # 2019/04/27 - 2019/04/27  ←caption[0]
        self.start = date[:10]
        self.end = date[-10:]
        matchOb = re.match(meet_caption_ptn, caption[1].string) # 茨城:第42回県高等学校春季　（取手ｸﾞﾘｰﾝｽﾎﾟｰﾂｾﾝﾀｰ） 長水路  ←caption[1]
        self.name = matchOb.group(1)
        self.place = matchOb.group(2)
        self.pool = matchOb.group(3)


class Event:
    def __init__(self, link):   # link = "/swims/ViewResult?h=V1100&code=0919601&sex=1&event=5&distance=4"
        matchOb = re.search(event_link_ptn, link)
        self.url = "http://www.swim-record.com" + link
        self.meet_id = matchOb.group(1)
        self.sex = int(matchOb.group(2))
        self.style = int(matchOb.group(3))
        self.distance = int(matchOb.group(4))

    def parse_table(self):
        html = get_html(self.url)
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("tr", align = "center", bgcolor = False)       # 中央寄せで背景なしクラス指定なし= レコード行
        lap_tables = soup.find_all("tr", align = "right", id = True, style = True)# このtrは見出しも含むLAPSのテーブル全体
        return table, lap_tables


class Record(Base): #個人種目の１記録
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)                      # 連番で振られるid
    meetid = Column(String, nullable = False)                   # 7桁の大会ID 0119721など0で始まることもある
    sex = Column(Integer, nullable = False)                     # 性別
    style = Column(Integer, nullable = False)                   # 泳法
    distance = Column(Integer, nullable = False)                # 距離
    name = Column(String, nullable = False)                     # 選手氏名
    team = Column(String, nullable = False)                     # 所属名
    grade = Column(String, nullable = False)                    # 学年
    time = Column(String, nullable = False)                     # タイム。#:##.##書式文字列
    laps = Column(String, nullable = False)                     # ラップタイム。#:##.##,#:##.##,...

    def __init__(self, meet_id, sex, style, distance, row, lap_table):
        self.meetid = meet_id
        self.sex = sex
        self.style = style
        self.distance = distance
        data = row.find_all("td")
        self.name = data[1].string
        self.team = data[2].string
        self.grade = data[3].string
        self.time = data[4].a.string if data[4].a is not None else ""
        laps = lap_table.find_all("td", width = True)
        self.laps = [lap.string for lap in laps]

    def fix_raw_data(self):
        self.name = del_space(self.name)
        self.team = del_space(self.team)
        self.grade = del_space(self.grade)
        self.time = format_time(del_space(self.time))
        self.laps = ",".join([format_time(del_space(lap)) for lap in self.laps])


class RelayResult(Base): #リレーの１結果
    __tablename__ = 'relay'
    id = Column(Integer, primary_key=True)                      # 連番で振られるid
    meetid = Column(String, nullable = False)                   # 7桁の大会ID 0119721など0で始まることもある
    sex = Column(Integer, nullable = False)                     # 性別
    style = Column(Integer, nullable = False)                   # 泳法
    distance = Column(Integer, nullable = False)                # 距離
    team = Column(String, nullable = False)                     # 所属名
    first = Column(String, nullable = False)                    # 第一泳者
    second = Column(String, nullable = False)                   # 第二泳者
    third = Column(String, nullable = False)                    # 第三泳者
    fourth = Column(String, nullable = False)                   # 第四泳者
    time = Column(String, nullable = False)                     # タイム。#:##.##書式文字列
    laps = Column(String, nullable = False)                     # ラップタイム。#:##.##,#:##.##,...

def create_table():
    Base.metadata.create_all(bind=engine)


# 大会一覧から大会IDの一覧をとってくる
def find_meet(year, area):
    url = r"http://www.swim-record.com/taikai/{}/{}.html".format(year, area)
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")
    #div内での一番最初のtableが競泳、そのなかでリンク先がコードになっているものを探す
    meet_id_aTags = soup.find("div", class_ = "result_main").find("table", recursive = False).find_all("a", href = meet_link_ptn)
    id_list = [a["href"][-7:] for a in meet_id_aTags] #大会コード七桁のみ抽出
    return id_list


# 指定年度の大会の情報をDBに追加
def fetch_meets(year):
    print("{}年の大会IDを集めています…".format(year))
    meet_ids = []
    for area in tqdm(constant.area_list):
        meet_ids.extend(find_meet(year, area))

    print("大会の情報を取得しています…")
    meets = [Meet(id) for id in tqdm(meet_ids)]
    session.add_all(meets)
    session.commit()


def arrange_events():
    targets = session.query(Meet).all() # .filter(Meet.start >= "2019/09/25").all()
    events = []
    print("{}の大会の全開催種目を集めています…".format(len(targets)))
    for meet in tqdm(targets):
        html = get_html("http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + meet.meetid)
        soup = BeautifulSoup(html, "lxml")
        aTags = soup.find_all("a", class_=True)             # 100m自由形などへのリンク
        events.extend([Event(a["href"]) for a in aTags])    # リンクから種目のインスタンス生成
    print("{}種目見つかりました。".format(len(events)))       # 25690 10min-1390meets
    return events


space_erase_table = str.maketrans("","","\n\r 　 ") #第三引数に指定した文字が削除される。左から、LF,CR,半角スペース,全角スペース,nbsp
def del_space(str):
    return str.translate(space_erase_table) if str is not None else ""

time_format_ptn = re.compile(r'([0-9]{0,2}):?([0-9]{2}).([0-9]{2})')
def format_time(time_str):
    if time_str == "":
        return ""
    else:
        ob = re.match(time_format_ptn, time_str)
        min = ob.group(1) if ob.group(1) != "" else 0
        return "{}:{}.{}".format(min, ob.group(2), ob.group(3))


# create_table()
# fetch_meets(19)

events = arrange_events()
records =[]

for e in tqdm(events):
    if e.style <= 5: # 個人種目＝自由形・背泳ぎ・平泳ぎ・バタフライ・個人メドレー
        table, lap_tables = e.parse_table()
        records.extend([Record(e.meet_id, e.sex, e.style, e.distance, row, lap_table) for row, lap_table in zip(table, lap_tables)])

for r in records:
    r.fix_raw_data()
    # print(r.meetid, r.style, r.name, r.team, r.grade, r.time,  r.laps)

session.add_all(records)
session.commit()

#
# if __name__ == '__main__':
#     fetch_meets(input())
