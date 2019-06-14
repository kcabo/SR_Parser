from tqdm import tqdm
import re
import csv

path = "tables2019/all_2019.csv"
ptn = re.compile(r"(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*)")
gaku_list = ["高校 1","高校 2","高校 3","リレー",""]
sex_list = ["男子", "混合"]

new_l =[]

with open(path, "r", encoding="utf-8-sig") as f2:
    reader = csv.reader(f2)
    for row in tqdm(reader):
        if row[7] in sex_list and row[2] in gaku_list:
            new_l.append(row)

#
# for i,r in enumerate(all_l):
#     matchOb = re.search(ptn, r)
#     # try:
#     if r != "":
#         if matchOb.group(8) in sex_list:
#             if matchOb.group(3) in gaku_list:
#                 print(r)
#                 new_l.append([r])
    # except:
    #     print(i, all_l[i], all_l[i].encode(), all_l[i] == "")
    #     break
outPath = "output_2019.csv"
with open(outPath, "w", encoding="utf-8-sig") as f:
    writer = csv.writer(f, lineterminator='\n')
    writer.writerows(new_l)

#
# t = "長江立志,BIGｱﾐ,中学 1,4688,0,自由形,50m,男子,2218721"
# ptn = re.compile(r"(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*)")
#
# matchOb = re.search(ptn, t)
# print(matchOb.group(8))
#
# gaku = matchOb.group(3)
#
# gaku_list = ["中学 3","高校 1","高校 2","高校 3","リレー",""]
#
# print(gaku in gaku_list)
