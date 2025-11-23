"""Minimal test to verify GUI initialization."""

import tkinter as tk
from tkinter import ttk

def test_minimal_gui():
    """Test basic Tkinter variable initialization."""

    print("Creating minimal GUI test...")

    # Create window
    window = tk.Tk()
    window.title("Minimal GUI Test")
    window.geometry("400x300")

    # Create variables WITHOUT master (old way)
    var1_no_master = tk.StringVar(value="Test without master")
    var2_no_master = tk.IntVar(value=123)

    # Create variables WITH master (new way)
    var1_with_master = tk.StringVar(master=window, value="Test with master")
    var2_with_master = tk.IntVar(master=window, value=456)

    # Create frame
    frame = ttk.Frame(window, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    # Test 1: Entry without master
    ttk.Label(frame, text="Entry (no master):").grid(row=0, column=0, sticky=tk.W, pady=5)
    entry1 = ttk.Entry(frame, textvariable=var1_no_master, width=30)
    entry1.grid(row=0, column=1, pady=5, padx=5)

    # Test 2: Entry with master
    ttk.Label(frame, text="Entry (with master):").grid(row=1, column=0, sticky=tk.W, pady=5)
    entry2 = ttk.Entry(frame, textvariable=var1_with_master, width=30)
    entry2.grid(row=1, column=1, pady=5, padx=5)

    # Test 3: Spinbox without master
    ttk.Label(frame, text="Spinbox (no master):").grid(row=2, column=0, sticky=tk.W, pady=5)
    spin1 = ttk.Spinbox(frame, from_=0, to=1000, textvariable=var2_no_master, width=10)
    spin1.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)

    # Test 4: Spinbox with master
    ttk.Label(frame, text="Spinbox (with master):").grid(row=3, column=0, sticky=tk.W, pady=5)
    spin2 = ttk.Spinbox(frame, from_=0, to=1000, textvariable=var2_with_master, width=10)
    spin2.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)

    # Debug: Print variable values
    print(f"\nVariable values after creation:")
    print(f"  var1_no_master: '{var1_no_master.get()}'")
    print(f"  var1_with_master: '{var1_with_master.get()}'")
    print(f"  var2_no_master: {var2_no_master.get()}")
    print(f"  var2_with_master: {var2_with_master.get()}")

    # Add quit button
    quit_btn = ttk.Button(frame, text="Quit", command=window.quit)
    quit_btn.grid(row=4, column=0, columnspan=2, pady=20)

    print("\nWindow created. Check if all fields are populated correctly.")
    print("Close the window to continue...\n")

    window.mainloop()
    window.destroy()

    print("Test completed!")


if __name__ == "__main__":
    test_minimal_gui()
