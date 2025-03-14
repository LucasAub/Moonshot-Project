import tkinter as tk
from tkinter import filedialog, ttk
import os
import threading
from src.analysis.analyzer import PDFAnalyzer
from src.remediation.remediator import PDFRemediator
from src.ui.drag_drop import DragDropHandler
from src.ui.report_window import ReportWindow
from src.ui.settings import Settings, SettingsWindow

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Accessibility Tool")
        self.root.geometry("600x400")
        self.root.minsize(500, 350)
        
        # Initialize settings
        self.settings = Settings()
        
        # Configure style
        self.configure_style()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create UI elements
        self.create_ui_elements()
        
        # Initialize drag and drop support
        self.setup_drag_drop()
    
    def configure_style(self):
        """Configure the UI style"""
        style = ttk.Style()
        
        # Use the system theme as a base
        style.theme_use('clam')  # Can use 'clam', 'alt', 'default', or 'classic'
        
        # Configure button style
        style.configure('TButton', font=('Arial', 12))
        
        # Configure frame style
        style.configure('TFrame', background='#f0f0f0')
        
        # Configure label style
        style.configure('TLabel', font=('Arial', 11))
        style.configure('Heading.TLabel', font=('Arial', 16, 'bold'))
    
    def create_ui_elements(self):
        """Create the UI elements"""
        # Heading
        heading = ttk.Label(
            self.main_frame,
            text="PDF Accessibility Tool",
            style='Heading.TLabel'
        )
        heading.pack(pady=(0, 20))
        
        # Description
        description = ttk.Label(
            self.main_frame,
            text="Make PDFs accessible for screen readers and assistive technologies",
            wraplength=500
        )
        description.pack(pady=(0, 30))
        
        # Select PDF button
        self.select_button = ttk.Button(
            self.main_frame,
            text="Select PDF",
            command=self.select_file,
            padding=(20, 10)
        )
        self.select_button.pack(pady=(0, 20))
        
        # Drop area
        self.drop_frame = ttk.LabelFrame(
            self.main_frame,
            text="Or drop your PDF here"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        # Add label to drop area
        drop_label = ttk.Label(
            self.drop_frame,
            text="Drag and drop a PDF file here",
            anchor="center"
        )
        drop_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=30)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready to process PDFs"
        )
        self.status_label.pack(pady=(20, 0))
        
        # Progress bar (hidden initially)
        self.progress = ttk.Progressbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            length=400,
            mode='indeterminate'
        )
        
        # Fix and Save button (hidden initially)
        self.fix_button = ttk.Button(
            self.main_frame,
            text="Fix and Save",
            command=self.fix_and_save,
            padding=(20, 10)
        )
        # We'll show this button only after analysis
    
    def setup_drag_drop(self):
        """Set up drag and drop functionality"""
        # Initialize drag and drop
        DragDropHandler.add_drag_drop_support(
            self.root,
            self.drop_frame,
            self.process_pdf
        )
    
    def select_file(self):
        """Open file dialog to select a PDF"""
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.process_pdf(file_path)
    
    def process_pdf(self, input_path):
        """Start PDF processing in a separate thread"""
        self.status_label.config(text=f"Processing {os.path.basename(input_path)}...")
        self.progress.pack(pady=(10, 0))
        self.progress.start()
        self.select_button.config(state=tk.DISABLED)
        
        # Start processing in a separate thread
        threading.Thread(target=self._simulate_processing, args=(input_path,), daemon=True).start()
    
    def _simulate_processing(self, input_path):
        """Process the selected PDF file"""
        try:
            # Analyze the PDF
            analyzer = PDFAnalyzer(input_path)
            analysis_results = analyzer.analyze()
            
            # For now, just print the analysis results
            print("Analysis Results:")
            print(f"Issues found: {len(analysis_results['issues'])}")
            for issue in analysis_results['issues']:
                print(f"- {issue['type']}: {issue['description']} (WCAG: {issue['wcag']})")
            
            print("\nDocument Info:")
            for key, value in analysis_results['document_info'].items():
                if key not in ['images', 'form_fields']:  # Skip large arrays
                    print(f"- {key}: {value}")
            
            # Update UI on completion (must be done in the main thread)
            self.root.after(0, self._processing_complete, input_path, analysis_results)
        except Exception as e:
            # Handle errors
            self.root.after(0, self._processing_error, str(e))
    
    def _processing_error(self, error_message):
        """Handle processing errors"""
        self.progress.stop()
        self.progress.pack_forget()
        self.select_button.config(state=tk.NORMAL)
        self.status_label.config(
            text=f"Error: {error_message}"
        )
    
    def _processing_complete(self, input_path, analysis_results=None):
        """Handle successful processing completion"""
        self.progress.stop()
        self.progress.pack_forget()
        self.select_button.config(state=tk.NORMAL)
        
        # Store the input path and analysis results for later use
        self.current_file = input_path
        self.current_analysis = analysis_results
        
        issues_count = len(analysis_results['issues']) if analysis_results else 0
        output_name = os.path.splitext(os.path.basename(input_path))[0] + "_accessible.pdf"
        self.status_label.config(
            text=f"Analysis complete. Found {issues_count} issues."
        )
        
        # Show the Fix and Save button
        self.fix_button.pack(pady=(10, 0))
        
        # Show report button
        self.report_button = ttk.Button(
            self.main_frame,
            text="View Report",
            command=lambda: self._show_report(analysis_results),
            padding=(20, 10)
        )
        self.report_button.pack(pady=(10, 0))
    
    def _show_report(self, analysis_results, remediation_results=None):
        """Show the accessibility report"""
        report_window = ReportWindow(self.root)
        report_window.display_report(analysis_results, remediation_results)
    
    def fix_and_save(self):
        """Fix accessibility issues and save the remediated PDF"""
        if not hasattr(self, 'current_file') or not self.current_file:
            return
        
        # Ask the user where to save the remediated PDF
        suggested_name = os.path.splitext(os.path.basename(self.current_file))[0] + "_accessible.pdf"
        output_path = filedialog.asksaveasfilename(
            title="Save Accessible PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=suggested_name
        )
        
        if not output_path:
            return  # User cancelled
        
        # Show progress during remediation
        self.status_label.config(text="Fixing accessibility issues...")
        self.progress.pack(pady=(10, 0))
        self.progress.start()
        self.fix_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        
        # Start remediation in a separate thread
        threading.Thread(
            target=self._remediate_and_save,
            args=(self.current_file, self.current_analysis, output_path),
            daemon=True
        ).start()
    
    def _remediate_and_save(self, input_path, analysis_results, output_path):
        """Remediate and save in a background thread"""
        try:
            # Create remediator with settings
            remediator = PDFRemediator(input_path, analysis_results)
            
            # Apply fixes based on settings
            ocr_enabled = self.settings.get('ocr', 'enabled')
            add_alt_text = self.settings.get('images', 'add_alt_text')
            use_ai = self.settings.get('images', 'use_ai_captioning')
            
            remediation_results = remediator.remediate(
                apply_ocr=ocr_enabled,
                add_alt_text=add_alt_text,
                use_ai_captioning=use_ai
            )
            
            # Save the remediated PDF
            remediator.save(output_path)
            
            # Store remediation results for reporting
            self.remediation_results = remediation_results
            
            # Print fixed issues
            print("Fixed issues:")
            for issue in remediation_results['fixed_issues']:
                print(f"- {issue}")
            
            # Save report if enabled
            if self.settings.get('general', 'save_report'):
                self._save_report(output_path, analysis_results, remediation_results)
            
            # Update UI on completion
            self.root.after(0, self._remediation_complete, output_path)
        except Exception as e:
            # Handle errors
            self.root.after(0, self._remediation_error, str(e))
    
    def _remediation_complete(self, output_path):
        """Handle successful remediation completion"""
        self.progress.stop()
        self.progress.pack_forget()
        self.fix_button.config(state=tk.NORMAL)
        self.select_button.config(state=tk.NORMAL)
        
        self.status_label.config(
            text=f"PDF successfully fixed and saved as {os.path.basename(output_path)}"
        )
        
        # Show the report with both analysis and remediation results
        if hasattr(self, 'remediation_results'):
            self._show_report(self.current_analysis, self.remediation_results)
        
        # Auto-open the fixed PDF if enabled
        if self.settings.get('general', 'auto_open_fixed_pdf') and os.path.exists(output_path):
            self._open_file(output_path)
        # Otherwise show open button
        elif os.path.exists(output_path):
            open_button = ttk.Button(
                self.main_frame,
                text="Open PDF",
                command=lambda: self._open_file(output_path)
            )
            open_button.pack(pady=(10, 0))
    
    def _remediation_error(self, error_message):
        """Handle remediation errors"""
        self.progress.stop()
        self.progress.pack_forget()
        self.fix_button.config(state=tk.NORMAL)
        self.select_button.config(state=tk.NORMAL)
        
        self.status_label.config(
            text=f"Error fixing PDF: {error_message}"
        )
    
    def _open_file(self, file_path):
        """Open a file using the default system application"""
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            print(f"Error opening file: {str(e)}")

    
    def create_ui_elements(self):
        """Create the UI elements"""
        # Header frame for title and settings button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Heading
        heading = ttk.Label(
            header_frame,
            text="PDF Accessibility Tool",
            style='Heading.TLabel'
        )
        heading.pack(side=tk.LEFT, pady=(0, 0))
        
        # Settings button
        settings_button = ttk.Button(
            header_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            padding=(10, 5)
        )
        settings_button.pack(side=tk.RIGHT)
        
        # Description
        description = ttk.Label(
            self.main_frame,
            text="Make PDFs accessible for screen readers and assistive technologies",
            wraplength=500
        )
        description.pack(pady=(0, 30))
        
        # Select PDF button
        self.select_button = ttk.Button(
            self.main_frame,
            text="Select PDF",
            command=self.select_file,
            padding=(20, 10)
        )
        self.select_button.pack(pady=(0, 20))
        
        # Drop area
        self.drop_frame = ttk.LabelFrame(
            self.main_frame,
            text="Or drop your PDF here"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        # Add label to drop area
        drop_label = ttk.Label(
            self.drop_frame,
            text="Drag and drop a PDF file here",
            anchor="center"
        )
        drop_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=30)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready to process PDFs"
        )
        self.status_label.pack(pady=(20, 0))
        
        # Progress bar (hidden initially)
        self.progress = ttk.Progressbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            length=400,
            mode='indeterminate'
        )
        
        # Fix and Save button (hidden initially)
        self.fix_button = ttk.Button(
            self.main_frame,
            text="Fix and Save",
            command=self.fix_and_save,
            padding=(20, 10)
        )
        # We'll show this button only after analysis

    def open_settings(self):
        """Open the settings window"""
        SettingsWindow(self.root, self.settings, self.on_settings_saved)

    def on_settings_saved(self):
        """Handle settings being saved"""
        # We could update UI or behavior based on new settings here
        pass
    
    def _save_report(self, pdf_path, analysis_results, remediation_results):
        """Save accessibility report as a text file"""
        try:
            # Create report filename based on PDF path
            report_path = os.path.splitext(pdf_path)[0] + "_accessibility_report.txt"
            
            with open(report_path, 'w') as f:
                # Write header
                f.write("PDF ACCESSIBILITY REPORT\n")
                f.write("======================\n\n")
                
                # Document info
                f.write("DOCUMENT INFORMATION\n")
                f.write("--------------------\n")
                for key, value in analysis_results['document_info'].items():
                    if key not in ['images', 'form_fields']:  # Skip large arrays
                        f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                f.write("\n")
                
                # Issues found
                f.write("ACCESSIBILITY ISSUES FOUND\n")
                f.write("-------------------------\n")
                if analysis_results['issues']:
                    for issue in analysis_results['issues']:
                        f.write(f"Issue: {issue.get('type', '').replace('_', ' ').title()}\n")
                        f.write(f"Description: {issue.get('description', 'No description')}\n")
                        if 'wcag' in issue:
                            f.write(f"WCAG Reference: {issue['wcag']}\n")
                        f.write("\n")
                else:
                    f.write("No issues found.\n\n")
                
                # Fixes applied
                f.write("FIXES APPLIED\n")
                f.write("------------\n")
                if remediation_results['fixed_issues']:
                    for fix in remediation_results['fixed_issues']:
                        f.write(f"- {fix}\n")
                else:
                    f.write("No fixes applied.\n")
            
            print(f"Report saved to {report_path}")
        except Exception as e:
            print(f"Error saving report: {str(e)}")