import threading

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