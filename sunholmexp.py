import math
import sys
import json
import random

level_exp_caps =  [
	0,
	300,
	900,
	2700,
	6500,
	14000,
	23000,
	34000,
	48000,
	64000,
	85000,
	100000,
	120000,
	140000,
	165000,
	195000,
	225000,
	265000,
	305000,
	355000,
	355000, # upper bound threshold at level 20, repeated for index delta convienience
]

quest_log_gold_map = [
	{ # Level 1
		"multiplier": 5,
		"dice_size": 4,
	},
	{ # Level 2
		"multiplier": 10,
		"dice_size": 4,
	},
	{ # Level 3
		"multiplier": 15,
		"dice_size": 6,
	},
	{ # Level 4
		"multiplier": 20,
		"dice_size": 6,
	},
	{ # Level 5
		"multiplier": 25,
		"dice_size": 8,
	},
	{ # Level 6
		"multiplier": 30,
		"dice_size": 8,
	},
	{ # Level 7
		"multiplier": 35,
		"dice_size": 10,
	},
	{ # Level 8
		"multiplier": 40,
		"dice_size": 10,
	},
	{ # Level 9
		"multiplier": 45,
		"dice_size": 12,
	},
	{ # Level 10
		"multiplier": 50,
		"dice_size": 12,
	},
	{ # Level 11
		"multiplier": 55,
		"dice_size": 20,
	},
	{ # Level 12
		"multiplier": 60,
		"dice_size": 20,
	},
	{ # Level 13
		"multiplier": 65,
		"dice_size": 20,
	},
	{ # Level 14
		"multiplier": 70,
		"dice_size": 20,
	},
	{ # Level 15
		"multiplier": 75,
		"dice_size": 20,
	},
	{ # Level 16
		"multiplier": 80,
		"dice_size": 20,
	},
	{ # Level 17
		"multiplier": 85,
		"dice_size": 20,
	},
	{ # Level 18
		"multiplier": 90,
		"dice_size": 20,
	},
	{ # Level 19
		"multiplier": 95,
		"dice_size": 20,
	},
	{ # Level 20
		"multiplier": 100,
		"dice_size": 20,
	},
	

]



def main():
	argv = sys.argv
	if len(argv) < 3:
		print("Error, must have [totalexp] [playername:playerexp] ...")
		exit(1)

	save = False
	if argv[-1] == "--save":
		argv = argv[:-1]
		save=True

	stage = False
	if argv[-1] == "--stage":
		argv = argv[:-1]
		stage=True


	player_exp_history = []
	with open("playerexpcache.json", "r") as f:
		player_exp_history = json.load(f)
	
	cached_player_exp = player_exp_history[-1]["players"]
	new_player_exp = {}
	for player in cached_player_exp:
		new_player_exp[player] = cached_player_exp[player]


	total_exp = int(argv[1])

	players = []

	quest_log_player_gold = {}

	for player in argv[2:]:
		player_name = player
		quest_log_bonus = False
		quest_log_gold = False

		# Suffix witwh + to indicate they wrote a quest log (effects gold only)
		if player_name.endswith("+"):
			player_name = player_name[:-1]
			quest_log_gold = True

		# Suffix with ++ to indicate that they completed the questlog within
		# a timeframe
		if player_name.endswith("+"):
			player_name = player_name[:-1]
			quest_log_bonus = True


		if player_name in cached_player_exp:
			player_exp = int(cached_player_exp[player_name])
		else:
			player_exp = 300
			print("New player", player_name, "starting at 300xp")

		player_level = get_level_from_exp(player_exp)

		if quest_log_gold:
			quest_log_player_gold[player_name] = bonus_gold_for_quest_log(player_level)

		players.append({
			"name": player_name,
			"exp": player_exp,
			"level": player_level,
			"quest_log_bonus": quest_log_bonus,
			"quest_log_bonus_exp": 0,
			"gained_exp": 0,
			"leveled_up": False
			})

	players = divide_exp(total_exp, players)

	bonus_exp = sum([x["gained_exp"] for x in players]) - total_exp


	for player in players:
		if player["quest_log_bonus"]:

			quest_log_bonus_exp = bonus_exp_for_quest_log(player["level"])

			if player["level"] < get_level_from_exp(math.ceil(player["exp"] + player["gained_exp"] + quest_log_bonus_exp)):
				player["leveled_up"] = True

			player["gained_exp"] += quest_log_bonus_exp
			player["quest_log_bonus_exp"] = quest_log_bonus_exp


	for player in players:
		quest_log_exp_string = ""
		if player["quest_log_bonus_exp"] > 0:
			quest_log_exp_string = str(player["quest_log_bonus_exp"])+"xp bonus from quest log, "
		if player["leveled_up"]:
			print("{player_name} leveled up to level {new_level} ({quest_log_exp_string}{new_total_exp}xp total). {remaining_exp_string}.".format(
				player_name=player["name"],
				new_level=str(player["level"]+1),
				quest_log_exp_string=quest_log_exp_string,
				new_total_exp=str(player["exp"] + player["gained_exp"]),
				remaining_exp_string=remaining_exp(player["level"]+1, player["exp"] + player["gained_exp"])
			))

		else:
			print("{player_name} gained {gained_exp}xp ({quest_log_exp_string}{new_total_exp}xp total). {remaining_exp_string}.".format(
				player_name=player["name"],
				gained_exp=str(player["gained_exp"]),
				quest_log_exp_string=quest_log_exp_string,
				new_total_exp=str(player["exp"] + player["gained_exp"]),
				remaining_exp_string=remaining_exp(player["level"], player["exp"] + player["gained_exp"]),
			))

		new_player_exp[player["name"]] = player["exp"] + player["gained_exp"]

		if player["name"] in quest_log_player_gold:
			print("- {player_name} also received {received_gold}Gp ({gold_multiplier}*1d{gold_dice_size}) for their quest log.".format(
				player_name=player["name"],
				received_gold=str(quest_log_player_gold[player["name"]]),
				gold_multiplier=str(quest_log_gold_map[player["level"]-1]["multiplier"]),
				gold_dice_size=str(quest_log_gold_map[player["level"]-1]["dice_size"]),
			))
	import datetime
	today = datetime.date.today()



	player_exp_history.append({
		"date": today.strftime('%Y/%m/%d'),
		"exp": total_exp,
		"bonus_exp":bonus_exp,
		"players": new_player_exp
	})

	if save:
		with open("playerexpcache.json", "w") as f:
			json.dump(player_exp_history, f, indent=4)
	elif stage:
		with open("playerexpcache-stage.json", "w") as f:
			json.dump(player_exp_history, f, indent=4)
		print("Results saved to staging file")

	else:
		print("Not Saving Results use --save to save results")

	print("Bonus Exp:", bonus_exp, "("+str(bonus_exp/len(players)) +")")

def bonus_exp_for_quest_log(level):
	delta = level_exp_caps[level] - level_exp_caps[level-1]
	return int(math.ceil(delta* .05))

def bonus_gold_for_quest_log(level):
	roll = random.randint(1,quest_log_gold_map[level-1]["dice_size"])
	return roll * quest_log_gold_map[level-1]["multiplier"]

def remaining_exp(current_level, current_exp):
	return "{exp_within_level}/{total_level_exp}xp through level {current_level} ({remaining_exp_within_level}xp remaining)".format(
		exp_within_level=str(current_exp - level_exp_caps[current_level-1]),
		total_level_exp=str(level_exp_caps[current_level]-level_exp_caps[current_level-1]),
		current_level=current_level,
		remaining_exp_within_level=str(level_exp_caps[current_level] - (current_exp)),
	)



def divide_exp(total_exp, players):
	if (total_exp == 0):
		for player in players:
			player["gained_exp"] = math.ceil(player["gained_exp"])


		return players

	all_players_leveled_up = True
	for player in players:
		if player["leveled_up"] == False:
			all_players_leveled_up = False
			break

	if all_players_leveled_up:
		return players


	max_player_level = max([x["level"] for x in players])

	total_player_slices = sum([adjusted_player_award(max_player_level, x["level"]) for x in players if not x["leveled_up"]] )
	for player in players:
		if player["leveled_up"]:
			continue
		adjusted_award = adjusted_player_award(max_player_level, player["level"])
		player["gained_exp"] += total_exp * adjusted_award / total_player_slices


	total_leftover_exp = 0

	for player in players:
		if player["level"] < get_level_from_exp(math.ceil(player["exp"] + player["gained_exp"])):
			player["leveled_up"] = True
			leftover_exp = player["exp"] + player["gained_exp"] - level_exp_caps[player["level"]]
			player["gained_exp"] = level_exp_caps[player["level"]] - player["exp"]
			total_leftover_exp += leftover_exp

	return divide_exp(total_leftover_exp, players)



def get_level_from_exp(exp):
	for i, level_exp_cap in enumerate(level_exp_caps):
		if exp < level_exp_cap:
			return i


def adjusted_player_award(max_player_level, player_level):
	return math.pow(math.sqrt(2), max_player_level-player_level)


if __name__ == "__main__":
	main()
