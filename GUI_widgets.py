import json
from abc import ABCMeta, abstractmethod
from tkinter import *
import AutoResizedText as Art


class Element(metaclass=ABCMeta):
    def __init__(self, master, title, value, **kwargs):
        self.master = master  # Материнский объект, управляющий элементами, оно же - фрейм для размещения
        self.kwargs = kwargs
        self.title = title
        self.value = value
        self.frame = Frame(self.master, highlightbackground="grey", highlightcolor="grey", highlightthickness=1)

    def pack(self, *args, **kwargs):
        self.frame.pack(*args, **kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    @abstractmethod
    def get(self):
        pass


class ListOfElements(Frame, metaclass=ABCMeta):
    def __init__(self, parent, list_of_pairs, **kwargs):
        Frame.__init__(self, parent)
        self.parent = parent
        self.kwargs = kwargs
        self.list_of_pairs = list_of_pairs  # dict: {title: content, ...}
        self.elements = []
        self.create_elements()

    def create_elements(self):
        for title, content in self.list_of_pairs.items():
            self.elements.append(ExpandedListElement(self, title, content, **self.kwargs))

    def get(self):
        new_dict = {}
        for element in self.elements:
            text = element.get()
            new_dict[element.title] = text
        return new_dict

    def pack(self, **kwargs):
        Frame.pack(self, side=TOP, fill=BOTH, expand=YES)
        for element in self.elements:
            element.pack(side=TOP, fill=BOTH, expand=YES)

    def pack_forget(self):
        Frame.pack_forget(self)
        for element in self.elements:
            element.pack_forget()


class ExpandedListElement(Element):
    def __init__(self, master, title='', value='', **kwargs):
        Element.__init__(self, master, title, value, **kwargs)

        self.text = json.dumps(value, indent=4)
        self.button = Button(self.frame, text=title, command=self.toggle, **kwargs)
        self.indent = Frame(self.frame, height=15)
        self.text_field = Art.AutoResizedText(self.frame, **kwargs)
        self.text_field.pi = None
        self.text_field.visible = False
        self.text_field.update(self.text)

    def pack(self, *args, **kwargs):
        self.frame.pack(*args, **kwargs)
        self.button.pack(*args, **kwargs)
        self.indent.pack(*args, **kwargs)
        self.text_field.pack(*args, **kwargs)
        self.text_field.pi = self.text_field.pack_info()
        if not self.text_field.visible:
            self.text_field.pack_forget()

    def pack_forget(self):
        self.frame.pack_forget()
        self.button.pack_forget()
        self.indent.pack_forget()
        self.text_field.pack_forget()

    def toggle(self):
        if self.text_field.visible:
            self.text_field.pack_forget()
        else:
            self.master.collapse_all()
            self.text_field.pack(self.text_field.pi)
        self.text_field.visible = not self.text_field.visible

    def collapse(self):
        if self.text_field.visible:
            self.text_field.visible = False
            self.text_field.pack_forget()

    def get(self):
        return json.loads(self.text_field.get())


class ExpandedList(ListOfElements):
    def __init__(self, parent, list_of_pairs, **kwargs):
        ListOfElements.__init__(self, parent, list_of_pairs, **kwargs)

    def create_elements(self):
        for title, content in self.list_of_pairs.items():
            self.elements.append(ExpandedListElement(self, title, content, **self.kwargs))

    def collapse_all(self):
        for element in self.elements:
            element.collapse()


class BoolSwitcher(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.btn = Button(self.frame, text=title, command=self.toggle, **kwargs)
        self.indicator = Label(self.frame, width=4)
        self.indicator.is_on = value
        if value:
            self.indicator["background"] = "green"
        else:
            self.indicator["background"] = "red"

    def toggle(self):
        self.indicator.is_on = not self.indicator.is_on
        if self.indicator.is_on:
            self.indicator["background"] = "green"
        else:
            self.indicator["background"] = "red"

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.btn.pack(side=LEFT, fill=BOTH, expand=YES)#, **kwargs)
        self.indicator.pack(side=RIGHT, fill=Y)

    def pack_forget(self):
        self.frame.pack_forget()

    def get(self):
        return self.indicator.is_on


class LabeledString(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.label = Label(self.frame, text=self.title, width=13, **kwargs)
        self.entry = Entry(self.frame, **kwargs)
        self.entry.insert(0, value)

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.label.pack(side=LEFT)#, **kwargs)
        self.entry.pack(side=RIGHT, fill=X, expand=YES)#, **kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    def get(self):
        return self.entry.get()


class LabeledInt(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.label = Label(self.frame, text=self.title, width=13, **kwargs)
        self.entry = Entry(self.frame, **kwargs)
        self.entry.insert(0, value)

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.label.pack(side=LEFT)#, **kwargs)
        self.entry.pack(side=RIGHT, fill=X, expand=YES)#, **kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    def get(self):
        return int(self.entry.get())


class ListOf(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.master = master
        self.list = value
        self.label = Label(self.frame, text=self.title, **kwargs)
        self.buttons = []
        self.buttons_frame = Frame(self.frame)
        self.additional_frame = Frame(self.frame)

        self.triple_button = TripleEntryWithTwoButtons(self.buttons_frame, **kwargs)
        self.triple_button.command = self.replace_by_double_button(self.triple_button, self.buttons_frame, **kwargs)
        self.triple_button.visible = False
        self.add_button = Button(self.additional_frame, text='+',
                                 command=self.button_add(self.triple_button), **kwargs)

    def replace_by_double_button(self, btn, frame, **kwargs):
        def wrapper(_btn=btn, _frame=frame):
            pass
        return wrapper

    def button_add(self, button):
        def wrapper(_button=button):
            self.triple_button.visible = True
            self.pack_forget()
            self.pack()
        return wrapper

    def button_delete(self, button):
        def wrapper(_button=button):
            self.buttons.remove(_button)
            _button.pack_forget()
        return wrapper

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.label.pack(side=TOP, fill=BOTH, expand=YES)
        self.buttons_frame.pack(expand=True, fill=X, padx=10, pady=10)
        self.additional_frame.pack(expand=True, fill=X, padx=10)
        for btn in self.buttons:
            btn.pack(fill=X, padx=5, pady=5)
        if self.triple_button.visible:
            self.triple_button.pack(fill=X, padx=5, pady=5)
        for btn in self.additional_frame.winfo_children():
            btn.pack(padx=5)

    def pack_forget(self):
        self.buttons_frame.pack_forget()
        self.additional_frame.pack_forget()

    def get(self):
        new_value = []
        for button in self.buttons:
            new_value.append(button.text)
        return new_value


class ListOfLabels(ListOf):
    def __init__(self, master, title, value, **kwargs):
        ListOf.__init__(self, master, title, value, **kwargs)
        for string in self.list:
            btn = LabelWithDelete(self.buttons_frame, text=string, **kwargs)
            btn.delete_command = self.button_delete(btn)
            self.buttons.append(btn)

    def replace_by_double_button(self, btn, frame, **kwargs):
        def wrapper(_btn=btn, _frame=frame):
            text = _btn.text
            pack_info = _btn.pack_info()
            new_btn = LabelWithDelete(_frame, text=text, **kwargs)
            new_btn.delete_command = self.button_delete(new_btn)
            _btn.text = ''
            _btn.pack_forget()
            self.triple_button.visible = False
            new_btn.pack(pack_info, fill=X, padx=5, pady=5)
            self.buttons.append(new_btn)
        return wrapper


class ListOfLabeledStringsWithDelete(ListOf):
    def __init__(self, master, title, value, **kwargs):
        ListOf.__init__(self, master, title, value, **kwargs)
        for _key, _value in self.list.items():
            btn = LabeledStringWithDelete(self.buttons_frame, title=_key, text=_value, **kwargs)
            btn.delete_command = self.button_delete(btn)
            self.buttons.append(btn)

    def replace_by_double_button(self, btn, frame, **kwargs):
        def wrapper(_btn=btn, _frame=frame):
            text = _btn.text
            pack_info = _btn.pack_info()
            new_btn = LabeledStringWithDelete(_frame, title=text, **kwargs)
            new_btn.delete_command = self.button_delete(new_btn)
            _btn.text = ''
            _btn.pack_forget()
            self.triple_button.visible = False
            new_btn.pack(pack_info, fill=X, padx=5, pady=5)
            self.buttons.append(new_btn)
        return wrapper

    def get(self):
        new_value = {}
        for button in self.buttons:
            new_value[button.title] = button.element.get()
        return new_value


class ListOfButtons(ListOf):
    def __init__(self, master, owner, title, value, **kwargs):
        ListOf.__init__(self, master, title, value, **kwargs)
        self.owner = owner
        for child in self.owner.node.children:
            btn = ButtonWithDelete(self.buttons_frame, text=child.data, **kwargs)
            frame = self.owner.create_frame(child)
            btn.command = self.owner.window.insert_frame(frame)
            btn.delete_command = self.button_delete(btn)
            btn.node = child
            self.buttons.append(btn)

    def replace_by_double_button(self, btn, frame, **kwargs):
        def wrapper(_btn=btn, _frame=frame):
            text = _btn.text
            pack_info = _btn.pack_info()
            new_btn = ButtonWithDelete(_frame, text=text, **kwargs)
            self.owner.create_node_and_command_for_button(new_btn)
            new_btn.delete_command = self.button_delete(new_btn)
            _btn.text = ''
            _btn.pack_forget()
            self.triple_button.visible = False
            new_btn.pack(pack_info, fill=X, padx=5, pady=5)
            self.buttons.append(new_btn)
        return wrapper


class ListOfKeyValuePairs(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.list = ListOfLabeledStringsWithDelete(master, title, value, **kwargs)

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.list.pack()

    def pack_forget(self):
        self.frame.pack_forget()

    def get(self):
        return self.list.get()


class ListOfMethods(Element):
    def __init__(self, master, title, value, **kwargs):
        Element.__init__(self, master, title, value, **kwargs)
        self.label = Label(self.frame, text=self.title, width=13, **kwargs)
        self.methods = ['GET', 'POST', 'PUT', 'DELETE']
        self.elements = []
        for method in self.methods:
            btn = Button(self.frame, text=method, **kwargs)
            btn['command'] = self.toggle(btn)
            btn.is_on = method in value
            if btn.is_on:
                btn["background"] = "green"
            else:
                btn["background"] = "red"
            self.elements.append(btn)

    def toggle(self, element):
        def wrapper(_element=element):
            element.is_on = not element.is_on
            if element.is_on:
                element["background"] = "green"
            else:
                element["background"] = "red"
        return wrapper

    def pack(self, **kwargs):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.label.pack(side=LEFT)
        for element in self.elements:
            element.pack(side=LEFT, fill=BOTH, expand=YES)

    def pack_forget(self):
        self.frame.pack_forget()
        self.label.pack_forget()
        for element in self.elements:
            element.pack_forget()

    def get(self):
        new_value = []
        for element in self.elements:
            if element.is_on:
                new_value.append(element['text'])
        return new_value


class SpecialList(ListOfElements):
    def __init__(self, parent, list_of_pairs, **kwargs):
        ListOfElements.__init__(self, parent, list_of_pairs, **kwargs)

    def create_elements(self):
        for title, value in self.list_of_pairs.items():
            self.elements.append(self.choose_type(value)(self, title, value, **self.kwargs))

    #def pack(self, **kwargs):
    #    ListOfElements.pack(self, **kwargs)
    #    max_width = 0
    #    for element in self.elements:
    #        if type(element) in (LabeledString, LabeledInt):
    #            current_width = element.label.winfo_reqwidth()
    #            print(current_width)
    #            if current_width > max_width:
    #                max_width = current_width
    #
    #    for element in self.elements:
    #        if type(element) in (LabeledString, LabeledInt):
    #            element.label['width'] = max_width * (какой-то коэффициент для шрифта)
    #
    def choose_type(self, value):
        _type = type(value)
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        if _type is bool:
            return BoolSwitcher
        try:
            int(value)
            return LabeledInt
        except (ValueError, TypeError):
            pass
        if _type is str:
            return LabeledString
        elif _type is list:
            if set(methods) & set(value):
                return ListOfMethods
            return ListOfLabels
        elif _type is dict:
            return ListOfKeyValuePairs
        elif value is None:
            return LabeledString
        else:
            print(value)
            raise Exception('No one type matches to <SpecialList> element')


class TripleEntryWithTwoButtons(Frame):
    def __init__(self, master, command=None, **kwargs):
        Frame.__init__(self, master)
        self._master = master
        self._command = command
        self.entry = Entry(self, **kwargs)
        self.ok_button = Button(self, text=' ✓ ', command=self._command, **kwargs)
        self.cancel_button = Button(self, text=' x ', command=self.pack_forget, **kwargs)

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.entry.pack(side=LEFT, fill=BOTH, expand=True)
        self.cancel_button.pack(side=RIGHT)
        self.ok_button.pack(side=RIGHT)

    def pack_forget(self):
        self.text = ''
        self._master.focus()
        self.entry.pack_forget()
        self.ok_button.pack_forget()
        self.cancel_button.pack_forget()
        super().pack_forget()

    @property
    def text(self):
        return self.entry.get()

    @text.setter
    def text(self, value):
        self.entry.delete(0, END)
        self.entry.insert(0, value)

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, value):
        self._command = value
        self.ok_button['command'] = value


class ElementWithDelete(Frame):
    def __init__(self, master, text='', delete_command=None, **kwargs):
        Frame.__init__(self, master)
        self.node = None
        self._text = text
        self._delete_command = delete_command
        self.element = None
        self.delete_button = Button(self, text=' - ', command=self._delete_command, **kwargs)

    def pack(self, *args, **kwargs):
        Frame.pack(self, *args, **kwargs)
        self.element.pack(side=LEFT, fill=BOTH, expand=True)
        self.delete_button.pack(side=RIGHT)

    def pack_forget(self):
        self.element.pack_forget()
        self.delete_button.pack_forget()
        Frame.pack_forget(self)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.element['text'] = value

    @property
    def delete_command(self):
        return self._delete_command

    @delete_command.setter
    def delete_command(self, value):
        self._delete_command = value
        self.delete_button['command'] = value


class ButtonWithDelete(ElementWithDelete):
    def __init__(self, master, text='', command=None, delete_command=None, **kwargs):
        ElementWithDelete.__init__(self, master, text, delete_command, **kwargs)
        self._command = command
        self.element = Button(self, text=self._text, command=self._command, **kwargs)

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, value):
        self._command = value
        self.element['command'] = value


class LabelWithDelete(ElementWithDelete):
    def __init__(self, master, text='', delete_command=None, **kwargs):
        ElementWithDelete.__init__(self, master, text, delete_command, **kwargs)
        self.element = Label(self, text=self._text, **kwargs)


class LabeledStringWithDelete(ElementWithDelete):
    def __init__(self, master, title='', text='', delete_command=None, **kwargs):
        ElementWithDelete.__init__(self, master, text, delete_command, **kwargs)
        self.element = Entry(self, **kwargs)
        self.element.insert(0, self._text)
        self.title = title
        self.label = Label(self, text=self.title, **kwargs)

    def pack(self, *args, **kwargs):
        self.label.pack(side=LEFT, fill=BOTH, expand=True)
        ElementWithDelete.pack(self, *args, **kwargs)
