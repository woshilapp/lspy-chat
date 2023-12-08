#test code,nothing to read

# def net00(data):
#     print("recv: " + data)

# print(net00("a"))

import json

ban = {"6":1}

# with open("./server/data/ban.json", "w") as f:
#     print(json.loads(f.read()))
#     f.write("sb")

f = open("./server/data/ban.json", "w") 
f.write(json.dumps(ban))