import socket,time,threading,os,json,sys
from prompt_toolkit import prompt,print_formatted_text as printf
from prompt_toolkit.history import InMemoryHistory

sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

def recv():
    while True:
        try:
            data = sock.recv(2048).decode('utf-8')
            if data:
                printf("recv from server:", data)
        except Exception as e:
            printf(e)
            break

def cli():
    history = InMemoryHistory()

    while True:
        text = prompt(":", history=history)

        if not text:
            continue

        textlist = text.split(' ')

        if textlist[0] == "send":
            textlist.pop(0)
            jsondict = {}
            for js in textlist:
                jss = js.split(":")
                jsondict[jss[0]] = jss[1]
            sock.send(json.dumps(jsondict).encode('utf-8'))

        elif textlist[0] == "test":
            textlist.pop(0)
            jsondict = {}
            for js in textlist:
                jss = js.split(":")
                jsondict[jss[0]] = jss[1]
            printf(json.dumps(jsondict))

        elif textlist[0] == "exit":
            os._exit(0)

        else:
            continue

def main():
    if len(sys.argv) != 2:
        printf("input ip")
        os._exit(0)

    sock.connect((sys.argv[1].split(":")[0], int(sys.argv[1].split(":")[1])))

    recvth = threading.Thread(target=recv, daemon=True)
    recvth.start()

    cli()

if __name__ == "__main__":
    main()