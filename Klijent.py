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
    file_preview_label.set('Downlaoding...')
    Label(file_preview_screen, textvar=file_preview_label, justify = LEFT, wraplength=500).pack()


    send_msg('Choose file')
    print('Sending file name', file_name)
    sock.send(file_name.encode())

    file = recv_file()

    is_file_binary = is_binary(file)

    print('Is binary', is_file_binary)

    if (is_file_binary):
        # https://core.tcl-lang.org/tk/tktview/bffa794b1b50745e0cf81c860b0bcbf36ccfb21a
        # the above issue prevents from using Scrollbar widget
        file_preview_label.set(base64.b64encode(file))
    else:
        file_preview_label.set(file.decode())

def app(choices, handlers, files_string = None):
    global app_screen
    global file_number
    global app_label_content
    app_screen = Toplevel(main_screen)
    app_screen.title("App")
    app_screen.geometry("600x350")

    app_label_content = StringVar()
    app_label_content.set("")

    app_screen.columnconfigure(0, minsize=100)
    app_screen.columnconfigure(1, minsize=100)
    app_screen.columnconfigure(2, minsize=100)
    app_screen.columnconfigure(3, minsize=100)
    app_screen.columnconfigure(4, minsize=100)

    #TODO empty state
    Label(app_screen, text = "Files:").grid(column=1, row=0 )

    if(files_string != None):
        files = json.loads(files_string)

        def make_command(file):
            def command():
                preview(file)

            return command
        i = 1
        for f in files:
            Button(app_screen, text=f, width=15, height=1, command=make_command(f)).grid(column=1, row=i)
            i = i+1
        file_number = i
    else:
        file_number = 1

    def on_closing():
        send_msg('EXIT')
        app_screen.destroy()

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
    # TODO make selectable
    Label(app_screen, textvariable = app_label_content, wraplength=100).grid(column = 3, row=10)

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
    global file_number
    filename = filedialog.askopenfilename(initialdir="~", title="Select file")

    with open(filename, 'rb') as file:
        content = file.read()
        send_file(content)

    name = filename.split('/')[-1]
    send_msg(name)
    status = get_msg()

    if(status == 'UPLOADED'):
        def make_command(filename):
            def command():
                preview(filename)
            return command
        Button(app_screen, text=name, width=15, height=1, command = make_command(name)).grid(column = 1,row=file_number)
        file_number = file_number +1
    else:
        storage_full()

def list_shared_with_me():
    pass

def get_shareable_link():
    link = sock.recv(4096).decode()
    app_label_content.set('{}'.format(link))

def share_verification():
    username_share = username_share_entry.get()
    username_share_entry.delete(0,END)
    sock.send(username_share.encode())
    message = sock.recv(4096).decode()
    if(message == 'NOT FOUND'):
        label_share_with_user.set("User doesn\'t exist, try again")
    else:
        app_label_content.set('Successfully shared with user {}'.format(username_share))
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


def create_folder():
    pass

def rename_folder():
    pass

def move_files():
    pass

def delete_folder():
    pass

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
        files_string = get_msg()
        login_screen.destroy()
        app(choices, handlers, files_string)
    elif(message == 'n'):
        files_string = get_msg()
        login_screen.destroy()
        app(choices[:4], handlers[:4], files_string)
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

    print('waiting for server response')
    status = get_msg()
    print('Status: {}'.format(status))

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


def access_via_link():
    # get link
    link_info = link_entry.get()
    send_msg('Access via link')
    sock.send(link_info.encode())
    message = get_msg()
    print(message)
    if(message == 'NOT FOUND'):
        link_error.set('Link not valid')
    else:
        preview_files_screen = Toplevel(main_screen)
        preview_files_screen.title('Fake google drive')
        preview_files_screen.geometry("250x250")

        files_str = get_msg()
        print(files_str)
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
#TODO multiple label onclick
# TODO ispisati get shareable link