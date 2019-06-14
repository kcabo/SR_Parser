from tqdm import tqdm
import re
import csv

path = "all_swimmers/all_3years.csv"
# ptn = re.compile(r"(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*)")
# gaku_list = ["高校 1","高校 2","高校 3","リレー",""]
# sex_list = ["男子", "混合"]

new_l =[]
c = 0
with open(path, "r", encoding="utf-8-sig") as f2:
    reader = csv.reader(f2)
    for row in tqdm(reader):
        c += 1

print(c)
