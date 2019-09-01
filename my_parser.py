from bs4 import BeautifulSoup, element
import re
import requests
import sys

import dic

link_ptn = re.compile(r"code=\d{7}$")
event_param_ptn = re.compile(r"&code=(\d{7})&sex=(\d)&event=(\d)&distance=(\d)")
result_link_ptn = re.compile(r"&sex=\d&event=\d&distance=\d")
meet_caption_ptn = re.compile(r"(.+)　（(.+)） (.水路)")

jrHigh_grade_ptn = re.compile(r"中.+([1-2])") #ここ状況に応じて変える
univ_grade_ptn = re.compile(r"大.+(\d)")


def get_html(url, params = None):
    if params is None:
        r = requests.get(url)
    else:
        r = requests.get(url, params = params)
    r.encoding = "cp932"
    html = r.text
    return html


class Meet:
    def __init__(self, meet_id):
        html = get_html("http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + meet_id)
        soup = BeautifulSoup(html, "lxml")

        self.id = meet_id # 例：0819301
        self.year =  meet_id[2:4]
        self.region = meet_id[:2]
        self.last3digits = meet_id[4:]

        caption = soup.find("div", class_ = "headder").find_all("td", class_ = "p14b")
        # 例：
        # 2019/04/27 - 2019/04/27  ←caption[0]
        # 茨城:第42回県高等学校春季　（取手ｸﾞﾘｰﾝｽﾎﾟｰﾂｾﾝﾀｰ） 長水路  ←caption[1]
        date = caption[0].string
        self.start_date = date[:10]
        self.end_date = date[-10:]

        matchOb = re.search(meet_caption_ptn, caption[1].string)
        self.meet_name = matchOb.group(1)
        self.place = matchOb.group(2)
        self.pool = matchOb.group(3)

        events_aTags = soup.find("div", class_ = "body").find_all("a", href = result_link_ptn)
        self.events = [Event(a["href"]) for a in events_aTags]
        self.count_events = len(self.events)

    def get_records(self, *event_id): #sex,style,distanceをつなげた三桁がevent_idに一致するか
        records = []
        for event in self.events:
            if event.event_id in event_id: #タプルで受け取った引数に含まれているか
                event.extract() #全データ抽出
                distance = dic.distance[event.distance]
                style = dic.style[event.style]

                if event.style < 6: #個人種目のとき
                    for r in event.records:

                        #----中学生のみを抽出----
                        # matchOb = re.search(jrHigh_grade_ptn, r.grade)

                        #----大学生のみを抽出----
                        matchOb = re.search(univ_grade_ptn, r.grade)


                        if matchOb is not None:
                            # grade = "中学" + str(int(matchOb.group(1)) + 1) #去年の記録のときは学年をいっこあげる
                            grade = "大学" + str(int(matchOb.group(1)))
                            records.append([r.name, r.team, grade, distance, style, r.time, self.id])
                        #--ここまで--

                else: #リレー種目のとき
                    for r in event.records:
                        if len(r.name) == 4: #棄権のときを除く
                            target_index = len(r.laps) / 4 - 1 #一泳のラップはどこにある？
                            if target_index >= 0 and int(target_index) == target_index:
                                records.append([r.name[0], r.team, r.grade, distance, style, r.laps[int(target_index)], self.id])

        # for eve in self.events:
        #     if eve.sex == sex and eve.style == style and eve.distance == distance:
        #         eve.extract()
        #
        #         if style < 6:
        #             for r in eve.records:
        #                 index = len(r.laps)/2 - 1
        #                 if index < 0:
        #                     print("\nラップが存在しません。id:{} name:{} time:{}".format(self.id, r.name, r.time))
        #                     records.append([r.name, r.team, r.grade, r.time, None, 0, dic.sex[sex], dic.style[style], dic.distance[distance], self.id])
        #                 else:
        #                     records.append([r.name, r.team, r.grade, r.time, r.laps[0], 0, dic.sex[sex], dic.style[style], dic.distance[distance], self.id])
        #         else:
        #             pass #リレーのの抽出は今度追加しよう
        return records

class Event:
    def __init__(self, href):
        matchOb = re.search(event_param_ptn, href)
        self.url = "http://www.swim-record.com" + href
        self.meet_id = matchOb.group(1)
        self.sex = int(matchOb.group(2))
        self.style = int(matchOb.group(3))
        self.distance = int(matchOb.group(4))
        self.is_relay = False if self.style < 6 else True
        self.event_id = self.sex * 100 + self.style * 10 + self.distance

    def extract(self):
        html = get_html(self.url)
        soup = BeautifulSoup(html, "lxml")
        rows = soup.find_all("tr", align = "center", bgcolor = False) #, class_ = False) #中央寄せで背景なしクラス指定なし= レコード行
        rows_lap = soup.find_all("tr", align = "right", id = True, style = True) #idとか指定してあるのはLAPのtrだけ このtrは見出しも含むLAPSのテーブル全体
        self.records = [Record(row, row_lap, self.is_relay) for row, row_lap in zip(rows, rows_lap)]

class Record:
    def __init__(self, row, row_lap, is_relay):
        data = row.find_all("td")
        if is_relay == False:
            self.name = fix_td2str(data[1])
            self.team = fix_td2str(data[2])
            self.grade = fix_td2str(data[3])
            self.time = conv_to_100sec(fix_td2str(data[4].a))
            laps = row_lap.find_all("td", width = True)
            self.laps = [conv_to_100sec(fix_td2str(lap.string)) for lap in laps]

        else:
             #名前のところが<br>タグで7つに区切られている。タグでないところのみ抽出
            self.name = [fix_relay_order(name) for name in data[1].contents if isinstance(name, element.NavigableString)]
            self.team = fix_td2str(data[2])
            self.grade = "Relay"
            self.time = conv_to_100sec(fix_td2str(data[4].a))
            laps = row_lap.find_all("td", width = True)
            self.laps = [conv_to_100sec(fix_td2str(lap.string)) for lap in laps]


space_erase_table = str.maketrans("","","\n\r 　 ") #第三引数に指定した文字が削除される。左から、LF,CR,半角スペース,全角スペース,nbsp
def fix_td2str(td):
    if td is None:
        return None
    else:
        fixed = td.string.translate(space_erase_table) if td.string is not None else None
        return fixed

space_and_nums = str.maketrans("","","\n\r 　 123.")
def fix_relay_order(s):
    fixed = s.translate(space_and_nums)
    return fixed

def conv_to_100sec(formatSec):
    if formatSec is None:
        return None
    colon_posi = formatSec.find(":")
    dot_posi = formatSec.find(".")
    num = formatSec.replace(".","").replace(":","")
    if num.isdecimal() == False or dot_posi == -1: #.がないときはもうタイムじゃないとしてNONE返す
        return None
    elif colon_posi == -1: #32.99とかのとき
        seconds = int(formatSec[:dot_posi])
        dotSec = int(formatSec[dot_posi + 1:])
        time_value = seconds * 100 + dotSec
    else: #1:45.89
        minutes = int(formatSec[:colon_posi])
        seconds = int(formatSec[colon_posi + 1 : dot_posi])
        dotSec = int(formatSec[dot_posi + 1:])
        time_value = (minutes * 60 + seconds) * 100 + dotSec
    return time_value

def meet_id_list(year, region_id):
    url = r"http://www.swim-record.com/taikai/{}/{}.html".format(year, region_id)
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")
    #div内での一番最初のtableが競泳、そのなかでリンク先がコードになっているものを探す
    meet_id_aTags = soup.find("div", class_ = "result_main").find("table", recursive = False).find_all("a", href = link_ptn)
    id_list = [a["href"][-7:] for a in meet_id_aTags] #大会コード七桁のみ抽出
    return id_list


#HTML文字列を受け取って記録をすべてリストにして返す
#以下ほぼ不要
def pop_meets_codes(html):
    results = []
    soup = BeautifulSoup(html, "lxml")
    #div内での一番最初のtableが競泳、そのなかでリンク先がコードになっているものを探す
    meet_code_aTags = soup.find("div", class_ = "result_main").find("table", recursive = False).find_all("a", href = link_ptn)
    if len(meet_code_aTags) == 0:
        return []
    for a in meet_code_aTags:
        code = a["href"][-7:] #大会コード七桁のみ抽出
        results.append(code)
    return results

def pop_record_notRelay(html):
    results = []
    soup = BeautifulSoup(html, "lxml")

    #予選も決勝も4つ目のdivのなかで複数のtableに分けて格納されている
    main_body = soup.find_all("div")[3]

    #div直下のtableを取得するが、このままだとテーブル化された見出しも含まれる
    tables = main_body.find_all("table", recursive = False)

    for t in tables:
        row = t.find_all("tr", align = "center", bgcolor = False) #中央寄せで背景なしのレコード行をしぼれるから次の二行はいらないかも
        # if len(row) != 2: #見出し(男子50m自由形とか)のレコード数ば1しかない
        #     continue
        for r in row:
            tds = r.find_all("td")
            if len(tds) != 9: #一行につき9列＝9データあるはずだから一応チェック
                raise Exception("trにおける必要なtdの数が足りません。通常は9です。")
            record = [tds[1], tds[2], tds[3], tds[4].a] #氏名、所属、学年 #記録はaタグ内にある
            for i, s in enumerate(record):
                fixed = str(s.string if s is not None else "").strip()
                record[i] = fixed
            results.append(record)
    return results

def pop_record_relay(html):
    results = []
    soup = BeautifulSoup(html, "lxml")

    #予選も決勝も4つ目のdivのなかで複数のtableに分けて格納されている
    main_body = soup.find_all("div")[3]

    #div直下のtableを取得するが、このままだとテーブル化された見出しも含まれる
    tables = main_body.find_all("table", recursive = False)

    for t in tables:
        row = t.find_all("tr", align = "center", bgcolor = False) #中央寄せで背景なしのレコード行をしぼれるから次の二行はいらないかも
        row_lap = t.find_all("tr", align = "right", id = True, style = True) #idとか指定してあるのはLAPのtrだけ
        if len(row) != len(row_lap):
            raise UnexpectedTable("通常レコード行とラップ行の数が一致しません")
        for order, r in enumerate(row):
            tds = r.find_all("td")
            if len(tds) != 7: #一行につき7列＝7データあるはずだから一応チェック
                raise Exception("trにおける必要なtdの数が足りません。通常は7です。")

            #1ー選手4人分のリスト
            swimmers_list = tds[1].contents
            swimmers_list_fixed = []
            for swr in swimmers_list:
                if len(swr) > 0:
                    name = str(swr).strip().strip("1""2""3""4""."" ")
                    swimmers_list_fixed.append(name)

            #2,3ーチーム名、リンクになっているタイム（誰かが失格だとここは--:--.--みたいになる、一泳失格か棄権のときは空白）
            team = str(tds[2].string if tds[2] is not None else "").strip()
            time_official = str(tds[3].a.string if tds[3].a is not None else "").strip()

            #４－リレーなのでラップタイムも取得する 同じrow_lapの同じindexにラップタイムがある。。。はず
            target_lap_tds = row_lap[order].find("table").find_all("td", width = True) #テーブル内においてwidthが設定されてるtdにタイムが格納されている
            laps = []
            for l_td in target_lap_tds:
                lap = str(l_td.string if l_td is not None else "").strip()
                laps.append(lap)

            record = [swimmers_list_fixed, team, time_official, laps]
            results.append(record)
    return results

def pop_meet_info(html):
    soup = BeautifulSoup(html, "lxml")
    meet_info = soup.find("div", class_ = "headder").find_all("td", class_ = "p14b")
    events_aTags = soup.find("div", class_ = "body").find_all("a", href = result_link_ptn)
    if len(events_aTags) == 0:
        return []
    events_list = []
    for a in events_aTags:
        link = a["href"]
        events_list.append(link)
    #日付、大会名、種目リンクリスト
    results = [meet_info[0].string, meet_info[1].string, events_list]
    return results
