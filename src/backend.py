
import socket
import select
import tkinter as tk

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    # Construct a message and send it to the server
    def send(self, data):
        data = str(data)
        size_prefix = f"{len(data.encode()):<10}"
        self.socket.sendall(f"${size_prefix}{data}$".encode())

    def receive(self):
        # Receive a message from the server
        try:
            first_byte = self.socket.recv(1)
            if first_byte != b"$":
                return None
            size_prefix = self.socket.recv(10)
            size = int(size_prefix.decode())
            data = self.socket.recv(size)
            last_byte = self.socket.recv(1)
            if last_byte != b"$":
                return None
            data = data.decode()
            print('Received:', data)
            return eval(data)
        except Exception as e:
            print('Exception:', e, 'at ChatClient.receive()')
            return None
    
        
    def check_for_data(self, window):
        # Check if there is data to receive
        readables, writables, exceptions = select.select([self.socket], [], [], 0)
        if not readables:
            window.root.after(100, self.check_for_data, window)
            return
        data = self.receive()
        if data:
            self.process(data=data, window=window)
        # Continue checking for data, after 100ms
        window.root.after(100, self.check_for_data, window)

    def close(self):
        self.socket.close()

    def process(self, purpose=None, data=None, window=None):
        print("Processing:", data)
        if purpose:
            # For login, send_message, start_reload_message_list, exit
            try:
                response = data
                if response["purpose"] == purpose:
                    if purpose == "login":
                        return response["result"]
                    elif purpose == "send_message":
                        return response["result"]
                    elif purpose == "start_reload_message_list":
                        return response["message_list"]
                    elif purpose == "exit":
                        return response["result"]
                    else:
                        print("Invalid purpose")
                        return False
                else:
                    print("Invalid purpose")
                    return False
            except:
                print("Invalid response")
                print(data)
                return False
            
        else:
            # For notifications
            try:
                if data["purpose"] == "receive_message":
                    window.add_message(data["from_user"], data["message"])
                    return True
                elif data["purpose"] == "reload_user_list":
                    window.reload_user_list(data["users"])
                    return True
                elif data["purpose"] == "continue_reload_message_list":
                    window.continue_reload_message_list(data["message_list"])
                    return True
            except Exception as e:
                print('Exception:', e, 'at ChatClient.process()')
                return False


    def login(self, username, password):
        data = {
            "purpose": "login",
            "username": username,
            "password": password
        }
        self.send(data)
        response = self.receive()
        return self.process(purpose="login", data=response)
        

    def send_message(self, from_user, to_user, message):
        data = {
            "purpose": "send_message",
            "from_user": from_user,
            "to_user": to_user,
            "message": message
        }
        self.send(data)
        response = self.receive()
        return self.process(purpose="send_message", data=response)
    
    def start_reload_message_list(self, user):
        data = {
            "purpose": "start_reload_message_list",
            "target_user": user
        }
        self.send(data)
        response = self.receive()
        return self.process(purpose="start_reload_message_list", data=response, window=user)
    
    def exit_chat(self):
        data = {
            "purpose": "exit"
        }
        self.send(data)
        response = self.receive()
        return self.process(purpose="exit", data=response)
