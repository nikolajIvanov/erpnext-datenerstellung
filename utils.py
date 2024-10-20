import importlib
from tkinter import messagebox

def import_module(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        try:
            return importlib.import_module(f"Master_Data_Generation.{module_name}")
        except ImportError:
            try:
                return importlib.import_module(f"Transaction_Data_Generation.{module_name}")
            except ImportError as e:
                messagebox.showerror("Error", f"Failed to import module {module_name}: {str(e)}")
                return None

def execute_function(module, function_name, *args):
    try:
        func = getattr(module, function_name)
        return func(*args)
    except AttributeError:
        messagebox.showerror("Error", f"Function {function_name} not found in module")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")