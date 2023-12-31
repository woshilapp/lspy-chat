import tkinter as tk
import tkinter.messagebox as tkmsgbox
from threading import Thread
from queue import Queue
import socket, json, re, os

root = tk.Tk()
root.geometry("760x580")
root.title("Tepy-Chat GUI Client")
root.configure(bg="white")

#Frames----------------------------------------------------------------------------

# 上部分Frame
top_frame = tk.Frame(root, height=40, bg="white", relief="groove", bd=2)
top_frame.pack(fill="x", padx=3, pady=3)
top_frame.propagate(False)

# 中间部分Frame
middle_frame = tk.Frame(root, bg="white", relief="groove", bd=2)
middle_frame.pack(fill="both", expand=True, padx=3, pady=0, ipady=3)

# 下部分Frame
bottom_frame = tk.Frame(root, height=40, bg="white", relief="groove", bd=2)
bottom_frame.pack(fill="x", padx=3, pady=3)

#Frames----------------------------------------------------------------------------

#Top-Frames----------------------------------------------------------------------------

def name_validate(P):
    return re.match(r'^[\w\u4e00-\u9fa5]{0,12}$', P) is not None

def ip_validate(P):
    return re.match(r'^[0-9.:]{0,21}$', P) is not None

vcmd_name = root.register(name_validate)  # 注册验证函数
vcmd_ip = root.register(ip_validate)

# 左对齐的部分
nick_label = tk.Label(top_frame, text="昵称:", width=8, bg="white")
nick_label.pack(side="left")

nick_input = tk.Entry(top_frame, width=15, validate="key", validatecommand=(vcmd_name, '%P'))
nick_input.pack(side="left", padx=1)

setn_button = tk.Button(top_frame, text="确认", width=5)
setn_button.pack(side="left", padx=3)

# 右对齐的部分
disc_button = tk.Button(top_frame, text="断开连接", width=5)
disc_button.pack(side="right")

conn_button = tk.Button(top_frame, text="连接", width=5)
conn_button.pack(side="right", padx=1)

ip_input = tk.Entry(top_frame, width=15, validate="key", validatecommand=(vcmd_ip, '%P'))
ip_input.pack(side="right", padx=3)

ip_label = tk.Label(top_frame, text="IP:", width=8, bg="white")
ip_label.pack(side="right", padx=3)

#Top-Frames----------------------------------------------------------------------------

#Middle-Frames----------------------------------------------------------------------------

onli_textbox = tk.Text(middle_frame, width=18, state="disabled")
onli_textbox.pack(fill="y", side="right", padx=3, pady=3)

msg_textbox = tk.Text(middle_frame, state="disabled")
msg_textbox.pack(fill="both", side="left", padx=3, pady=3, expand=True)
# msg_textbox.insert(tk.END, "long text..\n"*100)

scrollbar1 = tk.Scrollbar(msg_textbox, command=msg_textbox.yview)
scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
msg_textbox.config(yscrollcommand=scrollbar1.set)

#Middle-Frames----------------------------------------------------------------------------

#Bottom-Frames----------------------------------------------------------------------------

say_input = tk.Entry(bottom_frame)
say_input.pack(fill="x", side="left", padx=5, expand=True)

send_button = tk.Button(bottom_frame, text="发送", width=5)
send_button.pack(side="right", padx=5)

#Bottom-Frames----------------------------------------------------------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dataqueue = Queue()

def on_closing():
    if tkmsgbox.askokcancel("退出", "确定要退出吗? 聊天记录不会被保存"):
        root.destroy()
        os._exit(0)

def show_warn(text):
    tkmsgbox.showwarning("警告", text)

def show_info(text):
    tkmsgbox.showinfo("信息", text)

def printf(text):
    msg_textbox.config(state="normal")
    msg_textbox.insert(tk.END, text+"\n")
    msg_textbox.yview(tk.END)
    msg_textbox.config(state="disabled")

def sendata(msg):
    sock.send(str(msg).encode('utf-8'))
    
def sendmsg(msg):
    text = "{\"t\":\"201\", \"m\":\"" + msg + "\"}"
    sendata(text)

def connserver():
    try:
        sock.getpeername()
        return True
    except socket.error:
        return False

def recvthread():
    global sock, recvth
    while True:
        try:
            data = sock.recv(1024).decode("utf-8")
            if data == '':
                printf("Disconnect from server")
                recvth = Thread(target=recvthread,daemon=True)
                sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
                sock.setblocking(True)
                break
            if data != None:
                dataqueue.put_nowait(data)
        except socket.error:
            printf("Disconnect from server")
            recvth = Thread(target=recvthread,daemon=True)
            sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
            sock.setblocking(True)
            break

def procthread():
    while True:
        msg = dataqueue.get()
        try:
            data = json.loads(msg)
            
            if data["t"] == "0":
                pass
            
            elif data["t"] == "300":
                printf("Successfully set name")
            
            elif data["t"] == "301":
                show_info("已设置名称或名称已被使用")
            
            elif data["t"] == "302":
                show_info("名称不合法")
            
            elif data["t"] == "303":
                show_info("未设置名称")

            elif data["t"] == "304":
                printf("Kicked out of server")

            elif data["t"] == "305":
                printf("Banned from server")

            elif data["t"] == "400":
                printf("<" + data["u"] + ">" + data["m"])

            elif data["t"] == "401":
                printf("[Server]" + data["m"])
                sendata("{\"t\": \"202\"}") #because new user will recv it

            elif data["t"] == "410":
                to = ""

                for t in data["l"].split(","):
                    to += t + "\n"

                text = "在线列表:\n" + to

                onli_textbox.config(state="normal")
                onli_textbox.delete(1.0, tk.END)
                onli_textbox.insert(tk.END, text)
                onli_textbox.config(state="disabled")

        except json.decoder.JSONDecodeError:
            printf("json Recv Badpackets: "+msg)
            continue

        except KeyError:
            printf("key Recv Badpackets: "+msg)
            continue

        except TypeError:
            continue

def send_enter(event):
    if root.focus_get() == say_input and say_input.get() != "":
        #TODO: send msg
        if connserver():
            sendmsg(say_input.get())
            say_input.delete(0, tk.END)
        else:
            pass

def send_butt():
    if say_input.get() != "":
        #TODO: send msg
        if connserver():
            sendmsg(say_input.get())
            say_input.delete(0, tk.END)
        else:
            show_info("未连接到服务器")

def connect():
    if ip_input.get() == "":
        show_info("IP地址不能为空")
        return

    if connserver():
        printf("Already connect to server")
    else:
        ip = ip_input.get().split(":")[0]
        port = int(ip_input.get().split(":")[1])
        if len(ip.split(".")) != 4 or port < 0 or port > 65535:
            show_warn("不合法的IP地址")
        else:
            try:
                sock.connect((ip, port))
                printf("Connected to server")
                recvth.start()
            except socket.error:
                show_info("无法连接到服务器")

def disconnect():
    if connserver():
        onli_textbox.config(state="normal")
        onli_textbox.delete(1.0, tk.END)
        onli_textbox.insert(tk.END, "在线列表:")
        onli_textbox.config(state="disabled")
        sock.close()
    else:
        show_info("未连接到服务器")

def setname():
    if nick_input.get() == "":
        show_info("名字不能为空")
        return

    if connserver():
        text = "{\"t\":\"200\", \"n\":\"" + nick_input.get() + "\"}"
        sendata(text)
    else:
        show_info("未连接到服务器")

onli_textbox.config(state="normal") #init online
onli_textbox.insert(tk.END, "在线列表:")
onli_textbox.config(state="disabled")

send_button.config(command=send_butt)
conn_button.config(command=connect)
disc_button.config(command=disconnect)
setn_button.config(command=setname)

root.bind("<Return>", send_enter)
root.bind("<KP_Enter>", send_enter)

root.protocol("WM_DELETE_WINDOW", on_closing)

recvth = Thread(target=recvthread,daemon=True)
procth = Thread(target=procthread,daemon=True)

procth.start()
root.mainloop()