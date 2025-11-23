"""Settings GUI for ArcHelperPy."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Callable, Optional
from src.settings_manager import SettingsManager
from src.config import SUPPORTED_LANGUAGES
from src.localization import get_text


# Language display names
LANGUAGE_NAMES = {
    'en': 'English',
    'de': 'Deutsch (German)',
    'fr': 'Français (French)',
    'es': 'Español (Spanish)',
    'pt': 'Português (Portuguese)',
    'pl': 'Polski (Polish)',
    'no': 'Norsk (Norwegian)',
    'da': 'Dansk (Danish)',
    'it': 'Italiano (Italian)',
    'ru': 'Русский (Russian)',
    'ja': '日本語 (Japanese)',
    'zh-TW': '繁體中文 (Traditional Chinese)',
    'uk': 'Українська (Ukrainian)',
    'zh-CN': '简体中文 (Simplified Chinese)',
    'kr': '한국어 (Korean)',
    'tr': 'Türkçe (Turkish)',
    'hr': 'Hrvatski (Croatian)',
    'sr': 'Српски (Serbian)'
}


class SettingsGUI:
    """GUI window for application settings."""

    def __init__(self, settings_manager: SettingsManager, on_settings_changed: Optional[Callable] = None):
        """
        Initialize settings GUI.

        Args:
            settings_manager: SettingsManager instance
            on_settings_changed: Optional callback when settings are saved
        """
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        self.on_close_callback = None  # Callback when window is closed
        self.window = None
        self.is_open = False
        self.cancelled = False  # Track if user cancelled or saved
        self.language = settings_manager.get_language()  # Get current language for UI

    def show(self, blocking: bool = False):
        """
        Show the settings window.

        Args:
            blocking: If True, blocks until window is closed
        """
        if self.is_open:
            # Window already open, bring to front
            if self.window:
                self.window.lift()
                self.window.focus_force()
            return

        if blocking:
            # Create window directly in main thread (blocking)
            self._create_window()
        else:
            # Create window in a separate thread to avoid blocking
            # NOTE: Not using daemon=True because Tkinter windows need proper cleanup
            thread = threading.Thread(target=self._create_window, daemon=False)
            thread.start()

    def _create_window(self):
        """Create and display the settings window (runs in separate thread)."""
        try:
            self.is_open = True

            # Debug: Print settings values before creating window
            print(f"[DEBUG] Creating settings window with:")
            print(f"  Language: {self.settings_manager.get_language()}")
            print(f"  Capture size: {self.settings_manager.get_capture_size()}")
            print(f"  Hotkey: {self.settings_manager.get_recognition_hotkey()}")

            # Create main window
            self.window = tk.Tk()
            self.window.title(f"ArcHelperPy - {get_text(self.language, 'settings_title')}")
            self.window.geometry("700x450")
            self.window.resizable(False, False)

            # Keep window always on top
            self.window.attributes('-topmost', True)

            # Configure style
            style = ttk.Style()
            style.theme_use('clam')

            # Create main frame with padding
            main_frame = ttk.Frame(self.window, padding="20")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # Title
            title_label = ttk.Label(
                main_frame,
                text=get_text(self.language, 'settings_title'),
                font=('Arial', 16, 'bold')
            )
            title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

            # Language setting
            row = 1
            ttk.Label(main_frame, text=get_text(self.language, 'gui_language'), font=('Arial', 10)).grid(
                row=row, column=0, sticky=tk.W, pady=10
            )

            # Get current language and prepare display value
            current_lang = self.settings_manager.get_language()
            current_display = f"{current_lang} - {LANGUAGE_NAMES.get(current_lang, 'Unknown')}"
            print(f"[DEBUG] Setting language combo to: {current_display}")

            self.language_var = tk.StringVar(master=self.window, value=current_display)
            language_combo = ttk.Combobox(
                main_frame,
                textvariable=self.language_var,
                values=[f"{code} - {LANGUAGE_NAMES[code]}" for code in SUPPORTED_LANGUAGES],
                state='readonly',
                width=35
            )
            language_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))

            # Screenshot size setting
            row += 1
            ttk.Label(main_frame, text=get_text(self.language, 'screenshot_size'), font=('Arial', 10)).grid(
                row=row, column=0, sticky=tk.W, pady=10
            )

            size_frame = ttk.Frame(main_frame)
            size_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))

            current_width, current_height = self.settings_manager.get_capture_size()
            print(f"[DEBUG] Setting capture size to: {current_width}x{current_height}")

            ttk.Label(size_frame, text=get_text(self.language, 'width')).grid(row=0, column=0, sticky=tk.W)
            self.width_var = tk.IntVar(master=self.window, value=current_width)
            width_spinbox = ttk.Spinbox(
                size_frame,
                from_=50,
                to=500,
                textvariable=self.width_var,
                width=8
            )
            width_spinbox.grid(row=0, column=1, padx=5)

            ttk.Label(size_frame, text=get_text(self.language, 'height')).grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
            self.height_var = tk.IntVar(master=self.window, value=current_height)
            height_spinbox = ttk.Spinbox(
                size_frame,
                from_=50,
                to=500,
                textvariable=self.height_var,
                width=8
            )
            height_spinbox.grid(row=0, column=3, padx=5)

            ttk.Label(size_frame, text="px").grid(row=0, column=4, sticky=tk.W)

            # Recognition hotkey setting
            row += 1
            ttk.Label(main_frame, text=get_text(self.language, 'recognition_hotkey'), font=('Arial', 10)).grid(
                row=row, column=0, sticky=tk.W, pady=10
            )

            hotkey_frame = ttk.Frame(main_frame)
            hotkey_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))

            current_hotkey = self.settings_manager.get_recognition_hotkey()
            print(f"[DEBUG] Setting hotkey to: {current_hotkey}")
            self.hotkey_var = tk.StringVar(master=self.window, value=current_hotkey)
            self.hotkey_entry = ttk.Entry(
                hotkey_frame,
                textvariable=self.hotkey_var,
                width=20
            )
            self.hotkey_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

            # Recording state for hotkey capture
            self.recording_hotkey = False

            record_button = ttk.Button(
                hotkey_frame,
                text=get_text(self.language, 'record'),
                command=self._start_hotkey_recording,
                width=10
            )
            record_button.grid(row=0, column=1, padx=(10, 0))

            # Help text
            row += 1
            help_label = ttk.Label(
                main_frame,
                text=get_text(self.language, 'hotkey_help'),
                font=('Arial', 8),
                foreground='gray'
            )
            help_label.grid(row=row, column=0, columnspan=2, pady=(5, 20))

            # Buttons frame
            row += 1
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

            # Save button
            save_button = ttk.Button(
                button_frame,
                text=get_text(self.language, 'save'),
                command=self._save_settings,
                width=15
            )
            save_button.grid(row=0, column=0, padx=5)

            # Reset button
            reset_button = ttk.Button(
                button_frame,
                text=get_text(self.language, 'reset_to_defaults'),
                command=self._reset_settings,
                width=15
            )
            reset_button.grid(row=0, column=1, padx=5)

            # Cancel button
            cancel_button = ttk.Button(
                button_frame,
                text=get_text(self.language, 'cancel'),
                command=self._on_window_close,
                width=15
            )
            cancel_button.grid(row=0, column=2, padx=5)

            # Handle window close
            self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

            # Center window on screen
            self.window.update_idletasks()
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f'{width}x{height}+{x}+{y}')

            # Start the GUI event loop
            self.window.mainloop()

        except Exception as e:
            print(f"Error creating settings window: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_open = False
            self.window = None

    def _start_hotkey_recording(self):
        """Start recording a hotkey."""
        if self.recording_hotkey:
            return

        self.recording_hotkey = True
        self.hotkey_entry.config(state='normal')
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, get_text(self.language, 'press_hotkey'))
        self.hotkey_entry.config(state='readonly')

        # Bind key press event
        self.window.bind('<KeyPress>', self._record_keypress)

    def _record_keypress(self, event):
        """Record a key press for hotkey."""
        if not self.recording_hotkey:
            return

        # Build hotkey string from modifiers and key
        modifiers = []
        if event.state & 0x4:  # Control
            modifiers.append('ctrl')
        if event.state & 0x1:  # Shift
            modifiers.append('shift')
        if event.state & 0x20000:  # Alt
            modifiers.append('alt')

        # Get the key
        key = event.keysym.lower()

        # Skip if only modifier key pressed
        if key in ['control_l', 'control_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r']:
            return

        # Build hotkey string
        if modifiers:
            hotkey = '+'.join(modifiers) + '+' + key
        else:
            hotkey = key

        # Update entry
        self.hotkey_entry.config(state='normal')
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, hotkey)
        self.hotkey_entry.config(state='readonly')

        # Stop recording
        self.recording_hotkey = False
        self.window.unbind('<KeyPress>')

    def _save_settings(self):
        """Save settings and close window."""
        try:
            # Extract language code from selection
            lang_selection = self.language_var.get()
            language = lang_selection.split(' - ')[0]

            # Validate and save
            self.settings_manager.set_language(language)
            self.settings_manager.set_capture_size(
                self.width_var.get(),
                self.height_var.get()
            )
            self.settings_manager.set_recognition_hotkey(self.hotkey_var.get())

            # Save to file
            if self.settings_manager.save():
                # Call callback if provided
                if self.on_settings_changed:
                    self.on_settings_changed()

                self.cancelled = False

                # Store callback before closing window
                close_callback = self.on_close_callback

                # Close window first to properly cleanup Tkinter resources
                self._close_window()

                # Call close callback to exit the application (after window is closed)
                if close_callback:
                    close_callback()
            else:
                messagebox.showerror(
                    get_text(self.language, 'error_title'),
                    get_text(self.language, 'error_save_failed'),
                    parent=self.window
                )

        except ValueError as e:
            messagebox.showerror(
                get_text(self.language, 'invalid_settings_title'),
                str(e),
                parent=self.window
            )
        except Exception as e:
            messagebox.showerror(
                get_text(self.language, 'error_title'),
                f"An error occurred: {e}",
                parent=self.window
            )

    def _reset_settings(self):
        """Reset settings to defaults."""
        result = messagebox.askyesno(
            get_text(self.language, 'reset_confirm_title'),
            get_text(self.language, 'reset_confirm_message'),
            parent=self.window
        )

        if result:
            self.settings_manager.reset_to_defaults()

            # Update UI
            current_lang = self.settings_manager.get_language()
            current_display = f"{current_lang} - {LANGUAGE_NAMES[current_lang]}"
            self.language_var.set(current_display)

            width, height = self.settings_manager.get_capture_size()
            self.width_var.set(width)
            self.height_var.set(height)

            self.hotkey_var.set(self.settings_manager.get_recognition_hotkey())

    def _on_window_close(self):
        """Handle window close button (X)."""
        self.cancelled = True
        self._close_window()

        # Call close callback if provided
        if self.on_close_callback:
            self.on_close_callback()

    def _close_window(self):
        """Close the settings window."""
        if self.window:
            try:
                # Clear variable references to avoid cleanup issues
                self.language_var = None
                self.width_var = None
                self.height_var = None
                self.hotkey_var = None

                # Destroy window
                self.window.quit()
                self.window.destroy()
            except:
                pass
        self.is_open = False
        self.window = None

    def was_cancelled(self) -> bool:
        """Check if the settings window was cancelled (not saved)."""
        return self.cancelled

    def cleanup(self):
        """Cleanup GUI resources."""
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
        self.is_open = False
