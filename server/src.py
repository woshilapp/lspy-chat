import threading,json

class EventManager: #events
    def __init__(self, callback = None): #self
        self.events = {}
        self.callback = callback

    def reg_event(self, event_type, func):
        if event_type in self.events:
            self.events[event_type].append(func)
        else:
            self.events[event_type] = [func]

    def remove_event(self, event_type, func):
        if event_type in self.events:
            if func in self.events[event_type]:
                self.events[event_type].remove(func)

    def patch_event(self, event_type, conn, *args, **kwargs):
        if event_type in self.events:
            for func in self.events[event_type]:
                # func(conn, *args, **kwargs)
                threading.Thread(target=func, args=(conn, *args), kwargs=kwargs).start()
        else:
            self.callback("warnbp", conn)
            # logger.warning(connaddr[conn]+" sent a badpacket")
            #send 0
    
    def set_callback(self, func):
        self.callback = func

class ChanManager:
    def __init__(self):
        self.chanf = open("./server/data/chan.json", "r+") #with test
        # self.chanf = open("./data/chan.json", "r")
        self.perd = json.loads(self.chanf.read())
        print(self.perd)

        self.chand = {}

        for chan in self.perd.keys():
            self.chand[chan] = []

    def have_chan(self, chan):
        if chan in self.chand.keys():
            return True
        
        return False

    def have_perm(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if len(self.perd[chan]) == 0: #closed
            return False

        if self.perd[chan][0] == "*":
            if name in self.perd[chan]: #have whitelist
                return True
            
            return False #else False

        if name in self.perd[chan]: #in blacklist
            return False

        return True #else True

    def in_chan(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if name in self.chand[chan]:
            return True #in the chan
        
        return False
    
    def add_to_chan(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if name in self.chand[chan]:
            return False #in the chan

        self.chand[chan].append(name)

    def remove_from_chan(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if name not in self.chand[chan]:
            return False #name not found

        self.chand[chan].remove(name)

    def set_chan_perm(self, chan, perm):
        if not self.have_chan(chan): #chan not found
            return False
    
        if perm == "b": #blacklist
            if len(self.perd[chan]) == 0:
                pass

            elif self.perd[chan][0] == "*":
                self.perd[chan].pop(0)

        elif perm == "w": #whitelist
            if len(self.perd[chan]) == 0:
                self.perd[chan].append("*")

            elif self.perd[chan][0] != "*":
                self.perd[chan].insert(0, "*")

    def add_perm(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if name in self.perd[chan]:
            return False #already in

        self.perd[chan].append(name)

    def remove_perm(self, chan, name):
        if not self.have_chan(chan): #chan not found
            return False
        
        if name not in self.perd[chan]:
            return False #name not found

        self.perd[chan].remove(name)

    # def add_chan

    def __del__(self):
        self.chanf.seek(0)
        self.chanf.truncate()
        self.chanf.write(json.dumps(self.perd, indent=4))
        self.chanf.close()
        # print("destcurt")