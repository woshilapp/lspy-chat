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
online = {} #online user(sock:name)
connaddr = {} #socket address(sock:addr)
em = EventManager() #event manager
exitt = True #broadcast exit signal

def callback(type, conn):
    if type == "warnbp":
        logger.warning(connaddr[conn]+" sent a badpacket")

em.set_callback(callback)

def vagetkey(v, d): #value, dict
    for i in d.keys():
        if d[i] == v:
            return i
    
    return False

def kick(name):
    if vagetkey(name, online) == False:
        return False

    vagetkey(name, online).send("{\"t\":\"304\"}".encode('utf-8'))
    vagetkey(name, online).close()

def kickip(ipaddr):
    if vagetkey(ipaddr, connaddr) == False:
        return False

    vagetkey(ipaddr, connaddr).send("{\"t\":\"304\"}".encode('utf-8'))
    vagetkey(ipaddr, connaddr).close()

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
        text = "{\"t\":\"401\", \"m\":\"" + data["n"] + " Joined the server\"}"
        for c in online.keys():
            c.send(text.encode('utf-8'))
        logger.info(connaddr[conn]+" set name: "+data["n"])
    else:
        conn.send("{\"t\":\"302\"}".encode('utf-8'))

def p201(conn, data): #client msg
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
    else:
        text = "{\"t\":\"400\", \"m\":\"" + data["m"] + "\", \"u\":\"" + online[conn] + "\"}"
        for c in online.keys():
            c.send(text.encode('utf-8'))
        logger.info("Recv from "+online[conn]+": "+data["m"])

def p202(conn, data): #client get online
    if conn not in online.keys():
        conn.send("{\"t\":\"303\"}".encode('utf-8'))
        return 0
    
    onli = ""

    for i in online.values():
        onli = onli+","+i

    text = "{\"t\":\"410\", \"l\":\"" + onli[1:] + "\"}"

    conn.send(text.encode('utf-8'))

# init_event
em.reg_event("0", p0)
em.reg_event("200", p200)
em.reg_event("201", p201)
em.reg_event("202", p202)

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
                connaddr.pop(conn)
                if conn in online.keys():
                    text = "{\"t\":\"401\", \"m\":\"" + online[conn] + " Exited the server\"}"
                    online.pop(conn)
                    for c in online.keys():
                        c.send(text.encode('utf-8'))
                    
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
                        vagetkey(args[1], online).send("{\"t\":\"305\"}".encode('utf-8'))
                        vagetkey(args[1], online).close()

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
                            vagetkey(addr, connaddr).send("{\"t\":\"305\"}".encode('utf-8'))
                            vagetkey(addr, connaddr).close()

                    ban["ip"].append(args[1])

                    logger.info(args[1] + " banned from server")

            elif args[0] == "unbanip":
                if args[1] not in ban["ip"]:
                    logger.info(args[1] + " not banned")
                else:
                    ban["ip"].remove(args[1])
                    logger.info(args[1] + " unbanned from server")

            elif args[0] == "list":
                printf(str(list(online.values())))

            # elif args[0] == "eval":
            #     eval(args[1])
        
        except IndexError:
            pass

threading.Thread(target=accept_thread, name="accp_th").start()
threading.Thread(target=clear_thread, name="clar_th").start()
logger.info("Server Started")
cli()