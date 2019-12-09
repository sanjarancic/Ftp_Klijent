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

def preview(file_name):
    file_preview_screen = Toplevel(app_screen)
    file_preview_screen.title = file_name
    file_preview_screen.geometry('500x350')
    file_preview_label = StringVar()
    file_preview_label.set('Downlaoding...')
    Label(file_preview_screen, textvar=file_preview_label).pack()


    send_msg('Choose file')
    print('Sending file name', file_name)
    sock.send(file_name.encode())

    file = recv_file()

    is_file_binary = is_binary(file)

    print('Is binary', is_file_binary)

    if (is_file_binary):
        file_preview_label.set(base64.b64encode(file))
    else:
        file_preview_label.set(file.decode())




def app(choices, handlers, files_string = None):
    global app_screen
    app_screen = Toplevel(main_screen)
    app_screen.title("App")
    app_screen.geometry("500x350")

    if(files_string != None):
        files = json.loads(files_string)

        def make_command(file):
            def command():
                preview(file)

            return command

        for f in files:
            Button(app_screen, text=f, width=15, height=1, command=make_command(f)).pack()

    def on_closing():
        send_msg('EXIT')
        app_screen.destroy()

    app_screen.protocol("WM_DELETE_WINDOW", on_closing)

    def make_command(choice, handler):
        def command():
            send_msg(choice)
            handler()
        return command

    for choice, handler  in zip(choices, handlers):
        Button(app_screen, text=choice, width=15, height=1, command=make_command(choice, handler)).pack()

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
    filename = filedialog.askopenfilename(initialdir="~", title="Select file")

    with open(filename, 'rb') as file:
        content = file.read()
        send_file(content)

    name = filename.split('/')[-1]
    send_msg(name)
    status = get_msg()

    if(status == 'UPLOADED'):
        Button(app_screen, text=name, width=15, height=1).pack()
    else:
        storage_full()

def list_shared_with_me():
    pass

def get_shareable_link():
    pass

def share_with_user():
    pass

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
    files_string = get_msg()

    if(message == 'y'):
        login_screen.destroy()
        app(choices, handlers, files_string)
    elif(message == 'n'):
        login_screen.destroy()
        app(choices[:5], handlers[:5], files_string)
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
    Button(login_screen, text="Login", width=10, height=1, command=login_verification).pack()

def register_user():
    # get username and password
    username_info = username.get()
    print(username_info)
    send_msg(username_info)
    password_info = password.get()
    print(password_info)
    send_msg(password_info)
    is_premium_info = is_premium.get()
    if(is_premium_info == 1):
        is_premium_info = 'y'
    else:
        is_premium_info = 'n'
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
    Button(register_screen, text="Register", width=10, height=1, command=register_user).pack()


def main_account_screen():
    global main_screen
    main_screen = Tk()  # create a GUI window
    main_screen.geometry("500x250")
    main_screen.title('App')

    #set variables
    link = StringVar()

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

    main_screen.mainloop()  # start the GUI


main_account_screen()



#
# def app_menu():
#     client_type = sock.recv(4096).decode()
#     if(client_type == 'y'):
#         choices = ['Upload','Choose file','Shared with me','Get shareable link','Share with user','Create folder', 'Rename folder','Move files','Delete folder']
#     else:
#         choices = ['Upload', 'Choose file', 'Shared with me', 'Get shareable link', 'Share with user']
#     app_menu_choice = menu(choices)
#     for i in range(len(choices)):
#         if (app_menu_choice == str(i)):
#             sock.send(choices[i].encode())
#
#
#
# def non_empty_input(input_str):
#     input_res = input(input_str)
#     if len(input_res) == 0:
#         print('Please type something :(')
#         return non_empty_input(input_str)
#
#     return input_res
#
#
# def menu(menu_options):
#     options_count = len(menu_options)
#     for i in range(len(menu_options)):
#         print('{}. {}'.format(i + 1, menu_options[i]))
#
#     print('{}. Exit'.format(options_count + 1))
#
#     choice = input()
#
#     while (int(choice) - 1 not in list(range(len(menu_options) + 1 ))):
#         print('Invalid input. Try again :)')
#         choice = input()
#
#     if (int(choice) == options_count + 1):
#         exit()
#
#     return choice
#
#
# # default manu when you run the app
# def menu1():
#     menu1_choice = menu(['Sign up', 'Sign in', 'Access via link'])
#
#     return menu1_choice
#
# def registration_handler():
#     # sending data
#     username = non_empty_input('Username: ')
#     sock.send(username.encode())
#     password = non_empty_input('Password: ')
#     sock.send(password.encode())
#     is_premium = non_empty_input('Do you want to be premium (y/n): ')
#     if (is_premium == 'y'):
#         is_premium = 'y'
#     else:
#         is_premium = 'n'
#     sock.send(is_premium.encode())
#     sign_in_result = (sock.recv(4096).decode())
#     if (sign_in_result == 'registered'):
#         print('{} successfully registered'.format(username))
#         app_menu()
#     else:
#         print('User with {} username already exists! Try again'.format(username))
#         registration_handler()
#
#
# # sign up with option to go back
# def sign_up():
#     menu2_choice = menu(['Proceed to registration', 'Go back'])
#
#     if (menu2_choice == '1'):
#         # informing service that client wants to register
#         sock.sendall('register'.encode())
#
#         registration_handler()
#
#     # go back option
#     else:
#         welcome_menu()
#
# def login_handler():
#     username = non_empty_input('Username: ')
#     sock.send(username.encode())
#     password = non_empty_input('Password: ')
#     sock.send(password.encode())
#     sign_up_result = (sock.recv(4096).decode())
#     if(sign_up_result == 'OK'):
#         print('Welcome {}'.format(username))
#         app_menu()
#     else:
#         print('Username or password are not valid! Please try again :)')
#         login_handler()
#
# # sign in menu
# def sign_in():
#     sign_in_choice = menu(['Proceed to login', 'Go back'])
#
#     if (sign_in_choice == '1'):
#
#         # informing service that client wants to login
#         sock.send('login'.encode())
#
#         login_handler()
#
#     # go back option
#     else:
#         welcome_menu()
#
# # preview with link menu
# def enter_link():
#
#     link_choice = menu(['Proceed', 'Go back'])
#
#     if (link_choice == '1'):
#
#         # informing service that client wants to see someones drive
#         sock.sendall('view drive'.encode())
#
#         link = input('Enter link: ')
#
#     # go back option
#     else:
#         welcome_menu()
#
# def welcome_menu():
#     menu1_choice = menu1()
#     if (menu1_choice == '1'):
#         sign_up()
#     if(menu1_choice == '2'):
#         sign_in()
#     if(menu1_choice == '3'):
#         enter_link()
#
#
#
# welcome_menu()
#


#TODO memorry error exception