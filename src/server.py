
import socket
import select
import json
import os
import time


# Define a class handling the database
class DataBase:
    def __init__(self):
        self.database_path = os.path.join(os.path.dirname(__file__), "..", "db")
        # Consider another approach if the conversation history is too large
        self.history_path = os.path.join(self.database_path, "history.json")
        self.users_path = os.path.join(self.database_path, "users.json")
    
    def get_conversation(self, users_list):
        with open(self.history_path, "r") as f:
            history = json.load(f)
        
        for conversation in history["conversations"]:
            if set(users_list) == set(conversation["users"]):
                return conversation
        return None
    
    def add_message(self, from_user, user_list, message, timestamp):
        with open(self.history_path, "r") as f:
            history = json.load(f)
        
        for conversation in history["conversations"]:
            if set(user_list) == set(conversation["users"]):
                conversation["messages"].append({
                    "user": from_user,
                    "text": message,
                    "timestamp": timestamp
                })
                with open(self.history_path, "w") as f:
                    json.dump(history, f)
                return True
        return False
    
    def get_user_list(self):
        with open(self.users_path, "r") as f:
            users = json.load(f)
        
        usernames = []
        for user in users["users"]:
            usernames.append(user["username"])
        return usernames
    
    def get_password(self, username):
        with open(self.users_path, "r") as f:
            users = json.load(f)
        
        for user in users["users"]:
            if user["username"] == username:
                return user["password"]
        return None



# Define a class handling the server
class Server:
    def __init__(self, host, port):
        self.database = DataBase()
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        print("Server started on %s:%s" % (self.host, self.port))
        # Listen for incoming connections, with a maximum of 5 connections
        self.server.listen(5)
        self.server.setblocking(False)
        self.clients = {}       # {socket: address}
        self.active_users = {}  # {username: socket}

    
    def send(self, sock, data):
        data = str(data)
        size_prefix = f"{len(data.encode()):<10}"
        sock.sendall(f"${size_prefix}{data}$".encode())

    def receive(self, sock):
        try:
            first_byte = sock.recv(1)
            if first_byte != b"$":
                return None
            size_prefix = sock.recv(10)
            size = int(size_prefix.decode())
            data = sock.recv(size)
            last_byte = sock.recv(1)
            if last_byte != b"$":
                return None
            data = data.decode()
            print('Received:', data, 'from', self.clients[sock])
            return eval(data)
        except Exception as e:
            print('Exception:', e, 'at Server.receive()')
            return None
        

    def run(self):
        while True:
            # Get the list sockets which are ready to be read through select
            read_sockets, write_sockets, error_sockets = select.select([self.server] + list(self.clients.keys()), [], [])
            for sock in read_sockets:
                # New connection
                if sock == self.server:
                    sockfd, addr = self.server.accept()
                    sockfd.setblocking(False)
                    self.clients[sockfd] = addr
                    print("Client (%s, %s) connected" % addr)

                # Some incoming message from a client
                else:
                    try:
                        data = self.receive(sock)
                        if data:
                            # Call the request handler
                            result = self.request_handler(sock, data)
                            print("Result:", result)
                    except:
                        pass


    def request_handler(self, sock, data):
        print("Received:", data)
        purpose = data["purpose"]
        result = {
            "purpose": purpose,
            "result": False
        }

        # Process the request
        if purpose == "login":
            if self.login(sock, data["username"], data["password"]):
                result["result"] = True
                self.send(sock, result)
                self.send_active_users()
            else:
                self.send(sock, result)
        elif purpose == "send_message":
            if self.send_message(data["from_user"], data["to_user"], data["message"]):
                result["result"] = True
                self.send(sock, result)
            else:
                self.send(sock, result)
        elif purpose == "start_reload_message_list":
            self.reload_message_list(sock, data["target_user"])

        elif purpose == "exit":
            if self.exit_chat(sock):
                result["result"] = True
                self.send(sock, result)
                sock.close()
                self.send_active_users()
            else:
                self.send(sock, result)
        else:
            pass

        return result


    def login(self, sock, username, password):
        if self.database.get_password(username) == password:
            if username not in self.active_users.keys():
                self.active_users[username] = sock
                return True
            
        return False
    
    def send_message(self, from_user, to_user, message):
        data = {
            "purpose": "receive_message",
            "from_user": from_user,
            "message": message
        }
        print("Sending:", data)
        if to_user in self.active_users.keys():
            try:
                # Send the message to the target user
                self.send(self.active_users[to_user], data)
                print("Sent:", data)
            except Exception as e:
                print('Exception:', e, 'at Server.send_message()')
                return False
        # Save the message to the history
        timestamp = time.time()
        return self.database.add_message(from_user, [from_user, to_user], message, timestamp)
    
    
    def reload_message_list(self, sock, target_user):
        result_format = {
            "purpose": "reload_message_list",
            "message_list": []
        }
        # Get username from the socket
        username = None
        for user, user_sock in self.active_users.items():
            if user_sock == sock:
                username = user
                break
        if username:
            try:
                # Get the conversation history
                conversation = self.database.get_conversation([username, target_user])
                # Max messages to send at a time, prevent the packet from being too large
                max_messages = 10
                is_start = True
                for index in range(0, len(conversation["messages"]), max_messages):
                    result = result_format.copy()
                    if is_start:
                        result["purpose"] = "start_reload_message_list"
                        is_start = False
                    else:
                        result["purpose"] = "continue_reload_message_list"
                    
                    result["message_list"] = conversation["messages"][index:index+max_messages]
                    print("Sending:", result)
                    self.send(sock, result)
                    # time.sleep(0.1)

            except Exception as e:
                print('Exception:', e, 'at Server.reload_message_list()')
                result = result_format.copy()
                result["purpose"] = "start_reload_message_list"
                result["message_list"] = []
                self.send(sock, result)
    

    def send_active_users(self):
        data = {
            "purpose": "reload_user_list",
            # "active_users": list(self.active_users.keys())
            "users": []
        }

        user_status_format = {
            "username": "",
            "status": ""
        }
        for user in self.database.get_user_list():
            user_status = user_status_format.copy()
            user_status["username"] = user
            if user in self.active_users.keys():
                user_status["status"] = "online"
            else:
                user_status["status"] = "offline"
            data["users"].append(user_status)
        
        for user in self.active_users.keys():
            self.send(self.active_users[user], data)
        return True
        # for user in self.active_users.keys():
        #     # self.active_users[user].sendall(str(data).encode())
        #     self.send(self.active_users[user], data)
        # return True
    

    def exit_chat(self, sock):
        del self.clients[sock]
        # Update active_users
        for user, user_sock in self.active_users.items():
            if user_sock == sock:
                del self.active_users[user]
                break

        return True
    

if __name__ == '__main__':
    server = Server('localhost', 8080)
    server.run()


