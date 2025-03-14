import os
import json
import tkinter as tk
from tkinter import ttk

class Settings:
    """Manages application settings"""
    
    DEFAULT_SETTINGS = {
        "ocr": {
            "enabled": True,
            "auto_detect": True,
            "language": "eng"
        },
        "images": {
            "use_ai_captioning": False,
            "add_alt_text": True
        },
        "general": {
            "auto_open_fixed_pdf": False,
            "save_report": False
        }
    }
    
    def __init__(self):
        """Initialize settings with defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.settings_file = os.path.join(
            os.path.expanduser('~'),
            '.pdf_accessibility_tool',
            'settings.json'
        )
        self.load_settings()
    
    def get(self, section, key):
        """Get a setting value"""
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        return None
    
    def set(self, section, key, value):
        """Set a setting value"""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self.save_settings()
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update settings with loaded values, keeping defaults for missing values
                    for section, values in loaded_settings.items():
                        if section in self.settings:
                            for key, value in values.items():
                                if key in self.settings[section]:
                                    self.settings[section][key] = value
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")


class SettingsWindow:
    """UI for editing application settings"""
    
    def __init__(self, parent, settings, on_save_callback=None):
        """Initialize settings window"""
        self.settings = settings
        self.on_save_callback = on_save_callback
        
        # Create a new toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x400")
        self.window.minsize(400, 350)
        self.window.resizable(True, True)
        
        # Configure style
        self._configure_style()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.window, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create UI elements
        self._create_ui_elements()
    
    def _configure_style(self):
        """Configure the UI style"""
        style = ttk.Style()
        
        # Configure headings
        style.configure('Settings.Heading.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Settings.Section.TLabel', font=('Arial', 12, 'bold'))
    
    def _create_ui_elements(self):
        """Create the UI elements for settings"""
        # Settings heading
        heading = ttk.Label(
            self.main_frame,
            text="Application Settings",
            style='Settings.Heading.TLabel'
        )
        heading.pack(pady=(0, 20))
        
        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # OCR Settings
        self.ocr_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.ocr_frame, text="OCR")
        self._create_ocr_settings()
        
        # Image Settings
        self.image_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.image_frame, text="Images")
        self._create_image_settings()
        
        # General Settings
        self.general_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.general_frame, text="General")
        self._create_general_settings()
        
        # Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Save button
        self.save_button = ttk.Button(
            self.button_frame,
            text="Save",
            command=self._save_settings,
            padding=(20, 5)
        )
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        self.cancel_button = ttk.Button(
            self.button_frame,
            text="Cancel",
            command=self.window.destroy,
            padding=(20, 5)
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _create_ocr_settings(self):
        """Create OCR settings UI"""
        # OCR Enabled
        self.ocr_enabled_var = tk.BooleanVar(value=self.settings.get('ocr', 'enabled'))
        ocr_enabled_check = ttk.Checkbutton(
            self.ocr_frame,
            text="Enable OCR for image-based PDFs",
            variable=self.ocr_enabled_var
        )
        ocr_enabled_check.pack(anchor=tk.W, pady=5)
        
        # Auto-detect OCR need
        self.ocr_auto_detect_var = tk.BooleanVar(value=self.settings.get('ocr', 'auto_detect'))
        ocr_auto_detect_check = ttk.Checkbutton(
            self.ocr_frame,
            text="Automatically detect when OCR is needed",
            variable=self.ocr_auto_detect_var
        )
        ocr_auto_detect_check.pack(anchor=tk.W, pady=5)
        
        # OCR Language
        language_frame = ttk.Frame(self.ocr_frame)
        language_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(language_frame, text="OCR Language:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.ocr_language_var = tk.StringVar(value=self.settings.get('ocr', 'language'))
        languages = [
            ("English", "eng"),
            ("French", "fra"),
            ("Spanish", "spa"),
            ("German", "deu"),
            ("Italian", "ita")
        ]
        
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.ocr_language_var,
            values=[lang[1] for lang in languages],
            state="readonly"
        )
        language_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Help text
        ttk.Label(
            self.ocr_frame,
            text="OCR (Optical Character Recognition) extracts text from images and scanned PDFs.",
            wraplength=400,
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(15, 0))
    
    def _create_image_settings(self):
        """Create image settings UI"""
        # AI Captioning
        self.use_ai_captioning_var = tk.BooleanVar(value=self.settings.get('images', 'use_ai_captioning'))
        ai_captioning_check = ttk.Checkbutton(
            self.image_frame,
            text="Use AI to generate image descriptions (requires internet)",
            variable=self.use_ai_captioning_var
        )
        ai_captioning_check.pack(anchor=tk.W, pady=5)
        
        # Add Alt Text
        self.add_alt_text_var = tk.BooleanVar(value=self.settings.get('images', 'add_alt_text'))
        alt_text_check = ttk.Checkbutton(
            self.image_frame,
            text="Add alternative text to images",
            variable=self.add_alt_text_var
        )
        alt_text_check.pack(anchor=tk.W, pady=5)
        
        # Help text
        ttk.Label(
            self.image_frame,
            text="Alternative text (alt text) describes images for screen reader users. AI captioning provides more detailed descriptions but requires internet connection.",
            wraplength=400,
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(15, 0))
    
    def _create_general_settings(self):
        """Create general settings UI"""
        # Auto-open fixed PDF
        self.auto_open_var = tk.BooleanVar(value=self.settings.get('general', 'auto_open_fixed_pdf'))
        auto_open_check = ttk.Checkbutton(
            self.general_frame,
            text="Automatically open fixed PDF after saving",
            variable=self.auto_open_var
        )
        auto_open_check.pack(anchor=tk.W, pady=5)
        
        # Save report
        self.save_report_var = tk.BooleanVar(value=self.settings.get('general', 'save_report'))
        save_report_check = ttk.Checkbutton(
            self.general_frame,
            text="Save accessibility report with fixed PDF",
            variable=self.save_report_var
        )
        save_report_check.pack(anchor=tk.W, pady=5)
    
    def _save_settings(self):
        """Save settings and close window"""
        # Save OCR settings
        self.settings.set('ocr', 'enabled', self.ocr_enabled_var.get())
        self.settings.set('ocr', 'auto_detect', self.ocr_auto_detect_var.get())
        self.settings.set('ocr', 'language', self.ocr_language_var.get())
        
        # Save image settings
        self.settings.set('images', 'use_ai_captioning', self.use_ai_captioning_var.get())
        self.settings.set('images', 'add_alt_text', self.add_alt_text_var.get())
        
        # Save general settings
        self.settings.set('general', 'auto_open_fixed_pdf', self.auto_open_var.get())
        self.settings.set('general', 'save_report', self.save_report_var.get())
        
        # Call save callback if provided
        if self.on_save_callback:
            self.on_save_callback()
        
        # Close window
        self.window.destroy()