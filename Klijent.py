import json
from socket import *
from time import sleep
from threading import *
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import base64

srv_address = 'localhost'
srv_port = 2222
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((srv_address, srv_port))



def send_file(bytes):
    print("Sending:", bytes)
    # Send actual length ahead of data, with fixed byteorder and size
    sock.sendall(len(bytes).to_bytes(8, 'big'))
    # You have the whole thing in memory anyway; don't bother chunking
    sock.sendall(bytes)

def send_msg(message):
    print('sending message: {}'.format(message))
    sock.send(message.encode())
    response = sock.recv(4096).decode()
    print('message received: {}'.format(response))
    # return response

def get_msg():
    msg = sock.recv(4096).decode()
    print('Message received: {}'.format(msg))
    sock.send('OK'.encode())
    return msg


# https://stackoverflow.com/a/52723547
def recv_file():
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

def preview(file_name, screen=None):
    if (screen is None):
        screen = app_screen
    file_preview_screen = Toplevel(screen)
    file_preview_screen.title = file_name
    file_preview_screen.geometry('500x350')

    file_preview_label = StringVar()
    Label(file_preview_screen, textvar=file_preview_label, justify = LEFT, wraplength=500).pack()

    send_msg('Choose file')
    print('Sending file name', file_name)

    sock.send(file_name.encode())

    # if it's a directory
    if (file_name[-1] == '/'):
       dir_name = file_name
       files = json.loads(sock.recv(4096).decode())

       def make_command(file):
           def command():
               preview(file)

           return command

       for f in files:
           Button(file_preview_screen, text=f, width=15, height=1, command=make_command(dir_name + f)).pack()
    else:
        file_preview_label.set('Downloading...')
        file = recv_file()

        is_file_binary = is_binary(file)

        if (is_file_binary):
            # https://core.tcl-lang.org/tk/tktview/bffa794b1b50745e0cf81c860b0bcbf36ccfb21a
            # the above issue prevents from using Scrollbar widget
            file_preview_label.set(base64.b64encode(file))
        else:
            file_preview_label.set(file.decode())

def app(choices, handlers, screen=None, current_dir='/'):
    global app_screen
    global file_number
    global var
    global current_directory
    global file_buttons
    global files

    if screen == None:
        current_directory = '/'
        screen = main_screen
        app_screen_prev = None
        file_buttons = {}
    else:
        app_screen_prev = app_screen
    # keep previous screen in memory
    print(current_directory)


    app_screen = Toplevel(screen)
    app_screen.title("App")
    app_screen.geometry("600x350")

    var = StringVar()
    var.set('')
    file_label = StringVar()
    file_label.set("")

    app_screen.columnconfigure(0, minsize=100)
    app_screen.columnconfigure(1, minsize=100)
    app_screen.columnconfigure(2, minsize=100)
    app_screen.columnconfigure(3, minsize=100)
    app_screen.columnconfigure(4, minsize=100)

    send_msg('Get Files')
    sock.send(current_dir.encode())
    files_string = get_msg()

    print(files_string)

    Label(app_screen, textvariable = file_label).grid(column=1, row=0)

    files = json.loads(files_string)
    if not files:
        file_label.set('Empty')
        file_number = 1
    else:
        file_label.set('Files:')
    def make_command(file):
        def command():
            global current_directory
            if file[-1] == '/':
                current_directory = current_dir + file
                app(choices, handlers, app_screen, current_directory)
            else:
                preview(current_dir + file)

        return command
    i = 1
    for f in files:
        n = StringVar()
        n.set(f)
        btn = Button(app_screen, textvariable=n, width=15, height=1, command=make_command(f))
        btn.grid(column=1, row=i)
        file_buttons[current_dir + f] = [btn, n]
        i = i+1
    file_number = i


    def on_closing():
        global app_screen, current_directory
        send_msg('EXIT')
        app_screen.destroy()

        if(app_screen_prev is not None):
            current_directory = '/'.join(current_directory.split('/')[:-2]) + '/'
            app_screen = app_screen_prev

    app_screen.protocol("WM_DELETE_WINDOW", on_closing)

    def make_command(choice, handler):
        def command():
            send_msg(choice)
            handler()
        return command
    i=1
    for choice, handler  in zip(choices, handlers):
        Button(app_screen, text=choice, width=15, height=1, command=make_command(choice, handler)).grid(column=3, row = i)
        i = i+1

    link_field = Entry(app_screen, state='readonly',width = '35', readonlybackground='#d9d9d9', fg='black')
    link_field.config(textvariable=var, relief='flat')
    link_field.grid(column = 2, columnspan=2, row=10)

# https://stackoverflow.com/a/7392391
def is_binary(bytes):
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))

def delete_storage_full_screen():
    storage_full_screen.destroy()

def storage_full():
    global storage_full_screen
    storage_full_screen = Toplevel(app_screen)
    storage_full_screen.title("ERROR")
    storage_full_screen.geometry("150x100")
    Label(storage_full_screen, text="Storage full!").pack()
    Button(storage_full_screen, text="OK", command=delete_storage_full_screen).pack()

def upload_file():
    # TODO handle cancel upload
    global file_number
    filename = filedialog.askopenfilename(initialdir="~", title="Select file")

    with open(filename, 'rb') as file:
        content = file.read()
        send_file(content)

    name = filename.split('/')[-1]
    sock.recv(4096)
    sock.send('{}{}'.format(current_directory, name).encode())
    print('{}{}'.format(current_directory, name))
    status = get_msg()

    if(status == 'UPLOADED'):
        def make_command(filename):
            def command():
                preview(filename)
            return command
        n = StringVar()
        n.set(name)
        btn = Button(app_screen, textvariable=n, width=15, height=1, command = make_command(name))
        btn.grid(column = 1,row=file_number)
        file_buttons[current_directory + name] = [btn,n]
        file_number = file_number +1
    else:
        storage_full()

def list_shared_with_me():
    users_who_shared_with_me = sock.recv(4096).decode()
    users = json.loads(users_who_shared_with_me)

    shared_with_me_screen = Toplevel(app_screen)
    shared_with_me_screen.title("Shared with me")
    shared_with_me_screen.geometry("400x400")

    for user in users:

        def make_select_drive(user):
            def select_drive():
                send_msg('see user\'s drive')
                sock.send(user.encode())
                preview_drive()
            return select_drive

        Button(shared_with_me_screen, text=user, command = make_select_drive(user)).pack()

    def on_closing():
        send_msg('EXIT')
        shared_with_me_screen.destroy()

    shared_with_me_screen.protocol("WM_DELETE_WINDOW", on_closing)

def get_shareable_link():
    sock.send('salji'.encode())
    link = get_msg()
    var.set('{}'.format(link))

def share_verification():
    username_share = username_share_entry.get()
    username_share_entry.delete(0,END)
    sock.send(username_share.encode())
    message = sock.recv(4096).decode()
    if(message == 'NOT FOUND'):
        label_share_with_user.set("User doesn\'t exist, try again")
    else:
        var.set('Successfully shared with user {}'.format(username_share))
        share_user_screen.destroy()


def share_with_user():
    global username_share_entry
    global label_share_with_user
    global share_user_screen
    share_user_screen = Toplevel(app_screen)
    share_user_screen.title("Share with user")
    share_user_screen.geometry("250x150")

    username_share = StringVar()
    label_share_with_user = StringVar()
    label_share_with_user.set("Enter user you want to share with")

    Label(share_user_screen, textvariable = label_share_with_user).pack()
    username_share_entry = Entry(share_user_screen, textvariable=username_share)
    username_share_entry.pack()

    button_share = Button(share_user_screen, state = 'disabled', text="OK", command=share_verification)
    button_share.pack()

    username_share.trace("w", make_check_empty(button_share, [username_share]))


def create_folder_logic():
    global file_number
    folder_name = create_folder_entry.get() + '/'
    sock.send('{}{}'.format(current_directory,folder_name).encode())
    message = sock.recv(4096).decode()
    if (message == 'Successfull'):
        var.set('Successfull')
        def make_command(filename):
            def command():
                app(choices, handlers, app_screen, current_directory + filename)
            return command
        n = StringVar()
        n.set(folder_name)
        btn = Button(app_screen, textvariable=n, width=15, height=1, command = make_command(folder_name))
        btn.grid(column=1, row=file_number)
        file_buttons[current_directory + folder_name] = []
        file_buttons[current_directory + folder_name].append(btn)
        file_buttons[current_directory + folder_name].append(n)

        file_number = file_number +1
    else:
        var.set('Folder already exists :(')
    create_folder_screen.destroy()


def create_folder():
    global create_folder_screen
    global create_folder_entry
    folder_n = StringVar()
    create_folder_screen = Toplevel(app_screen)
    create_folder_screen.title("Create folder")
    create_folder_screen.geometry("400x150")
    label_create_folder = StringVar()
    label_create_folder.set("Enter the name of the folder you want to create")
    Label(create_folder_screen, textvariable = label_create_folder).pack()
    create_folder_entry = Entry(create_folder_screen, textvariable=folder_n)
    create_folder_entry.pack()
    button_create = Button(create_folder_screen, state='disabled', text="OK", command=create_folder_logic)
    button_create.pack()
    folder_n.trace("w", make_check_empty(button_create, [folder_n]))

    def on_closing():
        send_msg('EXIT')
        create_folder_screen.destroy()

    create_folder_screen.protocol("WM_DELETE_WINDOW", on_closing)


def rename_folder_logic():
    old_name = rename_folder_entry.get() + '/'
    new_name = new_name_entry.get() + '/'
    send_msg(current_directory)
    send_msg(old_name)
    send_msg(new_name)
    message = get_msg()
    if(message == 'not found'):
        var.set('Folder doesn\'t exist in this folder')
    elif message=='found':
        var.set('Successfully renamed folder {} to {}'.format(old_name,new_name))
        print(file_buttons)
        file_buttons[current_directory + old_name][1].set(new_name)
        file_buttons[current_directory + new_name] = file_buttons[current_directory + old_name]
        del file_buttons[current_directory + old_name]
    else:
        var.set('Name is taken')
    rename_folder_screen.destroy()


def rename_folder():
    global rename_folder_screen
    global rename_folder_entry
    global new_name_entry
    folder_old = StringVar()
    folder_new = StringVar()
    rename_folder_screen = Toplevel(app_screen)
    rename_folder_screen.title("Rename Folder")
    rename_folder_screen.geometry("400x150")

    label_rename_folder = StringVar()
    label_rename_folder.set("Enter the name of the folder you want to rename")
    Label(rename_folder_screen, textvariable=label_rename_folder).pack()
    rename_folder_entry = Entry(rename_folder_screen, textvariable=folder_old)
    rename_folder_entry.pack()

    new_name_label = StringVar()
    new_name_label.set("Enter new name")
    Label(rename_folder_screen, textvariable=new_name_label).pack()
    new_name_entry = Entry(rename_folder_screen, textvariable=folder_new)
    new_name_entry.pack()

    button_rename = Button(rename_folder_screen, state='disabled', text="OK", command=rename_folder_logic)
    button_rename.pack()

    folder_old.trace("w", make_check_empty(button_rename, [folder_old]))
    folder_new.trace("w",make_check_empty(button_rename,[folder_new]))

    def on_closing():
        send_msg('EXIT')
        rename_folder_screen.destroy()

    rename_folder_screen.protocol("WM_DELETE_WINDOW", on_closing)

def move_files():
    pass

def delete_folder_logic():
    folder_name = delete_folder_entry.get() + '/'
    send_msg(current_directory)
    sock.send(folder_name.encode())

    message = get_msg()
    if message=='not found':
        var.set('Folder doesn\'t exist in this folder')
    else:
        status = get_msg()
        if status == 'deleted':
            var.set('Folder successfully deleted')
            file_buttons[current_directory + folder_name][0].destroy()
        else:
            var.set('Folder is not empty!')

    delete_folder_screen.destroy()


def delete_folder():
    global delete_folder_screen
    global delete_folder_entry
    folder_n = StringVar()
    delete_folder_screen = Toplevel(app_screen)
    delete_folder_screen.title("Delete folder")
    delete_folder_screen.geometry("400x150")
    label_delete_folder = StringVar()
    label_delete_folder.set("Enter the name of the folder you want to delete")
    Label(delete_folder_screen, textvariable=label_delete_folder).pack()
    delete_folder_entry = Entry(delete_folder_screen, textvariable=folder_n)
    delete_folder_entry.pack()
    button_delete = Button(delete_folder_screen, state='disabled', text="OK", command=delete_folder_logic)
    button_delete.pack()
    folder_n.trace("w", make_check_empty(button_delete, [folder_n]))

    def on_closing():
        send_msg('EXIT')
        delete_folder_screen.destroy()

    delete_folder_screen.protocol("WM_DELETE_WINDOW", on_closing)


handlers = [upload_file, list_shared_with_me, get_shareable_link, share_with_user,
                           create_folder, rename_folder, move_files, delete_folder]

choices = ['Upload', 'Shared with me', 'Get shareable link', 'Share with user', 'Create folder',
             'Rename folder', 'Move files', 'Delete folder']

def login_verification():
    # get username and password
    username1 = username_verify.get()
    password1 = password_verify.get()
    send_msg(username1)
    send_msg(password1)

    # delete the entry after login button is pressed
    username_login_entry.delete(0, END)
    password_login_entry.delete(0, END)

    message = get_msg()

    if(message == 'y'):
        login_screen.destroy()
        app(choices, handlers)
    elif(message == 'n'):
        login_screen.destroy()
        app(choices[:4], handlers[:4])
    else:
        login_label.set('Username or password are not valid! Please try again :)')

# define login function
def login():
    global login_screen
    login_screen = Toplevel(main_screen)
    login_screen.title("Login")
    login_screen.geometry("500x250")

    def on_closing():
        send_msg('EXIT')
        login_screen.destroy()

    login_screen.protocol("WM_DELETE_WINDOW", on_closing)
    send_msg('login')

    global username_verify
    global password_verify
    global username_login_entry
    global password_login_entry
    global login_label

    username_verify = StringVar()
    password_verify = StringVar()
    login_label = StringVar()

    login_label.set('Please enter details below')

    Label(login_screen, textvariable=login_label).pack()

    Label(login_screen, text="Username").pack()
    username_login_entry = Entry(login_screen, textvariable=username_verify)
    username_login_entry.pack()

    Label(login_screen, text="Password").pack()
    password_login_entry = Entry(login_screen, textvariable=password_verify, show='*')
    password_login_entry.pack()

    button_login = Button(login_screen, text="Login", width=10, height=1, state='disabled', command=login_verification)
    button_login.pack()

    username_verify.trace("w", make_check_empty(button_login, [username_verify, password_verify]))
    password_verify.trace("w", make_check_empty(button_login, [username_verify, password_verify]))

def register_user():
    # get username and password
    username_info = username.get()
    password_info = password.get()
    is_premium_info = is_premium.get()
    if (is_premium_info == 1):
        is_premium_info = 'y'
    else:
        is_premium_info = 'n'

    send_msg(username_info)
    send_msg(password_info)
    send_msg(is_premium_info)

    # delete the entry afer registration button is pressed
    username_entry.delete(0, END)
    password_entry.delete(0, END)

    status = get_msg()

    if(status == 'registered'):
        register_screen.destroy()
        if (is_premium_info == 'y'):
            app(choices, handlers)
        else:
            app(choices[:5], handlers[:5])
    else:
        register_label.set('Username or password are not valid! Please try again!')

def register():
    global username
    global password
    global is_premium
    global username_entry
    global password_entry
    global register_screen
    global register_label

    register_screen = Toplevel(main_screen)
    register_screen.title("Register")
    register_screen.geometry("500x250")

    def on_closing():
        send_msg('EXIT')
        register_screen.destroy()

    register_screen.protocol("WM_DELETE_WINDOW", on_closing)

    # Set variables
    username = StringVar()
    password = StringVar()
    is_premium = IntVar()
    register_label = StringVar()
    register_label.set('Please enter details below')

    send_msg('register')
    Label(register_screen, textvariable=register_label).pack()

    # Set username label
    username_label = Label(register_screen, text="Username")
    username_label.pack()

    # Set username entry
    username_entry = Entry(register_screen, textvariable=username)
    username_entry.pack()

    # Set password label
    password_label = Label(register_screen, text="Password")
    password_label.pack()

    # Set password entry
    password_entry = Entry(register_screen, textvariable=password, show='*')
    password_entry.pack()

    # Set primary checkbox
    Checkbutton(register_screen, text="premium", variable=is_premium).pack()

    # Set register button
    button_register = Button(register_screen, text="Register", state = 'disabled', width=10, height=1, command=register_user)
    button_register.pack()

    username.trace("w", make_check_empty(button_register, [username, password]))
    password.trace("w", make_check_empty(button_register, [username,password]))

def preview_drive():
    preview_files_screen = Toplevel(main_screen)
    preview_files_screen.title('Fake google drive')
    preview_files_screen.geometry("250x250")

    files_str = get_msg()
    files = json.loads(files_str)

    def make_command(file):
        def command():
            preview(file, preview_files_screen)

        return command

    for f in files:
        Button(preview_files_screen, text=f, width=15, height=1, command=make_command(f)).pack()

    def on_closing():
        send_msg('EXIT')
        preview_files_screen.destroy()

    preview_files_screen.protocol("WM_DELETE_WINDOW", on_closing)


def access_via_link():
    # get link
    link_info = link_entry.get()
    send_msg('Access via link')
    sock.send(link_info.encode())
    message = get_msg()
    if(message == 'NOT FOUND'):
        link_error.set('Link not valid')
    else:
        preview_drive()



# https://stackoverflow.com/a/16688391
def make_check_empty(button,stringvars):
    def check_empty(*args):
        state = 'normal'

        for var in stringvars:
            if var.get() == '':
                state = 'disabled'

        button.config(state=state)
    return check_empty

def main_account_screen():
    global main_screen
    global link_entry
    global  link_error

    main_screen = Tk()  # create a GUI window
    main_screen.geometry("500x250")
    main_screen.title('App')

    #set variables
    link = StringVar()
    link_error = StringVar()
    link_error.set("")
    # create a Form label
    Label(text="Welcome to fake google drive", width="300").pack()

    # create Login Button
    Button(text="Login", width="30", command=login).pack()

    # create a register button
    Button(text="Register", width="30", command=register).pack()

    # field for link
    Label(text="Access via link", width="300").pack()
    link_entry = Entry(main_screen, width="30", textvariable=link)
    link_entry.pack()
    # create Go Button
    button_go = Button(text='Go',width='15',state = 'disabled', command = access_via_link)
    button_go.pack()
    link_error_label = Label(textvariable = link_error)
    link_error_label.pack()
    link.trace('w',make_check_empty(button_go,[link]))

    main_screen.mainloop()  # start the GUI


main_account_screen()


#TODO memorry error exception
#TODO multiple label onclick ... nisam sigurna da to postoji negde i dalje...we'll see :)