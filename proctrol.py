class proc(object):
    def __init__(self) -> None:
        pass

    def decode(in_str):
        unique_char = '\uE000'
        fin_dict = {}

        strc = in_str.split(unique_char)

        if len(strc) % 2 != 0 or len(strc) == 0:
            raise SyntaxError("Wrong string")

        for i in range(len(strc)):
            if i % 2 != 0:
                fin_dict[strc[i-1]] = strc[i] #decode

        return fin_dict

    def encode(in_dict):
        unique_char = '\uE000'
        fin_str = ""

        for i in range(len(in_dict.keys())):
            if i == 0:
                fin_str += list(in_dict.keys())[i] + unique_char + in_dict[list(in_dict.keys())[i]]
            else:
                fin_str += unique_char + list(in_dict.keys())[i] + unique_char + in_dict[list(in_dict.keys())[i]]

        return fin_str
