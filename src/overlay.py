"""Overlay UI module for displaying item information."""

import tkinter as tk
from tkinter import ttk
import threading
import queue
from src.config import OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_ALPHA, DEFAULT_LANGUAGE
from src.localization import get_text

# Color schemes for different rarities
RARITY_COLORS = {
    'common': '#9D9D9D',
    'uncommon': '#1EFF00',
    'rare': '#0070DD',
    'epic': '#A335EE',
    'legendary': '#FF8000',
    'mythic': '#E6CC80',
    'default': '#FFFFFF'
}

# Modern color palette
COLORS = {
    'bg_dark': '#1a1a1a',
    'bg_medium': '#2d2d2d',
    'bg_light': '#3d3d3d',
    'accent': '#00d4ff',
    'accent_dim': '#0099cc',
    'text_primary': '#ffffff',
    'text_secondary': '#b8b8b8',
    'text_tertiary': '#808080',
    'success': '#00ff88',
    'warning': '#ffaa00',
    'border': '#4d4d4d',
    'shadow': '#000000'
}

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

    def show(self, item_data, duration=0):
        """
        Show the overlay with item information.
        This method is thread-safe and can be called from any thread.

        Args:
            item_data: Item data dictionary to display
            duration: Time in seconds before auto-close (0 = no auto-close, default)
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

    def _create_overlay(self, item_data, _duration):
        """Create and display the overlay window."""
        # Close existing window if any
        self._close_window()

        # Create the window as Toplevel (not a new Tk instance)
        self.window = tk.Toplevel(self.root)
        self.window.title("ArcHelper")

        # Window configuration
        self.window.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")
        self.window.attributes('-topmost', True)  # Always on top
        self.window.attributes('-alpha', OVERLAY_ALPHA)  # Transparency
        self.window.configure(bg=COLORS['bg_dark'])

        # Try to make it tool window style (no taskbar icon)
        try:
            self.window.attributes('-toolwindow', True)
        except:
            pass

        # Remove window decorations for modern look
        self.window.overrideredirect(True)

        # Position near cursor
        self._position_near_cursor()

        # Create scrollable content
        self._create_content(item_data)

        # Bind close events
        self.window.bind('<Escape>', lambda e: self._close_window())

        # Setup click-outside detection
        if WIN32_AVAILABLE:
            self._setup_click_outside_detection()

    def _setup_click_outside_detection(self):
        """Setup detection for clicks outside the window."""
        def check_click_outside():
            if not self.window:
                return

            try:
                # Get current cursor position
                cursor_x, cursor_y = win32api.GetCursorPos()

                # Get window position and size
                win_x = self.window.winfo_x()
                win_y = self.window.winfo_y()
                win_width = self.window.winfo_width()
                win_height = self.window.winfo_height()

                # Check if left mouse button is pressed
                left_button_state = win32api.GetAsyncKeyState(win32con.VK_LBUTTON)

                # If button is pressed and cursor is outside window bounds
                if left_button_state & 0x8000:  # Button is currently pressed
                    if not (win_x <= cursor_x <= win_x + win_width and
                           win_y <= cursor_y <= win_y + win_height):
                        self._close_window()
                        return

                # Continue checking
                if self.window:
                    self.window.after(50, check_click_outside)

            except Exception:
                pass

        # Start checking after a short delay
        self.window.after(100, check_click_outside)

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

        # Border frame for modern look
        border_frame = tk.Frame(self.window, bg=COLORS['accent'], bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Main container
        container = tk.Frame(border_frame, bg=COLORS['bg_dark'], bd=0)
        container.pack(fill=tk.BOTH, expand=True)

        # Header with close button
        header = tk.Frame(container, bg=COLORS['bg_medium'], height=40)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        title_label = tk.Label(header, text=get_text(self.language, 'app_title'), font=('Segoe UI', 13, 'bold'),
                              fg=COLORS['accent'], bg=COLORS['bg_medium'])
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        close_btn = tk.Label(header, text="✕", font=('Arial', 17, 'bold'),
                            fg=COLORS['text_secondary'], bg=COLORS['bg_medium'],
                            cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        close_btn.bind('<Button-1>', lambda e: self._close_window())

        # Main content frame with padding
        main_frame = tk.Frame(container, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Create scrollable canvas with modern styling
        canvas = tk.Canvas(main_frame, bg=COLORS['bg_dark'], highlightthickness=0, bd=0)

        # Custom styled scrollbar
        scrollbar_frame = tk.Frame(main_frame, bg=COLORS['bg_medium'], width=8)
        scrollbar_canvas = tk.Canvas(scrollbar_frame, bg=COLORS['bg_medium'],
                                     highlightthickness=0, width=8)

        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Update scrollbar
            update_scrollbar()

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            update_scrollbar()

        def update_scrollbar():
            # Custom scrollbar drawing
            scrollbar_canvas.delete("all")
            if canvas.winfo_height() > 0:
                view = canvas.yview()
                total_height = scrollbar_canvas.winfo_height()
                bar_height = max(20, total_height * (view[1] - view[0]))
                bar_y = total_height * view[0]

                scrollbar_canvas.create_rectangle(1, bar_y, 7, bar_y + bar_height,
                                                  fill=COLORS['accent_dim'], outline='')

        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Add content to scrollable frame
        self._add_item_info(scrollable_frame, item_data)

        # Pack components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_frame.pack(side="right", fill="y")
        scrollbar_canvas.pack(fill="both", expand=True)

        self.window.after(100, update_scrollbar)

    def _add_item_info(self, parent, item_data):
        """Add item information to the frame."""

        # Content padding
        content = tk.Frame(parent, bg=COLORS['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Get rarity color
        rarity = item_data.get('rarity', 'common').lower()
        rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['default'])

        # Item name with rarity color
        name = item_data.get('name', {}).get(self.language, item_data.get('id', 'Unknown'))
        name_label = tk.Label(content, text=name, font=('Segoe UI', 19, 'bold'),
                             fg=rarity_color, bg=COLORS['bg_dark'],
                             wraplength=OVERLAY_WIDTH-60, justify='left')
        name_label.pack(anchor='w', pady=(0, 8))

        # Item type and rarity badge
        info_frame = tk.Frame(content, bg=COLORS['bg_dark'])
        info_frame.pack(anchor='w', pady=(0, 12))

        item_type = item_data.get('type', 'N/A')

        # Rarity badge
        rarity_badge = tk.Label(info_frame, text=rarity.upper(), font=('Segoe UI', 11, 'bold'),
                               fg=COLORS['bg_dark'], bg=rarity_color,
                               padx=8, pady=2)
        rarity_badge.pack(side=tk.LEFT, padx=(0, 8))

        # Type label
        type_label = tk.Label(info_frame, text=item_type, font=('Segoe UI', 12),
                             fg=COLORS['text_secondary'], bg=COLORS['bg_dark'])
        type_label.pack(side=tk.LEFT)

        # Description card
        description = item_data.get('description', {}).get(self.language, '')
        if description:
            self._add_card(content, description, COLORS['text_secondary'], italic=True)

        # Properties card
        properties = []
        if 'weightKg' in item_data:
            properties.append(('⚖', f"{item_data['weightKg']} {get_text(self.language, 'weight')}"))
        if 'stackSize' in item_data:
            properties.append(('📦', f"{get_text(self.language, 'stack')}: {item_data['stackSize']}"))
        if 'value' in item_data:
            properties.append(('💰', f"{item_data['value']} {get_text(self.language, 'credits')}"))

        if properties:
            prop_frame = self._create_card_frame(content)
            for icon, text in properties:
                prop_row = tk.Frame(prop_frame, bg=COLORS['bg_medium'])
                prop_row.pack(fill=tk.X, pady=2)

                icon_label = tk.Label(prop_row, text=icon, font=('Segoe UI', 13),
                                     fg=COLORS['accent'], bg=COLORS['bg_medium'])
                icon_label.pack(side=tk.LEFT, padx=(0, 8))

                text_label = tk.Label(prop_row, text=text, font=('Segoe UI', 12),
                                     fg=COLORS['text_primary'], bg=COLORS['bg_medium'])
                text_label.pack(side=tk.LEFT)

        # Crafting recipe
        if 'recipe' in item_data:
            self._add_material_section(content, get_text(self.language, 'crafting_recipe'), item_data['recipe'],
                                      COLORS['warning'])

            if 'craftBench' in item_data:
                bench_frame = tk.Frame(content, bg=COLORS['bg_light'], bd=0)
                bench_frame.pack(fill=tk.X, pady=(0, 12), padx=0)

                bench_label = tk.Label(bench_frame, text=f"📍 {get_text(self.language, 'requires')}: {item_data['craftBench']}",
                                      font=('Segoe UI', 12), fg=COLORS['accent'],
                                      bg=COLORS['bg_light'], padx=12, pady=6)
                bench_label.pack(anchor='w')

        # Recycles into
        if 'recyclesInto' in item_data:
            self._add_material_section(content, get_text(self.language, 'recycles_into'), item_data['recyclesInto'],
                                      COLORS['success'])

        # Salvages into
        if 'salvagesInto' in item_data:
            self._add_material_section(content, get_text(self.language, 'salvages_into'), item_data['salvagesInto'],
                                      COLORS['success'])

        # Used to craft (reverse mapping)
        items_using = self.database.get_items_using_material(item_data['id'])
        if items_using:
            self._add_crafting_uses_section(content, items_using)

        # Close instructions
        close_label = tk.Label(content, text=get_text(self.language, 'close_instruction'),
                              font=('Segoe UI', 11), fg=COLORS['text_tertiary'],
                              bg=COLORS['bg_dark'])
        close_label.pack(pady=(15, 5))

    def _create_card_frame(self, parent):
        """Create a card-style frame."""
        card = tk.Frame(parent, bg=COLORS['bg_medium'], bd=0)
        card.pack(fill=tk.X, pady=(0, 12), padx=0)

        inner = tk.Frame(card, bg=COLORS['bg_medium'])
        inner.pack(fill=tk.X, padx=12, pady=8)

        return inner

    def _add_card(self, parent, text, color, italic=False):
        """Add a card with text."""
        card = self._create_card_frame(parent)

        font_style = ('Segoe UI', 12, 'italic') if italic else ('Segoe UI', 12)
        label = tk.Label(card, text=text, font=font_style,
                        fg=color, bg=COLORS['bg_medium'],
                        wraplength=OVERLAY_WIDTH-70, justify='left')
        label.pack(anchor='w')

    def _add_material_section(self, parent, title, materials_dict, accent_color):
        """Add a materials section with modern styling."""
        # Section header
        header_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 8))

        header = tk.Label(header_frame, text=title, font=('Segoe UI', 14, 'bold'),
                         fg=accent_color, bg=COLORS['bg_dark'])
        header.pack(anchor='w')

        # Materials card
        card = self._create_card_frame(parent)

        for material_id, amount in materials_dict.items():
            material_item = self.database.get_item(material_id)
            material_name = material_item.get('name', {}).get(self.language, material_id) if material_item else material_id

            # Material row
            mat_row = tk.Frame(card, bg=COLORS['bg_medium'])
            mat_row.pack(fill=tk.X, pady=3)

            # Bullet point
            bullet = tk.Label(mat_row, text="●", font=('Segoe UI', 11),
                            fg=accent_color, bg=COLORS['bg_medium'])
            bullet.pack(side=tk.LEFT, padx=(0, 8))

            # Material name
            name_label = tk.Label(mat_row, text=material_name, font=('Segoe UI', 12),
                                 fg=COLORS['text_primary'], bg=COLORS['bg_medium'])
            name_label.pack(side=tk.LEFT)

            # Amount badge
            amount_badge = tk.Label(mat_row, text=f"x{amount}", font=('Segoe UI', 11, 'bold'),
                                   fg=COLORS['bg_dark'], bg=accent_color,
                                   padx=6, pady=1)
            amount_badge.pack(side=tk.RIGHT)

    def _add_crafting_uses_section(self, parent, items_using):
        """Add 'Used to Craft' section."""
        # Section header
        header_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 8))

        header_text = get_text(self.language, 'used_to_craft_count', count=len(items_using))
        header = tk.Label(header_frame, text=header_text, font=('Segoe UI', 14, 'bold'),
                         fg=COLORS['accent'], bg=COLORS['bg_dark'])
        header.pack(anchor='w')

        # Items card
        card = self._create_card_frame(parent)

        # Show first 5 items
        for used_item in items_using[:5]:
            used_name = used_item.get('name', {}).get(self.language, used_item['id'])
            amount = used_item.get('recipe', {}).get(used_item.get('id'), 0)

            # Item row
            item_row = tk.Frame(card, bg=COLORS['bg_medium'])
            item_row.pack(fill=tk.X, pady=3)

            # Arrow
            arrow = tk.Label(item_row, text="→", font=('Segoe UI', 13),
                           fg=COLORS['accent'], bg=COLORS['bg_medium'])
            arrow.pack(side=tk.LEFT, padx=(0, 8))

            # Item name
            name_label = tk.Label(item_row, text=used_name, font=('Segoe UI', 12),
                                 fg=COLORS['text_primary'], bg=COLORS['bg_medium'])
            name_label.pack(side=tk.LEFT)

        # Show "more" indicator if needed
        if len(items_using) > 5:
            more_frame = tk.Frame(card, bg=COLORS['bg_medium'])
            more_frame.pack(fill=tk.X, pady=(5, 0))

            more_label = tk.Label(more_frame, text=get_text(self.language, 'and_more', count=len(items_using) - 5),
                                 font=('Segoe UI', 11, 'italic'), fg=COLORS['text_tertiary'],
                                 bg=COLORS['bg_medium'])
            more_label.pack(anchor='w')

    def cleanup(self):
        """Cleanup overlay resources."""
        self._command_queue.put(('quit', ()))
        if self._gui_thread and self._gui_thread.is_alive():
            self._gui_thread.join(timeout=2)
