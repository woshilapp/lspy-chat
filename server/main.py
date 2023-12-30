#lspy-chat server test by Python 3.12.1
#
import socket,json,threading,logging,os,time,yaml,re
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
    if file.tell() != 0: #if null, dont do it
        file.write('\n')

with open("./config.yaml","r") as f: #读取配置文件
    global ip,port
    a = yaml.load(f.read(), Loader=yaml.FullLoader)["network"]
    ip = a["ip"]
    port = a["port"]

with open("./data/ban.json", "r") as f: #ban list(ip:[], id:[])
    global ban
    ban = json.loads(f.read())

sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM) #套接字的初始化
try:
    sock.bind((ip, port))
except OSError:
    logger.error("The port or address already use")

sock.settimeout(3)
sock.setblocking(False)
sock.listen(10)

logger.info("Listen on "+ip+":"+str(port))

slt = 0.000001 #const of sleep
connlist = {} #connection list(sock:bool) bool is run able
online = BidirectionalDict() #online user(sock:name)
connaddr = BidirectionalDict() #socket address(sock:addr)
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

def p0(conn, data):
    pass
    # logger.info("recv 0 from "+connaddr[conn])

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

    text = "{\"t\":\"410\", \"l\":\"" + onli[1:] + "\"}"

    conn.send(text.encode('utf-8'))

def p203(conn, data):
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0
    
    chans = ""

    for chan in cm.chand.keys():
        chans = chans+","+chan

    text = "{\"t\":\"411\", \"l\":\"" + chans[1:] + "\"}"

    conn.send(text.encode('utf-8'))

def p204(conn, data):
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

    text = "{\"t\":\"401\", \"m\":\"" + online[conn] + " Joined the channel\"}"

    for u in cm.chand[data["c"]]:
        online[u].send(text.encode('utf-8'))

    logger.info(online[conn]+" enter to chan: "+data["c"])

def p205(conn, data):
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

    text = "{\"t\":\"401\", \"m\":\"" + online[conn] + " Exited the channel\"}"

    for u in cm.chand[data["c"]]:
        online[u].send(text.encode('utf-8'))

    logger.info(online[conn]+" exit from chan: "+data["c"])

# init_event
em.reg_event("0", p0)
em.reg_event("200", p200)
em.reg_event("201", p201)
em.reg_event("202", p202)
em.reg_event("203", p203)
em.reg_event("204", p204)
em.reg_event("205", p205)

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
                            cm.remove_from_chan(online[conn])

                            text = "{\"t\":\"401\", \"m\":\"" + online[conn] + " Exited the channel\"}"

                            for u in cm.chand[chan]: #broadcast
                                online[u].send(text.encode('utf-8'))
                    
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
                data = conn.recv(10240).decode('utf-8')
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
    global exitt, ban

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
                f.write(json.dumps(ban, indent=4))
                exitt = False

            if args[0] == "say":
                text = "{\"t\":\"401\", \"m\":\"" + input_text[4:] + "\"}"
                for conn in online.keys():
                    conn.send(text.encode('utf-8'))
                logger.info("Recv from [Server]: " + input_text[4:])

            elif args[0] == "kick":
                kick(args[1])

            elif args[0] == "kickip":
                kickip(args[1])

            elif args[0] == "ban":
                if args[1] in ban["id"]:
                    logger.info(args[1] + " already banned")
                else:
                    if args[1] in online.values():
                        online[args[1]].send("{\"t\":\"305\"}".encode('utf-8'))
                        online[args[1]].close()

                    ban["id"].append(args[1])

                    logger.info(args[1] + " banned from server")

            elif args[0] == "unban":
                if args[1] not in ban["id"]:
                    logger.info(args[1] + " not banned")
                else:
                    ban["id"].remove(args[1])
                    logger.info(args[1] + " unbanned from server")

            elif args[0] == "banip":
                if args[1] in ban["ip"]:
                    logger.info(args[1] + " already banned")
                else:
                    for addr in connaddr.values():
                        if args[1] in addr:
                            connaddr[addr].send("{\"t\":\"305\"}".encode('utf-8'))
                            connaddr[addr].close()

                    ban["ip"].append(args[1])

                    logger.info(args[1] + " banned from server")

            elif args[0] == "unbanip":
                if args[1] not in ban["ip"]:
                    logger.info(args[1] + " not banned")
                else:
                    ban["ip"].remove(args[1])
                    logger.info(args[1] + " unbanned from server")

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

            # elif args[0] == "eval":
            #     eval(args[1])
        
        except IndexError:
            pass

threading.Thread(target=accept_thread, name="accp_th").start()
threading.Thread(target=clear_thread, name="clar_th").start()
logger.info("Server Started")
cli() #will it longer? (shitcode)