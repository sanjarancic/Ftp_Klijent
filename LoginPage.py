from tkinter import *

from Common import make_check_empty


class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        self.controller = controller

        self.login_label = StringVar()
        self.login_label.set('Please enter details below')

        self.username = StringVar()
        self.password = StringVar()

        Label(self, textvariable=self.login_label).pack()

        Label(self, text='Username').pack()
        Entry(self, textvariable=self.username).pack()

        Label(self, text='Password').pack()
        Entry(self, textvariable=self.password, show='*').pack()

        button_login = Button(self, text="Login", state='disabled', width="30", command=self.on_login_click)
        button_login.pack()

        self.username.trace('w', make_check_empty(button_login, [self.username, self.password]))
        self.password.trace('w', make_check_empty(button_login, [self.username, self.password]))

        Button(self, text="BACK", width="30", command=self.back_home).pack()

    def back_home(self):
        self.login_label.set('Please enter details below')
        self.username.set('')
        self.password.set('')
        self.controller.show_page('start')

    def on_login_click(self):
        self.controller.send_msg('login', True)
        self.controller.send_msg(self.username.get(), True)
        self.controller.send_msg(self.password.get())

        self.username.set('')
        self.password.set('')

        response = self.controller.get_msg()

        if response == 'y':
            self.controller.show_page('premium_user_drive')
        elif response == 'n':
            self.controller.show_page('regular_user_drive')
        else:
            self.login_label.set(response)
