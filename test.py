#test code,nothing to read

# def net00(data):
#     print("recv: " + data)

# print(net00("a"))

# import json

# ban = {"6":1}

# with open("./server/data/ban.json", "w") as f:
#     print(json.loads(f.read()))
#     f.write("sb")

# f = open("./server/data/ban.json", "w") 
# f.write(json.dumps(ban))

import server.src

#new proctrol

a = server.src.ChanManager()

unique_char = '\uE000'

dict1 = {}

string = "a"+unique_char+"b"+unique_char+"\sasa"+unique_char+"66"

strc = string.split(unique_char)

print(strc)

if len(strc) % 2 != 0 or len(strc) == 0:
    raise Exception("unlegit str")

for i in range(len(strc)):
    # print(type(strc[i-1]))
    if i % 2 != 0:
        dict1[strc[i-1]] = strc[i]

        # print(1)

print(dict1)
print(a.have_chan("a"))
print(a.have_perm("a", "ban1"), a.have_perm("b", "unban1"))
a.remove_perm("a", "dsb")
a.set_chan_perm("b", "w")
print(a.have_perm("b", "unban1"))