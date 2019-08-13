'''
Graphical user interface based on Tkinter standard library
'''

from tkinter import *
from tkinter import messagebox
import threading
import rewrite_core
import time
import json
from mitmproxy import ctx


def proxy_shutdown() -> None:
    '''Func stops proxy'''

    ctx.master.shutdown()


class Window:
    def __init__(self, master):
        self.window = Toplevel(master)

    def go(self):
        self.draw()
        self.new_value = None
        self.window.grab_set()
        self.window.focus_set()
        self.window.wait_window()
        return self.new_value

    def draw(self):
        pass

    def close(self):
        if self.window is not None:
            self.window.destroy()

    def open_window(self, window_class, value_for_rewrite):

        def wrapper(_window_class=window_class,
                    _value_for_rewrite=value_for_rewrite):

            self.subwindow = _window_class(self.window, _value_for_rewrite[0])
            self.return_value = self.subwindow.go()

            if self.return_value and value_for_rewrite:
                _value_for_rewrite[0] = self.return_value

            self.draw()
            del self.subwindow

        return wrapper


class GUI(threading.Thread, Window):

    def __init__(self, config_json, api_map):
        threading.Thread.__init__(self)
        self.config_json = [config_json]
        self.api_map = [api_map]
        self.start()

    def go(self):
        pass

    def quit(self):
        if self.window is not None:
            self.window.quit()  # Leave mainloop
            proxy_shutdown()

    def quit_dialog(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.window is not None:
                self.window.quit()  # Leave mainloop
                proxy_shutdown()

    def run(self):
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.quit_dialog)

        Button(self.window, text="API map").pack(side=TOP, fill=BOTH)

        Button(self.window, text="Config",
               command=self.open_window(ConfigWindow,
                                        self.config_json)).pack(side=TOP, fill=BOTH)

        self.draw()

        Exit_button = Button(self.window, text='Exit',
                             command=self.quit_dialog)
        Exit_button.pack(side=BOTTOM)

        self.window.mainloop()

        #  ctx.log.info('End of GUI life')
        #  there is a runtime error trowing in this instruction
        #  RuntimeError: There is no current event loop in thread ...

        self.window.update_idletasks()  # Updates it to force destruction

        self.window.destroy()  # Destroy root window and its childs

        #  Needs to clear manually or declare it as a local variable
        #  In other hand there is:
        #  `Tcl_AsyncDelete: async handler deleted by the wrong thread`
        del self.window


#    class ApiMapWindow(Window):
#        def __init__(self, master, )


class ConfigWindow(Window):
    def __init__(self, master, config_json):
        Window.__init__(self, master)

        self.config_json = config_json
        self.rule_buttons = []  # List of lists [[ json_rule, Button ]]

        for rule in self.config_json:
            self.rule_buttons.append([rule, Button(self.window)])

        for rule, btn in self.rule_buttons:
            btn.pack(side=TOP, fill=BOTH)

        buttons_frame = Frame(self.window)
        buttons_frame.pack(side=BOTTOM)
        Button(buttons_frame, text="Close", command=self.close).pack(side=RIGHT)
        Button(buttons_frame, text="Save", command=self.save_and_exit).pack(side=LEFT)

    def save_and_exit(self):
        config_json = []
        for rule, btn in self.rule_buttons:
            config_json.append(rule)
        self.new_value = config_json
        self.window.destroy()

    def draw(self):
        for rule_and_btn in self.rule_buttons:
            rule = rule_and_btn[0]
            btn = rule_and_btn[1]
            btn["text"] = rule.get('path_expr', '.*')
            btn["command"] = self.open_window(ModalWindow,
                                              rule_and_btn)


class ModalWindow(Window):
    def __init__(self, master, json_obj):
        Window.__init__(self, master)

        self.save_btn = Button(self.window, text='Save',
                               command=self.save_and_exit)
        self.cancel_btn = Button(self.window, text='Cancel',
                                 command=self.window.destroy)
        self.cancel_btn.pack(side=BOTTOM)
        self.save_btn.pack(side=BOTTOM)
        self.text = Text(self.window,
                         background='white')
        self.text.pack(side=TOP,
                       fill=BOTH,
                       expand=YES)
        text = json.dumps(json_obj, indent=4)
        self.text.insert('0.0', text)

    def save_and_exit(self):
        self.new_value = json.loads(self.text.get('0.0', END))
        self.window.destroy()
