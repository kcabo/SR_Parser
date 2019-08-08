import csv
import sys
from time import time
from datetime import datetime
from tqdm import tqdm

import my_parser
import dic

region_ids = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16",
    "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32",
    "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48",
    "49", "50", "51", "52", "53", "70", "80"
]

# region_ids = ["14"]

def records_in_csv(year):
    t1 = time()
    path = "output/2018.4/{}.csv".format(year)
    records = []
    count = 0
    print("\n{}年度の抽出を開始\t現在時刻：{}\n".format(year, datetime.now().strftime("%H:%M:%S")))

    for i, region_id in enumerate(region_ids):
        t2 = time()
        print("{:-^8} 進行中:{:>2}/55".format(dic.region[region_id], i + 1))

        meet_ids = my_parser.meet_id_list(year, region_id)
        for id in tqdm(meet_ids):
            meet = my_parser.Meet(id)
            if meet.pool == "長水路":
                records.extend(meet.get_records(112,113,114,115,116,117,122,123,124,132,133,134,142,143,144,154,155,164,165,166,174,175))

        print("> {:.2f}秒  レコード数:{:>5}\n".format(time() - t2, len(records) - count))
        count = len(records)

    with open(path, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(records)

    print("###{}年度を完了###経過：{:.2f}秒###".format(year,time() - t1))


def update_meets_info():
    path = "output/2018.4/meets_info.csv"
    info = []
    years = [19,18]
    print("Targets = {}".format(years))

    for year in years:
        for region_id in tqdm(region_ids):
            meet_ids = my_parser.meet_id_list(year, region_id)

            for id in meet_ids:
                meet = my_parser.Meet(id)
                info.append([
                    meet.id,
                    meet.year,
                    meet.region,
                    meet.last3digits,
                    meet.start_date,
                    meet.end_date,
                    meet.meet_name,
                    meet.place,
                    meet.pool,
                    meet.count_events,
                ])

    with open(path, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(info)


if __name__ == "__main__":

    target = input("####SR_PARSER###\ninput target years or 'update' >> ")

    if target == "update":
        update_meets_info()

    else:
        target_years = target.split(",")
        for y in target_years:
            if y.isdecimal():
                records_in_csv(int(y))
            else:
                print("invalid year")
                sys.exit(1)
