#lspy-chat server test by Python 3.12.1
#0.4 fixed the procotol
import socket,json,threading,logging,time,yaml,re
from prompt_toolkit import prompt,print_formatted_text as printf
from prompt_toolkit.history import InMemoryHistory
from src import *

class myconhandler(logging.StreamHandler): #重写StreamHandler实现切换输出函数的功能
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream(msg)
            # stream(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

filehandler = logging.FileHandler(filename='./data/server.log',mode='a',encoding='utf-8')
filehandler.setFormatter(logging.Formatter("[%(levelname)s][%(asctime)s]%(message)s",datefmt="%Y-%m-%d %H:%M:%S"))
filehandler.setLevel(logging.INFO) #log filehandler
consolehandler = myconhandler(printf)
consolehandler.setFormatter(logging.Formatter("[%(levelname)s][%(asctime)s]%(message)s",datefmt="%Y-%m-%d %H:%M:%S"))
consolehandler.setLevel(logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('prompt_toolkit').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,handlers=[filehandler,consolehandler])
logger = logging.getLogger(__name__) #日志模块，输出文件为'server.log'

#do files
with open('./data/server.log', 'a') as file:
    if file.tell() != 0: #if null, don't do it
        file.write('\n')

with open("./config.yaml","r") as f: #read config
    global ip,port
    cfgtext = f.read()
    net = yaml.load(cfgtext, Loader=yaml.FullLoader)["network"]
    recd = yaml.load(cfgtext, Loader=yaml.FullLoader)["records"]
    ip = net["ip"]
    port = net["port"]
    enrd = recd["enable"]

with open("./data/ban.json", "r") as f: #ban list(ip:[], id:[])
    global ban
    ban = json.loads(f.read())

sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM) #init server socket
try:
    sock.bind((ip, port))
except OSError:
    logger.error("The port or address already use")

sock.settimeout(3)
sock.setblocking(False)
sock.listen(10)

logger.info("Listen on " + ip + ":" + str(port))

slt = 0.000001 #const of sleep
connlist = {} #connection list(sock:bool) bool is run able
online = BidirectionalDict() #online user(sock:name)
connaddr = BidirectionalDict() #socket address(sock:addr)
rm = RecordsManager(enrd) #records manager
em = EventManager() #event manager
cm = ChanManager() #channel manager
exitt = True #broadcast exit signal

def callback(type, conn):
    if type == "warnbp":
        logger.warning(connaddr[conn]+" sent a badpacket")

em.set_callback(callback)

# def vagetkey(v, d): #value, dict
#     for i in d.keys():
#         if d[i] == v:
#             return i
#      
#     return False           we needn't it because BidirectionalDict

def kick(name):
    if online[name] == False:
        return False

    online[name].send("{\"t\":\"304\"}".encode('utf-8'))
    online[name].close()

def kickip(ipaddr):
    if connaddr[ipaddr] == False:
        return False

    connaddr[ipaddr].send("{\"t\":\"304\"}".encode('utf-8'))
    connaddr[ipaddr].close()

def banid(id):
    if id in ban["id"]:
        logger.info(id + " already banned")
    else:
        if id in online.values():
            online[id].send("{\"t\":\"305\"}".encode('utf-8'))
            online[id].close()

        ban["id"].append(id)

        logger.info(id + " banned from server")

def unbanid(id):
    if id not in ban["id"]:
        logger.info(id + " not banned")
    else:
        ban["id"].remove(id)
        logger.info(id + " unbanned from server")

def banip(ip):
    if ip in ban["ip"]:
        logger.info(ip + " already banned")
    else:
        for addr in connaddr.values():
            if ip in addr:
                connaddr[addr].send("{\"t\":\"305\"}".encode('utf-8'))
                connaddr[addr].close()

        ban["ip"].append(ip)

        logger.info(ip + " banned from server")

def unbanip(ip):
    if ip not in ban["ip"]:
        logger.info(ip + " not banned")
    else:
        ban["ip"].remove(ip)
        logger.info(ip + " unbanned from server")

def server_msg(chan, text):
    ttext = "{\"t\":\"401\", \"m\":\"" + text + "\", \"c\": \"" + chan + "\"}"

    if chan == "*":
        for conn in online.keys():
            if type(conn) == str:
                continue
            else:
                conn.send(ttext.encode('utf-8'))
        logger.info("Recv from [Server]: " + text + " to chan: *")
        
    else:
        for u in cm.chand[chan]:
            online[u].send(ttext.encode('utf-8'))
        logger.info("Recv from [Server]: " + text + " to chan: " + chan)
        rm.append_text(chan, "[Server]" + text) #record

@badpacket_warn(callback)
def p0(conn, data):
    pass
    # logger.info("recv 0 from "+connaddr[conn])

@badpacket_warn(callback)
def p200(conn, data): #client login
    if data["n"] in online.values() or conn in online.keys():
        conn.send("{\"t\":\"301\"}".encode('utf-8'))
        return 0
    
    if re.match('^[a-zA-Z0-9\u4e00-\u9fa5_]{1,12}$',data["n"]):

        if data["n"] in ban["id"]: #do ban
            conn.send("{\"t\":\"305\"}".encode('utf-8'))
            return 0

        online[conn] = data["n"]
        conn.send("{\"t\":\"300\"}".encode('utf-8'))

        logger.info(connaddr[conn]+" set name: "+data["n"])
    else:
        conn.send("{\"t\":\"302\"}".encode('utf-8'))

@badpacket_warn(callback)
def p201(conn, data): #client msg
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))

    if not cm.in_chan(data["c"], online[conn]):
        conn.send("{\"t\":\"307\"}".encode('utf-8'))

    else:
        text = "{\"t\":\"400\", \"m\":\"" + data["m"] + "\", \"u\":\"" + online[conn] + "\", \"c\": \"" + data["c"] + "\"}"
        for u in cm.chand[data["c"]]:
            online[u].send(text.encode('utf-8'))
        logger.info("Recv from "+online[conn]+": "+data["m"]+" to chan: "+data["c"])
        rm.append_text(data["c"], "<"+online[conn]+">"+data["m"])

@badpacket_warn(callback)
def p202(conn, data): #client get online
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0
    
    if not cm.in_chan(data["c"], online[conn]):
        conn.send("{\"t\":\"307\"}".encode('utf-8'))
        return 0
    
    onli = ""

    for i in cm.chand[data["c"]]:
        onli = onli+","+i

    text = "{\"t\":\"410\", \"l\":\"" + onli[1:] + "\", \"c\": \"" + data["c"] + "\"}"

    conn.send(text.encode('utf-8'))

@badpacket_warn(callback)
def p203(conn, data): #client get chans
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0
    
    chans = ""

    for chan in cm.chand.keys():
        chans = chans+","+chan

    text = "{\"t\":\"411\", \"l\":\"" + chans[1:] + "\"}"

    conn.send(text.encode('utf-8'))

@badpacket_warn(callback)
def p204(conn, data): #client join chan
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0

    if not cm.have_chan(data["c"]):
        conn.send("{\"t\":\"309\"}".encode('utf-8'))
        return 0

    if online[conn] in cm.chand[data["c"]]:
        conn.send("{\"t\":\"308\"}".encode('utf-8'))
        return 0
    
    if not cm.have_perm(data["c"], online[conn]): #permission check
        conn.send("{\"t\":\"310\"}".encode('utf-8'))
        return 0

    cm.add_to_chan(data["c"], online[conn])

    conn.send("{\"t\":\"306\"}".encode('utf-8'))

    server_msg(data["c"], online[conn] + " Joined the channel")

@badpacket_warn(callback)
def p205(conn, data): #client exit chan
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0

    if not cm.have_chan(data["c"]):
        conn.send("{\"t\":\"309\"}".encode('utf-8'))
        return 0

    if online[conn] not in cm.chand[data["c"]]:
        conn.send("{\"t\":\"307\"}".encode('utf-8'))
        return 0

    cm.remove_from_chan(data["c"], online[conn])

    server_msg(data["c"], online[conn] + " Exited the channel")

@badpacket_warn(callback)
def p206(conn, data): #client get records
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0

    if not cm.have_chan(data["c"]):
        conn.send("{\"t\":\"309\"}".encode('utf-8'))
        return 0

    if online[conn] not in cm.chand[data["c"]]:
        conn.send("{\"t\":\"307\"}".encode('utf-8'))
        return 0

    text = "{\"t\": \"420\", \"c\": \"" + data["c"] + "\", \"m\": \"" + rm.get_text(data["c"])[:-2] + "\"}"

    conn.send(text.encode("utf-8"))

# init_event
em.reg_event("0", p0)
em.reg_event("200", p200)
em.reg_event("201", p201)
em.reg_event("202", p202)
em.reg_event("203", p203)
em.reg_event("204", p204)
em.reg_event("205", p205)
em.reg_event("206", p206)

def accept_thread():
    while exitt:
        try:
            time.sleep(slt)
            conn, addr = sock.accept()

            if addr[0] in ban["ip"]: #do ban
                try:
                    conn.send("{\"t\":\"305\"}".encode('utf-8'))
                    conn.close()
                except Exception:
                    pass
                
                continue

            conn.setblocking(False)
            connlist[conn] = True
            connaddr[conn] = addr[0] + ":" + str(addr[1])
            threading.Thread(target=recv_thread, args=(conn,), name="rc" + connaddr[conn]).start()
            logger.info("Connect to "+connaddr[conn])
        except BlockingIOError:
            pass
        except Exception as e:
            logger.error("Uncaught error: "+str(e))

def clear_thread():
    while exitt:
        time.sleep(2.5)
        needrm = []
        for conn in connlist.keys():
            try:
                conn.send("{\"t\":\"0\"}".encode('utf-8'))
            except socket.error:
                logger.info("Disconnect from "+connaddr[conn])
                connlist[conn] = False
                needrm.append(conn)
                connaddr.del_pair(conn)
                if conn in online.keys():
                    for chan in cm.chand.keys():
                        if online[conn] in cm.chand[chan]:
                            cm.remove_from_chan(chan, online[conn])

                            server_msg(chan, online[conn] + " Exited the channel")
                    
                    online.del_pair(conn)
                    
            except Exception as e:
                logger.error("Uncaught error: "+str(e))
        
        for conn in needrm:
            time.sleep(0.001) #wait recvth exit
            connlist.pop(conn)

def recv_thread(conn):
    try:
        while exitt and connlist[conn]:
            try:
                time.sleep(slt)
                data = conn.recv(1024).decode('utf-8')
                if data != None and data != "":
                    # logger.debug(data)
                    js = json.loads(data)
                    if "t" in js:
                        em.patch_event(js["t"], conn, js)
            except BlockingIOError:
                pass
            except socket.error:
                pass
            except UnicodeDecodeError:
                conn.close()
            except json.decoder.JSONDecodeError:
                conn.close()
            except KeyError:
                logger.warning(connaddr[conn]+" sent a badpacket")
        # connlist.pop(conn) #it will make danger
    except Exception as e:
        # pass
        logger.debug(str(type(e))+" "+str(e))

def cli():
    global exitt,ban

    history = InMemoryHistory()

    while exitt:
        input_text = prompt(">", history=history)
        args = input_text.split(' ')
        while True: #remove null args
            if '' in args:
                args.remove('')
            else:
                break
        
        if len(args) == 0:
            continue
        
        try:
            if args[0] == "exit":
                f = open("./data/ban.json", "w")
                f.write(json.dumps(ban, indent=4, ensure_ascii=False))
                f.flush()   # wtf
                f.close()
                cm.__del__()
                exitt = False

            if args[0] == "saya":
                intext = input_text[5:]
                intext.replace("\\", "\\\\")

                server_msg("*", intext)

            elif args[0] == "say":
                intext = input_text[5+len(args[1]):]
                intext.replace("\\", "\\\\")
                
                server_msg(args[1], intext)

            elif args[0] == "kick":
                kick(args[1])

            elif args[0] == "kickip":
                kickip(args[1])

            elif args[0] == "ban":
                banid(args[1])

            elif args[0] == "unban":
                unbanid(args[1])

            elif args[0] == "banip":
                banip(args[1])

            elif args[0] == "unbanip":
                unbanip(args[1])

            elif args[0] == "list":
                printf(str(cm.chand[args[1]]))

            elif args[0] == "listchan":
                printf(str(list(cm.chand.keys())))

            elif args[0] == "chanper": #chanper %chan% [b/w]
                cm.set_chan_perm(args[1], args[2])

            elif args[0] == "userper": #userper %user% [add/del] %chan%
                if args[2] == "add":
                    cm.add_perm(args[3], args[1])
                
                if args[2] == "del":
                    cm.remove_perm(args[3], args[1])

            elif args[0] == "rdclean": #rdclean %channel%
                rm.clean_text(args[1])

            elif args[0] == "eval":
                eval(args[1])
        
        except Exception:
            pass

threading.Thread(target=accept_thread, name="accp_th").start()
threading.Thread(target=clear_thread, name="clar_th").start()
logger.info("Server Started")
cli() #will it longer? (shitcode)