
from frontend import MainApp, LoginGui
from backend import ChatClient


# The ChatApp class is the main class of the chat application
# It creates the ChatClient, MainApp, and LoginGui objects and runs the application
class ChatApp:
    def __init__(self):
        self.client = ChatClient('localhost', 8080)
        self.main_app = MainApp(self.client)
        self.login_gui = LoginGui(self.main_app, self.client)

    def run(self):
        self.login_gui.start()

if __name__ == '__main__':
    app = ChatApp()
    app.run()




