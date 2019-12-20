from tkinter import *
from tkinter import messagebox
from Common import *

class StartPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller

        self.link = StringVar()

        Label(self, text="Welcome to fake google drive", width="300").pack()
        Button(self, text="Login", width="30", command=self.show_login).pack()
        Button(self, text="Register", width="30", command=self.show_register).pack()
        Label(self,text='Enter link:', width='300').pack()
        Entry(self, width="30", textvariable=self.link).pack()
        button_go = Button(self, text='Go', width='15', state='disabled', command=self.access_via_link)
        button_go.pack()
        self.link.trace('w', make_check_empty(button_go, [self.link]))

    def show_login(self):
        self.controller.show_page('login')

    def show_register(self):
        self.controller.show_page('register')

    def access_via_link(self):
        self.controller.send_msg('access via link', True)
        self.controller.send_msg(self.link.get())

        status = self.controller.get_msg()

        if status == 'ok':
            self.controller.show_page('access_via_link')
        else:
            messagebox.showerror('Error', status)
