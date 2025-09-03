#!/usr/bin/env python3
"""
RockSmith Guitar Mute GUI - Graphical interface for PSARC file processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os
import sys
from pathlib import Path
from typing import Optional, List
import logging
import subprocess
import signal
import atexit

# Configure Windows to run all subprocess calls silently
if sys.platform == "win32":
    import subprocess
    # Ensure all subprocess calls are silent by default
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Set console mode to prevent showing console windows
    try:
        import ctypes
        from ctypes import wintypes
        
        # Hide console window for this process if it exists
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get console window handle
        console_window = kernel32.GetConsoleWindow()
        if console_window:
            user32.ShowWindow(console_window, 0)  # SW_HIDE
            
    except Exception:
        pass  # Ignore if unable to hide console

# Import main module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rocksmith_guitar_mute import RocksmithGuitarMute, setup_logging


def patch_subprocess_for_silence():
    """Patch subprocess module to ensure all calls are silent on Windows."""
    if sys.platform == "win32":
        import subprocess
        original_run = subprocess.run
        original_popen = subprocess.Popen
        
        def silent_run(*args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            if 'capture_output' not in kwargs and 'stdout' not in kwargs:
                kwargs['capture_output'] = True
            return original_run(*args, **kwargs)
        
        def silent_popen(*args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return original_popen(*args, **kwargs)
        
        subprocess.run = silent_run
        subprocess.Popen = silent_popen


class RocksmithGuitarMuteGUI:
    """Graphical interface for RockSmith Guitar Mute."""
    
    def __init__(self):
        # Apply subprocess patches for silent operation
        patch_subprocess_for_silence()
        
        # Setup logging for GUI
        gui_log_file = Path("RockSmithGuitarMute_GUI.log")
        setup_logging(verbose=True, log_file=str(gui_log_file))
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing RockSmith Guitar Mute GUI")
        
        self.root = tk.Tk()
        self.root.title("RockSmith Guitar Mute - Graphical Interface")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)
        self.model_var = tk.StringVar(value="htdemucs_6s")
        self.device_var = tk.StringVar(value="auto")
        self.workers_var = tk.IntVar(value=os.cpu_count())
        
        # Processing state
        self.processing = False
        self.paused = False
        self.cancelled = False
        self.processor = None
        self.processing_thread = None
        
        # Flag to track clean shutdown
        self.shutdown_requested = False
        
        # Queue for inter-thread communication
        self.message_queue = queue.Queue()
        
        # Logging configuration
        self.setup_gui_logging()
        
        # Interface creation
        self.create_widgets()
        self.setup_layout()
        
        # Start message monitoring
        self.check_queue()
        
        # Register cleanup function
        atexit.register(self.cleanup)
    
    def setup_gui_logging(self):
        """Configure logging for the graphical interface."""
        # Logger for the interface
        self.logger = logging.getLogger("GUI")
        self.logger.setLevel(logging.INFO)
        
        # Custom handler to send logs to the GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, message_queue):
                super().__init__()
                self.message_queue = message_queue
            
            def emit(self, record):
                msg = self.format(record)
                self.message_queue.put(('log', msg))
        
        gui_handler = GUILogHandler(self.message_queue)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to main logger
        root_logger = logging.getLogger()
        root_logger.addHandler(gui_handler)
    
    def create_widgets(self):
        """Create all interface widgets."""
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === File Selection Section ===
        files_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input/Output
        ttk.Label(files_frame, text="Input File/Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        input_frame = ttk.Frame(files_frame)
        input_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=2)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_path, width=60)
        self.input_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(input_frame, text="File", command=self.select_input_file).grid(row=0, column=1, padx=2)
        ttk.Button(input_frame, text="Folder", command=self.select_input_folder).grid(row=0, column=2, padx=2)
        
        ttk.Label(files_frame, text="Output Folder:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        
        output_frame = ttk.Frame(files_frame)
        output_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=2)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=60)
        self.output_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(output_frame, text="Browse", command=self.select_output_folder).grid(row=0, column=1)
        
        files_frame.columnconfigure(0, weight=1)
        
        # === Options Section ===
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkbox to overwrite files
        self.overwrite_check = ttk.Checkbutton(
            options_frame, 
            text="Allow overwriting existing files",
            variable=self.overwrite_var
        )
        self.overwrite_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Demucs Model
        ttk.Label(options_frame, text="Demucs Model:").grid(row=1, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            options_frame, 
            textvariable=self.model_var,
            values=["htdemucs_6s", "htdemucs", "htdemucs_ft", "mdx_extra", "mdx"],
            state="readonly",
            width=20
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Device
        ttk.Label(options_frame, text="Device:").grid(row=2, column=0, sticky=tk.W, pady=2)
        device_combo = ttk.Combobox(
            options_frame,
            textvariable=self.device_var,
            values=["auto", "cpu", "cuda"],
            state="readonly",
            width=20
        )
        device_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Number of workers
        ttk.Label(options_frame, text="Number of processes:").grid(row=3, column=0, sticky=tk.W, pady=2)
        workers_spin = ttk.Spinbox(
            options_frame,
            from_=1,
            to=os.cpu_count() * 2,
            textvariable=self.workers_var,
            width=20
        )
        workers_spin.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # === Progress Section ===
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        # === Control Buttons Section ===
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame,
            text="Start Processing",
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_button = ttk.Button(
            control_frame,
            text="Pause",
            command=self.pause_processing,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            control_frame,
            text="Cancel",
            command=self.cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # === Logs Section ===
        logs_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text area with scrollbar
        log_text_frame = ttk.Frame(logs_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_text_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#f8f9fa',
            fg='#212529'
        )
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button to clear logs
        ttk.Button(logs_frame, text="Clear Logs", command=self.clear_logs).pack(anchor=tk.E, pady=(5, 0))
    
    def setup_layout(self):
        """Configure layout and styles."""
        # Style for main button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("", 10, "bold"))
    
    def select_input_file(self):
        """Select an input file."""
        filename = filedialog.askopenfilename(
            title="Select a PSARC file",
            filetypes=[("PSARC Files", "*.psarc"), ("All Files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
    
    def select_input_folder(self):
        """Select an input folder."""
        folder = filedialog.askdirectory(title="Select a folder containing PSARC files")
        if folder:
            self.input_path.set(folder)
    
    def select_output_folder(self):
        """Select the output folder."""
        folder = filedialog.askdirectory(title="Select the output folder")
        if folder:
            self.output_path.set(folder)
    
    def validate_inputs(self) -> bool:
        """Validate user inputs."""
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input file or folder.")
            return False
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please select an output folder.")
            return False
        
        input_path = Path(self.input_path.get())
        if not input_path.exists():
            messagebox.showerror("Error", f"The input path does not exist: {input_path}")
            return False
        
        return True
    
    def start_processing(self):
        """Start processing in the background."""
        if not self.validate_inputs():
            return
        
        # Check existing files if necessary
        if not self.overwrite_var.get():
            input_path = Path(self.input_path.get())
            output_path = Path(self.output_path.get())
            
            if input_path.is_file():
                output_file = output_path / input_path.name
                if output_file.exists():
                    result = messagebox.askyesno(
                        "Existing File",
                        f"The file {output_file.name} already exists. Do you want to replace it?"
                    )
                    if not result:
                        return
            else:
                # Check if there are files that would be overwritten
                psarc_files = list(input_path.glob("*.psarc"))
                existing_files = [f for f in psarc_files if (output_path / f.name).exists()]
                
                if existing_files:
                    result = messagebox.askyesno(
                        "Existing Files",
                        f"{len(existing_files)} file(s) already exist in the output folder. "
                        "Do you want to replace them?"
                    )
                    if not result:
                        return
        
        # Update interface
        self.processing = True
        self.paused = False
        self.cancelled = False
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.NORMAL)
        
        self.status_var.set("Initializing...")
        self.progress_var.set(0)
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_files, daemon=False)  # Not daemon
        self.processing_thread.start()
    
    def pause_processing(self):
        """Pause or resume processing."""
        if self.paused:
            self.paused = False
            self.pause_button.config(text="Pause")
            self.status_var.set("Resuming processing...")
            self.message_queue.put(('log', "Processing resumed"))
        else:
            self.paused = True
            self.pause_button.config(text="Resume")
            self.status_var.set("Processing paused...")
            self.message_queue.put(('log', "Processing paused"))
    
    def cancel_processing(self):
        """Cancel current processing."""
        result = messagebox.askyesno("Confirmation", "Are you sure you want to cancel processing?")
        if result:
            self.cancelled = True
            self.status_var.set("Cancelling...")
            self.message_queue.put(('log', "Cancellation requested by user"))
    
    def process_files(self):
        """Process files in the background."""
        try:
            # Logging configuration for this thread
            setup_logging(verbose=True)
            
            # Check if shutdown was requested before starting
            if self.shutdown_requested or self.cancelled:
                self.message_queue.put(('log', "Processing cancelled before start"))
                return
            
            # Processor initialization
            self.message_queue.put(('log', f"Initializing with model {self.model_var.get()}"))
            self.message_queue.put(('status', "Initializing processor..."))
            
            processor = RocksmithGuitarMute(
                demucs_model=self.model_var.get(),
                device=self.device_var.get()
            )
            
            # Check cancellation again
            if self.shutdown_requested or self.cancelled:
                self.message_queue.put(('log', "Processing cancelled during initialization"))
                return
            
            input_path = Path(self.input_path.get())
            output_path = Path(self.output_path.get())
            
            # Determine files to process
            if input_path.is_file():
                files_to_process = [input_path] if input_path.suffix.lower() == '.psarc' else []
            else:
                files_to_process = list(input_path.glob("*.psarc"))
            
            if not files_to_process:
                self.message_queue.put(('log', "No PSARC files found"))
                self.message_queue.put(('status', "No files to process"))
                return
            
            total_files = len(files_to_process)
            self.message_queue.put(('log', f"Processing {total_files} file(s)"))
            
            processed_count = 0
            
            for i, psarc_file in enumerate(files_to_process):
                # Check for cancellation at the start of each file
                if self.cancelled or self.shutdown_requested:
                    self.message_queue.put(('log', "Processing cancelled"))
                    break
                
                # Pause handling
                while self.paused and not self.cancelled and not self.shutdown_requested:
                    threading.Event().wait(0.1)
                
                # Check again after pause
                if self.cancelled or self.shutdown_requested:
                    break
                
                # Status update
                self.message_queue.put(('status', f"Processing {psarc_file.name} ({i+1}/{total_files})"))
                self.message_queue.put(('progress', (i / total_files) * 100))
                
                try:
                    # File processing
                    result = processor.process_psarc_file(
                        psarc_file,
                        output_path,
                        force=self.overwrite_var.get()
                    )
                    
                    # Check for cancellation after processing
                    if self.cancelled or self.shutdown_requested:
                        break
                    
                    if result:
                        processed_count += 1
                        self.message_queue.put(('log', f"✓ File processed successfully: {result.name}"))
                    else:
                        self.message_queue.put(('log', f"⚠ File skipped: {psarc_file.name}"))

                except Exception as e:
                    self.message_queue.put(('log', f"✗ Error processing {psarc_file.name}: {e}"))
                    # Check for cancellation after error
                    if self.cancelled or self.shutdown_requested:
                        break
                
                # Progress update
                self.message_queue.put(('progress', ((i + 1) / total_files) * 100))
            
            # Processing completed
            if not self.cancelled and not self.shutdown_requested:
                self.message_queue.put(('status', f"Processing completed - {processed_count}/{total_files} files processed"))
                self.message_queue.put(('log', f"Processing completed successfully! {processed_count} file(s) processed"))
                self.message_queue.put(('progress', 100))
            
        except Exception as e:
            if not self.shutdown_requested:
                self.message_queue.put(('log', f"Critical error: {e}"))
                self.message_queue.put(('status', "Error during processing"))
        
        finally:
            # Always clean up and signal completion
            try:
                # Clear processor reference
                if 'processor' in locals():
                    del processor
                    
                # Force garbage collection
                import gc
                gc.collect()
                
                # Clear PyTorch cache if available
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except:
                    pass
                    
            except Exception as e:
                if not self.shutdown_requested:
                    self.message_queue.put(('log', f"Error in processing cleanup: {e}"))
            
            # Interface reset
            if not self.shutdown_requested:
                self.message_queue.put(('processing_done', None))
    
    def check_queue(self):
        """Check message queue and update interface."""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    self.add_log_message(msg_data)
                elif msg_type == 'status':
                    self.status_var.set(msg_data)
                elif msg_type == 'progress':
                    self.progress_var.set(msg_data)
                elif msg_type == 'processing_done':
                    self.processing_finished()
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_queue)
    
    def add_log_message(self, message: str):
        """Add a message to the activity log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_logs(self):
        """Clear the activity log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def processing_finished(self):
        """Called when processing is finished."""
        self.processing = False
        self.paused = False
        self.cancelled = False
        
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pause")
        self.cancel_button.config(state=tk.DISABLED)
        
        if not self.cancelled:
            messagebox.showinfo("Completed", "Processing is complete!")
    
    def cleanup(self):
        """Clean up resources and terminate processes."""
        if self.shutdown_requested:
            return
            
        self.shutdown_requested = True
        self.logger.info("Starting application cleanup...")
        
        try:
            # Cancel any ongoing processing
            if self.processing:
                self.cancelled = True
                self.logger.info("Cancelling ongoing processing...")
                
            # Wait for processing thread to finish (with timeout)
            if self.processing_thread and self.processing_thread.is_alive():
                self.logger.info("Waiting for processing thread to complete...")
                self.processing_thread.join(timeout=5.0)
                
                if self.processing_thread.is_alive():
                    self.logger.warning("Processing thread did not stop gracefully")
                
            # Clean up PyTorch/CUDA resources
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                self.logger.info("PyTorch resources cleaned up")
            except Exception as e:
                self.logger.debug(f"PyTorch cleanup error: {e}")
                
            # Force cleanup of all daemon threads
            for thread in threading.enumerate():
                if thread != threading.current_thread() and thread.is_alive():
                    thread.daemon = True
                    self.logger.debug(f"Set thread {thread.name} as daemon")
                    
            # Clear the message queue
            try:
                while not self.message_queue.empty():
                    self.message_queue.get_nowait()
            except:
                pass
                
            self.logger.info("Cleanup completed successfully")
                        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def force_exit(self):
        """Force exit the application."""
        try:
            self.logger.info("Force exit requested")
            self.cleanup()
            
            # Terminate any remaining child processes
            if sys.platform == "win32":
                try:
                    import psutil
                    current_process = psutil.Process()
                    children = current_process.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except:
                            pass
                except ImportError:
                    pass
            
            # Force exit
            os._exit(0)
        except Exception as e:
            print(f"Error in force_exit: {e}")
            os._exit(1)
    
    def run(self):
        """Launch the graphical interface."""
        # Application closing configuration
        def on_closing():
            self.logger.info("Application close requested")
            
            if self.processing:
                result = messagebox.askyesno(
                    "Confirmation",
                    "Processing is in progress. Do you really want to quit?"
                )
                if not result:
                    return
                    
                # Cancel processing gracefully
                self.cancelled = True
                self.logger.info("User requested application shutdown during processing")
                
                # Wait a bit for cancellation to take effect
                if self.processing_thread and self.processing_thread.is_alive():
                    self.logger.info("Waiting for processing to stop...")
                    self.processing_thread.join(timeout=3.0)
                    
                    if self.processing_thread.is_alive():
                        self.logger.warning("Processing thread did not stop gracefully")
            
            # Cleanup resources
            self.cleanup()
            
            # Destroy the GUI
            try:
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                self.logger.debug(f"Error destroying GUI: {e}")
            
            # Schedule force exit after a short delay
            def delayed_force_exit():
                import time
                time.sleep(1)  # Give time for normal exit
                self.logger.info("Performing delayed force exit")
                os._exit(0)
            
            force_exit_thread = threading.Thread(target=delayed_force_exit, daemon=True)
            force_exit_thread.start()
            
            # Try normal exit first
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
            except:
                os._exit(0)
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Handle Ctrl+C and other signals
        if sys.platform == "win32":
            try:
                signal.signal(signal.SIGINT, lambda s, f: on_closing())
                signal.signal(signal.SIGTERM, lambda s, f: on_closing())
            except:
                pass
        
        try:
            # Start main loop
            self.root.mainloop()
        except KeyboardInterrupt:
            on_closing()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            on_closing()
        finally:
            self.cleanup()
            # Final force exit as last resort
            try:
                os._exit(0)
            except:
                pass


def main():
    """Main entry point for the graphical interface."""
    
    # Set up signal handlers for clean shutdown
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        try:
            os._exit(0)
        except:
            pass
    
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except:
            pass
    
    app = None
    try:
        app = RocksmithGuitarMuteGUI()
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
        if app:
            app.cleanup()
        sys.exit(0)
    except Exception as e:
        try:
            messagebox.showerror("Critical Error", f"Error starting the application: {e}")
        except:
            print(f"Critical Error: {e}")
        if app:
            app.cleanup()
        sys.exit(1)
    finally:
        # Ultimate cleanup and force exit
        if app:
            app.cleanup()
        
        # Clean up any remaining threads
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.is_alive():
                thread.daemon = True
        
        # Force cleanup of PyTorch resources
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except:
            pass
        
        # Force garbage collection
        try:
            import gc
            gc.collect()
        except:
            pass
        
        # Force exit
        try:
            sys.exit(0)
        except:
            os._exit(0)


if __name__ == "__main__":
    main()
