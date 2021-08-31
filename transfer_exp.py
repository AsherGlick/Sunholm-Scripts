import math
import numpy as np
from typing import List
from PIL import Image
import argparse

level_xp_caps =  [
    0,      # Level Start 1
    300,    # Level Start 2
    900,    # Level Start 3
    2700,   # Level Start 4
    6500,   # Level Start 5
    14000,  # Level Start 6
    23000,  # Level Start 7
    34000,  # Level Start 8
    48000,  # Level Start 9
    64000,  # Level Start 10
    85000,  # Level Start 11
    100000, # Level Start 12
    120000, # Level Start 13
    140000, # Level Start 14
    165000, # Level Start 15
    195000, # Level Start 16
    225000, # Level Start 17
    265000, # Level Start 18
    305000, # Level Start 19
    355000, # Level Start 20 
    355000, # upper bound threshold at level 20, repeated for index delta convienience
]


def scaling(source_player_level: int, target_player_level: int) -> float:
    return math.pow(math.sqrt(2), source_player_level-target_player_level)

# def xp_remaining_in_level(input_xp: int) -> int:
#   level = level_from_xp(input_xp)

#   return level_xp_caps[level] - input_xp

def level_from_xp(xp: int) -> int:
    for i, level_xp_cap in enumerate(level_xp_caps):
        if xp < level_xp_cap:
            return i
    if xp == level_xp_caps[-1]:
        return 20

    print("Error, more xp then possible", xp)
    return 20





def main():

    parser = argparse.ArgumentParser(description="Transfer Scaled XP Between Players")

    parser.add_argument('-d', '--donor', metavar="xp", type=int, action='extend', nargs="+", help="A source of XP to be given to the receiver", required=True)
    parser.add_argument('-r', '--receiver', metavar="xp", type=int, help="The XP the receiver already has", required=True)

    parsed_args = parser.parse_args()


    receiver_xp = parsed_args.receiver

    donor_xps = parsed_args.donor

    print("Receiver's XP starting at {xp} (Level {level})".format(
        xp=receiver_xp,
        level=level_from_xp(receiver_xp)
    ))

    if len(donor_xps) > 1:
        for (index, donor_xp) in enumerate(donor_xps):
            print()
            receiver_xp = gift(donor_xp, receiver_xp, index+1)
    else:
        receiver_xp = gift(donor_xps[0], receiver_xp)


def gift(donor_xp, receiver_xp, donor_index=None):
    new_xp = transfer_xp_scaled_level_range(donor_xp, receiver_xp)


    if donor_index is None:
        donor_index = ""
    else:
        donor_index = " " + str(donor_index)

    print("Donor{donorindex}'s {donorxp}XP (Level {donorlevel}) being given to receiver.".format(
        donorlevel=level_from_xp(donor_xp),
        donorxp=donor_xp,
        donorindex=donor_index,
    ))

    print("They Received {}XP ({:.2f}% of the donor's xp was transferred)".format(new_xp-receiver_xp, (new_xp-receiver_xp)/donor_xp*100 ))
    print("Now they have {}XP (Level {})".format(new_xp, level_from_xp(new_xp)))

    return new_xp

# Build the scaled xp cap list
scaled_xp_caps = [0]
for i in range(19):
    original_xp_required = level_xp_caps[i+1] - level_xp_caps[i]
    scaling_value = scaling(i+1, 1)
    scaled_xp_required = math.floor(original_xp_required * scaling_value)
    scaled_xp_caps.append(scaled_xp_caps[-1] + scaled_xp_required)
scaled_xp_caps.append(scaled_xp_caps[-1])


def to_scaled_xp(xp: int) -> int:
    # scale each level chunk by chunk
    # We can probably lookup the scaled whole-level values then just scale the current level

    level = level_from_xp(xp)
    gained_xp_in_level = xp - level_xp_caps[level-1]

    scaling_value = scaling(level, 1)

    scaled_xp_in_level = scaling_value * gained_xp_in_level

    # print(level, scaling_value, gained_xp_in_level, scaled_xp_caps[level-1])

    return scaled_xp_in_level + scaled_xp_caps[level-1]



def get_level_from_scaled_xp(scaled_xp: int) -> int:
    for i, level_xp_cap in enumerate(scaled_xp_caps):
        if scaled_xp < level_xp_cap:
            return i
    if scaled_xp == scaled_xp_caps[-1]:
        return 20

    print("Error, more scaled xp then possible", scaled_xp)
    return 20

def from_scaled_xp(scaled_xp: int) -> int:

    level = get_level_from_scaled_xp(scaled_xp)

    scaling_value = scaling(level, 1)
    scaled_xp_in_level = scaled_xp - scaled_xp_caps[level-1]

    xp = int(round(scaled_xp_in_level / scaling_value))

    return level_xp_caps[level-1] + xp

# last_scaled_i = 0
# for i in range(355000):
#   scaled_i = to_scaled_xp(i)
#   if last_scaled_i > scaled_i:
#       print("Invalid Scale", i, scaled_i, last_scaled_i)
#       last_scaled_i = scaled_i
#   if i != from_scaled_xp(scaled_i):
#       print("Failure", i, from_scaled_xp(scaled_i))
#       exit(1)
# print("No error!")



def transfer_xp_scaled_level_range(source_xp: int, target_xp: int) -> int:

    if source_xp <= 0:
        return target_xp

    scaled_source = to_scaled_xp(source_xp)
    scaled_target = to_scaled_xp(target_xp)

    scaled_source = int(math.floor(scaled_source * .5))

    total_scaled_xp = scaled_source + scaled_target

    if total_scaled_xp > scaled_xp_caps[-1]:
        total_scaled_xp = scaled_xp_caps[-1]


    return from_scaled_xp(total_scaled_xp)



################################################################################
################################################################################
################################################################################
def tenth_level_segments():
    segments = []
    for i in range(19):
        for j in np.linspace(level_xp_caps[i], level_xp_caps[i+1], 11)[0:-1]:
            segments.append(int(j))
    segments.append(level_xp_caps[20])
    return segments


################################################################################
# Run a few tests to identify if there are any situations where having more xp
# as an input does not yeild more xp as an output then a previous iteration
################################################################################
def tests(array_2d):

    # Generate a grid of test case input values 
    array_2d = []
    for xp_a in tenth_level_segments():
        row = []
        for xp_b in tenth_level_segments():
            row.append(transfer_xp_scaled_level_range(xp_a, xp_b))
        array_2d.append(row)

    print(array_2d)
    write_csv(array_2d, "testcsv.csv")
    # tests(rows)


    segments_length = len(tenth_level_segments())

    img = Image.new(
        mode="RGB",
        size=(segments_length, segments_length),
        color=(255,255,255)
    )




    error_count = 0
    for y in range(segments_length-1):
        for x in range(segments_length):
            if (array_2d[y][x] == -1 or array_2d[y+1][x] == -1):
                continue
            if (array_2d[y][x] > array_2d[y+1][x]): 
                error_count += 1
    print ("vertical errors", error_count)



    error_count = 0
    for y in range(segments_length):
        for x in range(segments_length-1):
            if array_2d[y][x] == -1:
                img.load()[x,y] = (128,128,128)
                continue
            if array_2d[y][x+1] == -1:
                img.load()[x+1,y] = (128,128,128)
                continue
            if (array_2d[y][x] > array_2d[y][x+1]):
                print("error", y, x)
                error_count += 1
                img.load()[x+1,y] = (255 - ((x+1)%2*30),0,0)
            elif (array_2d[y][x] == array_2d[y][x+1]):
                img.load()[x+1,y] = (0, 255 - ((x+1)%2*30),0)

    print ("horizontal errors", error_count)

    img.save("errors.png")


    # error_count = 0
    # for (row_i, row) in enumerate(array_2d):
    #   last_elem = None
    #   for (col_i,elem) in enumerate(row):
    #       if last_elem != None:
    #           if last_elem >= elem and last_elem != -1 and elem != -1:
    #               # print("error", row_i, col_i)
    #               error_count += 1

    #       last_elem = elem

    # print("errors:", error_count)

def write_csv(array_2d: List[List[int]], file:str):
    segments = tenth_level_segments()
    csv = "\n".join(
        [
            ",".join(
                [str(segments[row_i])+" Source"]+[
                    str(element) for element in row
                ]
            )
        for (row_i, row) in enumerate(array_2d)]
    )

    with open(file, "w") as f:
        f.write(csv)

################################################################################
################################################################################
################################################################################
if __name__ == "__main__":
    main()
