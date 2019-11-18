"""
Graphical user interface based on Tkinter standard library
"""

import json
import threading
import GUI_widgets as GW
from abc import ABCMeta, abstractmethod
from tkinter import *
from tkinter import messagebox

from mitmproxy import ctx


def proxy_shutdown() -> None:
    """Func stops proxy"""

    ctx.master.shutdown()


class Window(metaclass=ABCMeta):
    """Base class for all windows in the GUI"""

    def __init__(self, master):
        self.new_value = None
        self.window = Toplevel(master)
        self.window.protocol("WM_DELETE_WINDOW", self.close_childs_recursive)
        self.master = master
        self.subwindow = None
        self.flag_for_delete = False

    def go(self):
        """The main functionality"""
        self.draw()  # Method for updating all infos in components
        self.window.transient(self.master)
        self.window.grab_set()
        self.window.focus_set()
        self.window.wait_window()
        return self.new_value

    def close(self):
        """Closes this window"""
        if self.window is not None:
            self.window.destroy()

    @abstractmethod
    def draw(self):
        """Updates all components"""

    def close_childs_recursive(self):
        """Closes all this window childs and then this window"""
        self.flag_for_delete = True
        if self.subwindow is not None:
            self.subwindow.close_childs_recursive()
        self.close()

    def open_window(self, window_class, config):
        """Opens new window as a child of current. Then passes control
        to him and waits for the completion of his work with some result.
        Returns a parameterized function as a result"""

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
    """Stores json config and methods for thread safe accessing to it"""

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
    """Main GUI window and a working thread"""

    def __init__(self, addon, config_json, api_map):
        threading.Thread.__init__(self)
        self.addon = addon
        self.window = None
        self.master = None
        self.subwindow = None
        self.flag_for_delete = False
        self.config_json = Config(config_json)
        self.api_map = Config(api_map)
        self.start()

    def go(self):
        """Has no parent that can run this"""
        pass

    def close(self):
        """Overrides close of other windows"""
        self.window.quit()  # Leave mainloop
        proxy_shutdown()

    def draw(self):
        """Don't need for this class now. It has no changes."""
        pass

    def quit_dialog(self):
        """Opens dialog window for quit"""
        mb = messagebox.askyesnocancel("Quit", "Do you want to save before quit?")
        if mb is None:
            return
        if mb:
            self.addon.save_api_map()
            self.addon.save_config()
            self.close_childs_recursive()
        else:
            self.close_childs_recursive()

    def run(self):
        """This runs as a thread"""
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

        exit_button = Button(self.window, text='Save/Exit',
                             command=self.quit_dialog)
        exit_button.pack(side=BOTTOM)

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
    """Window for API map of our addon"""

    def __init__(self, master, api_map):
        Window.__init__(self, master)

        self.api_frame = Frame(self.window)
        self.api_frame.pack(side=TOP)

        self.api_map = api_map

        self.api_list = []

        for api in self.api_map.config:  # Each 'api' is a tuple (json, string_file_name)
            config = Config(api[0], button=Button(self.api_frame), name=api[1])
            self.api_list.append(config)

        empty_frame = Frame(self.window, height=15)
        empty_frame.pack(side=TOP)

        buttons_frame = Frame(self.window)
        buttons_frame.pack(side=BOTTOM)
        Button(buttons_frame, text="Close",
               command=self.close_childs_recursive).pack(side=RIGHT)
        Button(buttons_frame, text="Save",
               command=self.save_and_exit).pack(side=LEFT)

    def save_and_exit(self):
        """Saves new config to parent window then closes this"""
        api_map = []
        for api in self.api_list:
            api_map.append((api.config, api.name))
        self.new_value = api_map
        self.window.destroy()

    def draw(self):
        """Places new texts and and new commands to buttons"""

        for widget in self.api_frame.winfo_children():
            widget.pack_forget()
        for api in self.api_list:
            api.button.pack_forget()
            api.button["text"] = api.name
            api.button["command"] = self.open_window(ApiSubwindow, api)
            api.button.pack()


class ApiSubwindow(Window):
    """Window for single API map file"""

    def __init__(self, master, api_file):
        Window.__init__(self, master)

        self.api_frame = Frame(self.window)
        self.api_frame.pack(side=TOP)

        self.api_file = api_file

        self.sections_list = []

        for section in self.api_file.config.items():
            self.sections_list.append((section[0], json.dumps(section[1], indent=4)))

        self.e_list = GW.ExpandedList(self.api_frame, self.sections_list)

        empty_frame = Frame(self.window, height=15)
        empty_frame.pack(side=TOP)

        buttons_frame = Frame(self.window)
        buttons_frame.pack(side=BOTTOM)
        Button(buttons_frame, text="Close",
               command=self.close_childs_recursive).pack(side=RIGHT)
        Button(buttons_frame, text="Save",
               command=self.save_and_exit).pack(side=LEFT)

    def save_and_exit(self):
        """Saves new config to parent window then closes this"""
        self.new_value = self.e_list.get()
        self.window.destroy()

    def draw(self):
        """Places new texts and and new commands to buttons"""
        pass


class ConfigWindow(Window):
    """Window that stores rules config that control the behavior of the addon"""
    def __init__(self, master, config_json):
        Window.__init__(self, master)

        self.configs_frame = Frame(self.window)
        self.configs_frame.pack(side=TOP, fill=BOTH)

        self.config_json = config_json
        self.rule_list = []

        for rule in self.config_json.config:
            button = GW.DoubleButtonWithDelete(self.configs_frame)
            config = Config(rule, button)
            self.rule_list.append(config)

        buttons_frame = Frame(self.window)
        buttons_frame.pack(side=BOTTOM)
        Button(buttons_frame, text="Close",
               command=self.close_childs_recursive).pack(side=RIGHT)
        Button(buttons_frame, text="Save",
               command=self.save_and_exit).pack(side=LEFT)

    def save_and_exit(self):
        """Saves new config to parent window then closes this"""

        # TODO: Посмотреть, нельзя ли таки объединить методы под общим соусом
        config_json = []
        for rule in self.rule_list:
            config_json.append(rule.config)
        self.new_value = config_json
        self.window.destroy()

    def draw(self):
        """Places new texts and and new commands to buttons"""

        # TODO: Посмотреть, нельзя ли таки объединить методы под общим соусом

        for widget in self.configs_frame.winfo_children():
            widget.pack_forget()

        for rule in self.rule_list:
            rule.button.text = rule.config.get('path_expr', '.*')
            rule.button.command = self.open_window(ModalWindow, rule)
            rule.button.delete_command = self.button_delete(rule.button)
            rule.button.pack(side=TOP, fill=BOTH)

    def button_delete(self, button):
        # TODO: сделать безопаснее, т.к. удаление из листа в цикле плохая идея.
        def wrapper(_button=button):
            for config in self.rule_list:
                if config.button == _button:
                    self.rule_list.remove(config)
                    break
            self.draw()
        return wrapper


class ModalWindow(Window):
    """Simple modal window with config in text panel and save button"""
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

    def draw(self):
        """Don't need for this class now. It has no changes."""
        pass

    def save_and_exit(self):
        """Saves new config to parent window then closes this"""
        try:
            self.new_value = json.loads(self.text.get('0.0', END))
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка!",
                                 "Проверьте правильность введенного JSON",
                                 parent=self.window)
            return
        self.window.destroy()
