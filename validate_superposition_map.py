from argparse import ArgumentParser
from itertools import tee
from typing import List, Tuple
import sys

FLOOR = "X"
DOOR = "D"
HIDDEN_DOOR = "H"
STAIRS_UP = "U"
STAIRS_DOWN = "L"
START = "S"
ANCHOR = "A"
EMPTY = " "


class SuperpositionFloor:
    def __init__(self, input_lines: List[str]):
        if not input_lines:
            raise ValueError(
                "SuperpositionFloor must be a non-empty list of strings")
        self.lines = [line.rstrip() for line in input_lines]
        self.anchor = None
        self.errors = []
        for row, line in enumerate(self.lines):
            for col, char in enumerate(line):
                if char in [ANCHOR, START]:
                    if self.anchor is not None:
                        self.errors.append(
                            f"Multiple anchors may not be on the same floor. Anchor at {(row, col)} ignored.")
                    self.anchor = (row, col)
        if self.anchor is None:
            self.errors.append("No anchor found on this floor!")
        anchor_mod = self.anchor[1] % 2
        self.stairs_up = set()
        self.stairs_down = set()
        for row, line in enumerate(self.lines):
            for col, char in enumerate(line):
                if char != EMPTY and col % 2 != anchor_mod:
                    self.errors.append(
                        f"At position {self.get_coord_deltas((row, col))}, a character is misaligned. Ignoring.")
                elif char == STAIRS_UP:
                    self.stairs_up.add(self.get_coord_deltas((row, col)))
                elif char == STAIRS_DOWN:
                    self.stairs_down.add(self.get_coord_deltas((row, col)))
                else:
                    # TODO: validate and add warnings for other things like doors and whatnot
                    pass

    def get_coord_deltas(self, coord: Tuple[int, int]) -> Tuple[int, int]:
        return (coord[0] - self.anchor[0], coord[1] - self.anchor[1])


class Args:
    pass


def main():
    argument_parser = ArgumentParser(
        description="Validate a text file describing a superposition map")
    argument_parser.add_argument(
        "-f", type=str, default=0, help="A valid path to the text file to validate. Defaults to read from stdin")
    args = Args()
    argument_parser.parse_args(namespace=args)

    errors = []
    floors: List[SuperpositionFloor] = []

    with open(args.f) as stream:
        floor_lines: List[str] = []
        for line in stream:
            if line.startswith("-"):
                if floor_lines:
                    floors.append(SuperpositionFloor(floor_lines))
                    errors.append(floors[-1].errors)
                    floor_lines = []
                else:
                    print("Extraneous '-' delimiter lines detected")
            else:
                floor_lines.append(line)

    if not floors:
        print("No floors processed!")
        return
    if floors[0].stairs_down:
        errors[0].append(
            f"Bottom floor had stairs down at these relative coordinates: {floors[0].stairs_down}")
    if floors[-1].stairs_up:
        errors[-1].append(
            f"Top floor had stairs up at these relative coordinates: {floors[0].stairs_up}")

    if len(floors) > 1:
        downstairs_it, upstairs_it = tee(floors)
        next(upstairs_it)
        for floor, (downstairs, upstairs) in enumerate(zip(downstairs_it, upstairs_it)):
            unmatched_stairs_up = downstairs.stairs_up - upstairs.stairs_down
            unmatched_stairs_down = upstairs.stairs_down - downstairs.stairs_up
            if unmatched_stairs_up:
                errors[floor].append(
                    f"Floor {floor} had unmatched stairs up at these relative coordinates {unmatched_stairs_up}")
            if unmatched_stairs_down:
                errors[floor+1].append(
                    f"Floor {floor+1} had unmatched stairs down at these relative coordinates {unmatched_stairs_down}")

    if any(map(lambda floor_errors: len(floor_errors) > 0, errors)):
        for floor_num, floor_errors in enumerate(errors):
            if not floor_errors:
                continue
            print(
                f"Problems detected in floor {floor_num} The following errors occurred:")
            print("\n".join(floor_errors))
            print("Also, this is the entire floor:")
            print("\n".join(floors[floor_num].lines))
    else:
        print("No problems detected :)")


if __name__ == "__main__":
    main()
