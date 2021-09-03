import math
import sys
import json
import random
import datetime
import argparse
import os
from typing import Any, List, Dict
from dataclasses import dataclass

################################ Level EXP Caps ################################
# The The amount of exp you need to be at a specific level.                    #
################################################################################
level_exp_caps: List[int] = [
    0,  # Min XP for level 1
    300,  # Min XP for Level 2
    900,  # Min XP for level 3
    2700,  # Min XP for level 4
    6500,  # Min XP for level 5
    14000,  # Min XP for level 6
    23000,  # Min XP for level 7
    34000,  # Min XP for level 8
    48000,  # Min XP for level 9
    64000,  # Min XP for level 10
    85000,  # Min XP for level 11
    100000,  # Min XP for level 12
    120000,  # Min XP for level 13
    140000,  # Min XP for level 14
    165000,  # Min XP for level 15
    195000,  # Min XP for level 16
    225000,  # Min XP for level 17
    265000,  # Min XP for level 18
    305000,  # Min XP for level 19
    355000,  # Min XP for level 20
    355000,  # upper bound threshold at level 20, repeated for index delta convenience
]

############################## Quest Log Gold Map ##############################
# A lookup table for mapping the level of a character to the rng units to use  #
# when calculating how much gold they will get for writing a quest log.        #
################################################################################
quest_log_gold_map = [
    {  # Level 1
        "multiplier": 5,
        "dice_size": 4,
    },
    {  # Level 2
        "multiplier": 10,
        "dice_size": 4,
    },
    {  # Level 3
        "multiplier": 15,
        "dice_size": 6,
    },
    {  # Level 4
        "multiplier": 20,
        "dice_size": 6,
    },
    {  # Level 5
        "multiplier": 25,
        "dice_size": 8,
    },
    {  # Level 6
        "multiplier": 30,
        "dice_size": 8,
    },
    {  # Level 7
        "multiplier": 35,
        "dice_size": 10,
    },
    {  # Level 8
        "multiplier": 40,
        "dice_size": 10,
    },
    {  # Level 9
        "multiplier": 45,
        "dice_size": 12,
    },
    {  # Level 10
        "multiplier": 50,
        "dice_size": 12,
    },
    {  # Level 11
        "multiplier": 55,
        "dice_size": 20,
    },
    {  # Level 12
        "multiplier": 60,
        "dice_size": 20,
    },
    {  # Level 13
        "multiplier": 65,
        "dice_size": 20,
    },
    {  # Level 14
        "multiplier": 70,
        "dice_size": 20,
    },
    {  # Level 15
        "multiplier": 75,
        "dice_size": 20,
    },
    {  # Level 16
        "multiplier": 80,
        "dice_size": 20,
    },
    {  # Level 17
        "multiplier": 85,
        "dice_size": 20,
    },
    {  # Level 18
        "multiplier": 90,
        "dice_size": 20,
    },
    {  # Level 19
        "multiplier": 95,
        "dice_size": 20,
    },
    {  # Level 20
        "multiplier": 100,
        "dice_size": 20,
    },
]


# We are rewriting sunholmexp.py as an event source model

EVENTSOURCE_FILE="exp_events.json"

def main() -> None:
    parser = argparse.ArgumentParser(description="A Tool For Managing and Leveling Sunholm Players")


    subparsers = parser.add_subparsers(help="Commands", dest="command")

    parser_session_exp = subparsers.add_parser("exp", help="Grant a set of players exp for a session.")
    parser_session_exp.add_argument('exp', type=int, help="The Amount of exp that was gained this session")
    parser_session_exp.add_argument('-p', '--player', metavar="player", type=str, action='append', default=[], help="A player who participated this session.")
    parser_session_exp.add_argument('-q', '--questlog', metavar="player", type=str, action='append', default=[], help="A player who wrote a quest log for last session and participated in this one.")
    parser_session_exp.add_argument('-f', '--fastlog', metavar="player", type=str, action='append', default=[], help="A player who wrote a quest log for last session within a time limit and participated in this one.")

    parser_new_player = subparsers.add_parser("new", help="Add a new player to the game")
    parser_new_player.add_argument('playername', type=str, help="The name of the new player.")
    parser_new_player.add_argument('--startingxp', metavar="xp", type=int, help="How much XP should the player start with", default=300)

    parser_new_player = subparsers.add_parser("bonus", help="Give an out of band bonus to a player")
    parser_new_player.add_argument('playername', type=str, help="The name of the player.")
    parser_new_player.add_argument('bonusxp', type=int, help="How much xp bonus to give.")

    parser_new_player = subparsers.add_parser("list", help="List current exp and levels")
    parser_new_player.add_argument('playername', type=str, nargs="?", default="", help="The name of the player.")

    parser_new_player = subparsers.add_parser("last", help="Print out the change dialog from the most recent session")
    # TODO, maybe an ability to print out an even more early one

    parsed_args = parser.parse_args()


    # print(parsed_args)
    if parsed_args.command == "exp":
        add_exp_event(
            exp_gained=parsed_args.exp,
            attending_players=parsed_args.player,
            questlog_players=parsed_args.questlog,
            fastlog_players=parsed_args.fastlog,
        )
        list_previous_update()
        return

    elif parsed_args.command == "new":
        add_new_player_event(
            player_name=parsed_args.playername,
            starting_exp=parsed_args.startingxp)
        list_previous_update()
        return

    elif parsed_args.command == "bonus":
        add_bonus_exp_event(
            player_name=parsed_args.playername,
            bonus_exp=parsed_args.bonusxp
        )
        list_previous_update()
        return

    elif parsed_args.command == "list":
        list_current_state(parsed_args.playername)
        return

    elif parsed_args.command == "last":
        list_previous_update()
        return

    print("Error, a command must be chosen. Use --help to see commands")


def add_event(event: Any) -> None:
    event_list = get_event_list()


    today = datetime.datetime.now()
    event["date"] = today.strftime('%Y/%m/%d-%H:%M:%S')

    event_list.append(event)

    with open(EVENTSOURCE_FILE, "w") as f:
        json.dump(event_list, f, indent=4)


def get_event_list() -> List[Any]:
    if not os.path.exists(EVENTSOURCE_FILE): 
        with open(EVENTSOURCE_FILE, "w") as f:
            json.dump([], f)

    with open(EVENTSOURCE_FILE, "r") as f:
        eventsource = json.load(f)

    return eventsource


def add_exp_event(
    exp_gained: int,
    attending_players: List[str],
    questlog_players: List[str],
    fastlog_players: List[str]
) -> None:
    # TODO: Validate that the players present actually exist

    if len(attending_players) + len(questlog_players) + len(fastlog_players) < 1:
        print("No players specified. Please specify some players")
        exit(1)

    if exp_gained < 1:
        print("No EXP granted. Please grant some EXP")
        exit(1)

    add_event({
        "type": "sessionexp",
        "exp_gained": exp_gained,
        "players": attending_players,
        "questlog_players": questlog_players,
        "fastlog_players": fastlog_players,
    })

def add_new_player_event(
    player_name: str,
    starting_exp: int
) -> None:
    # TODO: Validate that this player does not already exist
    add_event({
        "type": "newplayer",
        "name": player_name,
        "exp": starting_exp,
    })

def add_bonus_exp_event(
    player_name: str,
    bonus_exp: int
) -> None:
    # TODO: Validate that this player exists
    add_event({
        "type": "bonusexp",
        "name": player_name,
        "bonusexp": bonus_exp,
    })


def list_previous_update(n=0) -> None:
    events = get_event_list()

    if n <= 0:
        n = len(events)+n

    output_string = "Showing the result of event {n} of {total_count} events.".format(
        n=n,
        total_count=len(events))
    print(output_string)
    print("="*len(output_string))

    state = State()
    for event in events[:n-1]:
        process_event(event, state)

    print("\n".join(process_event(events[n-1], state)))


def list_current_state(filter_player: str="") -> None: # todo this is not the right function but I am co-opting it for testing
    events = get_event_list()

    state = State()

    for event in events:
        process_event(event, state)

    for player in state.players:
        if filter_player != "" and player != filter_player:
            continue


        exp = state.players[player]
        level = get_level_from_exp(exp)

        remaining_exp = remaining_exp_string(level, exp)

        print("{player} {exp}xp (Level {level}) {remaining_exp}".format(
            player=player,
            exp=exp,
            level=level,
            remaining_exp=remaining_exp
        ))



class State:
    players: Dict[str,int] = {}




def process_event(event: Any, state: State) -> List[str]:
    if event["type"] == "newplayer":
        return process_new_player_event(event, state)
    elif event["type"] == "bonusexp":
        return process_bonus_exp_event(event, state)
    elif event["type"] == "sessionexp":
        return process_session_exp_event(event, state)
    else:
        print("ERROR: Invalid Event", event)
        return []

########################### Process New Player Event ###########################
# This function processes a new player event and outputs text indicating the   #
# player that was added. Prints a warning if the player already exists as      #
# this is not a valid event. If the player already exists the exp will be      #
# overwritten by this event.                                                   #
################################################################################
def process_new_player_event(event: Any, state: State) -> List[str]:
    if event["name"] in state.players:
        print("WARNING: Duplicate New Players", event)

    state.players[event["name"]] = event["exp"]

    return [
        "Created the new player {name} starting with {exp}xp (Level {level})".format(
            name=event["name"],
            exp=event["exp"],
            level=get_level_from_exp(event["exp"])
        )
    ]


################################################################################
def process_bonus_exp_event(event: Any, state: State) -> List[str]:
    if event["name"] not in state.players:
        print("WARNING: Player not found for bonus", event)
        return []

    state.players[event["name"]] += event["bonusexp"]
    current_player_level = get_level_from_exp(state.players[event["name"]])

    return [
        "{name} {direction} {exp}xp. They are currently at Level {level}".format(
            name=event["name"],
            direction="gained" if event["bonusexp"] > 0 else "lost",
            exp=abs(event["bonusexp"]),
            level=current_player_level,
        )
    ]


# def player_leveling_text(name, old_xp, new_xp) -> List[str]:
#     old_level = get_level_from_exp(old_xp)
#     new_level = get_level_from_exp(new_xp)

#     delta_exp = new_xp - old_xp
#     next_level = new_level + 1

#     if new_level > old_level:
#         return [
#             "**{name} Leveld up to level {new_level}** "
#         ]
#     else:
#         return [
#             "**{name} gained {delta_exp}xp ({exp_till_next_level}xp until level {next_level})** Including a 700xp bonus from a fast quest log. 40714xp total, 6714/14000xp through level 8."
#         ]

# **sillvester gained 6212xp (494xp until level 6)**. 13506xp total, 7006/7500xp through level 5.
#
# **avallach gained 2897xp (5088xp until level 9)** Including a 700xp bonus from a fast quest log . 42912xp total, 8912/14000xp through level 8.
#      avallach also received 160Gp (40 * 1d10) for their quest log.
#
# **ignar gained 2197xp (3980xp until level 9)**. 44020xp total, 10020/14000xp through level 8.
#
# **mae gained 2897xp (7286xp until level 9)** Including a 700xp bonus from a fast quest log. 40714xp total, 6714/14000xp through level 8.
#     mae also received 320Gp (40 * 1d10) for their quest log.

# jimmy leveled up to level 5 (6500xp total). 0/7500xp through level 5 (7500xp remaining).

@dataclass
class LevelingUpPlayer:
    name: str
    exp: int
    level: int
    should_get_quest_log_bonus_exp: bool = False
    quest_log_bonus_exp: int = 0
    gained_exp: int = 0
    leveled_up: bool = False
    quest_log_bonus_gold: int = 0

def process_session_exp_event(event: Any, state: State) -> List[str]:
    total_exp = event["exp_gained"]

    players: List[LevelingUpPlayer] = []

    quest_log_player_gold = {}

    # Init Player State
    for player in event["players"]:
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.players[player],
                level=get_level_from_exp(state.players[player]),
            )
        )

    for player in event["questlog_players"]:
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.players[player],
                level=get_level_from_exp(state.players[player]),
                should_get_quest_log_bonus_exp=True
            )
        )

    for player in event["fastlog_players"]:
        player_level: int = get_level_from_exp(state.players[player])
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.players[player],
                level=player_level,
                should_get_quest_log_bonus_exp=True,
                quest_log_bonus_gold=bonus_gold_for_quest_log(player_level, seed=event["date"]),
            )
        )

    players = divide_exp(total_exp, players)

    bonus_exp = sum([player.gained_exp for player in players]) - total_exp

    for player in players:
        if player.should_get_quest_log_bonus_exp:

            quest_log_bonus_exp = bonus_exp_for_quest_log(player.level)

            if player.level < get_level_from_exp(math.ceil(player.exp + player.gained_exp + quest_log_bonus_exp)):
                player.leveled_up = True

            player.gained_exp += quest_log_bonus_exp
            player.quest_log_bonus_exp = quest_log_bonus_exp

    output_lines: List[str] = []

    for player in players:
        quest_log_exp_string = ""
        if player.quest_log_bonus_exp > 0:
            quest_log_exp_string = " Including a {exp}xp bonus from a fast quest log".format(
                exp=str(player.quest_log_bonus_exp)
            )
        if player.leveled_up:
            output_lines.append("{player_name} leveled up to level {new_level} ({quest_log_exp_string}{new_total_exp}xp total). {remaining_exp_string}.".format(
                player_name=player.name,
                new_level=str(player.level + 1),
                quest_log_exp_string=quest_log_exp_string,
                new_total_exp=str(player.exp + player.gained_exp),
                remaining_exp_string=remaining_exp_string(player.level + 1, player.exp + player.gained_exp)
            ))

        else:
            current_exp = player.exp + player.gained_exp
            output_lines.append("**{player_name} gained {gained_exp}xp ({remaining_exp_within_level}xp until Level {next_level})**{quest_log_exp_string}. {new_total_exp}xp total, {exp_within_level}/{total_level_exp}xp through Level {current_level}".format(
                player_name=player.name,
                gained_exp=str(player.gained_exp),
                quest_log_exp_string=quest_log_exp_string,
                new_total_exp=str(player.exp + player.gained_exp),
                current_level=player.level,
                next_level=player.level+1,
                remaining_exp_within_level=str(level_exp_caps[player.level] - (current_exp)),
                total_level_exp=str(level_exp_caps[player.level] - level_exp_caps[player.level - 1]),
                exp_within_level=str(current_exp - level_exp_caps[player.level - 1]),
            ))


        if player.quest_log_bonus_gold > 0:
            output_lines.append("     {player_name} also received {received_gold}Gp ({gold_multiplier} x 1d{gold_dice_size}) for their quest log.".format(
                player_name=player.name,
                received_gold=str(player.quest_log_bonus_gold),
                gold_multiplier=str(quest_log_gold_map[player.level - 1]["multiplier"]),
                gold_dice_size=str(quest_log_gold_map[player.level - 1]["dice_size"]),
            ))

        output_lines.append("")

    output_lines.append("Bonus Exp: {bonus_exp} ({per_player} per player)".format(
        bonus_exp=bonus_exp,
        per_player=str(bonus_exp / len(players))
    ))

    return output_lines

################################################################################
# bonus_exp_for_quest_log
#
# Calculates the 5% exp bonus for a character at a given level.
################################################################################
def bonus_exp_for_quest_log(level: int) -> int:
    delta = level_exp_caps[level] - level_exp_caps[level - 1]
    return int(math.ceil(delta * .05))


################################################################################
# bonus_gold_for_quest_log
#
# Calculates the random amount of gold a character will receive for writing
# a quest log within the time limit.
################################################################################
def bonus_gold_for_quest_log(level: int, seed:str) -> int:
    random.seed(seed)
    roll = random.randint(1, quest_log_gold_map[level - 1]["dice_size"])
    return roll * quest_log_gold_map[level - 1]["multiplier"]


################################################################################
# remaining_exp_string
#
# Returns a string containing formatted text about how much exp is remaining
# in the current level.
################################################################################
def remaining_exp_string(current_level: int, current_exp: int) -> str:
    return "{exp_within_level}/{total_level_exp}xp through level {current_level} ({remaining_exp_within_level}xp remaining)".format(
        exp_within_level=str(current_exp - level_exp_caps[current_level - 1]),
        total_level_exp=str(level_exp_caps[current_level] - level_exp_caps[current_level - 1]),
        current_level=current_level,
        remaining_exp_within_level=str(level_exp_caps[current_level] - (current_exp)),
    )


################################################################################
# divide_exp
#
# Injects the divided exp into each of the player objects. See
# adjusted_player_award() for more info on how exp is divided.
################################################################################
def divide_exp(total_exp: int, players: List[LevelingUpPlayer]) -> Any:
    if (total_exp == 0):
        for player in players:
            player.gained_exp = math.ceil(player.gained_exp)

        return players

    all_players_leveled_up = True
    for player in players:
        if not player.leveled_up:
            all_players_leveled_up = False
            break

    if all_players_leveled_up:
        return players

    max_player_level = max([player.level for player in players])

    total_player_slices = sum([adjusted_player_award(max_player_level, player.level) for player in players if not player.leveled_up])
    for player in players:
        if player.leveled_up:
            continue
        adjusted_award = adjusted_player_award(max_player_level, player.level)
        player.gained_exp += total_exp * adjusted_award / total_player_slices

    total_leftover_exp = 0

    for player in players:
        if player.level < get_level_from_exp(math.ceil(player.exp + player.gained_exp)):
            player.leveled_up = True
            leftover_exp = player.exp + player.gained_exp - level_exp_caps[player.level]
            player.gained_exp = level_exp_caps[player.level] - player.exp
            total_leftover_exp += leftover_exp

    return divide_exp(total_leftover_exp, players)


################################################################################
# get_level_from_exp
#
# Calculate what level someone would be given the amount of exp they have.
################################################################################
def get_level_from_exp(exp: int) -> int:
    for i, level_exp_cap in enumerate(level_exp_caps):
        if exp < level_exp_cap:
            return i
    return 20


################################################################################
# adjusted_player_award
#
# Calculates how many shares of the exp pool a character should get based on the
# difference between their level and the highest level of any character in the
# party. Every two levels of difference leads to a doubling of the shares of
# the pool.
################################################################################
def adjusted_player_award(max_player_level: int, player_level: int) -> float:
    return math.pow(math.sqrt(2), max_player_level - player_level)


if __name__ == "__main__":
    main()
