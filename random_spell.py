import json
import random

with open("spells_20210508.json") as f:
    spells = json.load(f)

random_spells = random.sample(spells, 3)

max_length = 0
for random_spell in random_spells:
    if max_length < len(random_spell["text"]):
        max_length = len(random_spell["text"])

for random_spell in random_spells:
    print("{} : https://www.dndbeyond.com{}".format(
        random_spell["text"].ljust(max_length, ' '),
        random_spell["link"]
    ))
