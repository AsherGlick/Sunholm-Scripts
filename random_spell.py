import json
import datetime
import random
import sys

today = datetime.datetime.now()
date = today.strftime('%Y/%m/%d')




with open("spells_20210917.json") as f:
    spells = json.load(f)

# random.seed(date)
random_spells = random.sample(spells, int(sys.argv[1]))

cost_lookup = {
    "Cantrip": 10,
    "1st": 60,
    "2nd": 120,
    "3rd": 200,
    "4th": 320,
    "5th": 640,
    "6th": 1280,
    "7th": 2560,
    "8th": 5120,
    "9th": 10240,
}


random_spells.sort(key=lambda x: str(cost_lookup[x["level"]]).zfill(5) + x["text"])


print("__{padding}**Legend 03's Spells** - {date}{padding}__".format(date=date, padding=" "*16))
for random_spell in random_spells:
    print("\n**{name}** - <https://www.dndbeyond.com{link}>\n{cost}Gp - {level} Level - {school}".format(
        name=random_spell["text"],#.ljust(max_length, ' '),
        level=random_spell["level"],
        cost=cost_lookup[random_spell["level"]],
        link=random_spell["link"],
        school=random_spell["school"].capitalize(),
    ))
