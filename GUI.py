'''
Graphical user interface based on Tkinter standard library
'''

import tkinter
from tkinter import messagebox
import threading
import rewrite_core
import time
from mitmproxy import ctx


class GUI(threading.Thread):

    def __init__(self):
        #ctx.log.info('Creating new GUI')
        threading.Thread.__init__(self)
        self.start()
    
    def quit(self):
        if self.root is not None:
            #print(self.root.winfo_exists())
            self.root.quit()  # Leave mainloop

    def callback(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.root is not None:
                self.root.quit()  # Leave mainloop

    def run(self):
        self.root = tkinter.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        
        label = tkinter.Label(self.root, text="Hello World")
        label.pack()
        
        self.root.mainloop()

        #  ctx.log.info('End of GUI life')
        #  there is a runtime error trowing in this instruction
        #  RuntimeError: There is no current event loop in thread ...

        self.root.update_idletasks()  # We update it ourselves to force destruction.

        self.root.destroy()  # Destroy root window and its childs

        #  Needs to clear manually or declare it as a local variable
        #  In other hand there is:
        #  `Tcl_AsyncDelete: async handler deleted by the wrong thread`
        del self.root
