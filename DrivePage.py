import base64
import json
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog

from Common import make_check_empty, is_binary


class DrivePage(Frame):
    def __init__(self, parent, controller, is_premium, display_actions):
        Frame.__init__(self, parent)

        self.controller = controller
        self.display_actions = display_actions
        self.is_premium = is_premium

        self.current_directory = '/'
        self.is_my_drive = True

        self.file_buttons = {}
        self.action_buttons = {}

        self.columnconfigure(0, minsize=100)
        self.columnconfigure(1, minsize=100)
        self.columnconfigure(2, minsize=100)
        self.columnconfigure(3, minsize=100)
        self.columnconfigure(4, minsize=100)

        self.file_label = StringVar()
        self.shareable_link_label = StringVar()
        self.shareable_link = StringVar()
        self.back_text = StringVar()
        self.back_text.set('Logout')

        Label(self, textvariable=self.file_label).grid(column=1, row=0)
        Label(self, textvariable=self.shareable_link_label).grid(column=3, row=99)
        Entry(self, textvariable=self.shareable_link, relief='flat', width="35", state='readonly', readonlybackground='#d9d9d9', fg='black').grid(column=2, columnspan=3, row=100)

        Button(self, textvariable=self.back_text, command=self.on_go_back, width=15, height=1).grid(column=3, row=120)

        self.initialize_actions()

    def initialize_actions(self):
        if self.display_actions:
            self.action_buttons = {
                'upload': Button(self, text="Upload", command=self.upload, width=15, height=1),
                'shared_with_me': Button(self, text="Shared with me", command=self.shared_with_me, width=15, height=1),
                'get_shareable_link': Button(self, text='Get shareable link', command=self.get_shareable_link, width=15,
                                             height=1),
                'share_with_user': Button(self, text="Share with user", command=self.share_with_user, width=15,
                                          height=1)
            }
            if self.is_premium:
                self.action_buttons['create_folder'] = Button(self, text="Create folder", command=self.create_folder, width=15, height=1)
                self.action_buttons['rename_folder']=Button(self, text="Rename folder", command=self.rename_folder, width=15, height=1)
                self.action_buttons['delete_folder'] = Button(self, text="Delete folder", command=self.delete_folder, width=15, height=1)

            for i, button in enumerate(self.action_buttons.values(), start=1):
                button.grid(column=3, row=i)

    def destroy_action_buttons(self):
        for button in self.action_buttons.values():
            button.destroy()

    def upload(self):
        filename = filedialog.askopenfilename(initialdir="~", title="Select file")

        # when user exits filename will be empty tuple
        if filename:
            self.controller.send_msg('upload', True)
            self.controller.send_msg(self.current_directory, True)
            name = filename.split('/')[-1]
            self.controller.send_msg(name, True)

            with open(filename, 'rb') as file:
                content = file.read()

            self.controller.send_file(content)

            status = self.controller.get_msg()

            if status == 'uploaded':
                self.get_files()
            else:
                messagebox.showerror('Error', 'Storage full')

    def shared_with_me(self):
        self.controller.send_msg('shared with me', True)
        self.controller.send_msg('gogogo')

        users = json.loads(self.controller.get_msg())

        self.shared_with_me_popup = Toplevel(self)
        self.shared_with_me_popup.geometry('300x300')

        if len(users) == 0:
            Label(self.shared_with_me_popup, text="No one loves you :(").pack()

        for user in users:
            Button(self.shared_with_me_popup, text=user, command=lambda: self.select_shared_with_me(user), width=15, height=1).pack()

    def select_shared_with_me(self, user):
        self.shared_with_me_popup.destroy()
        self.is_my_drive = False
        self.controller.send_msg('select user', True)
        self.controller.send_msg(user, True)
        self.current_directory = '/'
        self.get_files()
        self.destroy_action_buttons()

    def get_shareable_link(self):
        self.controller.send_msg('get shareable link', True)
        self.controller.send_msg('GOGOGO')
        link = self.controller.get_msg()
        self.shareable_link_label.set('Shareable link:')
        self.shareable_link.set(link)

    def share_with_user(self):
        user_to_share = simpledialog.askstring('Input', 'User you want to share with:')

        if user_to_share:
            self.controller.send_msg('share with user', True)
            self.controller.send_msg(user_to_share)

            status = self.controller.get_msg()

            if status == 'shared':
                messagebox.showinfo('Success', 'Successfully shared with user {}'.format(user_to_share))
            else:
                messagebox.showerror('Error', status)

    def create_folder(self):
        folder_name = simpledialog.askstring('Input', 'Folder name:', parent=self)

        if folder_name:
            self.controller.send_msg('create folder', True)
            self.controller.send_msg(self.current_directory, True)
            self.controller.send_msg(folder_name)

            status = self.controller.get_msg()

            if status == 'created':
                self.get_files()
            else:
                messagebox.showerror('Error', status)

    def rename_folder(self):
        self.rename_folder_popup = Toplevel(self)
        self.rename_folder_popup.geometry('500x250')

        self.old_folder = StringVar()
        self.new_folder = StringVar()

        Label(self.rename_folder_popup, text='Enter the name of the folder you want to rename:').pack()
        Entry(self.rename_folder_popup, textvariable=self.old_folder).pack()

        Label(self.rename_folder_popup, text='Enter new name:').pack()
        Entry(self.rename_folder_popup, textvariable=self.new_folder).pack()

        btn = Button(self.rename_folder_popup, state='disabled', text='OK', command=self.rename_folder_handler)
        btn.pack()

        self.old_folder.trace('w', make_check_empty(btn, [self.old_folder, self.new_folder]))
        self.new_folder.trace('w', make_check_empty(btn, [self.old_folder, self.new_folder]))

    def rename_folder_handler(self):
        self.controller.send_msg('rename folder', True)
        self.controller.send_msg(self.current_directory, True)
        self.controller.send_msg(self.old_folder.get(), True)
        self.controller.send_msg(self.new_folder.get())

        status = self.controller.get_msg()

        self.rename_folder_popup.destroy()
        if status == 'renamed':
            self.get_files()
        else:
            messagebox.showerror('Error', status)

    def delete_folder(self):
        folder_name = simpledialog.askstring('Input', 'Enter the name of the folder to delete')

        if folder_name:
            self.controller.send_msg('delete folder', True)
            self.controller.send_msg(self.current_directory, True)
            self.controller.send_msg(folder_name)

            status = self.controller.get_msg()

            if status == 'deleted':
                self.get_files()
            else:
                messagebox.showerror('Error', status)

    def on_go_back(self):
        if self.current_directory == '/':
            if self.is_my_drive:
                # don't send logout if we're on access_via_link page
                if self.display_actions:
                    self.controller.send_msg('logout', True)
                self.controller.show_page('start')
            else:
                self.is_my_drive = True
                self.controller.send_msg('reset selected user', True)
                self.initialize_actions()
                self.get_files()
        else:
            self.current_directory = '/'.join(self.current_directory.split('/')[:-2])
            if self.current_directory == '':
                self.current_directory = '/'
                self.back_text.set('Logout')
            else:
                self.back_text.set('Back')
            self.get_files()

    def destroy_file_buttons(self):
        for btn in self.file_buttons.values():
            btn.destroy()

    def get_files(self):
        self.controller.send_msg('get files', True)

        self.controller.send_msg(self.current_directory)

        files = json.loads(self.controller.get_msg())

        if len(files) == 0:
            self.file_label.set('Empty')
        else:
            self.file_label.set('Files:')

        self.destroy_file_buttons()

        def make_command(file_name):
            def command():
                if file_name[-1] == '/':
                    self.current_directory = self.current_directory + file_name
                    self.back_text.set('Back')
                    self.get_files()
                else:
                    self.preview_file(file_name)

            return command

        for i, file_name in enumerate(files, start=1):
            btn = Button(self, text=file_name, width=15, height=1, command=make_command(file_name))
            btn.grid(column=1, row=i)

            self.file_buttons[file_name] = btn

    def preview_file(self, file_name):

        self.controller.send_msg('get file', True)
        self.controller.send_msg(self.current_directory + file_name)

        status = self.controller.get_msg()

        if status == 'OK':
            self.controller.send_msg('OK')
            self.file_preview_screen = Toplevel(self)

            self.file_preview_screen.title = file_name
            self.file_preview_screen.geometry('500x500')

            file_preview_text = Text(self.file_preview_screen)
            file_preview_text.pack()

            # in bytes
            file_content = self.controller.get_file()

            if is_binary(file_content):
                file_preview_text.insert(END, base64.b64encode(file_content))
            else:
                file_preview_text.insert(END, file_content.decode())

            Button(self.file_preview_screen, text="Download", command=lambda: self.download_file(file_content), width=15,
                   height=1).pack()
            if self.display_actions and self.is_my_drive:
                Button(self.file_preview_screen, text="Move", command=lambda: self.move_file(file_name), width=15, height=1).pack()
        else:
            messagebox.showerror('Error',status)

    def download_file(self, file_content):
        self.file_preview_screen.destroy()
        path = filedialog.asksaveasfilename(initialdir='~', title='Select where to download')
        if path:
            with open(path, 'wb') as file:
                file.write(file_content)

    def move_file(self, file_name):
        self.file_preview_screen.destroy()

        from_directory = self.current_directory
        self.move_button = Button(self, text='Move here', width=15, height=1, command=lambda: self.move_here(from_directory, file_name))
        self.move_button.grid(row=101, column=3)

    def move_here(self, from_directory, file_name):
        self.controller.send_msg('move files', True)

        self.controller.send_msg(from_directory, True)
        self.controller.send_msg(file_name, True)
        self.controller.send_msg(self.current_directory)

        status = self.controller.get_msg()

        if status == 'moved':
            self.move_button.destroy()
            self.get_files()
        else:
            messagebox.showerror('Error', status)