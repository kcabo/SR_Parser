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
    year = Column(Integer, nullable = False)                    # 開催年
    area = Column(Integer, nullable = False)                    # 地域(整数)
    code = Column(Integer, nullable = False)                    # 下三桁

    def __init__(self, meet_id):
        self.meetid = meet_id
        self.year = int(meet_id[:2])
        self.area = int(meet_id[2:4])
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


class IndividualEvent: # 個人種目
    def __init__(self, link):   # link = "/swims/ViewResult?h=V1100&code=0919601&sex=1&event=5&distance=4"
        matchOb = re.search(event_link_ptn, link)
        self.url = "http://www.swim-record.com" + link
        self.meet_id = matchOb.group(1)
        self.sex = int(matchOb.group(2))
        self.style = int(matchOb.group(3))
        self.distance = int(matchOb.group(4))



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


def fetch_meets(year):
    print("{}年の大会IDを集めています…".format(year))
    meet_ids = []
    for area in tqdm(constant.area_list):
        meet_ids.extend(find_meet(year, area))

    print("大会の情報を取得しています…")
    meets = [Meet(id) for id in tqdm(meet_ids)]

    session.add_all(meets)
    session.commit()



targets = session.query(Meet).all() # .filter(Meet.meetid == "0919701").all()
events = []
for meet in tqdm(targets):
    html = get_html("http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + meet.meetid)
    soup = BeautifulSoup(html, "lxml")
    events_aTags = soup.find_all("a", class_=True)
    events.extend([IndividualEvent(a["href"]) for a in events_aTags])

# for e in events:
#     print(e.url)

print(len(events)) #25690 10min-1390meets

#
# if __name__ == '__main__':
#     fetch_meets(input())
