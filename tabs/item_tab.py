import tkinter as tk
from tkinter import ttk, messagebox
from utils import import_module, execute_function


class ItemTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Items")
        self.create_widgets()

    def create_widgets(self):
        create_frame = ttk.LabelFrame(self.frame, text="Create Items")
        create_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(create_frame, text="Number of Bikes:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.bike_entry = ttk.Entry(create_frame, width=10)
        self.bike_entry.grid(row=0, column=1, padx=5, pady=5)
        self.bike_entry.insert(0, "5")

        ttk.Label(create_frame, text="Number of Components:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.component_entry = ttk.Entry(create_frame, width=10)
        self.component_entry.grid(row=1, column=1, padx=5, pady=5)
        self.component_entry.insert(0, "30")

        ttk.Button(create_frame, text="Create Items", command=self.create_items).grid(row=2, column=0, columnspan=2,
                                                                                      pady=10)

        delete_frame = ttk.LabelFrame(self.frame, text="Delete Items")
        delete_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(delete_frame, text="Delete All Items", command=self.delete_items).pack(pady=10)

    def create_items(self):
        try:
            num_bikes = int(self.bike_entry.get())
            num_components = int(self.component_entry.get())

            item_module = import_module("item_generation_master_data")
            if item_module:
                execute_function(item_module, "generate_bikes", num_bikes)
                execute_function(item_module, "generate_components", num_components)
                messagebox.showinfo("Success",
                                    f"Created {num_bikes} bikes and {num_components} components successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for bikes and components.")

    def delete_items(self):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all items?"):
            item_module = import_module("item_generation_master_data")
            if item_module:
                execute_function(item_module, "delete_items")
                messagebox.showinfo("Success", "All items have been deleted successfully!")