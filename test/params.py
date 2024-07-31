import sys

sys.path.append("..")
from utils import getSQLDataUtils


# print(str(getSQLDataUtils.get_cookie("7495279362416609893")["cookie"],encoding="utf-8"))


def print_extended_alphabet_2():
    search_data = []
    for char1 in range(ord('a'), ord('z') + 1):
        search_data.append(str(chr(char1)))
        for char2 in range(ord('a'), ord('z') + 1):
            search_data.append(str(chr(char1) + chr(char2)))
            for char3 in range(ord('a'), ord('z') + 1):
                search_data.append(str(chr(char1) + chr(char2) + chr(char3)))

    print(search_data)


print_extended_alphabet_2()
