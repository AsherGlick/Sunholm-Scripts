import math
import numpy as np
from typing import List
from PIL import Image

level_exp_caps =  [
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

# def xp_remaining_in_level(input_exp: int) -> int:
#   level = level_from_exp(input_exp)

#   return level_exp_caps[level] - input_exp

def level_from_exp(exp: int) -> int:
    for i, level_exp_cap in enumerate(level_exp_caps):
        if exp < level_exp_cap:
            return i
    if exp == level_exp_caps[-1]:
        return 20

    print("Error, more exp then possible", exp)
    return 20


def main():
    gift(23000, 300)
    print("====")
    gift(23000, 800)
    print("====")
    gift(300, 23000)
    print("====")
    gift(355000, 300)
    print("====")
    gift(300, 300)
    print("====")
    gift(10000, 10000)


def gift(donor_exp, receiver_exp):
    new_exp = transfer_exp_scaled_level_range(donor_exp, receiver_exp)


    print("Giving from level {} ({} exp) to level {} ({} exp)".format(level_from_exp(donor_exp), donor_exp, level_from_exp(receiver_exp), receiver_exp))

    print("They Received {} exp ({:.2f}% of the donor's exp was transferred)".format(new_exp-receiver_exp, (new_exp-receiver_exp)/donor_exp*100 ))
    print("Now they have level {} ({} exp)".format(level_from_exp(new_exp), new_exp))


# Build the scaled exp cap list
scaled_exp_caps = [0]
for i in range(19):
    original_exp_required = level_exp_caps[i+1] - level_exp_caps[i]
    scaling_value = scaling(i+1, 1)
    scaled_exp_required = math.floor(original_exp_required * scaling_value)
    scaled_exp_caps.append(scaled_exp_caps[-1] + scaled_exp_required)
scaled_exp_caps.append(scaled_exp_caps[-1])


def to_scaled_exp(exp: int) -> int:
    # scale each level chunk by chunk
    # We can probably lookup the scaled whole-level values then just scale the current level

    level = level_from_exp(exp)
    gained_exp_in_level = exp - level_exp_caps[level-1]

    scaling_value = scaling(level, 1)

    scaled_exp_in_level = scaling_value * gained_exp_in_level

    # print(level, scaling_value, gained_exp_in_level, scaled_exp_caps[level-1])

    return scaled_exp_in_level + scaled_exp_caps[level-1]



def get_level_from_scaled_exp(scaled_exp: int) -> int:
    for i, level_exp_cap in enumerate(scaled_exp_caps):
        if scaled_exp < level_exp_cap:
            return i
    if scaled_exp == scaled_exp_caps[-1]:
        return 20

    print("Error, more scaled exp then possible", scaled_exp)
    return 20

def from_scaled_exp(scaled_exp: int) -> int:

    level = get_level_from_scaled_exp(scaled_exp)

    scaling_value = scaling(level, 1)
    scaled_exp_in_level = scaled_exp - scaled_exp_caps[level-1]

    exp = int(round(scaled_exp_in_level / scaling_value))

    return level_exp_caps[level-1] + exp

# last_scaled_i = 0
# for i in range(355000):
#   scaled_i = to_scaled_exp(i)
#   if last_scaled_i > scaled_i:
#       print("Invalid Scale", i, scaled_i, last_scaled_i)
#       last_scaled_i = scaled_i
#   if i != from_scaled_exp(scaled_i):
#       print("Failure", i, from_scaled_exp(scaled_i))
#       exit(1)
# print("No error!")



def transfer_exp_scaled_level_range(source_exp: int, target_exp: int) -> int:

    if source_exp <= 0:
        return target_exp

    scaled_source = to_scaled_exp(source_exp)
    scaled_target = to_scaled_exp(target_exp)

    scaled_source = int(math.floor(scaled_source * .5))

    total_scaled_exp = scaled_source + scaled_target

    if total_scaled_exp > scaled_exp_caps[-1]:
        total_scaled_exp = scaled_exp_caps[-1]


    return from_scaled_exp(total_scaled_exp)



################################################################################
################################################################################
################################################################################
def tenth_level_segments():
    segments = []
    for i in range(19):
        for j in np.linspace(level_exp_caps[i], level_exp_caps[i+1], 11)[0:-1]:
            segments.append(int(j))
    segments.append(level_exp_caps[20])
    return segments


################################################################################
# Run a few tests to identify if there are any situations where having more exp
# as an input does not yeild more exp as an output then a previous iteration
################################################################################
def tests(array_2d):

    # Generate a grid of test case input values 
    array_2d = []
    for exp_a in tenth_level_segments():
        row = []
        for exp_b in tenth_level_segments():
            row.append(transfer_exp_scaled_level_range(exp_a, exp_b))
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
