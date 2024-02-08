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

#new proctrol

unique_char = '\uE000'

dict1 = {}

string = "a"+unique_char+"b"+unique_char+"\sasa"+unique_char+"66"

strc = string.split(unique_char)

# print(strc)

if len(strc) % 2 != 0 or len(strc) == 0:
    raise Exception("unlegit str")

for i in range(len(strc)):
    # print(type(strc[i-1]))
    if i % 2 != 0:
        dict1[strc[i-1]] = strc[i] #decode

        # print(1)

stre = ""

for i in range(len(dict1.keys())):
    if i == 0:
        stre += list(dict1.keys())[i] + unique_char + dict1[list(dict1.keys())[i]]
    else:
        stre += unique_char + list(dict1.keys())[i] + unique_char + dict1[list(dict1.keys())[i]]

print(dict1)
print(stre)

print("hello"[:-1])