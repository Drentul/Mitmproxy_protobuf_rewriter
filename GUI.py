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
        self.window.protocol("WM_DELETE_WINDOW", self.close_childs_recursive)
        self.master = master
        self.subwindow = None
        self.flag_for_delete = False

    def go(self):
        self.draw()
        self.new_value = None
        self.window.transient(self.master)
        self.window.grab_set()
        self.window.focus_set()
        self.window.wait_window()
        return self.new_value

    def close(self):
        if self.window is not None:
            self.window.destroy()

    def draw(self):
        pass

    def close_childs_recursive(self):
        self.flag_for_delete = True
        if self.subwindow is not None:
            self.subwindow.close_childs_recursive()
        self.close()

    def open_window(self, window_class, config) -> None:

        def wrapper(_window_class=window_class,
                    _config=config):

            self.subwindow = _window_class(self.window, _config)
            self.return_value = self.subwindow.go()

            del self.subwindow
            self.subwindow = None
            if self.flag_for_delete is True:
                return

            if self.return_value and _config:
                _config.config = self.return_value

            self.draw()

        return wrapper


class Config:
    '''Represents object that stores json config'''

    def __init__(self, config, button=None, path=None, name=''):
        self.name = name
        self.path = path
        self._config = config
        self.button = button
        self.config_mutex = threading.Lock()

    config = property()

    @config.getter
    def config(self):
        with self.config_mutex:
            return self._config

    @config.setter
    def config(self, value):
        with self.config_mutex:
            self._config = value


class GUI(threading.Thread, Window):

    def __init__(self, config_json, api_map):
        threading.Thread.__init__(self)
        self.window = None
        self.master = None
        self.subwindow = None
        self.flag_for_delete = False
        self.config_json = Config(config_json)
        self.api_map = Config(api_map)
        self.start()

    def go(self):
        pass

    def close(self):
        self.window.quit()  # Leave mainloop
        proxy_shutdown()

    def quit_dialog(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.close_childs_recursive()

    def run(self):
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.quit_dialog)

        Button(self.window, text="API map",
               command=self.open_window(ApiMapWindow,
                                        self.api_map)).pack(side=TOP, fill=BOTH)

        Button(self.window, text="Config",
               command=self.open_window(ConfigWindow,
                                        self.config_json)).pack(side=TOP,
                                                                fill=BOTH)

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


class ApiMapWindow(Window):
    def __init__(self, master, api_map):
        Window.__init__(self, master)

        self.api_map = api_map

        self.api_list = []

        for api in self.api_map.config:
            config = Config(api, button=Button(self.window),
                            name=api.get("file_path", "no_name"))
            self.api_list.append(config)

        for api in self.api_list:
            api.button.grid(row=0, column=0, columnspan=2)

        filenames_frame = Frame(self.window)
        filenames_frame.grid(row=0, column=0, columnspan=2)
        server_frame = Frame(self.window)
        server_frame.grid(row=0, column=2, columnspan=2)
        api_rules_frame = Frame(self.window)
        api_rules_frame.grid(row=0, column=4, columnspan=2)
        save_button_frame = Frame(self.window)
        save_button_frame.grid(row=1, column=0, columnspan=3)
        close_button_frame = Frame(self.window)
        close_button_frame.grid(row=1, column=3, columnspan=3)

        self.text = Text(self.window,
                         background='white')
        self.text.grid(row=0, column=2, columnspan=2)

        self.text = Text(self.window,
                         background='white')
        self.text.grid(row=0, column=4, columnspan=2)

        Button(self.window, text="Save",
               command=self.save_and_exit).grid(row=1, column=2, sticky='w')
        Button(self.window, text="Close",
               command=self.close_childs_recursive).grid(row=1, column=4)

    def save_and_exit(self):
        api_map = []
        for api in self.api_list:
            api_map.append(api.config)
        self.new_value = api_map
        self.window.destroy()

    def draw(self):
        for api in self.api_list:
            api.button["text"] = api.name
            api.button["command"] = self.open_window(ModalWindow,
                                                     api)


class ConfigWindow(Window):
    def __init__(self, master, config_json):
        Window.__init__(self, master)

        self.config_json = config_json
        self.rule_list = []

        for rule in self.config_json.config:
            button = Button(self.window)
            config = Config(rule, button)
            self.rule_list.append(config)
            button.pack(side=TOP, fill=BOTH)

        buttons_frame = Frame(self.window)
        buttons_frame.pack(side=BOTTOM)
        Button(buttons_frame, text="Close",
               command=self.close_childs_recursive).pack(side=RIGHT)
        Button(buttons_frame, text="Save",
               command=self.save_and_exit).pack(side=LEFT)

    def save_and_exit(self):
        config_json = []
        for rule in self.rule_list:
            config_json.append(rule.config)
        self.new_value = config_json
        self.window.destroy()

    def draw(self):
        for rule in self.rule_list:
            rule.button["text"] = rule.config.get('path_expr', '.*')
            rule.button["command"] = self.open_window(ModalWindow,
                                                      rule)


class ModalWindow(Window):
    def __init__(self, master, config):
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
        text = json.dumps(config.config, indent=4)
        self.text.insert('0.0', text)

    def save_and_exit(self):
        self.new_value = json.loads(self.text.get('0.0', END))
        self.window.destroy()
