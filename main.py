import tkinter as tk
from tkinter import ttk
import sys
import os
from tabs.item_tab import ItemTab
from tabs.supplier_tab import SupplierTab
from tabs.warehouse_tab import WarehouseTab
from tabs.purchase_order_tab import PurchaseOrderTab

# Füge beide Ordner zum Python-Pfad hinzu
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, 'Master_Data_Generation'))
sys.path.append(os.path.join(base_dir, 'Transaction-Data_Generation'))


class DemoDataGUI:
    def __init__(self, master):
        self.master = master
        master.title("Demo Data Management")
        master.geometry("600x400")

        self.create_menu()
        self.create_notebook()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        ItemTab(self.notebook)
        SupplierTab(self.notebook)
        WarehouseTab(self.notebook)
        PurchaseOrderTab(self.notebook)


def main():
    root = tk.Tk()
    app = DemoDataGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
