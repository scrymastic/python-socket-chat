
import tkinter as tk


class LoginGui:
    def __init__(self, main_app, chat_client):
        self.main_app = main_app
        self.chat_client = chat_client
        self.root = None

    def start(self):
        self.root = tk.Tk()

        self.root.title("Login")
        self.root.geometry("250x100")

        # Frame for username label and entry
        self.root.username_frame = tk.Frame(self.root)
        self.root.username_frame.pack(fill=tk.BOTH, expand=True)

        # Create a label for the username
        self.root.username_label = tk.Label(self.root.username_frame, text="Username:")
        self.root.username_label.pack(side=tk.LEFT)

        # Create an entry for the username
        self.root.username_entry = tk.Entry(self.root.username_frame, width=30)
        self.root.username_entry.pack(side=tk.RIGHT)

        # Frame for password label and entry
        self.root.password_frame = tk.Frame(self.root)
        self.root.password_frame.pack(fill=tk.BOTH, expand=True)

        # Create a label for the password
        self.root.password_label = tk.Label(self.root.password_frame, text="Password:")
        self.root.password_label.pack(side=tk.LEFT)

        # Create an entry for the password
        self.root.password_entry = tk.Entry(self.root.password_frame, width=30)
        self.root.password_entry.bind("<Return>", self.login)
        self.root.password_entry.pack(side=tk.RIGHT)

        # Bind the focus method to the username entry
        self.root.username_entry.bind("<Return>", self.set_focus_to_password)

        # Create a button for logging in
        self.root.login_button = tk.Button(self.root, width=10, text="Login", command=self.login)
        self.root.login_button.pack()

        self.root.mainloop()

    def finish(self):
        self.root.destroy()

    def login(self, event=None):
        username = self.root.username_entry.get()
        password = self.root.password_entry.get()
        if self.chat_client.login(username, password):
            self.main_app.start(self, username)
        else:
            print("Invalid username or password")

    def set_focus_to_password(self, event=None):
        self.root.password_entry.focus()


class MainApp:
    def __init__(self, chat_client):
        self.chat_client = chat_client
        self.root = None
        self.user_list = []
        self.message_list = []
        self.username = None

    def start(self, login_gui, username):
        login_gui.finish()

        self.username = username

        self.root = tk.Tk()

        self.root.after(100, self.chat_client.check_for_data, self)
        self.root.protocol("WM_DELETE_WINDOW", self.finish)

        self.root.title("Chat App")
        self.root.geometry("500x300")

        # Frame for user list and current user
        self.root.frame_users = tk.Frame(self.root)
        self.root.frame_users.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame for the current user
        self.root.frame_current_user = tk.Frame(self.root.frame_users)
        self.root.frame_current_user.pack(side=tk.BOTTOM, fill=tk.X)

        # Create a frame for the user list
        self.root.frame_user_list = tk.Frame(self.root.frame_users)
        self.root.frame_user_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create a listbox for displaying user names
        self.root.user_list = tk.Listbox(self.root.frame_user_list, height=0, width=20)
        self.root.user_list.bind("<<ListboxSelect>>", self.start_reload_message_list)
        self.root.user_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a label for the current user in the new frame
        self.root.current_user_label = tk.Label(self.root.frame_current_user, text="Logged in as: " + username)
        self.root.current_user_label.pack(side=tk.LEFT)

        # Frame for messages and input
        self.root.frame_messages = tk.Frame(self.root)
        self.root.frame_messages.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Frame for input field and send button
        self.root.input_frame = tk.Frame(self.root.frame_messages)
        self.root.input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Create a frame for the message list and scrollbar
        self.root.messages_frame = tk.Frame(self.root.frame_messages)
        self.root.scrollbar = tk.Scrollbar(self.root.messages_frame)
        # self.root.message_list = tk.Listbox(self.root.messages_frame, height=0, width=50, yscrollcommand=self.root.scrollbar.set)
        self.root.message_list = tk.Text(self.root.messages_frame, height=0, width=50, yscrollcommand=self.root.scrollbar.set)
        self.root.message_list.config(state=tk.DISABLED)
        self.root.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.root.message_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.root.messages_frame.pack(fill=tk.BOTH, expand=True)

        # Create an entry field for typing messages
        self.root.message_entry = tk.Entry(self.root.input_frame, width=40)
        self.root.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.root.message_entry.bind("<Return>", self.send_message)

        # Create a send button
        self.root.send_button = tk.Button(self.root.input_frame, text="Send", command=self.send_message)
        self.root.send_button.pack(side=tk.RIGHT)

        self.root.mainloop()

    def finish(self):
        error_code = self.chat_client.exit_chat()
        self.root.destroy()

    # Add a message to the message list
    def add_message(self, from_user, message):     
        if from_user == self.to_username(self.root.user_list.selection_get()):
            self.root.message_list.config(state=tk.NORMAL)
            self.root.message_list.insert(tk.END, from_user + ": " + message + "\n")
            self.root.message_list.config(state=tk.DISABLED)
            # See the last message
            self.root.message_list.yview(tk.END)
            # Empty the message entry
            self.root.message_entry.delete(0, tk.END)

        elif from_user == self.username:
            self.root.message_list.config(state=tk.NORMAL)
            self.root.message_list.insert(tk.END, "You: " + message + "\n")
            self.root.message_list.config(state=tk.DISABLED)
            # See the last message
            self.root.message_list.yview(tk.END)
            # Empty the message entry
            self.root.message_entry.delete(0, tk.END)

        else:
            print("Message from", from_user, "currently not displayed")


    # Start the process of reloading the message list
    def start_reload_message_list(self, event=None):
        target = self.to_username(self.root.user_list.selection_get())

        if not target or target == self.username or target not in self.user_list:
            return
        
        print("Starting reload for", target)
        message_list = self.chat_client.start_reload_message_list(target)
        print("Message list:", message_list)
        # self.root.message_list.delete(0, tk.END)
        self.root.message_list.config(state=tk.NORMAL)
        self.root.message_list.delete("1.0", tk.END)
        self.root.message_list.config(state=tk.DISABLED)
        for message in message_list:
            sender = message["user"]
            text = message["text"]
            timestamp = message["timestamp"]
            
            # self.root.message_list.insert(tk.END, sender + ": " + text)
            self.add_message(sender, text)

    # Continue the process of reloading the message list
    def continue_reload_message_list(self, message_list):
        print("Continuing reload:", message_list)
        for message in message_list:
            sender = message["user"]
            text = message["text"]
            timestamp = message["timestamp"]
            
            self.add_message(sender, text)
    
    # Reload the user list
    def reload_user_list(self, users):
        self.root.user_list.delete(0, tk.END)
        self.user_list = []
        for user in users:
            username = user["username"]
            if username != self.username:
                self.user_list.append(username)
                status = user["status"]
                self.root.user_list.insert(tk.END, username + "/" + status)

    # Send a message to the selected user
    def send_message(self, event=None):
        message = self.root.message_entry.get()
        if not message:
            return
        selected_user = self.root.user_list.selection_get()
        target_user = self.to_username(selected_user)
        print("Sending message to", target_user, ":", message)
        if self.chat_client.send_message(self.username, target_user, message):
            self.add_message(self.username, message)
        else:
            print("Failed to send message")


    def to_username(self, display_name):
        return display_name.split("/")[0]
    


