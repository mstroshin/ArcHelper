"""Overlay UI module for displaying item information."""

import tkinter as tk
from tkinter import ttk
import threading
import queue
import os
from functools import lru_cache
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
    """Manages overlay windows for displaying item information using Tkinter.

    Supports a primary overlay (opened via show) and additional spawned overlays
    created when clicking items/materials inside any overlay window.
    """

    def __init__(self, database, settings_manager=None, language=DEFAULT_LANGUAGE):
        """
        Initialize the overlay UI.

        Args:
            database: ItemDatabase instance
            settings_manager: SettingsManager instance for marking items
            language: Language code for item names/descriptions
        """
        self.database = database
        self.settings_manager = settings_manager
        self.language = language
        self.root = None
        # Primary window (opened via show)
        self.window = None
        # Additional spawned windows
        self._spawned_windows = []
        self.auto_close_timer = None
        self._command_queue = queue.Queue()
        self._running = False
        self._gui_thread = None
        self._outside_detection_started = False
        # Image cache to avoid reloading from disk
        self._image_cache = {}
        # Flag to suppress outside-click mass close when explicitly clicking a window's X
        self._suppress_outside_close = False
        # Optional callback invoked when the primary overlay window is closed manually
        self._close_callback = None

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
                            self._create_overlay(*args, close_existing=True)
                        elif command == 'loading':
                            # Close only the primary window (not spawned), then show loading
                            self._create_loading_overlay(close_existing=True)
                        elif command == 'error':
                            # args: (message,)
                            message = args[0]
                            self._create_error_overlay(message, close_existing=True)
                        elif command == 'spawn':
                            # args: (item_id,)
                            item_id = args[0]
                            item_data = self.database.get_item(item_id)
                            if item_data:
                                self._create_overlay(item_data, 0, close_existing=False)
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

    def show_loading(self):
        """Show an overlay immediately with a loading indicator while recognition runs."""
        self._command_queue.put(('loading', ()))

    def show_error(self, message: str):
        """Show an overlay with an error message after a failed recognition or missing data.

        Args:
            message: Error text to display in the overlay.
        """
        self._command_queue.put(('error', (message,)))

    def _close_window(self, invoke_callback=True):
        """Close the primary overlay window.

        Args:
            invoke_callback: If True, invokes the close callback (cancels recognition).
                           Set to False when replacing window programmatically.
        """
        if self.window:
            try:
                if self.auto_close_timer:
                    self.root.after_cancel(self.auto_close_timer)
                    self.auto_close_timer = None
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            # Invoke close callback (used to cancel recognition) only if requested
            if invoke_callback:
                try:
                    if self._close_callback:
                        self._close_callback()
                except Exception:
                    pass

    def _destroy_spawned(self, win):
        """Destroy a spawned window and remove it from tracking."""
        try:
            win.destroy()
        except Exception:
            pass
        self._spawned_windows = [w for w in self._spawned_windows if w != win]

    def _create_overlay(self, item_data, _duration, close_existing=True):
        """Create and display an overlay window.

        Args:
            item_data: item data dict
            _duration: (unused) reserved for future auto-close support
            close_existing: if True, replaces primary window; else spawns new window
        """
        if close_existing:
            # Don't invoke callback when replacing window programmatically
            self._close_window(invoke_callback=False)
            win = tk.Toplevel(self.root)
            self.window = win
        else:
            win = tk.Toplevel(self.root)
            self._spawned_windows.append(win)

        win.title("ArcHelper")
        win.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")
        win.attributes('-topmost', True)
        win.attributes('-alpha', OVERLAY_ALPHA)
        win.configure(bg=COLORS['bg_dark'])
        try:
            win.attributes('-toolwindow', True)
        except Exception:
            pass
        win.overrideredirect(True)

        self._position_near_cursor(win)
        self._create_content(win, item_data)

        # Close handlers
        if close_existing:
            win.bind('<Escape>', lambda e: self._close_window())
            win.protocol('WM_DELETE_WINDOW', self._close_window)
        else:
            win.bind('<Escape>', lambda e, w=win: self._destroy_spawned(w))
            win.protocol('WM_DELETE_WINDOW', lambda w=win: self._destroy_spawned(w))

        if WIN32_AVAILABLE:
            self._start_global_click_outside_detection()

    def _create_loading_overlay(self, close_existing=True):
        """Create and display a loading overlay while recognition processes."""
        if close_existing:
            # Don't invoke callback when replacing window programmatically
            self._close_window(invoke_callback=False)
            win = tk.Toplevel(self.root)
            self.window = win
        else:
            win = tk.Toplevel(self.root)
            self._spawned_windows.append(win)

        win.title("ArcHelper")
        win.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")
        win.attributes('-topmost', True)
        win.attributes('-alpha', OVERLAY_ALPHA)
        win.configure(bg=COLORS['bg_dark'])
        try:
            win.attributes('-toolwindow', True)
        except Exception:
            pass
        win.overrideredirect(True)

        self._position_near_cursor(win)

        border_frame = tk.Frame(win, bg=COLORS['accent'], bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        container = tk.Frame(border_frame, bg=COLORS['bg_dark'], bd=0)
        container.pack(fill=tk.BOTH, expand=True)
        header = tk.Frame(container, bg=COLORS['bg_medium'], height=40)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        title_label = tk.Label(header, text=get_text(self.language, 'app_title'), font=('Segoe UI', 13, 'bold'),
                               fg=COLORS['accent'], bg=COLORS['bg_medium'])
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        self._make_draggable(win, header)
        close_btn = tk.Label(header, text="✕", font=('Arial', 17, 'bold'),
                             fg=COLORS['text_secondary'], bg=COLORS['bg_medium'],
                             cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        def on_close_click(event, w=win):
            self._suppress_outside_close = True
            if w == self.window:
                self._close_window()
            else:
                self._destroy_spawned(w)
        close_btn.bind('<Button-1>', on_close_click)

        main_frame = tk.Frame(container, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        loading_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        loading_frame.pack(expand=True)
        loading_label = tk.Label(loading_frame,
                                 text=get_text(self.language, 'recognizing'),
                                 font=('Segoe UI', 16, 'bold'),
                                 fg=COLORS['accent'], bg=COLORS['bg_dark'])
        loading_label.pack(pady=(40, 20))
        try:
            progress = ttk.Progressbar(loading_frame, mode='indeterminate', length=220)
            progress.pack(pady=10)
            progress.start(12)
        except Exception:
            pass
        hint = tk.Label(loading_frame, text=get_text(self.language, 'close_instruction'),
                        font=('Segoe UI', 11), fg=COLORS['text_tertiary'], bg=COLORS['bg_dark'])
        hint.pack(pady=(30, 10))

        if close_existing:
            win.bind('<Escape>', lambda e: self._close_window())
            win.protocol('WM_DELETE_WINDOW', self._close_window)
        else:
            win.bind('<Escape>', lambda e, w=win: self._destroy_spawned(w))
            win.protocol('WM_DELETE_WINDOW', lambda w=win: self._destroy_spawned(w))

        if WIN32_AVAILABLE:
            self._start_global_click_outside_detection()

    def _create_error_overlay(self, message: str, close_existing=True):
        """Create and display an error overlay after loader when something fails."""
        if close_existing:
            # Don't invoke callback when replacing window programmatically
            self._close_window(invoke_callback=False)
            win = tk.Toplevel(self.root)
            self.window = win
        else:
            win = tk.Toplevel(self.root)
            self._spawned_windows.append(win)

        win.title("ArcHelper")
        win.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")
        win.attributes('-topmost', True)
        win.attributes('-alpha', OVERLAY_ALPHA)
        win.configure(bg=COLORS['bg_dark'])
        try:
            win.attributes('-toolwindow', True)
        except Exception:
            pass
        win.overrideredirect(True)

        self._position_near_cursor(win)

        border_frame = tk.Frame(win, bg=COLORS['warning'], bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        container = tk.Frame(border_frame, bg=COLORS['bg_dark'], bd=0)
        container.pack(fill=tk.BOTH, expand=True)
        header = tk.Frame(container, bg=COLORS['bg_medium'], height=40)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        title_label = tk.Label(header, text=get_text(self.language, 'app_title'), font=('Segoe UI', 13, 'bold'),
                               fg=COLORS['warning'], bg=COLORS['bg_medium'])
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        self._make_draggable(win, header)
        close_btn = tk.Label(header, text="✕", font=('Arial', 17, 'bold'),
                             fg=COLORS['text_secondary'], bg=COLORS['bg_medium'],
                             cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        def on_close_click(event, w=win):
            self._suppress_outside_close = True
            if w == self.window:
                self._close_window()
            else:
                self._destroy_spawned(w)
        close_btn.bind('<Button-1>', on_close_click)

        main_frame = tk.Frame(container, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        error_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        error_frame.pack(expand=True)
        error_label = tk.Label(error_frame,
                                text=message,
                                font=('Segoe UI', 15, 'bold'),
                                fg=COLORS['warning'], bg=COLORS['bg_dark'],
                                wraplength=OVERLAY_WIDTH-60, justify='left')
        error_label.pack(pady=(40, 20))
        hint = tk.Label(error_frame, text=get_text(self.language, 'close_instruction'),
                        font=('Segoe UI', 11), fg=COLORS['text_tertiary'], bg=COLORS['bg_dark'])
        hint.pack(pady=(10, 10))

        if close_existing:
            win.bind('<Escape>', lambda e: self._close_window())
            win.protocol('WM_DELETE_WINDOW', self._close_window)
        else:
            win.bind('<Escape>', lambda e, w=win: self._destroy_spawned(w))
            win.protocol('WM_DELETE_WINDOW', lambda w=win: self._destroy_spawned(w))

        if WIN32_AVAILABLE:
            self._start_global_click_outside_detection()

    def _get_all_windows(self):
        """Return list of all current overlay windows."""
        return [w for w in ([self.window] + self._spawned_windows) if w]

    def _close_all_windows(self):
        """Close all overlay windows (primary and spawned)."""
        self._close_window()
        for w in list(self._spawned_windows):
            self._destroy_spawned(w)

    def _start_global_click_outside_detection(self):
        """Start a single detector that closes all overlays when clicking outside every window."""
        if self._outside_detection_started:
            return
        self._outside_detection_started = True

        def check():
            if not self._get_all_windows():
                self._outside_detection_started = False
                return
            try:
                # Skip one iteration if we purposely clicked a close button
                if self._suppress_outside_close:
                    self._suppress_outside_close = False
                else:
                    cursor_x, cursor_y = win32api.GetCursorPos()
                    left_state = win32api.GetAsyncKeyState(win32con.VK_LBUTTON)
                    if left_state & 0x8000:
                        inside_any = False
                        for w in self._get_all_windows():
                            try:
                                wx = w.winfo_x(); wy = w.winfo_y(); ww = w.winfo_width(); wh = w.winfo_height()
                                if wx <= cursor_x <= wx + ww and wy <= cursor_y <= wy + wh:
                                    inside_any = True
                                    break
                            except Exception:
                                pass
                        if not inside_any:
                            self._close_all_windows()
                            self._outside_detection_started = False
                            return
            except Exception:
                pass
            # Continue polling
            self.root.after(50, check)

        self.root.after(100, check)

    def _position_near_cursor(self, win):
        """Position a window near the cursor."""
        if WIN32_AVAILABLE:
            try:
                cursor_x, cursor_y = win32api.GetCursorPos()
                x = cursor_x + 20
                y = cursor_y + 20
                screen_width = win.winfo_screenwidth()
                screen_height = win.winfo_screenheight()
                if x + OVERLAY_WIDTH > screen_width:
                    x = screen_width - OVERLAY_WIDTH - 10
                if y + OVERLAY_HEIGHT > screen_height:
                    y = screen_height - OVERLAY_HEIGHT - 10
                win.geometry(f"+{x}+{y}")
            except Exception:
                pass

    def _create_content(self, win, item_data):
        """Create the content for a given overlay window."""
        border_frame = tk.Frame(win, bg=COLORS['accent'], bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        container = tk.Frame(border_frame, bg=COLORS['bg_dark'], bd=0)
        container.pack(fill=tk.BOTH, expand=True)
        header = tk.Frame(container, bg=COLORS['bg_medium'], height=40)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        title_label = tk.Label(header, text=get_text(self.language, 'app_title'), font=('Segoe UI', 13, 'bold'),
                               fg=COLORS['accent'], bg=COLORS['bg_medium'])
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        # Make window draggable by header
        self._make_draggable(win, header)

        # Close button chooses correct close behavior
        close_btn = tk.Label(header, text="✕", font=('Arial', 17, 'bold'),
                             fg=COLORS['text_secondary'], bg=COLORS['bg_medium'],
                             cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        def on_close_click(event, w=win):
            # Prevent outside click detector from treating this as outside all windows
            self._suppress_outside_close = True
            if w == self.window:
                self._close_window()
            else:
                self._destroy_spawned(w)
        close_btn.bind('<Button-1>', on_close_click)

        main_frame = tk.Frame(container, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        canvas = tk.Canvas(main_frame, bg=COLORS['bg_dark'], highlightthickness=0, bd=0)
        scrollbar_frame = tk.Frame(main_frame, bg=COLORS['bg_medium'], width=8)
        scrollbar_canvas = tk.Canvas(scrollbar_frame, bg=COLORS['bg_medium'], highlightthickness=0, width=8)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            update_scrollbar()
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            update_scrollbar()
        def update_scrollbar():
            scrollbar_canvas.delete("all")
            if canvas.winfo_height() > 0:
                view = canvas.yview()
                total_height = scrollbar_canvas.winfo_height()
                bar_height = max(20, total_height * (view[1] - view[0]))
                bar_y = total_height * view[0]
                scrollbar_canvas.create_rectangle(1, bar_y, 7, bar_y + bar_height,
                                                  fill=COLORS['accent_dim'], outline='')
        scrollable_frame.bind("<Configure>", on_frame_configure)
        # Bind mouse wheel to all relevant widgets within this overlay so scrolling works regardless of focus.
        # Each overlay gets its own closure with its canvas reference.
        for _w in (win, border_frame, container, main_frame, canvas, scrollable_frame, scrollbar_frame):
            try:
                _w.bind("<MouseWheel>", on_mousewheel)
            except Exception:
                pass
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self._add_item_info(scrollable_frame, item_data)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_frame.pack(side="right", fill="y")
        scrollbar_canvas.pack(fill="both", expand=True)
        win.after(100, update_scrollbar)

    def _add_item_info(self, parent, item_data):
        """Add item information to the frame."""

        # Content padding
        content = tk.Frame(parent, bg=COLORS['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Get rarity color
        rarity = item_data.get('rarity', 'common').lower()
        rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['default'])

        # Item name with checkbox on the right
        name_row = tk.Frame(content, bg=COLORS['bg_dark'])
        name_row.pack(fill=tk.X, anchor='w', pady=(0, 8))

        # Item name with rarity color
        name = item_data.get('name', {}).get(self.language, item_data.get('id', 'Unknown'))
        name_label = tk.Label(name_row, text=name, font=('Segoe UI', 19, 'bold'),
                             fg=rarity_color, bg=COLORS['bg_dark'],
                             wraplength=OVERLAY_WIDTH-150, justify='left')
        name_label.pack(side=tk.LEFT, anchor='w')

        # Checkbox for marking items (if settings_manager is available) - right of name
        if self.settings_manager and item_data:
            item_id = item_data.get('id')
            is_marked = self.settings_manager.is_item_marked(item_id)

            # Create checkbox frame
            checkbox_frame = tk.Frame(name_row, bg=COLORS['bg_dark'], cursor='hand2')
            checkbox_frame.pack(side=tk.RIGHT, padx=(10, 0))

            # Checkbox label (visual indicator)
            checkbox_label = tk.Label(checkbox_frame,
                                     text="✓" if is_marked else "☐",
                                     font=('Arial', 16, 'bold'),
                                     fg=COLORS['success'] if is_marked else COLORS['text_tertiary'],
                                     bg=COLORS['bg_dark'],
                                     cursor='hand2')
            checkbox_label.pack(side=tk.LEFT, padx=(0, 6))

            # Text label "Ищу"
            text_label = tk.Label(checkbox_frame,
                                 text="Ищу",
                                 font=('Segoe UI', 12),
                                 fg=COLORS['text_secondary'],
                                 bg=COLORS['bg_dark'],
                                 cursor='hand2')
            text_label.pack(side=tk.LEFT)

            # Toggle function
            def toggle_mark(event=None):
                nonlocal is_marked
                if self.settings_manager.is_item_marked(item_id):
                    self.settings_manager.unmark_item(item_id)
                    is_marked = False
                    checkbox_label.config(text="☐", fg=COLORS['text_tertiary'])
                else:
                    self.settings_manager.mark_item(item_id)
                    is_marked = True
                    checkbox_label.config(text="✓", fg=COLORS['success'])
                # Save settings immediately
                self.settings_manager.save()

            # Bind click to all elements
            checkbox_frame.bind('<Button-1>', toggle_mark)
            checkbox_label.bind('<Button-1>', toggle_mark)
            text_label.bind('<Button-1>', toggle_mark)

        # Item image (if available)
        img = self._load_item_image(item_data.get('id'))
        if img:
            img_label = tk.Label(content, image=img, bg=COLORS['bg_dark'])
            img_label.image = img  # keep reference
            img_label.pack(anchor='w', pady=(0, 12))
        else:
            # Optional subtle placeholder if no image found
            placeholder = tk.Label(content, text='[no image]', font=('Segoe UI', 10, 'italic'),
                                   fg=COLORS['text_tertiary'], bg=COLORS['bg_dark'])
            placeholder.pack(anchor='w', pady=(0, 12))

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
        # (Description removed per request)

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

        # Recycles into (skip if empty) - MOVED UP for better visibility
        if 'recyclesInto' in item_data and item_data['recyclesInto'] and len(item_data['recyclesInto']) > 0:
            self._add_material_section(content, get_text(self.language, 'recycles_into'), item_data['recyclesInto'],
                                      COLORS['success'])

        # Salvages into (skip if empty) - MOVED UP for better visibility
        if 'salvagesInto' in item_data and item_data['salvagesInto'] and len(item_data['salvagesInto']) > 0:
            self._add_material_section(content, get_text(self.language, 'salvages_into'), item_data['salvagesInto'],
                                      COLORS['success'])

        # Crafting recipe (skip if empty dict or no entries > 0)
        if 'recipe' in item_data and item_data['recipe'] and len(item_data['recipe']) > 0:
            self._add_material_section(content, get_text(self.language, 'crafting_recipe'), item_data['recipe'],
                                      COLORS['warning'])

        # Used to craft (reverse mapping)
        items_using = self.database.get_items_using_material(item_data['id'])
        if items_using:
            self._add_crafting_uses_section(content, items_using)

        # Hideout usage (bench requirements)
        hideout_usage = self.database.get_hideout_usage(item_data['id']) if hasattr(self.database, 'get_hideout_usage') else []
        if hideout_usage:
            self._add_hideout_usage_section(content, hideout_usage)

        # Close instructions
        close_label = tk.Label(content, text=get_text(self.language, 'close_instruction'),
                              font=('Segoe UI', 11), fg=COLORS['text_tertiary'],
                              bg=COLORS['bg_dark'])
        close_label.pack(pady=(15, 5))

    def _get_contrasting_text_color(self, bg_hex):
        """Return a contrasting text color (dark or light) for the given background hex color."""
        try:
            hexv = bg_hex.lstrip('#')
            if len(hexv) != 6:
                return COLORS['text_primary']
            r = int(hexv[0:2], 16)
            g = int(hexv[2:4], 16)
            b = int(hexv[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            # If background is light, use dark text; else use light text
            return COLORS['bg_dark'] if luminance > 0.55 else COLORS['text_primary']
        except Exception:
            return COLORS['text_primary']

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
        # Skip entirely if materials_dict is falsy or has no entries
        if not materials_dict or len(materials_dict) == 0:
            return
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
            rarity = (material_item.get('rarity') if material_item else 'default') or 'default'
            rarity_color = RARITY_COLORS.get(rarity.lower(), RARITY_COLORS['default'])
            text_contrast = self._get_contrasting_text_color(rarity_color)

            # Material row
            mat_row = tk.Frame(card, bg=COLORS['bg_medium'], cursor='hand2')
            mat_row.pack(fill=tk.X, pady=3)

            # Bullet point colored by rarity
            bullet = tk.Label(mat_row, text="●", font=('Segoe UI', 11),
                              fg=rarity_color, bg=COLORS['bg_medium'])
            bullet.pack(side=tk.LEFT, padx=(0, 8))

            # Material name colored by rarity
            name_label = tk.Label(mat_row, text=material_name, font=('Segoe UI', 12, 'bold'),
                                   fg=rarity_color, bg=COLORS['bg_medium'])
            name_label.pack(side=tk.LEFT)

            # Amount badge uses rarity color background with contrasting text
            amount_badge = tk.Label(mat_row, text=f"x{amount}", font=('Segoe UI', 11, 'bold'),
                                     fg=text_contrast, bg=rarity_color,
                                     padx=6, pady=1)
            amount_badge.pack(side=tk.RIGHT)

            # Click binding to spawn new overlay if item exists
            if material_item:
                def _spawn(mid=material_id):
                    self._command_queue.put(('spawn', (mid,)))
                mat_row.bind('<Button-1>', lambda e, f=_spawn: f())
                bullet.bind('<Button-1>', lambda e, f=_spawn: f())
                name_label.bind('<Button-1>', lambda e, f=_spawn: f())
                amount_badge.bind('<Button-1>', lambda e, f=_spawn: f())

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
        # Show all items (scrollable container handles overflow)
        for used_item in items_using:
            used_name = used_item.get('name', {}).get(self.language, used_item['id'])
            rarity = (used_item.get('rarity') or 'default').lower()
            rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['default'])
            contrast = self._get_contrasting_text_color(rarity_color)

            # Item row
            item_row = tk.Frame(card, bg=COLORS['bg_medium'], cursor='hand2')
            item_row.pack(fill=tk.X, pady=3)

            # Arrow colored by rarity
            arrow = tk.Label(item_row, text="→", font=('Segoe UI', 13),
                             fg=rarity_color, bg=COLORS['bg_medium'])
            arrow.pack(side=tk.LEFT, padx=(0, 8))

            # Item name colored by rarity
            name_label = tk.Label(item_row, text=used_name, font=('Segoe UI', 12, 'bold'),
                                   fg=rarity_color, bg=COLORS['bg_medium'])
            name_label.pack(side=tk.LEFT)

            # Optional small rarity badge
            badge = tk.Label(item_row, text=rarity.upper(), font=('Segoe UI', 9, 'bold'),
                             fg=contrast, bg=rarity_color, padx=4, pady=1)
            badge.pack(side=tk.RIGHT, padx=(8, 0))

            def _spawn_used(iid=used_item['id']):
                self._command_queue.put(('spawn', (iid,)))
            # Bind clicks
            item_row.bind('<Button-1>', lambda e, f=_spawn_used: f())
            arrow.bind('<Button-1>', lambda e, f=_spawn_used: f())
            name_label.bind('<Button-1>', lambda e, f=_spawn_used: f())
            badge.bind('<Button-1>', lambda e, f=_spawn_used: f())

    def _add_hideout_usage_section(self, parent, usage_entries):
        """Add section showing in which hideout benches (levels) the item is required."""
        header_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 8))
        header_text = get_text(self.language, 'hideout_uses_count', count=len(usage_entries))
        header = tk.Label(header_frame, text=header_text, font=('Segoe UI', 14, 'bold'),
                          fg=COLORS['accent'], bg=COLORS['bg_dark'])
        header.pack(anchor='w')

        card = self._create_card_frame(parent)
        # Group by bench to make output cleaner
        by_bench = {}
        for entry in usage_entries:
            bench_id = entry.get('bench_id')
            by_bench.setdefault(bench_id, []).append(entry)

        for bench_id, entries in by_bench.items():
            bench = self.database.get_hideout_bench(bench_id) if hasattr(self.database, 'get_hideout_bench') else None
            bench_name = bench.get('name', {}).get(self.language, bench_id) if bench else bench_id
            # Bench header row
            bench_row = tk.Frame(card, bg=COLORS['bg_medium'])
            bench_row.pack(fill=tk.X, pady=(4,2))
            bench_label = tk.Label(bench_row, text=f"🏠 {bench_name}", font=('Segoe UI', 12, 'bold'),
                                   fg=COLORS['accent'], bg=COLORS['bg_medium'])
            bench_label.pack(side=tk.LEFT)
            # Individual level requirements
            for e in entries:
                lvl = e.get('level')
                qty = e.get('quantity')
                req_row = tk.Frame(card, bg=COLORS['bg_medium'])
                req_row.pack(fill=tk.X, pady=1)
                lvl_label = tk.Label(req_row, text=f"• L{lvl} x{qty}", font=('Segoe UI', 11),
                                     fg=COLORS['text_primary'], bg=COLORS['bg_medium'])
                lvl_label.pack(side=tk.LEFT, padx=(18,0))

    def _make_draggable(self, win, widget):
        """Enable dragging of a toplevel window using the given widget as handle."""
        def start(event):
            try:
                win._drag_start_x = event.x
                win._drag_start_y = event.y
            except Exception:
                pass
        def drag(event):
            try:
                x = win.winfo_x() + event.x - getattr(win, '_drag_start_x', 0)
                y = win.winfo_y() + event.y - getattr(win, '_drag_start_y', 0)
                win.geometry(f"+{x}+{y}")
            except Exception:
                pass
        widget.bind('<Button-1>', start)
        widget.bind('<B1-Motion>', drag)


    def cleanup(self):
        """Cleanup overlay resources."""
        self._command_queue.put(('quit', ()))
        if self._gui_thread and self._gui_thread.is_alive():
            self._gui_thread.join(timeout=2)
        # Ensure all spawned windows are closed
        for w in list(self._spawned_windows):
            self._destroy_spawned(w)
        if self.window:
            self._close_window()
        # Clear callback
        self._close_callback = None

    def _load_item_image(self, item_id):
        """Load and cache a PhotoImage for the given item id.

        Lookup order in Data/Items/Images/:
            <item_id>.webp  (preferred)
            <item_id>.png
            <item_id>.jpg

        WEBP requires Pillow. PNG/JPG fallback to Pillow; PNG may load via tk.PhotoImage.
        Images are thumbnailed to max 200x200 preserving aspect ratio.
        Returns PhotoImage or None if not found/failed.
        """
        if not item_id:
            return None
        # Normalize weapon IDs with roman numeral suffixes to _1 (image naming convention)
        normalized_id = self._normalize_image_id(item_id)
        # Return cached image if already loaded for original id
        if item_id in self._image_cache:
            return self._image_cache[item_id]
        # Also allow reuse if normalized id already cached
        if normalized_id in self._image_cache:
            self._image_cache[item_id] = self._image_cache[normalized_id]
            return self._image_cache[item_id]
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            images_dir = os.path.join(base_dir, 'Data', 'Items', 'Images')
            # Build candidate list using normalized id first (so roman variants resolve to *_1 files)
            candidates = [
                os.path.join(images_dir, f'{normalized_id}.webp'),
                os.path.join(images_dir, f'{normalized_id}.png'),
                os.path.join(images_dir, f'{normalized_id}.jpg'),
            ]
            img_path = next((p for p in candidates if os.path.isfile(p)), None)
            if not img_path:
                return None
            photo = None
            try:
                from PIL import Image, ImageTk  # type: ignore
                im = Image.open(img_path)
                # Resize to fit overlay nicely (max 200x200 preserving aspect)
                im.thumbnail((200, 200), Image.LANCZOS)
                photo = ImageTk.PhotoImage(im)
            except Exception:
                try:
                    # Fallback: direct PhotoImage (only works for GIF/PNG)
                    photo = tk.PhotoImage(file=img_path)
                except Exception:
                    photo = None
            if photo:
                # Cache under both original and normalized ids for fast future access
                self._image_cache[normalized_id] = photo
                self._image_cache[item_id] = photo
            return photo
        except Exception:
            return None

    def _normalize_image_id(self, item_id: str) -> str:
        """Normalize item id for image lookup.

        Weapons have JSON ids ending with _i, _ii, _iii, _iv but images dont use suffixes.
        """
        try:
            lower = item_id.lower()
            for suffix in ('_i', '_ii', '_iii', '_iv'):
                if lower.endswith(suffix):
                    # Strip the roman part and append _1
                    base = item_id[: -len(suffix)]
                    return base
        except Exception:
            pass
        return item_id

    # Public API ------------------------------------------------------------
    def set_close_callback(self, callback):
        """Set a callback invoked when the primary overlay window is closed.

        Args:
            callback: Callable or None. If None, removes existing callback.
        """
        self._close_callback = callback
