from tkinter import ttk, messagebox
from src.utils.utils import import_module, execute_function
from datetime import datetime


class PurchaseOrderTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Purchase Orders")
        self.create_widgets()

    def create_widgets(self):
        create_frame = ttk.LabelFrame(self.frame, text="Create Purchase Orders")
        create_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(create_frame, text="Number of POs:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.po_entry = ttk.Entry(create_frame, width=10)
        self.po_entry.grid(row=0, column=1, padx=5, pady=5)
        self.po_entry.insert(0, "10")

        ttk.Label(create_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.start_date = ttk.Entry(create_frame, width=12)
        self.start_date.grid(row=1, column=1, padx=5, pady=5)
        self.start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(create_frame, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.end_date = ttk.Entry(create_frame, width=12)
        self.end_date.grid(row=2, column=1, padx=5, pady=5)
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Button(create_frame, text="Create Purchase Orders", command=self.create_purchase_orders).grid(row=3, column=0, columnspan=2, pady=10)

        delete_frame = ttk.LabelFrame(self.frame, text="Delete Purchase Orders")
        delete_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(delete_frame, text="Delete All Purchase Orders", command=self.delete_purchase_orders).pack(pady=10)

    def create_purchase_orders(self):
        try:
            num_pos = int(self.po_entry.get())
            start_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date.get(), "%Y-%m-%d")

            if start_date > end_date:
                messagebox.showerror("Error", "Start date must be before end date.")
                return

            print("Attempting to import create_purchase_order module")
            po_module = import_module("create_purchase_order")
            print(f"Imported module: {po_module}")
            if po_module:
                print("Executing generate_purchase_orders function")
                result = execute_function(po_module, "generate_purchase_orders", num_pos, start_date, end_date)
                print(f"Function execution result: {result}")
                messagebox.showinfo("Success", f"Created {num_pos} purchase orders successfully!")
        except Exception as e:
            print(f"Error in create_purchase_orders: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_purchase_orders(self):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all purchase orders?"):
            po_module = import_module("create_purchase_order")
            if po_module:
                execute_function(po_module, "delete_purchase_orders")
                messagebox.showinfo("Success", "All purchase orders have been deleted successfully!")