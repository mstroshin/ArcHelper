"""Overlay UI module for displaying item information."""

import tkinter as tk
from tkinter import ttk
import threading
import queue
from src.config import OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_ALPHA, DEFAULT_LANGUAGE

try:
    import win32api
    import win32con
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class OverlayUI:
    """Manages the overlay window for displaying item information using Tkinter."""

    def __init__(self, database, language=DEFAULT_LANGUAGE):
        """
        Initialize the overlay UI.

        Args:
            database: ItemDatabase instance
            language: Language code for item names/descriptions
        """
        self.database = database
        self.language = language
        self.root = None
        self.window = None
        self.auto_close_timer = None
        self._command_queue = queue.Queue()
        self._running = False
        self._gui_thread = None

        # Start the GUI thread
        self._start_gui_thread()

    def _start_gui_thread(self):
        """Start the dedicated GUI thread with event loop."""
        def gui_loop():
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the root window
            self._running = True

            # Process commands from queue
            def process_queue():
                try:
                    while not self._command_queue.empty():
                        command, args = self._command_queue.get_nowait()
                        if command == 'show':
                            self._create_overlay(*args)
                        elif command == 'close':
                            self._close_window()
                        elif command == 'quit':
                            self._running = False
                            self.root.quit()
                            return
                except queue.Empty:
                    pass

                if self._running:
                    self.root.after(100, process_queue)

            process_queue()
            self.root.mainloop()

        self._gui_thread = threading.Thread(target=gui_loop, daemon=True)
        self._gui_thread.start()

        # Wait for GUI thread to initialize
        import time
        while self.root is None:
            time.sleep(0.01)

    def show(self, item_data, duration=10):
        """
        Show the overlay with item information.
        This method is thread-safe and can be called from any thread.

        Args:
            item_data: Item data dictionary to display
            duration: Time in seconds before auto-close (0 = no auto-close)
        """
        self._command_queue.put(('show', (item_data, duration)))

    def _close_window(self):
        """Close the current overlay window."""
        if self.window:
            try:
                if self.auto_close_timer:
                    self.root.after_cancel(self.auto_close_timer)
                    self.auto_close_timer = None
                self.window.destroy()
            except:
                pass
            self.window = None

    def _create_overlay(self, item_data, duration):
        """Create and display the overlay window."""
        # Close existing window if any
        self._close_window()

        # Create the window as Toplevel (not a new Tk instance)
        self.window = tk.Toplevel(self.root)
        self.window.title("ArcHelper - Item Info")

        # Window configuration
        self.window.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")
        self.window.attributes('-topmost', True)  # Always on top
        self.window.attributes('-alpha', OVERLAY_ALPHA)  # Transparency

        # Try to make it tool window style (no taskbar icon)
        try:
            self.window.attributes('-toolwindow', True)
        except:
            pass

        # Position near cursor
        self._position_near_cursor()

        # Create scrollable content
        self._create_content(item_data)

        # Bind close events
        self.window.bind('<Escape>', lambda e: self._close_window())
        self.window.bind('<Button-1>', lambda e: self._close_window())  # Close on click

        # Auto-close timer
        if duration > 0:
            self.auto_close_timer = self.root.after(duration * 1000, self._close_window)

    def _position_near_cursor(self):
        """Position the window near the cursor."""
        if WIN32_AVAILABLE:
            try:
                cursor_x, cursor_y = win32api.GetCursorPos()
                # Offset the window slightly from cursor
                x = cursor_x + 20
                y = cursor_y + 20

                # Ensure window stays on screen
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()

                if x + OVERLAY_WIDTH > screen_width:
                    x = screen_width - OVERLAY_WIDTH - 10

                if y + OVERLAY_HEIGHT > screen_height:
                    y = screen_height - OVERLAY_HEIGHT - 10

                self.window.geometry(f"+{x}+{y}")
            except Exception as e:
                print(f"Error positioning window: {e}")

    def _create_content(self, item_data):
        """Create the content for the overlay window."""

        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollable canvas
        canvas = tk.Canvas(main_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add content to scrollable frame
        self._add_item_info(scrollable_frame, item_data)

        # Pack scrollbar and canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_item_info(self, parent, item_data):
        """Add item information to the frame."""

        # Item name
        name = item_data.get('name', {}).get(self.language, item_data.get('id', 'Unknown'))
        name_label = tk.Label(parent, text=name, font=('Arial', 14, 'bold'),
                             fg='#FFD700', bg='#2b2b2b', wraplength=OVERLAY_WIDTH-40)
        name_label.pack(anchor='w', pady=(0, 5))

        # Item type and rarity
        item_type = item_data.get('type', 'N/A')
        rarity = item_data.get('rarity', 'N/A')

        info_text = f"Type: {item_type} | Rarity: {rarity}"
        info_label = tk.Label(parent, text=info_text, font=('Arial', 9),
                             fg='#CCCCCC', bg='#2b2b2b')
        info_label.pack(anchor='w', pady=(0, 10))

        # Separator
        separator = tk.Frame(parent, height=2, bg='#555555')
        separator.pack(fill='x', pady=5)

        # Description
        description = item_data.get('description', {}).get(self.language, '')
        if description:
            desc_label = tk.Label(parent, text=description, font=('Arial', 9),
                                 fg='#FFFFFF', bg='#2b2b2b', wraplength=OVERLAY_WIDTH-40,
                                 justify='left')
            desc_label.pack(anchor='w', pady=(0, 10))

        # Properties (weight, stack size, value)
        properties = []
        if 'weightKg' in item_data:
            properties.append(f"Weight: {item_data['weightKg']} kg")
        if 'stackSize' in item_data:
            properties.append(f"Stack: {item_data['stackSize']}")
        if 'value' in item_data:
            properties.append(f"Value: {item_data['value']}")

        if properties:
            prop_text = " | ".join(properties)
            prop_label = tk.Label(parent, text=prop_text, font=('Arial', 9),
                                 fg='#AAAAAA', bg='#2b2b2b')
            prop_label.pack(anchor='w', pady=(0, 10))

        # Crafting recipe
        if 'recipe' in item_data:
            self._add_section(parent, "Crafting Recipe:", item_data['recipe'])

            if 'craftBench' in item_data:
                bench_label = tk.Label(parent, text=f"Craft Bench: {item_data['craftBench']}",
                                      font=('Arial', 9), fg='#88CCFF', bg='#2b2b2b')
                bench_label.pack(anchor='w', pady=(0, 10))

        # Recycles into
        if 'recyclesInto' in item_data:
            self._add_section(parent, "Recycles Into:", item_data['recyclesInto'])

        # Salvages into
        if 'salvagesInto' in item_data:
            self._add_section(parent, "Salvages Into:", item_data['salvagesInto'])

        # Used to craft (reverse mapping)
        items_using = self.database.get_items_using_material(item_data['id'])
        if items_using:
            self._add_section_header(parent, f"Used to Craft ({len(items_using)} items):")
            for used_item in items_using[:5]:  # Show first 5
                used_name = used_item.get('name', {}).get(self.language, used_item['id'])
                amount = used_item.get('recipe', {}).get(item_data['id'], 0)
                item_label = tk.Label(parent, text=f"  • {used_name} (x{amount})",
                                     font=('Arial', 9), fg='#FFFFFF', bg='#2b2b2b')
                item_label.pack(anchor='w')

            if len(items_using) > 5:
                more_label = tk.Label(parent, text=f"  ... and {len(items_using) - 5} more",
                                     font=('Arial', 9, 'italic'), fg='#888888', bg='#2b2b2b')
                more_label.pack(anchor='w', pady=(0, 10))

        # Close instructions
        close_label = tk.Label(parent, text="\nPress ESC or click to close",
                              font=('Arial', 8, 'italic'), fg='#666666', bg='#2b2b2b')
        close_label.pack(pady=(10, 0))

    def _add_section_header(self, parent, title):
        """Add a section header."""
        header = tk.Label(parent, text=title, font=('Arial', 10, 'bold'),
                         fg='#88FF88', bg='#2b2b2b')
        header.pack(anchor='w', pady=(10, 5))

    def _add_section(self, parent, title, materials_dict):
        """Add a materials section."""
        self._add_section_header(parent, title)

        for material_id, amount in materials_dict.items():
            material_item = self.database.get_item(material_id)
            material_name = material_item.get('name', {}).get(self.language, material_id) if material_item else material_id

            material_label = tk.Label(parent, text=f"  • {material_name} x{amount}",
                                     font=('Arial', 9), fg='#FFFFFF', bg='#2b2b2b')
            material_label.pack(anchor='w')

    def cleanup(self):
        """Cleanup overlay resources."""
        self._command_queue.put(('quit', ()))
        if self._gui_thread and self._gui_thread.is_alive():
            self._gui_thread.join(timeout=2)
