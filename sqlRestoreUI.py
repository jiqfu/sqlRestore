from tkinter import *
from tkinter.scrolledtext import *

import pyperclip

from SqlRestore.SqlRestore import SqlRestore


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # 输入框
        self.input = ScrolledText(self, width=400, undo=True, autoseparators=False)
        # 按钮
        self.createButton = Button(self, width=50, text="生成", relief='solid', command=self.click)
        self.master = master
        self.master.geometry('600x400+200+200')
        self.master.resizable(width=False, height=False)
        # 窗口名
        self.master.title("sql还原工具")
        self.pack()
        self.create_widgets()

    def click(self):
        result = SqlRestore.restore(self.input.get('1.0', END))
        self.input.delete(1.0, END)
        self.input.insert(INSERT, result)
        pyperclip.copy(result)

    def create_widgets(self):
        self.input.pack()
        self.createButton.pack()


def main():
    root = Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
