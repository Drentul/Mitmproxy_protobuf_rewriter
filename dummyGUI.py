"""
Graphical user interface based on Tkinter standard library
"""

import json
import os
from os import listdir, unlink
import GUI_widgets as GW
from tkinter import *
from tkinter import messagebox
from tkinter import font
from conf import *


def load_configs():
    config_file_path = CONFIG_FILE_PATH
    api_rules_dir = API_RULES_DIR

    try:
        with open(config_file_path) as _config:
            config_json = json.load(_config)
    except Exception:
        pass
    # TODO сделать обработку исключений в духе: "См. в лог прокси"

    api_map = []  # list of tuples [(json, string_file_name), ..]
    api_files = [f for f in listdir(api_rules_dir) if
                 os.path.isfile(os.path.join(api_rules_dir, f))]
    for api_file in api_files:
        try:
            with open(os.path.join(api_rules_dir, api_file)) as json_api_rule:
                api_rule = json.load(json_api_rule)
        except json.JSONDecodeError:
            # Excluding invalid configs with error
            continue
        api_map.append((api_rule, api_file))

    return api_map, config_json


def create_main_tree(api_for_tree, config_for_tree):
    root = ConfigsTreeNode(None)
    api_map_node = root.add_child(ConfigsTreeNode("API map"))
    config_node = root.add_child(ConfigsTreeNode("Config"))
    for api_config, name in api_for_tree:
        api_file_node = api_map_node.add_child(ConfigsTreeNode(name))
        api_file_node.add_child(ConfigsTreeNode(api_config))
    for conf in config_for_tree:
        name = conf["path_expr"]
        conf_node = config_node.add_child(ConfigsTreeNode(name))
        conf_node.add_child(ConfigsTreeNode(conf))
    return root


def print_tree(node):
    print(node.data)
    for child in node.children:
        print_tree(child)


class ConfigsTreeNode:
    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)
        return obj

    def remove_child(self, obj):
        self.children.remove(obj)

    def get_children(self, data):
        for child in self.children:
            if child.data == data:
                return child

    def change_data(self, new_data):
        self.data = new_data


def compare_trees(node1, node2):
    # TODO: описать рекурсивный алгоритм сравнения деревьев.
    pass


class FrameLayout(Frame):
    def __init__(self, master, window, node):
        self.master = master
        self.window = window
        self.node = node
        self.buttons = []
        Frame.__init__(self, self.master, background='yellow')
        self.buttons_frame = Frame(self)
        self.additional_frame = Frame(self)

    def pack(self):
        Frame.pack(self, expand=True, fill=X, padx=50)
        self.buttons_frame.pack(expand=True, fill=X, padx=10, pady=10)
        self.additional_frame.pack(expand=True, fill=X, padx=10)
        for btn in self.buttons:
            btn.pack(fill=X, padx=5, pady=5)
        for btn in self.additional_frame.winfo_children():
            btn.pack(padx=5)

    def pack_forget(self):
        Frame.pack_forget(self)
        self.save_to_tree()
        self.buttons_frame.pack_forget()
        self.additional_frame.pack_forget()

    def save_to_tree(self):
        nodes = []
        for btn in self.buttons:
            if btn.node is not None:
                nodes.append(btn.node)
        self.node.children = nodes

    def button_delete(self, button):
        def wrapper(_button=button):
            self.buttons.remove(_button)
            _button.pack_forget()
        return wrapper

    def button_add(self, button):
        def wrapper(_button=button):
            self.buttons.append(_button)
            self.pack_forget()
            self.pack()
        return wrapper

    def create_node_and_command_for_button(self, button):
        button.node = None


class RootFrame(FrameLayout):
    def __init__(self, master, window, node):
        FrameLayout.__init__(self, master, window, node)  # master = content_frame (черный)

        self.buttons = []

        api_node = self.node.get_children('API map')
        api_frame = APIFrame(self.master, self.window, api_node)
        api_btn = Button(self.buttons_frame, text=api_node.data,
                         command=self.window.insert_frame(api_frame),
                         font=self.window.buttons_font)
        api_btn.node = api_node
        
        config_node = self.node.get_children('Config')
        config_frame = ConfigFrame(self.master, self.window, config_node)
        config_btn = Button(self.buttons_frame, text=config_node.data,
                            command=self.window.insert_frame(config_frame),
                            font=self.window.buttons_font)
        config_btn.node = config_node
        
        self.buttons.append(api_btn)
        self.buttons.append(config_btn)


class MediumFrame(FrameLayout):
    def __init__(self, master, window, node):
        FrameLayout.__init__(self, master, window, node)

        self.buttons = []
        for child in self.node.children:
            btn = GW.DoubleButtonWithDelete(self.buttons_frame, text=child.data,
                                            font=self.window.buttons_font)
            frame = self.create_frame(child)
            btn.command = self.window.insert_frame(frame)
            btn.delete_command = self.button_delete(btn)
            btn.node = child
            self.buttons.append(btn)
        self.triple_button = GW.TripleEntryWithTwoButtons(self.buttons_frame, font=self.window.buttons_font)
        self.triple_button.node = None
        self.triple_button.command = self.replace_by_double_button(self.triple_button, self.buttons_frame)
        self.add_button = Button(self.additional_frame, text='+',
                                 command=self.button_add(self.triple_button),
                                 font=self.window.buttons_font)

    def replace_by_double_button(self, btn, frame):
        def wrapper(_btn=btn, _frame=frame):
            text = _btn.text
            pack_info = _btn.pack_info()
            new_btn = GW.DoubleButtonWithDelete(_frame, text=text, font=self.window.buttons_font)
            self.create_node_and_command_for_button(new_btn)
            new_btn.delete_command = self.button_delete(new_btn)
            _btn.text = ''
            _btn.pack_forget()
            new_btn.pack(pack_info)
            self.buttons.append(new_btn)
        return wrapper

    def create_frame(self, node):
        return LeafFrame(node)


class APIFrame(MediumFrame):
    def create_node_and_command_for_button(self, button):
        button.node = ConfigsTreeNode(button.text)
        button.node.children.append(ConfigsTreeNode({'server': [], 'errors': [], 'rules': []}))
        frame = self.create_frame(button.node)
        button.command = self.window.insert_frame(frame)

    def create_frame(self, node):
        return APILeaf(self.master, self.window, node)


class ConfigFrame(MediumFrame):
    def create_node_and_command_for_button(self, button):
        button.node = ConfigsTreeNode(button.text)
        button.node.children.append(ConfigsTreeNode({'path_expr': button.text}))
        frame = self.create_frame(button.node)
        button.command = self.window.insert_frame(frame)

    def create_frame(self, node):
        return ConfigLeaf(self.master, self.window, node)


class LeafFrame(FrameLayout):
    def __init__(self, master, window, node):
        FrameLayout.__init__(self, master, window, node)


class APILeaf(LeafFrame):
    def __init__(self, master, window, node):
        FrameLayout.__init__(self, master, window, node)

        self.buttons = []

        self.sections_list = []
        self.child = self.node.children[0]
        api_config = self.child.data  # {'server':'', 'errors': '', 'rules': ''}
        for key, value in api_config.items():
            self.sections_list.append((key, json.dumps(value, indent=4)))
        self.expanded_list = GW.ExpandedList(self.buttons_frame, self.sections_list,
                                             font=self.window.buttons_font)

        self.expanded_list.node = self.child
        self.buttons.append(self.expanded_list)

    def save_to_tree(self):
        self.child.data = self.expanded_list.get()


class ConfigLeaf(LeafFrame):
    def __init__(self, master, window, node):
        FrameLayout.__init__(self, master, window, node)

        self.buttons = []
        self.child = self.node.children[0]
        text = json.dumps(self.child.data, indent=4)
        self.text_field = Text(self.buttons_frame,
                               font=self.window.buttons_font)
        self.text_field.insert(1.0, text)
        self.buttons.append(self.text_field)

    def save_to_tree(self):
        self.child.data = json.loads(self.text_field.get(1.0, END))


class StackOfFrames:
    def __init__(self):
        self.stack = []

    def len(self):
        return len(self.stack)

    def push(self, frame: Frame):
        self.stack.append(frame)

    def pop(self):
        return self.stack.pop()

    def clear(self):
        self.stack = []


class MainWindow:
    def __init__(self, _api, _config):
        self.api = _api
        self.config = _config
        self.current_root = create_main_tree(self.api, self.config)
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.quit_dialog)
        self.stack_of_frames = StackOfFrames()
        self.current_frame = None

        # Fonts
        self.buttons_font = font.Font(font=("Arial", 18))

        # Frames
        self.center_frame = Frame(self.window)
        self.content_frame = Frame(self.center_frame, borderwidth=5, background='black')
        self.description_frame = Frame(self.center_frame, width=300, borderwidth=5, background='green')
        self.buttons_panel = Frame(self.window, height=80, borderwidth=5, background='red')
        self.left_buttons_panel = Frame(self.buttons_panel, background='magenta')
        self.right_buttons_panel = Frame(self.buttons_panel, background='yellow')

        # Buttons
        self.back_button_image = PhotoImage(file='icons/icons8-go-back-64.png')
        self.back_button = Button(self.left_buttons_panel, image=self.back_button_image, command=self.back)
        self.save_button = Button(self.left_buttons_panel, text='SAVE',
                                  font=self.buttons_font, command=self.save_all)
        self.exit_button = Button(self.right_buttons_panel, text='EXIT',
                                  font=self.buttons_font, command=self.quit_dialog)
        self.undo_button = Button(self.right_buttons_panel, text='RESET',
                                  font=self.buttons_font, command=self.reset_changes)

        # Frames
        self.current_frame = RootFrame(self.content_frame, self, self.current_root)
        self.description = Message(self.description_frame)

        self.draw()

    def draw(self):
        self.window.geometry('1024x768')
        self.window.minsize(600, 400)

        self.window.pack_propagate(False)
        self.center_frame.pack_propagate(False)
        self.content_frame.pack_propagate(False)
        self.description_frame.pack_propagate(False)
        self.buttons_panel.pack_propagate(False)
        self.left_buttons_panel.pack_propagate(False)
        self.right_buttons_panel.pack_propagate(False)

        self.center_frame.pack(fill=BOTH, expand=True, side=TOP)
        self.content_frame.pack(fill=BOTH, expand=True, side=LEFT)
        self.description_frame.pack(fill=BOTH, expand=False, side=RIGHT)
        self.buttons_panel.pack(fill=BOTH, expand=False, side=BOTTOM)
        self.left_buttons_panel.pack(fill=BOTH, expand=True, side=LEFT)
        self.right_buttons_panel.pack(fill=BOTH, expand=True, side=RIGHT)

        self.back_button.pack(side=LEFT)
        if self.stack_of_frames.len() == 0:
            self.back_button.pack_forget()

        self.save_button.pack(side=RIGHT, padx=10)
        self.exit_button.pack(side=LEFT, padx=10)
        self.undo_button.pack(side=RIGHT, padx=10)

        self.current_frame.pack()

    def redraw(self):
        for widget in self.window.winfo_children():
            widget.pack_forget()
        self.draw()

    def reset_changes(self):
        self.current_frame.pack_forget()
        self.stack_of_frames.clear()
        self.current_root = create_main_tree(self.api, self.config)
        self.current_frame = RootFrame(self.content_frame, self, self.current_root)
        self.draw()

    def insert_frame(self, frame: Frame):
        def wrapper(_frame=frame):
            if self.current_frame is not None:
                self.stack_of_frames.push(self.current_frame)
                self.current_frame.pack_forget()

            self.current_frame = _frame
            self.redraw()
        return wrapper

    def delete_frame(self):
        try:
            self.current_frame.pack_forget()
            self.current_frame = self.stack_of_frames.pop()
            self.redraw()
        except IndexError as e:
            print(e)

    def quit_dialog(self):
        """Opens dialog window for quit"""
        mb = messagebox.askyesnocancel("Quit", "Do you want to save before quit?")
        if mb is None:
            return
        if mb:
            self.save_api_map()
            self.save_config()
            self.window.destroy()
        else:
            self.window.destroy()

    def del_btn(self, btn):
        def wrapper(_btn=btn):
            _btn.pack_forget()
        return wrapper

    def replace_by_double_button(self, btn, frame):
        def wrapper(_btn=btn, _frame=frame):
            text = _btn.text
            pack_info = _btn.pack_info()
            new_btn = GW.DoubleButtonWithDelete(_frame, text=text)
            new_btn.delete_command = self.del_btn(new_btn)
            _btn.pack_forget()
            new_btn.pack(pack_info)
        return wrapper

    def back(self):
        self.delete_frame()

    def save_all(self):
        self.current_frame.save_to_tree()
        self.save_api_map()
        self.save_config()
        self.api, self.config = load_configs()

    def save_api_map(self):
        # Remove all files
        for the_file in listdir(API_RULES_DIR):
            file_path = os.path.join(API_RULES_DIR, the_file)
            try:
                if os.path.isfile(file_path):
                    unlink(file_path)
            except Exception as e:
                print(e)

        # Creating files and writes jsons to it
        api_map = self.current_root.get_children('API map')
        for node in api_map.children:
            _file = node.data
            _api = node.children[0].data
            with open(os.path.join(API_RULES_DIR, _file), 'w+') as api_file:
                json.dump(_api, api_file, indent=4)

    def save_config(self):
        config_json = self.current_root.get_children('Config')
        _config = []
        for node in config_json.children:
            _config.append(node.children[0].data)
        with open(CONFIG_FILE_PATH, 'w+') as config_file:
            json.dump(_config, config_file, indent=4)


if __name__ == '__main__':
    api, config = load_configs()
    main = MainWindow(api, config)
    main_window = main.window

    main_window.mainloop()
