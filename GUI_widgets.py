from tkinter import *
import AutoResizedText as Art


class ListElement:
    def __init__(self, parent, master, title='', text=''):

        self.title = title
        self.text = text

        self.master = master  # Материнский объект, управляющий элементами
        self.parent = parent  # Окно или фрейм в котором мы будем размещать элементы
        self.frame = Frame(self.parent)
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)

        self.button = Button(self.frame, text=title, command=self.toggle)
        self.button.pack(side=TOP, fill=BOTH, expand=YES)
        self.indent = Frame(self.frame, height=15)
        self.indent.pack(side=TOP, fill=BOTH, expand=YES)
        self.text_field = Art.AutoResizedText(self.frame)
        self.text_field.pack(side=TOP, fill=BOTH, expand=YES)
        self.text_field.pi = self.text_field.pack_info()
        self.text_field.visible = True
        self.toggle()
        self.text_field.update(self.text)

    def pack(self):
        self.frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.button.pack(side=TOP, fill=BOTH, expand=YES)
        self.indent.pack(side=TOP, fill=BOTH, expand=YES)
        self.text_field.pack(side=TOP, fill=BOTH, expand=YES)

    def toggle(self):
        if self.text_field.visible:
            self.text_field.pack_forget()
        else:
            self.master.collapse_all()
            self.text_field.pack(self.text_field.pi)
        self.text_field.visible = not self.text_field.visible


class ExpandedList:
    def __init__(self, parent, list_of_pairs):
        self.list_of_pairs = list_of_pairs
        self.parent = parent
        self.elements = []
        self.create_elements()

    def create_elements(self):
        for title, content in self.list_of_pairs:
            self.elements.append(ListElement(self.parent, self, title, content))

    def collapse_all(self):
        for element in self.elements:
            if element.text_field.visible:
                element.text_field.visible = False
                element.text_field.pack_forget()

    def get(self):
        new_dict = {}
        for element in self.elements:
            new_dict[element.title] = element.text_field.get()
        return new_dict


class DoubleButtonWithDelete(Frame):
    def __init__(self, master, text='', command=None, delete_command=None):
        Frame.__init__(self, master)
        self._text = text
        self._command = command
        self._delete_command = delete_command
        self.main_btn = Button(self, text=self._text, command=self._command)
        self.delete_button = Button(self, text=' - ', command=self._delete_command)

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.main_btn.pack(side=LEFT, fill=BOTH, expand=True)
        self.delete_button.pack(side=RIGHT)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.main_btn['text'] = value

    @property
    def command(self):
        return self._text

    @command.setter
    def command(self, value):
        self._text = value
        self.main_btn['command'] = value

    @property
    def delete_command(self):
        return self._text

    @delete_command.setter
    def delete_command(self, value):
        self._text = value
        self.delete_button['command'] = value
