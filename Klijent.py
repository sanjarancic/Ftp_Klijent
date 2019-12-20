from tkinter import *
from socket import *

from DrivePage import DrivePage
from StartPage import StartPage
from RegisterPage import RegisterPage
from LoginPage import LoginPage

srv_address = 'localhost'
srv_port = 2222
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((srv_address, srv_port))

page_keys = ['start', 'register','login']
pages = [StartPage, RegisterPage, LoginPage]


class FakeGoogleDrive(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        page_container = Frame(self)
        page_container.pack(side="top", fill="both", expand=True)
        page_container.grid_rowconfigure(0, weight=1)
        page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            'start': StartPage(page_container, self),
            'login': LoginPage(page_container, self),
            'register': RegisterPage(page_container, self),
            'access_via_link': DrivePage(page_container, self, False, False),
            'premium_user_drive': DrivePage(page_container, self, True, True),
            'regular_user_drive': DrivePage(page_container, self, False, True)
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky='nsew')

        self.show_page('start')

    def show_page(self, page):
        p = self.pages[page]
        p.tkraise()
        if page in ['access_via_link', 'premium_user_drive', 'regular_user_drive']:
            p.get_files()

        self.title(page)

    def send_msg(self,message, wait = False):
        print('Sending message: ', message)
        sock.send(message.encode())
        if (wait):
            sock.recv(4096).decode()

    def get_msg(self, respond=False):
        message = sock.recv(4096).decode()
        print('Message received: ', message)

        if (respond):
            sock.send('OK'.encode())

        return message

    # https://stackoverflow.com/a/52723547
    def get_file(self):
        # Get the expected length (eight bytes long, always)
        expected_size = b""
        while len(expected_size) < 8:
            more_size = sock.recv(8 - len(expected_size))
            if not more_size:
                raise Exception("Short file length received")
            expected_size += more_size

        # Convert to int, the expected file length
        expected_size = int.from_bytes(expected_size, 'big')

        # Until we've received the expected amount of data, keep receiving
        packet = b""  # Use bytes, not str, to accumulate
        while len(packet) < expected_size:
            buffer = sock.recv(expected_size - len(packet))
            if not buffer:
                raise Exception("Incomplete file received")
            packet += buffer
        return packet

    def send_file(self, bytes):
        print("Sending:", bytes)
        # Send actual length ahead of data, with fixed byteorder and size
        sock.sendall(len(bytes).to_bytes(8, 'big'))
        # You have the whole thing in memory anyway; don't bother chunking
        sock.sendall(bytes)


app = FakeGoogleDrive()
app.geometry('600x500')
app.mainloop()