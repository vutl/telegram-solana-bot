my_useless_dict = {}


def add(pair):
    my_useless_dict[str(pair)] = ""


def check(pair):
    for pair1 in my_useless_dict:
        if str(pair) == pair1:
            return True
    return False