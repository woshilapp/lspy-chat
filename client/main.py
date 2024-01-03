#lspy-chat client test by Python 3.12.1
#
import socket,time,os,json,queue
from prompt_toolkit import prompt,print_formatted_text as printf
from prompt_toolkit.completion import Completer,Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from threading import Thread

default_chan = "" #default channel
dataqueue = queue.Queue() #procth too slow
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
sock.setblocking(True)

class MyCompleter(Completer):
    def get_completions(self, document, complete_event):
        words = ['/help','/say','/list','/listchan','/enter','/esc','/setname','/exit','/connect','/disconnect','/default'] #添加以/开头的命令
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        for word in words:
            if word.startswith(word_before_cursor):
                yield Completion(word, start_position=-len(word_before_cursor))

class mainclient(object):
    def __init__(self):
        self.recvth = Thread(target=self.recvthread,daemon=True)
        self.procth = Thread(target=self.procthread,daemon=True)

    def start(self):
        # self.recvth.start()
        self.procth.start()
        self.cli()

    def recvthread(self):
        global sock
        while True:
            try:
                data = sock.recv(512).decode("utf-8")
                if data == '':
                    printf("Disconnect from server")
                    self.recvth = Thread(target=self.recvthread,daemon=True)
                    sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
                    sock.setblocking(True)
                    break
                if data != None:
                    dataqueue.put_nowait(data)
            except socket.error:
                printf("Disconnect from server")
                self.recvth = Thread(target=self.recvthread,daemon=True)
                sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
                sock.setblocking(True)
                break

    def procthread(self):
        while True:
            msg = dataqueue.get()
            try:
                data = json.loads(msg)
                
                if data["t"] == "0":
                    pass
                
                elif data["t"] == "300":
                    printf("Successfully set name")
                
                elif data["t"] == "301":
                    printf("Already set name or name is be used")
                
                elif data["t"] == "302":
                    printf("Name is illegal")
                
                elif data["t"] == "303":
                    printf("say:Name not set")

                elif data["t"] == "304":
                    printf("Kicked out of server")

                elif data["t"] == "305":
                    printf("Banned from server")

                elif data["t"] == "306":
                    pass

                elif data["t"] == "307":
                    printf("You are not on the channel")

                elif data["t"] == "308":
                    printf("You already in this channel")

                elif data["t"] == "309":
                    printf("Channel not found")

                elif data["t"] == "310":
                    printf("Permission denied, You can't access this channel")

                elif data["t"] == "400":
                    printf("["+data["c"]+"]" + "<" + data["u"] + ">" + data["m"])

                elif data["t"] == "401":
                    printf("["+data["c"]+"]" + "[Server]" + data["m"])

                elif data["t"] == "410":
                    text = "["+data["c"]+"]"+"online:" + data["l"]
                    printf(text)

                elif data["t"] == "411":
                    text = "channels:" + data["l"]
                    printf(text)

            except json.decoder.JSONDecodeError:
                print("json",msg)
                printf("Recv Badpackets")
                continue

            except KeyError:
                print("key",msg)
                printf("Recv Badpackets")
                continue

            except TypeError:
                continue

    def cli(self):
        global sock, default_chan
        commands = MyCompleter()
        history = InMemoryHistory()
        helpitem = "{0:<25}\t{1:<25}\t{2:<25}"
        printf("Welcome to Lspy-Chat Beta")
        printf("Type \'/help\' to get help")
        printf("Made on 2024/01/03 by Win11inVMware")
        while True:
            try:
                get = prompt('>',completer=commands,history=history,complete_style=CompleteStyle.READLINE_LIKE,auto_suggest=False)
            except KeyboardInterrupt as e:
                print('^C')
                printf("bye")
                os._exit(0)

            if get == '':
                continue

            elif get[:1] == '/':
                args = get.split(" ")

                while True:
                    if "" in args:
                        args.remove("")
                    else:
                        break

                # if get[1:5] == 'eval': #debugging code
                #     eval(get[6:])
                #     coutinue

                try:
                    if args[0] == '/help':
                        printf(helpitem.format("command:","usage:","comment:"))
                        printf(helpitem.format("help","/help","Print command help"))
                        printf(helpitem.format("say","/say <chan> <text>","Send message to channel"))
                        printf(helpitem.format("setname","/setname <username>","Set your name"))
                        printf(helpitem.format("list","/list <chan>","Print online user in the channel"))
                        printf(helpitem.format("listchan","/listchan","Print channels"))
                        printf(helpitem.format("enter","/enter <chan>","Enter in a channel"))
                        printf(helpitem.format("esc","/esc <chan>","Escape the channel"))
                        printf(helpitem.format("default","/default","Set the default channel (not to use /say)"))
                        printf(helpitem.format("connect","/connect <ip>:<port>","Connect to server"))
                        printf(helpitem.format("disconnect","/disconnect","Disconnect from server"))
                        printf(helpitem.format("exit","/exit","Exit from this program"))

                    elif args[0] == '/say':
                        if connserver():
                            self.sendmsg(get[6+len(args[1]):], args[1])
                        else:
                            printf("say:Not connected to server")
                    
                    elif args[0] == '/setname':
                        if connserver():
                            text = "{\"t\":\"200\", \"n\":\"" + args[1] + "\"}"
                            self.sendata(text)
                        else:
                            printf("setname:Not connected to server")
                                
                    elif args[0] == '/list':
                        if connserver():
                            text = "{\"t\":\"202\", \"c\": \"" + args[1] + "\"}"
                            self.sendata(text)
                        else:
                            printf("list:Not connected to server")

                    elif args[0] == '/listchan':
                        if connserver():
                            text = "{\"t\":\"203\"}"
                            self.sendata(text)
                        else:
                            printf("listchan:Not connected to server")

                    elif args[0] == '/connect':
                        if connserver():
                            printf("connect:Already connect to server")
                        else:
                            ip = args[1].split(":")[0]
                            port = int(args[1].split(":")[1])
                            if len(ip.split(".")) != 4 or port < 0 or port > 65535:
                                printf("connect:Illegal ip address")
                            else:
                                try:
                                    sock.connect((ip, port))
                                    printf("connect:Connected to server")
                                    self.recvth.start()
                                except socket.error:
                                    printf("connect:Couldn't connect to server")
                    
                    elif args[0] == '/disconnect':
                        if connserver():
                            sock.close()
                        else:
                            printf("disconnect:Not connected to server")

                    elif args[0] == '/enter':
                        if connserver():
                            text = "{\"t\":\"204\", \"c\":\"" + args[1] + "\"}"
                            self.sendata(text)
                        else:
                            printf("enter:Not connected to server")

                    elif args[0] == '/esc':
                        if connserver():
                            text = "{\"t\":\"205\", \"c\":\"" + args[1] + "\"}"
                            self.sendata(text)
                        else:
                            printf("esc:Not connected to server")

                    elif args[0] == '/default':
                        default_chan = args[1]

                    elif args[0] == '/exit':
                        printf("bye")
                        os._exit(0)

                    else:
                        printf('Invalid command,type \'/help\' to get help')
                
                except IndexError:
                    printf("Parameters less than needs")

            else:
                if connserver():
                    self.sendmsg(get, default_chan)
                else:
                    printf("say:Not connected to server")

    def sendata(self,msg):
        sock.send(str(msg).encode('utf-8'))
    
    def sendmsg(self,msg,chan):
        text = "{\"t\":\"201\", \"m\":\"" + msg + "\", \"c\": \"" + chan + "\"}"
        self.sendata(text)

def connserver():
    try:
        sock.getpeername()
        return True
    except socket.error:
        return False

if __name__ == '__main__':
    mainclient().start()