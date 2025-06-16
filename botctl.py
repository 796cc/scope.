import socket
import asyncio

CONTROL_PORT = 8765

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('127.0.0.1', CONTROL_PORT))
        except ConnectionRefusedError:
            print("Could not connect to the bot control server. Is the bot running?")
            return
        s.sendall(cmd.encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        print(data.decode())

def main():
    print("Bot Control Terminal (type 'exit' or 'quit' to leave)")
    print("Commands: restart, shutdown, status <msg>, list <type>, logs")
    while True:
        try:
            cmd = input("botctl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting botctl.")
            break
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd:
            send_command(cmd)

if __name__ == "__main__":
    main()