import platform
import os

class DragDropHandler:
    """Provides cross-platform drag and drop functionality for Tkinter"""
    
    @staticmethod
    def add_drag_drop_support(root, frame, callback):
        """
        Add drag and drop support to a Tkinter frame
        
        Args:
            root: The Tkinter root window
            frame: The frame to enable drag and drop on
            callback: Function to call when files are dropped (takes a file path argument)
        """
        system = platform.system()
        
        try:
            if system == "Windows" or system == "Darwin":  # Windows or macOS
                try:
                    import tkinterdnd2
                    
                    # If not already using TkinterDnD.Tk, replace the root
                    if not isinstance(root, tkinterdnd2.TkinterDnD.Tk):
                        # This is a bit of a hack to use TkinterDnD with an existing Tk instance
                        # In a real application, you would use TkinterDnD.Tk from the start
                        tkinterdnd2.TkinterDnD._require(root)
                    
                    # Register the frame to receive drops
                    frame.drop_target_register('DND_Files')
                    frame.dnd_bind('<<Drop>>', lambda e: _handle_drop(e, callback))
                    
                    return True
                    
                except ImportError:
                    print("Warning: tkinterdnd2 not available. Drag and drop disabled.")
                    return False
            else:  # Linux and others
                try:
                    # Use Tkinter built-in drag and drop for Linux
                    # This method is less reliable on Linux but can sometimes work
                    root.bind('<Drop>', lambda e: _handle_drop_basic(e, callback))
                    return True
                except Exception as e:
                    print(f"Warning: Could not enable drag and drop: {str(e)}")
                    return False
        except Exception as e:
            print(f"Warning: Error setting up drag and drop: {str(e)}")
            return False

def _handle_drop(event, callback):
    """Handle drag and drop event using tkinterdnd2"""
    # Get the dropped data
    data = event.data
    
    # Handle Windows paths (braces and quotes)
    if data.startswith('{') and data.endswith('}'):
        data = data[1:-1]
    
    # Handle multiple files (we'll take the first one)
    files = data.split() if ' ' in data else [data]
    
    # Clean up file paths based on platform
    clean_files = []
    for file in files:
        if file.startswith('"') and file.endswith('"'):
            file = file[1:-1]
        clean_files.append(file)
    
    # Check for PDF files
    pdf_files = [f for f in clean_files if f.lower().endswith('.pdf')]
    
    if pdf_files:
        callback(pdf_files[0])  # Process the first PDF

def _handle_drop_basic(event, callback):
    """Handle basic Tkinter drag and drop event (mainly for Linux)"""
    data = event.data
    
    if isinstance(data, str) and data.lower().endswith('.pdf'):
        callback(data)