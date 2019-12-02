# Version: 1.2
# Author: Miguel Martinez Lopez
# Uncomment the next line to see my email
# print "Author's email: ", "61706c69636163696f6e616d656469646140676d61696c2e636f6d".decode("hex")

try:
    from Tkinter import Frame, Text
    from Tkconstants import *
    import tkfont
except ImportError:
    from tkinter import Frame, Text
    from tkinter.constants import *
    from tkinter import font as tkfont
import json


class AutoResizedText(Frame):
    def __init__(self, master, width=0, height=0, family="Arial", size=15, *args, **kwargs):
        
        Frame.__init__(self, master, width=width, height=height)
        self.pack_propagate(False)

        self._min_width = width
        self._min_height = height

        self._textarea = Text(self, *args, **kwargs)

        if family is None and size is None:
            self._font = tkfont.Font(family=family, size=size)
        else:
            self._font = tkfont.Font(font=self._textarea["font"])

        self._textarea.config(font=self._font)
        self._textarea.bind('<KeyRelease>', self.resize)

        self._textarea.pack(expand=True, fill='both')

    def _fit_to_size_of_text(self):
        text = self._textarea.get("1.0", END)
        number_of_lines = 0
        widget_width = 0

        for line in text.split("\n"):
            widget_width = max(widget_width, self._font.measure(line))
            number_of_lines += 1

        # We need to add this extra space to calculate the correct width
        widget_width += 2*self._textarea['bd'] + 2*self._textarea['padx'] + self._textarea['insertwidth']

        if widget_width < self._min_width:
            widget_width = self._min_width

        self._textarea.configure(height=number_of_lines)
        widget_height = max(self._textarea.winfo_reqheight(), self._min_height)

        self.config(width=widget_width, height=widget_height)

        # If we don't call update_idletasks, the window won't be resized before an insertion
        self.update_idletasks()

    def resize(self, *args, **kwargs):
        return self._fit_to_size_of_text()

    def get(self, start="1.0", end=END):
        return self._textarea.get(start, end)

    def update(self, text):
        self._textarea.delete('1.0', 'end')
        self._textarea.insert('1.0', text)
        self._fit_to_size_of_text()


if __name__ == '__main__':
    try:
        from Tkinter import Tk
    except ImportError:
        from tkinter import Tk

    root = Tk()
    auto_text = AutoResizedText(root, family="Arial", size=15, width = 100, height = 50)
    auto_text.pack()
    auto_text.focus()
    root.mainloop()
