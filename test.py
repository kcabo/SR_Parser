import requests
from bs4 import BeautifulSoup
import re
# url = "http://www.swim-record.com/swims/ViewResult/?h=V1100&code=1418301&sex=1&event=1&distance=2"
# url = "http://www.swim-record.com/swims/ViewResult/?h=V1000&code=1418301"
url = "http://www.swim-record.com/taikai/18/41.html"
params = {
"h" : "V1100",
"code" : 1418301,
"sex" : 1,
"event" : 6,
"distance" : 5
}
r = requests.get(url) #, params=params)
r.encoding = "cp932"
html = r.text
soup = BeautifulSoup(html, "lxml")

a = soup.find("select", class_ = "select").find_all("option", value = True)
str = ""
for i in a:
    # str += "\"" + i["value"].replace(r".html","") + "\" : \"" + i.string + "\",\n"
    str += "\"" + i["value"].replace(r".html","") + "\", "
path = "output_selection.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write(str)
# o = soup.find("div", class_ = "headder").find_all("td", class_ = "p14b")
#
# o = soup.find("div", class_ = "body").find_all("a", href = re.compile(r"h=V1100&code=1418301&sex=\d&event=\d&distance=\d"))
# print(len(o))
# for i in o:
#     print(i["href"])



# o = soup.find_all("div")[3].find_all("table", recursive = False)[2].find_all("tr", recursive = False)[2].find_all("td")[1]
# op = o.contents
#
# print(str(op))
# for o2 in op:
#     print(str(o2).strip().replace("\xa0",""))
#     print(len(o2))
#     print(o)


# n = soup.find_all("table")

# o = soup.find_all(class_ = "p12bw")[0].parent.parent.next_sibling.next_sibling.tr.td.string #予選がこれで見つかる
# p = soup.find_all(text = re.compile(".*/22.*"))
#
# print(n[-1].find_all_next())
# print("------")
# print(n[-2].find_all("tr")[-1].find_all("td")[0].string)
# print(o)
# print(p)
# print(soup.prettify())
# print(r.elapsed.total_seconds())
# print("あ")
