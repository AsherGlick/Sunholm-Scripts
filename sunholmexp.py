import math
import json
import random
import datetime
import argparse
import os
from typing import Any, List, Dict
from dataclasses import dataclass
from collections import defaultdict

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

MAX_LEVEL = 20

# Ideally, the most levels anyone will be behind the highest level in the faction
# If you are outside this window you will be automatically granted 1 level after each session
DESIRED_LEVEL_WINDOW = 5

# We are rewriting sunholmexp.py as an event source model

EVENTSOURCE_FILE = "exp_events.json"

# Faux player name to represent the faction's coffers
FACTION_PLAYER_NAME = "_RCC_"

class State:
    def __init__(self):
        # player -> attribute -> quantity
        # Attribute can be experience points, gold, items, or other tags
        # We need to add the faux faction player here since it never actually joins the campaign
        self.player_attrs: Dict[str, Dict[str,int]] = {FACTION_PLAYER_NAME: defaultdict(lambda: 0)}

    # Make the player level of nested dict a not-defaultdict so players must be explicitly added
    # If an unknown player is referenced in a get/set/move method, a KeyError will be raised
    def add_player(self, player: str):
        assert player not in self.player_attrs
        self.player_attrs[player] = defaultdict(lambda: 0)

    def has_player(self, player: str) -> bool:
        return player in self.player_attrs

    def get_attr(self, player: str, attr: str) -> int:
        return self.player_attrs[player][attr]

    def add_attr(self, player: str, attr: str, n: int):
        self.player_attrs[player][attr] += n

    def set_attr(self, player: str, attr: str, n: int):
        self.player_attrs[player][attr] = n

    def move_attr(self, sender: str, recver: str, attr: str, n: int):
        self.add_attr(sender, attr, -n)
        self.add_attr(recver, attr, n)

    def get_gold(self, player: str) -> int:
        return self.get_attr(player, "gold")

    def add_gold(self, player: str, gold: int):
        self.add_attr(player, "gold", gold)

    def set_gold(self, player: str, gold: int):
        self.set_attr(player, "gold", gold)

    def move_gold(self, sender: str, recver: str, gold: int):
        self.move_attr(sender, recver, "gold", gold)

    def get_exp(self, player: str) -> int:
        return self.get_attr(player, "exp")

    def add_exp(self, player: str, exp: int):
        self.add_attr(player, "exp", exp)

    def set_exp(self, player: str, exp: int):
        self.set_attr(player, "exp", exp)


def main() -> None:
    parser = argparse.ArgumentParser(description="A Tool For Managing and Leveling Sunholm Players")

    subparsers = parser.add_subparsers(help="Commands", dest="command")

    parser_session_exp = subparsers.add_parser("session", help="Grant a set of players exp and gold for a session.")
    parser_session_exp.add_argument('exp', type=str, help="The Amount of exp that was gained this session")
    parser_session_exp.add_argument('gold', type=str, default="0", help="The Amount of gold that was gained this session")
    parser_session_exp.add_argument('-p', '--player', metavar="player", type=str, action='append', default=[], help="A player who participated this session.")
    parser_session_exp.add_argument('-q', '--questlog', metavar="player", type=str, action='append', default=[], help="A player who wrote a quest log for last session and participated in this one.")
    parser_session_exp.add_argument('-f', '--fastlog', metavar="player", type=str, action='append', default=[], help="A player who wrote a quest log for last session within a time limit and participated in this one.")
    parser_session_exp.add_argument('-n', '--null', metavar="player", type=str, action='append', default=[], help="A player who was not part of the day's quest but I want to leave in my command history because I am lazy.")

    parser_new_player = subparsers.add_parser("new", help="Add a new player to the game")
    parser_new_player.add_argument('playername', type=str, help="The name of the new player.")
    parser_new_player.add_argument('--startingxp', metavar="xp", type=int, help="How much XP should the player start with", default=300)

    parser_bonus_exp = subparsers.add_parser("bonus", help="Give an out of band xp bonus to a player")
    parser_bonus_exp.add_argument('playername', type=str, help="The name of the player.")
    parser_bonus_exp.add_argument('bonusxp', type=int, help="How much xp bonus to give.")

    parser_levelup = subparsers.add_parser("levelup", help="Give an out of band level bonus to a player")
    parser_levelup.add_argument('playername', type=str, help="The name of the player.")
    parser_levelup.add_argument('levels', type=int, help="How many bonus levels to give.")
    parser_levelup.add_argument('--preserve-percentage', help="Preserve level progress as a percentage.", action='store_true')

    parser_give = subparsers.add_parser("give", help="Grant a player a number of gp, items, or attributes")
    parser_give.add_argument('recverplayer', type=str, help=f"The name of the recipient player, or '{FACTION_PLAYER_NAME}' if the gift is being placed in the faction coffers.")
    parser_give.add_argument('count', type=str, help="The amount of the thing to be given.")
    parser_give.add_argument('gift', type=str, help="The name of the thing to be given.")
    parser_give.add_argument('--from', metavar="player", type=str, help=f"The name of the sender player to take from, or '{FACTION_PLAYER_NAME}' if the gift is being taken from the faction coffers.")

    parser_player_list = subparsers.add_parser("list", help="List current exp and levels")
    parser_player_list.add_argument('playername', type=str, nargs="?", default="", help="The name of the player.")
    parser_player_list.add_argument('--sortby', type=str, choices=["exp", "name"], help="Sort list output")

    parser_last_event = subparsers.add_parser("last", help="Print out the change dialog from the most recent session")
    # TODO, maybe an ability to print out an even more early one

    parsed_args = parser.parse_args()


    # print(parsed_args)
    if parsed_args.command == "session":
        add_session_event(
            exp_gained=parsed_args.exp,
            gold_gained=parsed_args.gold,
            attending_players=parsed_args.player,
            questlog_players=parsed_args.questlog,
            fastlog_players=parsed_args.fastlog,
        )
        list_previous_update()

    elif parsed_args.command == "give":
        add_gift_event(
            recver_player=parsed_args.recverplayer,
            count=parsed_args.count,
            gift=parsed_args.gift,
            sender_player=getattr(parsed_args, "from"),
            )
        list_previous_update()

    elif parsed_args.command == "new":
        if parsed_args.playername == FACTION_PLAYER_NAME:
            print(f"Player added with illegal name {FACTION_PLAYER_NAME}, exiting")
            exit(1)
        add_new_player_event(
            player_name=parsed_args.playername,
            starting_exp=parsed_args.startingxp)
        list_previous_update()

    elif parsed_args.command == "bonus":
        add_bonus_exp_event(
            player_name=parsed_args.playername,
            bonus_exp=parsed_args.bonusxp
        )
        list_previous_update()

    elif parsed_args.command == "levelup":
        add_levelup_event(
            player_name=parsed_args.playername,
            levels=parsed_args.levels,
            preserve_percentage=parsed_args.preserve_percentage,
        )
        list_previous_update()

    elif parsed_args.command == "list":
        list_current_state(parsed_args.playername, parsed_args.sortby)

    elif parsed_args.command == "last":
        list_previous_update()

    else:
        print("Error, a command must be chosen. Use --help to see commands")


def add_event(event: Any) -> None:
    event_list = get_event_list()


    today = datetime.datetime.now()
    event["date"] = today.strftime('%Y/%m/%d-%H:%M:%S')

    event_list.append(event)

    with open(EVENTSOURCE_FILE, "w") as f:
        json.dump(event_list[::-1], f, indent=4)


def get_event_list() -> List[Any]:
    if not os.path.exists(EVENTSOURCE_FILE):
        with open(EVENTSOURCE_FILE, "w") as f:
            json.dump([], f)

    with open(EVENTSOURCE_FILE, "r") as f:
        eventsource = json.load(f)[::-1]

    return eventsource


def add_session_event(
    exp_gained: str,
    gold_gained: str,
    attending_players: List[str],
    questlog_players: List[str],
    fastlog_players: List[str]
) -> None:
    # TODO: Validate that the players present actually exist

    if len(attending_players) + len(questlog_players) + len(fastlog_players) < 1:
        print("No players specified. Please specify some players")
        exit(1)

    add_event({
        "type": "sessionexp", # ideally type is "session" but in the spirit of the event source model...
        "exp_gained": exp_gained,
        "gold_gained": gold_gained,
        "players": attending_players,
        "questlog_players": questlog_players,
        "fastlog_players": fastlog_players,
    })

def add_gift_event(
    recver_player: str,
    count: int,
    gift: str,
    sender_player: str,
) -> None:
    gift_event = {
        "type": "gift",
        "recver_player": recver_player,
        "count": count,
        "gift": gift,
    }
    if sender_player:
        gift_event["sender_player"] = sender_player
    add_event(gift_event)

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

def add_levelup_event(
    player_name: str,
    levels: int,
    preserve_percentage: bool,
) -> None:
    # TODO: Validate that this player exists
    add_event({
        "type": "levelup",
        "name": player_name,
        "levels": levels,
        "preserve_percentage": preserve_percentage,
    })


def list_previous_update(n=0) -> None:
    events = get_event_list()

    if n <= 0:
        n = len(events)+n

    output_string = f"Showing the result of event {n} of {len(events)} events."
    print(output_string)
    print("="*len(output_string))

    state = State()
    for event in events[:n-1]:
        process_event(event, state)

    print("\n".join(process_event(events[n-1], state)))


def list_current_state(filter_player: str="", sortby: str="") -> None: # todo this is not the right function but I am co-opting it for testing
    events = get_event_list()

    state = State()

    for event in events:
        process_event(event, state)

    player_iter = state.player_attrs.keys()
    if sortby == "exp":
        player_iter = sorted(player_iter, key=lambda name: state.get_exp(name))
    elif sortby == "name":
        player_iter = sorted(player_iter)
    elif sortby:
        raise ValueError(f"Output cannot be sorted by '{sortby}' ")
    for player in player_iter:
        if filter_player != "" and player != filter_player:
            continue


        exp = state.get_exp(player)
        level = get_level_from_exp(exp)

        remaining_exp = remaining_exp_string(level, exp)

        print(f"{player} {exp}xp (Level {level}) {remaining_exp}")


################################################################################
# Get a percentage of the total amount of EXP that would be required for each
# player to level up if they were at the beginning of their respective level
################################################################################
def get_party_level_percentage(state: State, players: List[str], percentage: int) -> int:
    total_level_exp = 0
    for player in players:
        exp = state.get_exp(player)
        level = get_level_from_exp(exp)

        level_exp = level_exp_caps[level] - level_exp_caps[level - 1]

        total_level_exp += level_exp

    return int(total_level_exp / 100 * percentage)


def process_event(event: Any, state: State) -> List[str]:
    if event["type"] == "newplayer":
        return process_new_player_event(event, state)
    elif event["type"] == "bonusexp":
        return process_bonus_exp_event(event, state)
    elif event["type"] == "levelup":
        return process_levelup_event(event, state)
    elif event["type"] == "gift":
        return process_gift_event(event, state)
    elif event["type"] == "sessionexp":
        return process_session_event(event, state)
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
    if state.has_player(event["name"]):
        print("WARNING: Duplicate New Players", event)

    state.add_player(event["name"])
    state.set_exp(event["name"], event["exp"])

    return [
        f"Created the new player {event['name']} starting with {event['exp']}xp (Level {get_level_from_exp(event['exp'])})"
    ]


################################################################################
def process_bonus_exp_event(event: Any, state: State) -> List[str]:
    if not state.has_player(event["name"]):
        print("WARNING: Player not found for bonus", event)
        return []

    state.add_exp(event["name"], event["bonusexp"])
    current_player_level = get_level_from_exp(state.get_exp(event["name"]))

    return [
        "{name} {direction} {exp}xp. They are currently at Level {level}".format(
            name=event["name"],
            direction="gained" if event["bonusexp"] > 0 else "lost",
            exp=abs(event["bonusexp"]),
            level=current_player_level,
        )
    ]


################################################################################
def process_levelup_event(event: Any, state: State) -> List[str]:
    name = event["name"]
    level_change = event["levels"]
    preserve_percentage = event["preserve_percentage"]

    current_exp = state.get_exp(name)
    target_level = get_level_from_exp(current_exp) + level_change

    if not state.has_player(name):
        print("WARNING: Player not found for bonus", event)
        return []

    # TODO: explicitly support level penalties.
    if level_change < 1:
        print("WARNING: Levelup levels less than 1", event)
        return []

    # TODO: should this level up as high as possible or error out?
    if (target_level >= MAX_LEVEL and preserve_percentage) or (target_level > MAX_LEVEL and not preserve_percentage):
        print("WARNING: Levelup would exceed max", event)
        return []

    gained_exp = exp_needed_for_bonus_levels(current_exp=current_exp, level_change=level_change, preserve=preserve_percentage)
    state.add_exp(name, gained_exp)

    return [
        f"{name} gained {level_change} levels (from {gained_exp}exp). They are currently at Level {get_level_from_exp(state.get_exp(name))}"
    ]


################################################################################
def process_gift_event(event: Any, state: State) -> List[str]:
    output_lines = []

    recver = event["recver_player"]
    count = int(event["count"])
    gift = event["gift"]

    state.add_attr(recver, gift, count)
    output_lines.append(
        f"Granted {count} units of {gift} to {recver}, who now has {state.get_attr(recver, gift)} units of {gift}",
    )
    if "sender_player" in event:
        sender = event["sender_player"]
        state.add_attr(sender, gift, -count)
        output_lines.append(f"    This gift came from {sender}, who now has {state.get_attr(sender, gift)} units of {gift}")

    return output_lines


@dataclass
class LevelingUpPlayer:
    name: str
    exp: int
    level: int
    should_get_quest_log_bonus_exp: bool = False
    quest_log_bonus_exp: int = 0
    gained_exp: int = 0
    leveled_up: bool = False
    gold_reward: int = 0
    quest_log_bonus_gold: int = 0

# Total amount of experience needed to make a character gain level_change levels instantly
# If preserve is set, their percentage progress from their current level carries over
def exp_needed_for_bonus_levels(current_exp: int, level_change: int = 1, preserve: bool = False) -> int:
    current_level = get_level_from_exp(current_exp)
    intended_level = current_level + level_change
    if intended_level > MAX_LEVEL:
        print(f"Cannot increase a level beyond {MAX_LEVEL}")
        exit(1)

    current_level_min, current_level_max = level_exp_caps[current_level - 1], level_exp_caps[current_level]
    intended_level_min, intended_level_max = level_exp_caps[current_level + level_change - 1], level_exp_caps[current_level + level_change]

    preserved_exp = 0
    if preserve:
        progress = (current_exp - current_level_min) / (current_level_max - current_level_min)
        preserved_exp = math.ceil(progress * (intended_level_max - intended_level_min))

    return (intended_level_min + preserved_exp) - current_exp

def process_session_event(event: Any, state: State) -> List[str]:
    # Make sure random numbers are generate the same for this event
    random.seed(event["date"])

    all_player_names = event["players"] + event["questlog_players"] + event["fastlog_players"]

    exp_gain_chunks = event["exp_gained"].split("+")

    total_exp = 0

    for exp_gain_chunk in exp_gain_chunks:
        if exp_gain_chunk.strip()[-1] == "%":
            total_exp += get_party_level_percentage(
                state,
                all_player_names,
                int(exp_gain_chunk.strip()[:-1])
            )
        else:
            total_exp += int(exp_gain_chunk)



    players: List[LevelingUpPlayer] = []

    total_gold_reward = 0
    player_gold_reward = 0
    faction_gold_reward = 0

    if "gold_gained" in event:
        # Distribute gold between players evenly with a faction tax
        total_gold_reward = sum(map(int, event["gold_gained"].split("+")))
        gold_left = total_gold_reward
        faction_gold_reward = gold_left // 5 # Hardcoded 20% faction fee for session gold rewards
        gold_left -= faction_gold_reward
        player_gold_reward = gold_left // len(all_player_names)
        gold_left -= player_gold_reward * len(all_player_names)
        faction_gold_reward += gold_left # Players should all get equal gold; remainders sent to faction

    # Init Player State
    for player in event["players"]:
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.get_exp(player),
                level=get_level_from_exp(state.get_exp(player)),
                gold_reward=player_gold_reward
            )
        )

    for player in event["questlog_players"]:
        player_level: int = get_level_from_exp(state.get_exp(player))
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.get_exp(player),
                level=get_level_from_exp(state.get_exp(player)),
                gold_reward=player_gold_reward,
                quest_log_bonus_gold=bonus_gold_for_quest_log(player_level),
            )
        )

    for player in event["fastlog_players"]:
        player_level: int = get_level_from_exp(state.get_exp(player))
        players.append(
            LevelingUpPlayer(
                name=player,
                exp=state.get_exp(player),
                level=player_level,
                gold_reward=player_gold_reward,
                quest_log_bonus_gold=bonus_gold_for_quest_log(player_level),
                should_get_quest_log_bonus_exp=True,
            )
        )

    autolevel_threshold = get_level_from_exp(max([state.get_exp(player) for player in state.player_attrs], key=get_level_from_exp)) - DESIRED_LEVEL_WINDOW
    autoleveled_players = [player for player in players if player.level < autolevel_threshold]
    non_autoleveled_players = [player for player in players if player.level >= autolevel_threshold]
    for autoleveled_player in autoleveled_players:
        autoleveled_player.gained_exp = exp_needed_for_bonus_levels(current_exp=autoleveled_player.exp)
        autoleveled_player.leveled_up = True
    non_autoleveled_players = divide_exp(total_exp, non_autoleveled_players)
    bonus_exp = sum([player.gained_exp for player in non_autoleveled_players]) - total_exp

    players = sorted(autoleveled_players + non_autoleveled_players, key=lambda player: [player.name for player in players].index(player.name))

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
            quest_log_exp_string = f" Including a {player.quest_log_bonus_exp}xp bonus from a fast quest log"
        if player.leveled_up:
            # TODO: should be updated to be visually nicer as well.
            # jimmy leveled up to level 5 (6500xp total). 0/7500xp through level 5 (7500xp remaining).
            output_lines.append("**{player_name} {maybe_auto}leveled up to level {new_level}** ({quest_log_exp_string}{new_total_exp}xp total). {remaining_exp_string}.".format(
                player_name=player.name,
                maybe_auto="auto" if player in autoleveled_players else "",
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

        if player_gold_reward + player.quest_log_bonus_gold > 0:
            output_line = f"     {player.name} also received {player_gold_reward + player.quest_log_bonus_gold}Gp total"
            if player.quest_log_bonus_gold > 0:
                output_line += f", including {player.quest_log_bonus_gold}Gp ({quest_log_gold_map[player.level - 1]['multiplier']} x 1d{quest_log_gold_map[player.level - 1]['dice_size']}) for their quest log."
            output_lines.append(output_line)

        output_lines.append("")

    output_lines.append(f"Total Exp: {total_exp}")
    output_lines.append(f"Bonus Exp: {bonus_exp} ({str(bonus_exp / len(players))} per player)")

    if total_gold_reward > 0:
        output_lines.append("")
        output_lines.append(f"Total Gold: {total_gold_reward}")
        output_lines.append(f"    The party contributed {faction_gold_reward}Gp to the faction coffers, which now contains {state.get_gold(FACTION_PLAYER_NAME) + faction_gold_reward}Gp")

    state.add_gold(FACTION_PLAYER_NAME, faction_gold_reward)
    for player in players:
        state.add_exp(player.name, player.gained_exp)
        state.add_gold(player.name, player.gold_reward + player.quest_log_bonus_gold)

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
def bonus_gold_for_quest_log(level: int) -> int:
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

    if all(player.leveled_up for player in players):
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
    return MAX_LEVEL


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
