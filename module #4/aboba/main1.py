import tkinter as tk
from tkinter import ttk 
import os
import sys

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_dir()


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учет")
        self.geometry("1400x600")

    def init_ui(self):
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky="nsew")
  
        for header in headers:
            self.partners_table.heading(header, text=header)
            self.partners_table.column(header, width=100)
        self.partners_table.grid(row=0, column=0, sticky="nsew")
        self.partners_table.bind("<Double-1>", self.edit_partner)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.partners_table.yview)
        self.partners_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10) 

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.load_partners()

   

    
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()