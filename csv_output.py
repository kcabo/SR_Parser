import csv
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

# region_ids = ["22"]

def records_in_csv(year):
    t1 = time()
    path = "output/Fr100.csv"
    records = []
    print("{}年度の抽出を開始\t現在時刻：{}\n".format(year, datetime.now().strftime("%H:%M:%S")))

    for i, region_id in enumerate(region_ids):
        t2 = time()
        print("{:-^8} 進行中:{}/55".format(dic.region[region_id], i + 1))

        meet_ids = my_parser.meet_id_list(year, region_id)
        for id in tqdm(meet_ids):
            meet = my_parser.Meet(id)
            records.extend(meet.get_records(sex = 1, style = 1, distance = 3))

        print(">{:.3f}\n".format(time() - t2))

    with open(path, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(records)

    print("###{}年度を完了###経過：{:.3f}秒###".format(year,time() - t2))


def update_meets_info():
    path = "output/meets_info.csv"
    info = []
    years = [19,18,17]
    print("Targes = {}".format(years))

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

    target = input("year? or 'update' >> ")

    if target == "update":
        update_meets_info()

    elif target.isdecimal():
        records_in_csv(int(target))

    else:
        print("invalid")
