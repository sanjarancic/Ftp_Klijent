# stringvars - array of tk.StringVar()
# disable/enable button if StringVar is empty
def make_check_empty(button,stringvars):
    def check_empty(*args):
        state = 'normal'

        for var in stringvars:
            if var.get() == '':
                state = 'disabled'

        button.config(state=state)
    return check_empty


# https://stackoverflow.com/a/7392391
def is_binary(bytes):
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))