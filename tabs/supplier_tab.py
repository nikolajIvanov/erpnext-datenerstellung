import tkinter as tk
from tkinter import ttk, messagebox
from utils import import_module, execute_function


class SupplierTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Suppliers")
        self.create_widgets()

    def create_widgets(self):
        create_frame = ttk.LabelFrame(self.frame, text="Create Suppliers")
        create_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(create_frame, text="Number of Suppliers:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.supplier_entry = ttk.Entry(create_frame, width=10)
        self.supplier_entry.grid(row=0, column=1, padx=5, pady=5)
        self.supplier_entry.insert(0, "10")

        ttk.Button(create_frame, text="Create Suppliers", command=self.create_suppliers).grid(row=1, column=0,
                                                                                              columnspan=2, pady=10)

        delete_frame = ttk.LabelFrame(self.frame, text="Delete Suppliers")
        delete_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(delete_frame, text="Delete All Suppliers", command=self.delete_suppliers).pack(pady=10)

    def create_suppliers(self):
        try:
            num_suppliers = int(self.supplier_entry.get())

            supplier_module = import_module("supplier_generation_master_data")
            if supplier_module:
                execute_function(supplier_module, "generate_suppliers", num_suppliers)
                messagebox.showinfo("Success", f"Created {num_suppliers} suppliers successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of suppliers.")

    def delete_suppliers(self):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all suppliers?"):
            supplier_module = import_module("supplier_generation_master_data")
            if supplier_module:
                execute_function(supplier_module, "delete_suppliers")
                messagebox.showinfo("Success", "All suppliers have been deleted successfully!")