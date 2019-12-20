from tkinter import *

from Common import make_check_empty


class RegisterPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        self.controller = controller

        self.username = StringVar()
        self.password = StringVar()
        self.is_premium = IntVar()

        self.register_label = StringVar()
        self.register_label.set('Please enter details below')


        Label(self, textvariable=self.register_label, width="300").pack()

        Label(self, text='Username').pack()
        Entry(self, textvariable=self.username).pack()

        Label(self, text='Password').pack()
        Entry(self, textvariable=self.password, show='*').pack()

        Checkbutton(self, text="premium", variable=self.is_premium).pack()

        button_register = Button(self, text="Register", state='disabled', width="30", command=self.on_register_click)
        button_register.pack()

        self.username.trace('w', make_check_empty(button_register, [self.username, self.password]))
        self.password.trace('w', make_check_empty(button_register, [self.username, self.password]))

        Button(self, text="BACK", width="30", command=self.back_home).pack()


    def back_home(self):
        self.username.set('')
        self.password.set('')
        self.register_label.set('Please enter details below')
        self.controller.show_page('start')

    def on_register_click(self):
        self.controller.send_msg('register', True)

        self.controller.send_msg(self.username.get(), True)
        self.controller.send_msg(self.password.get(), True)
        self.controller.send_msg( 'y' if self.is_premium.get() == 1 else 'n')

        self.username.set('')
        self.password.set('')

        response = self.controller.get_msg()

        if response == 'registered':
            if self.is_premium.get() == 1:
                self.controller.show_page('premium_user_drive')
            else:
                self.controller.show_page('regular_user_drive')
        else:
            self.register_label.set(response)