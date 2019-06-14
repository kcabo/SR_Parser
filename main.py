import requests
import re
import csv
from time import time
from tqdm import tqdm

from my_parse import pop_record_notRelay, pop_record_relay, pop_meets_codes, pop_meet_info

event_config_ptn = re.compile(r"&sex=(\d)&event=(\d)&distance=(\d)")
events_dic = {
    1:"自由形",
    2:"背泳ぎ",
    3:"平泳ぎ",
    4:"バタフライ",
    5:"個人メドレー",
    6:"フリーリレー",
    7:"メドレーリレー"
}
distance_dic = {
    1:"25m",
    2:"50m",
    3:"100m",
    4:"200m",
    5:"400m",
    6:"800m",
    7:"1500m"
}
sex_dic = {
    1:"男子",
    2:"女子",
    3:"混合"
}
region_dic = {
    "01" : "北海道",
    "02" : "青森",
    "03" : "岩手",
    "04" : "宮城",
    "05" : "秋田",
    "06" : "山形",
    "07" : "福島",
    "08" : "茨城",
    "09" : "栃木",
    "10" : "群馬",
    "11" : "埼玉",
    "12" : "千葉",
    "13" : "東京",
    "14" : "神奈川",
    "15" : "山梨",
    "16" : "長野",
    "17" : "新潟",
    "18" : "富山",
    "19" : "石川",
    "20" : "福井",
    "21" : "静岡",
    "22" : "愛知",
    "23" : "三重",
    "24" : "岐阜",
    "25" : "滋賀",
    "26" : "京都",
    "27" : "大阪",
    "28" : "兵庫",
    "29" : "奈良",
    "30" : "和歌山",
    "31" : "鳥取",
    "32" : "島根",
    "33" : "岡山",
    "34" : "広島",
    "35" : "山口",
    "36" : "香川",
    "37" : "徳島",
    "38" : "愛媛",
    "39" : "高知",
    "40" : "福岡",
    "41" : "佐賀",
    "42" : "長崎",
    "43" : "熊本",
    "44" : "大分",
    "45" : "宮崎",
    "46" : "鹿児島",
    "47" : "沖縄",
    "48" : "学連関東",
    "49" : "学連中部",
    "50" : "学連関西",
    "51" : "学連中・四国",
    "52" : "学連九州",
    "53" : "学連北部",
    "70" : "全国大会",
    "80" : "国際大会"
}
region_list = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16",
    "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32",
    "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48",
    "49", "50", "51", "52", "53", "70", "80"
]
meet_header_ptn = re.compile(r"(.+)　（(.+)） (.水路)")

# url = "http://www.swim-record.com/swims/ViewResult/?h=V1100&code=4118702&sex=1&event=1&distance=2" #佐賀県の少ないやつ
# url = "http://www.swim-record.com/swims/ViewResult/?h=V1000&code=1418608"
# html = get_html(url)
# l = pop_meet_info(html)
#
# print(len(l))
# print(l)
#

def get_html(url, params = None):
    if params is None:
        r = requests.get(url)
    else:
        r = requests.get(url, params = params)
    r.encoding = "cp932"
    html = r.text
    return html

def create_meets_info_table(meets_view_url):
    #特定の年度・地域の大会一覧画面からそれぞれの大会の日付や場所などの情報を抽出し、csvの文字列を返す
    html = get_html(meets_view_url)
    meet_code_list = pop_meets_codes(html)
    csvStr = ""

    for id in meet_code_list:
        meet_info_url = "http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + id
        m_html = get_html(meet_info_url)
        meet_info = pop_meet_info(m_html)
        if meet_info == []:
            continue
        matchOb = re.search(meet_header_ptn, meet_info[1])
        #大会ID	年度	区分地域	識別三桁	開始日付	終了日付	大会名	会場	水路	種目一覧
        row = [id, id[2:4], id[0:2], id[4:], meet_info[0][:10], meet_info[0][-10:], matchOb.group(1), matchOb.group(2), matchOb.group(3), str(len(meet_info[2]))]
        csvStr += ",".join(row) + "\n"

    return csvStr

def conv_to_100sec(formatSec):
    colon_posi = formatSec.find(":")
    dot_posi = formatSec.find(".")
    num = formatSec.replace(".","").replace(":","")
    if num.isdecimal() == False or dot_posi == -1: #.がないときはもうタイムじゃないとして空白返す
        return ""
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

def create_record_table_4one_meet(meet_id): #いち大会ごとにID渡して処理する
    meet_info_url = "http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + meet_id
    m_html = get_html(meet_info_url)
    meet_info = pop_meet_info(m_html)
    result_view_url = "http://www.swim-record.com/swims/ViewResult/"
    # csvStr = ""
    if meet_info == []:
        return []
    all_result4meet = []
    for event_link in meet_info[2]: #各種目のリンクのリスト
        matchOb = re.search(event_config_ptn, event_link)
        sex = matchOb.group(1)
        event = matchOb.group(2)
        distance = matchOb.group(3)
        # if sex == "1":
        params = {
        "h" : "V1100",
        "code" : meet_id,
        "sex" : sex,
        "event" : event,
        "distance" : distance
        }
        html = get_html(result_view_url, params)
        if event == "6" or event == "7": #リレーのとき
            relay_result = pop_record_relay(html)
            for r_result in relay_result: #リレーの結果が何チームもあるなかから一つずつ取り出す
                #リレー全体タイムの処理
                row = [
                    r"&all",
                    r_result[1].replace("　",""),
                    "リレー", #学年はリレーと表示
                    str(conv_to_100sec(r_result[2])),
                    "99",
                    events_dic[int(event)],
                    distance_dic[int(distance)],
                    sex_dic[int(sex)],
                    meet_id
                ]
                # csvStr += ",".join(row) + "\n"
                all_result4meet.append(row)

                #泳者ごとの処理
                if len(r_result[0]) == 4: #ちゃんと四人いたらやる
                    lap_list = r_result[3]
                    lap_count = len(lap_list) #200mなら4 400mなら8、800mなら16ある 長水路ならば
                    lap_width = lap_count // 4 #一人の記録は何ラップ分か 1,2,4
                    for order in range(1, 5): #1,2,3,4

                        #前の泳者のindex
                        foreIndex = lap_width * (order - 1) - 1

                        #処理中の泳者のindex
                        aftIndex = lap_width * order - 1

                        #一人分のタイム
                        try:
                            if order == 1: #第一泳者のとき
                                time = conv_to_100sec(lap_list[aftIndex])
                            else:
                                time = conv_to_100sec(lap_list[aftIndex]) - conv_to_100sec(lap_list[foreIndex])
                        except:
                            time = ""

                        row = [
                            r_result[0][order - 1].replace("　",""), #indexだから引く1
                            r_result[1].replace("　",""),
                            "リレー", #学年はリレーと表示
                            str(time),
                            str(order),
                            events_dic[int(event)],
                            distance_dic[int(distance)],
                            sex_dic[int(sex)],
                            meet_id
                        ]
                        # csvStr += ",".join(row) + "\n"
                        all_result4meet.append(row)

        else:
            result = pop_record_notRelay(html)
            for r in result:
                row = [
                    r[0].replace("　",""),
                    r[1].replace("　",""),
                    r[2],
                    str(conv_to_100sec(r[3])),
                    "0",
                    events_dic[int(event)],
                    distance_dic[int(distance)],
                    sex_dic[int(sex)],
                    meet_id
                ]
                # csvStr += ",".join(row) + "\n"
                all_result4meet.append(row)

    return all_result4meet

if __name__ == "__main__":
    csvStr = ""
    for i, region in enumerate(region_list):
        # startT = time()
        region_name = region_dic[region]
        print("地域:{}を実行中です。進行:{}/55".format(region_name, i))
        url = "http://www.swim-record.com/taikai/17/{}.html".format(region)
        csvStr += create_meets_info_table(url)

    path = "MeetsID.csv"
    with open(path, "a", encoding="utf-8-sig") as f:
        f.write(csvStr)

#
# if __name__ == "__main__":
#     t1 = time()
#
#     for i, region in enumerate(region_list):
#         startT = time()
#         region_name = region_dic[region]
#         print("地域:{}を実行中です。進行:{}/55".format(region_name, i))
#         url = "http://www.swim-record.com/taikai/19/{}.html".format(region)
#         html = get_html(url)
#         meet_code_list = pop_meets_codes(html) #大会IDの一覧を取得
#         all_result4region = []
#         count_record = 0
#         for meet_id in tqdm(meet_code_list):
#             all_result4meet = create_record_table_4one_meet(meet_id)
#             count_record += len(all_result4meet)
#             all_result4region.extend(all_result4meet)
#
#         path = "tables2019/{}_2019.csv".format(region_name)
#         with open(path, "w", encoding="utf-8-sig") as f:
#             writer = csv.writer(f, lineterminator='\n')
#             writer.writerows(all_result4region)
#
#         log = "{},{}大会,{}レコード,{}秒".format(region_name, len(meet_code_list), count_record, int(time() - startT))
#         print(log)
#         with open("log_2019.csv", "a", encoding="utf-8-sig") as f2:
#             print(log, file = f2)
#
#     t2 = time()
#     print("2019年全地域の処理完了\n実行時間：{}".format(t2-t1))
#
#     # url = "http://www.swim-record.com/taikai/18/41.html"
#     # # csv = create_meets_info_table(url)
#     #
#     # html = get_html(url)
#     # meet_code_list = pop_meets_codes(html) #大会IDの一覧を取得
#     # # csvStr = "氏名,所属,学年,記録,泳順,種目,距離,性別,大会ID\n"
#     #
#     # for c in tqdm(meet_code_list):
#     #     meet_info_url = "http://www.swim-record.com/swims/ViewResult/?h=V1000&code=" + c
#     #     csvStr += create_record_table(meet_info_url, c)
#     #
#     # path = "佐賀2018.csv"
#     # with open(path, "w", encoding="utf-8-sig") as f:
#     #     f.write(csvStr)
#     #
#     # t2 = time()
#     # print("実行時間：{}".format(t2-t1))
#
