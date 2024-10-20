import tkinter as tk
from tkinter import ttk, messagebox
from utils import import_module, execute_function


class WarehouseTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Warehouses")
        self.create_widgets()

    def create_widgets(self):
        create_frame = ttk.LabelFrame(self.frame, text="Create Warehouses")
        create_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(create_frame, text="Number of Warehouses:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.warehouse_entry = ttk.Entry(create_frame, width=10)
        self.warehouse_entry.grid(row=0, column=1, padx=5, pady=5)
        self.warehouse_entry.insert(0, "5")

        ttk.Button(create_frame, text="Create Warehouses", command=self.create_warehouses).grid(row=1, column=0,
                                                                                                columnspan=2, pady=10)

        delete_frame = ttk.LabelFrame(self.frame, text="Delete Warehouses")
        delete_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(delete_frame, text="Delete All Warehouses", command=self.delete_warehouses).pack(pady=10)

    def create_warehouses(self):
        try:
            num_warehouses = int(self.warehouse_entry.get())

            warehouse_module = import_module("warehouse_generation_master_data")
            if warehouse_module:
                execute_function(warehouse_module, "generate_warehouses", num_warehouses)
                messagebox.showinfo("Success", f"Created {num_warehouses} warehouses successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of warehouses.")

    def delete_warehouses(self):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all warehouses?"):
            warehouse_module = import_module("warehouse_generation_master_data")
            if warehouse_module:
                execute_function(warehouse_module, "delete_warehouses")
                messagebox.showinfo("Success", "All warehouses have been deleted successfully!")