import tkinter as tk
from tkinter import ttk

class ReportWindow:
    """Window for displaying detailed accessibility reports"""
    
    def __init__(self, parent, title="Accessibility Report", width=600, height=500):
        # Create a new toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.window.minsize(500, 400)
        
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
        style.configure('Report.Heading.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Report.Subheading.TLabel', font=('Arial', 12, 'bold'))
        
        # Configure sections
        style.configure('Report.Section.TFrame', padding=10)
    
    def _create_ui_elements(self):
        """Create the UI elements for the report"""
        # Report heading
        heading = ttk.Label(
            self.main_frame,
            text="PDF Accessibility Report",
            style='Report.Heading.TLabel'
        )
        heading.pack(pady=(0, 20))
        
        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.summary_frame, text="Summary")
        
        # Issues tab
        self.issues_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.issues_frame, text="Issues Found")
        
        # Fixes tab
        self.fixes_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.fixes_frame, text="Applied Fixes")
    
    def display_report(self, analysis_results, remediation_results=None):
        """
        Display accessibility report
        
        Args:
            analysis_results: Dictionary containing analysis results
            remediation_results: Dictionary containing remediation results (optional)
        """
        # Clear existing content
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        for widget in self.issues_frame.winfo_children():
            widget.destroy()
        for widget in self.fixes_frame.winfo_children():
            widget.destroy()
        
        # Get issues and document info
        issues = analysis_results.get('issues', [])
        doc_info = analysis_results.get('document_info', {})
        
        # Display summary
        self._display_summary(doc_info, issues, remediation_results)
        
        # Display issues
        self._display_issues(issues)
        
        # Display fixes
        if remediation_results:
            self._display_fixes(remediation_results.get('fixed_issues', []))
    
    def _display_summary(self, doc_info, issues, remediation_results):
        """Display summary information"""
        # Create a frame for the summary content
        summary_content = ttk.Frame(self.summary_frame)
        summary_content.pack(fill=tk.BOTH, expand=True)
        
        # File Information
        file_info_frame = ttk.LabelFrame(summary_content, text="Document Information")
        file_info_frame.pack(fill=tk.X, pady=10)
        
        # Add document info
        row = 0
        for key, value in doc_info.items():
            if key not in ['images', 'form_fields']:  # Skip large arrays
                label = ttk.Label(file_info_frame, text=f"{key.replace('_', ' ').title()}:")
                label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                
                value_label = ttk.Label(file_info_frame, text=str(value))
                value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                
                row += 1
        
        # Accessibility Summary
        issues_count = len(issues)
        fixed_count = len(remediation_results.get('fixed_issues', [])) if remediation_results else 0
        
        summary_frame = ttk.LabelFrame(summary_content, text="Accessibility Summary")
        summary_frame.pack(fill=tk.X, pady=10)
        
        # Issues count
        ttk.Label(summary_frame, text="Issues Found:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_frame, text=str(issues_count)).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Fixed count
        ttk.Label(summary_frame, text="Issues Fixed:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_frame, text=str(fixed_count)).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Compliance score (simplified calculation)
        score = 100 if issues_count == 0 else int(100 * (fixed_count / issues_count)) if issues_count > 0 else 0
        
        ttk.Label(summary_frame, text="Compliance Score:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        score_label = ttk.Label(summary_frame, text=f"{score}%")
        score_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # WCAG compliance
        wcag_frame = ttk.LabelFrame(summary_content, text="WCAG 2.1 Compliance")
        wcag_frame.pack(fill=tk.X, pady=10)
        
        # Extract unique WCAG criteria from issues
        wcag_criteria = set()
        for issue in issues:
            if 'wcag' in issue:
                criteria = issue['wcag'].split(', ')
                for criterion in criteria:
                    wcag_criteria.add(criterion)
        
        # Display WCAG criteria
        if wcag_criteria:
            for i, criterion in enumerate(sorted(wcag_criteria)):
                ttk.Label(wcag_frame, text=f"Criterion {criterion}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
                status = "Fixed" if remediation_results else "Issue Detected"
                ttk.Label(wcag_frame, text=status).grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        else:
            ttk.Label(wcag_frame, text="No specific WCAG criteria identified").pack(padx=5, pady=5)
    
    def _display_issues(self, issues):
        """Display detailed information about identified issues"""
        if not issues:
            ttk.Label(self.issues_frame, text="No accessibility issues were found in this document.").pack(pady=20)
            return
        
        # Create a scrollable frame for issues
        canvas = tk.Canvas(self.issues_frame)
        scrollbar = ttk.Scrollbar(self.issues_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add issues to the scrollable frame
        for i, issue in enumerate(issues):
            issue_frame = ttk.Frame(scrollable_frame, style='Report.Section.TFrame')
            issue_frame.pack(fill=tk.X, pady=5)
            
            # Issue type
            issue_type = issue.get('type', 'Unknown Issue Type')
            type_label = ttk.Label(
                issue_frame,
                text=issue_type.replace('_', ' ').title(),
                style='Report.Subheading.TLabel'
            )
            type_label.pack(anchor=tk.W)
            
            # Issue description
            description = issue.get('description', 'No description available')
            desc_label = ttk.Label(issue_frame, text=description, wraplength=500)
            desc_label.pack(anchor=tk.W, pady=(5, 0))
            
            # WCAG reference
            if 'wcag' in issue:
                wcag_label = ttk.Label(
                    issue_frame,
                    text=f"WCAG Reference: {issue['wcag']}",
                    font=('Arial', 9, 'italic')
                )
                wcag_label.pack(anchor=tk.W, pady=(5, 0))
            
            # Add a separator after each issue except the last one
            if i < len(issues) - 1:
                ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)
    
    def _display_fixes(self, fixes):
        """Display information about applied fixes"""
        if not fixes:
            ttk.Label(self.fixes_frame, text="No fixes have been applied yet.").pack(pady=20)
            return
        
        # Create a scrollable frame for fixes
        canvas = tk.Canvas(self.fixes_frame)
        scrollbar = ttk.Scrollbar(self.fixes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add fixes to the scrollable frame
        for i, fix in enumerate(fixes):
            fix_frame = ttk.Frame(scrollable_frame, padding=5)
            fix_frame.pack(fill=tk.X, pady=2)
            
            # Fix description
            fix_label = ttk.Label(fix_frame, text=f"✓ {fix}", wraplength=500)
            fix_label.pack(anchor=tk.W)