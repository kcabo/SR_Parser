from bs4 import BeautifulSoup
import re

link_ptn = re.compile(r"code=\d{7}$")
link_results_ptn = re.compile(r"&sex=\d&event=\d&distance=\d")

#HTML文字列を受け取って記録をすべてリストにして返す

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

def pop_meet_info(html):
    soup = BeautifulSoup(html, "lxml")
    meet_info = soup.find("div", class_ = "headder").find_all("td", class_ = "p14b")
    events_aTags = soup.find("div", class_ = "body").find_all("a", href = link_results_ptn)
    if len(events_aTags) == 0:
        return []
    events_list = []
    for a in events_aTags:
        link = a["href"]
        events_list.append(link)
    #日付、大会名、種目リンクリスト
    results = [meet_info[0].string, meet_info[1].string, events_list]
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
