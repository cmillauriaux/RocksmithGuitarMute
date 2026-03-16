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
import time

# Import conditionnel de Pillow (PIL)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARN] Pillow is not available - images will not display")

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
from rocksmith_guitar_mute import RocksmithGuitarMute, setup_logging, VARIANT_CONFIGS


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


class SplashScreen:
    """Écran de démarrage avec logo."""
    
    def __init__(self, parent):
        self.splash = tk.Toplevel(parent)
        self.splash.title("RockSmith Guitar Mute")
        self.splash.configure(bg='#1e1e1e')
        
        # Configuration de la fenêtre
        window_width = 400
        window_height = 300
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.splash.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.splash.overrideredirect(True)  # Enlever les bordures de fenêtre
        self.splash.attributes('-topmost', True)
        
        # Créer le contenu
        self.create_splash_content()
        
        # Variables pour le contrôle
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Loading...")
        
        # Ajouter les éléments de progression
        self.add_progress_elements()
        
    def create_splash_content(self):
        """Créer le contenu de l'écran de démarrage."""
        main_frame = tk.Frame(self.splash, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Charger et afficher le logo
        try:
            # Chemin vers le logo (supposé être dans le répertoire parent)
            logo_path = Path(__file__).parent.parent / "RSGM_v1a.png"
            if logo_path.exists() and PIL_AVAILABLE:
                image = Image.open(logo_path)
                # Redimensionner l'image si nécessaire
                image = image.resize((200, 200), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(image)
                
                logo_label = tk.Label(main_frame, image=self.logo_photo, bg='#1e1e1e')
                logo_label.pack(pady=(10, 20))
            else:
                # Logo de fallback si le fichier n'existe pas ou Pillow indisponible
                logo_label = tk.Label(main_frame, text="RSGM", font=("Arial", 24, "bold"), 
                                    fg='#ffffff', bg='#1e1e1e')
                logo_label.pack(pady=(10, 20))
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback logo in case of error
            logo_label = tk.Label(main_frame, text="RSGM", font=("Arial", 24, "bold"), 
                                fg='#ffffff', bg='#1e1e1e')
            logo_label.pack(pady=(10, 20))
        
        # Titre
        title_label = tk.Label(main_frame, text="RockSmith Guitar Mute", 
                              font=("Arial", 16, "bold"), fg='#ffffff', bg='#1e1e1e')
        title_label.pack(pady=(0, 10))
        
        # Version
        version_label = tk.Label(main_frame, text="Interface Graphique", 
                                font=("Arial", 10), fg='#cccccc', bg='#1e1e1e')
        version_label.pack(pady=(0, 20))
    
    def add_progress_elements(self):
        """Ajouter les éléments de progression."""
        progress_frame = tk.Frame(self.splash, bg='#1e1e1e')
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Barre de progression
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Splash.Horizontal.TProgressbar",
                       background='#0078d4',
                       troughcolor='#333333',
                       borderwidth=0,
                       lightcolor='#0078d4',
                       darkcolor='#0078d4')
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          variable=self.progress_var,
                                          maximum=100,
                                          mode='determinate',
                                          style="Splash.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Statut
        self.status_label = tk.Label(progress_frame, textvariable=self.status_var,
                                   font=("Arial", 9), fg='#cccccc', bg='#1e1e1e')
        self.status_label.pack()
    
    def update_progress(self, value, status=""):
        """Mettre à jour la progression."""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.splash.update()
    
    def destroy(self):
        """Fermer l'écran de démarrage."""
        try:
            self.splash.destroy()
        except:
            pass


class RocksmithGuitarMuteGUI:
    """Graphical interface for RockSmith Guitar Mute."""
    
    def __init__(self):
        try:
            print("Début d'initialisation de l'interface GUI")
            
            # Apply subprocess patches for silent operation
            patch_subprocess_for_silence()
            print("[OK] Patches subprocess appliqués")
            
            # Setup logging for GUI - version simplifiée pour éviter les conflits
            print("[OK] Configuration des logs simplifiée...")
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler("RockSmithGuitarMute_GUI.log"),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info("Initializing RockSmith Guitar Mute GUI")
            print("[OK] Logging configuré")
            
            # Créer d'abord la fenêtre principale
            print("Création de la fenêtre principale...")
            self.root = tk.Tk()
            self.root.withdraw()  # Cacher la fenêtre principale pendant la création
            print("[OK] Fenêtre principale créée")
            
            # Créer et afficher l'écran de démarrage
            print("Creating startup screen...")
            self.splash = SplashScreen(self.root)
            self.splash.update_progress(10, "Initialization...")
            print("[OK] Startup screen created")
            
            self.root.title("RockSmith Guitar Mute - Graphical Interface")
            # Size window to fit screen with some margin
            screen_height = self.root.winfo_screenheight()
            win_height = min(950, screen_height - 80)
            self.root.geometry(f"900x{win_height}")
            self.root.minsize(700, 500)
            
            # Configurer le thème sombre
            print("Setting up dark theme...")
            self.setup_dark_theme()
            print("[OK] Dark theme configured")
            
            self.splash.update_progress(40, "Initializing variables...")
            
            # Variables
            print("Initializing variables...")
            self.input_path = tk.StringVar()
            self.output_path = tk.StringVar()
            self.overwrite_var = tk.BooleanVar(value=False)
            self.model_var = tk.StringVar(value="htdemucs_6s")
            self.device_var = tk.StringVar(value="auto")
            self.workers_var = tk.IntVar(value=os.cpu_count())
            self.reduce_vocals_var = tk.IntVar(value=100)

            # Variant selection variables
            self.variant_vars = {}
            for variant_name in ["no_guitar", "no_vocals", "no_bass", "no_guitar_no_bass", "no_guitar_no_bass_no_vocals", "drums_only", "vocals_and_drums"]:
                self.variant_vars[variant_name] = tk.BooleanVar(value=(variant_name == "no_guitar"))

            # Custom variants: list of (name, [stems]) tuples
            self.custom_variants = []

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
            print("[OK] Variables initialized")
            
            self.splash.update_progress(60, "Configuring log system...")
            
            # Logging configuration
            print("Configuring GUI log system...")
            self.setup_gui_logging()
            print("[OK] GUI log system configured")
            
            self.splash.update_progress(80, "Creating components...")
            
            # Interface creation
            print("Creating widgets...")
            self.create_widgets()
            print("[OK] Widgets created")
            
            print("Configuring layout...")
            self.setup_layout()
            print("[OK] Layout configured")
            
            # Appliquer le style sombre aux combobox après création
            print("Applying dark style to widgets...")
            self.apply_dark_style_to_widgets()
            print("[OK] Dark style applied")
            
            self.splash.update_progress(90, "Finalizing...")
            
            # Start message monitoring
            print("Starting message monitoring...")
            self.check_queue()
            print("[OK] Message monitoring started")
            
            # Register cleanup function
            atexit.register(self.cleanup)
            print("[OK] Fonction de nettoyage enregistrée")
            
            # Finaliser l'initialisation
            self.splash.update_progress(100, "Ready!")
            print("Finalizing...")
            time.sleep(0.5)  # Short pause to see "Ready!"
            
            # Afficher la fenêtre principale et fermer le splash
            print("Displaying main window...")
            self.root.deiconify()
            self.splash.destroy()
            print("[OK] GUI interface completely initialized - window visible")
            
        except Exception as e:
            print(f"[ERROR] ERREUR CRITIQUE lors de l'initialisation: {e}")
            print(f"Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'splash'):
                try:
                    self.splash.destroy()
                except:
                    pass
            raise
    
    def setup_dark_theme(self):
        """Configurer le thème sombre pour l'application."""
        # Configuration de la fenêtre principale
        self.root.configure(bg='#1e1e1e')
        
        # Configuration du style TTK
        style = ttk.Style()
        
        # Utiliser le thème clam comme base
        style.theme_use('clam')
        
        # Couleurs du thème sombre améliorées
        colors = {
            'bg': '#1e1e1e',           # Arrière-plan principal
            'fg': '#ffffff',           # Texte principal
            'select_bg': '#0078d4',    # Arrière-plan sélection
            'select_fg': '#ffffff',    # Texte sélection
            'entry_bg': '#2d2d2d',     # Arrière-plan champs de saisie
            'entry_fg': '#ffffff',     # Texte champs de saisie
            'button_bg': '#404040',    # Arrière-plan boutons
            'button_fg': '#ffffff',    # Texte boutons
            'frame_bg': '#252525',     # Arrière-plan frames
            'border': '#555555',       # Bordures
            'disabled': '#666666',     # Éléments désactivés
            'hover_bg': '#505050'      # Survol
        }
        
        # Configuration des styles TTK améliorés
        style.configure('TLabel', 
                       background=colors['bg'], 
                       foreground=colors['fg'],
                       font=('Segoe UI', 9))
        
        style.configure('TFrame', 
                       background=colors['bg'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('TLabelFrame', 
                       background=colors['bg'],
                       foreground=colors['fg'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=colors['border'])
        
        style.configure('TLabelFrame.Label',
                       background=colors['bg'],
                       foreground=colors['fg'],
                       font=('Segoe UI', 9, 'bold'))
        
        style.configure('TEntry', 
                       foreground=colors['entry_fg'],
                       fieldbackground=colors['entry_bg'],
                       borderwidth=1,
                       insertcolor=colors['fg'],
                       relief='solid',
                       bordercolor=colors['border'])
        
        style.map('TEntry',
                 bordercolor=[('focus', colors['select_bg'])])
        
        style.configure('TButton', 
                       background=colors['button_bg'],
                       foreground=colors['button_fg'],
                       borderwidth=1,
                       focuscolor='none',
                       relief='solid',
                       bordercolor=colors['border'],
                       font=('Segoe UI', 9))
        
        style.map('TButton',
                 background=[('active', colors['hover_bg']),
                           ('pressed', colors['select_bg'])],
                 bordercolor=[('focus', colors['select_bg'])])
        
        style.configure('Accent.TButton',
                       background=colors['select_bg'],
                       foreground=colors['select_fg'],
                       borderwidth=1,
                       focuscolor='none',
                       relief='solid',
                       bordercolor=colors['select_bg'],
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Accent.TButton',
                 background=[('active', '#106ebe'),
                           ('pressed', '#005a9e')])
        
        style.configure('TCheckbutton',
                       background=colors['bg'],
                       foreground=colors['fg'],
                       focuscolor='none',
                       font=('Segoe UI', 9))
        
        style.map('TCheckbutton',
                 background=[('active', colors['bg'])])
        
        style.configure('TCombobox',
                       foreground='#ffffff',
                       fieldbackground='#404040',
                       background='#404040',
                       borderwidth=1,
                       arrowcolor='#ffffff',
                       relief='solid',
                       bordercolor=colors['border'],
                       font=('Segoe UI', 9),
                       insertcolor='#ffffff')
        
        style.map('TCombobox',
                 bordercolor=[('focus', colors['select_bg'])],
                 fieldbackground=[('readonly', '#404040')],
                 foreground=[('readonly', '#ffffff')])
        
        # Configuration manuelle pour les listes déroulantes des combobox
        self.root.option_add('*TCombobox*Listbox.Background', '#404040')
        self.root.option_add('*TCombobox*Listbox.Foreground', '#ffffff')
        self.root.option_add('*TCombobox*Listbox.selectBackground', colors['select_bg'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
        self.root.option_add('*TCombobox*Listbox.borderWidth', '1')
        self.root.option_add('*TCombobox*Listbox.relief', 'solid')
        
        style.configure('TSpinbox',
                       foreground='#ffffff',
                       fieldbackground='#404040',
                       borderwidth=1,
                       arrowcolor='#ffffff',
                       relief='solid',
                       bordercolor=colors['border'],
                       font=('Segoe UI', 9))
        
        style.map('TSpinbox',
                 bordercolor=[('focus', colors['select_bg'])])
        
        style.configure('TProgressbar',
                       background=colors['select_bg'],
                       troughcolor='#404040',
                       borderwidth=1,
                       lightcolor=colors['select_bg'],
                       darkcolor=colors['select_bg'],
                       relief='solid')
        
        style.configure('Horizontal.TSeparator',
                       background=colors['border'])
    
    def apply_dark_style_to_widgets(self):
        """Appliquer le style sombre aux widgets après leur création."""
        try:
            # Configurer les options pour les listes déroulantes
            self.root.option_add('*TCombobox*Listbox.Background', '#1a1a1a')
            self.root.option_add('*TCombobox*Listbox.Foreground', '#ffffff')
            self.root.option_add('*TCombobox*Listbox.selectBackground', '#0078d4')
            self.root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
            
            # Forcer la mise à jour des styles
            style = ttk.Style()
            style.configure('TCombobox',
                           foreground='#ffffff',
                           fieldbackground='#404040',
                           background='#404040')
            
        except Exception as e:
            self.logger.debug(f"Error applying dark theme: {e}")
    
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

        # Scrollable container
        self.canvas = tk.Canvas(self.root, bg='#1e1e1e', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(self.canvas, bg='#1e1e1e')
        self.canvas_window = self.canvas.create_window((0, 0), window=main_frame, anchor='nw')

        # Update scroll region when content changes
        def on_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        main_frame.bind('<Configure>', on_configure)

        # Make canvas window fill width
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', on_canvas_configure)

        # Enable mousewheel scrolling
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.canvas.bind_all('<MouseWheel>', on_mousewheel)

        # Add padding inside main_frame
        main_frame.configure(padx=20, pady=20)
        
        # === Header avec logo ===
        header_frame = tk.Frame(main_frame, bg='#1e1e1e')
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Charger et afficher le logo dans l'en-tête
        try:
            logo_path = Path(__file__).parent.parent / "RSGM_v1a.png"
            if logo_path.exists() and PIL_AVAILABLE:
                image = Image.open(logo_path)
                # Redimensionner pour l'en-tête (plus petit)
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                self.header_logo = ImageTk.PhotoImage(image)
                
                logo_frame = tk.Frame(header_frame, bg='#1e1e1e')
                logo_frame.pack(side=tk.LEFT, padx=(0, 20))
                
                logo_label = tk.Label(logo_frame, image=self.header_logo, bg='#1e1e1e')
                logo_label.pack()
            
            # Informations de l'application
            info_frame = tk.Frame(header_frame, bg='#1e1e1e')
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            title_label = tk.Label(info_frame, text="RockSmith Guitar Mute", 
                                 font=("Segoe UI", 22, "bold"), 
                                 fg='#ffffff', bg='#1e1e1e')
            title_label.pack(anchor=tk.W)
            
            subtitle_label = tk.Label(info_frame, text="Graphical Interface for PSARC Processing", 
                                    font=("Segoe UI", 12), 
                                    fg='#cccccc', bg='#1e1e1e')
            subtitle_label.pack(anchor=tk.W, pady=(5, 0))
            
        except Exception as e:
            self.logger.error(f"Error loading header logo: {e}")
            # In case of error, display only the title
            title_label = tk.Label(header_frame, text="RockSmith Guitar Mute", 
                                 font=("Segoe UI", 22, "bold"), 
                                 fg='#ffffff', bg='#1e1e1e')
            title_label.pack(anchor=tk.W)
        
        # Ligne de séparation avec style amélioré
        separator_frame = tk.Frame(main_frame, height=2, bg='#555555')
        separator_frame.pack(fill=tk.X, pady=(0, 25))
        
        # === File Selection Section ===
        files_frame = self.create_section_frame(main_frame, "File Selection")
        files_frame.pack(fill=tk.X, pady=(0, 20))
        
        files_content = tk.Frame(files_frame, bg='#2d2d2d')
        files_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Input
        input_label = tk.Label(files_content, text="Input File/Folder:", 
                              font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d')
        input_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        input_frame = tk.Frame(files_content, bg='#2d2d2d')
        input_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 15))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_path, 
                                   bg='#404040', fg='#ffffff', insertbackground='#ffffff',
                                   relief='solid', bd=1, font=("Segoe UI", 10))
        self.input_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 10))
        
        input_file_btn = self.create_button(input_frame, "File", self.select_input_file)
        input_file_btn.grid(row=0, column=1, padx=5)
        
        input_folder_btn = self.create_button(input_frame, "Folder", self.select_input_folder)
        input_folder_btn.grid(row=0, column=2, padx=5)
        
        # Output
        output_label = tk.Label(files_content, text="Output Folder:", 
                               font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d')
        output_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        
        output_frame = tk.Frame(files_content, bg='#2d2d2d')
        output_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_path, 
                                    bg='#404040', fg='#ffffff', insertbackground='#ffffff',
                                    relief='solid', bd=1, font=("Segoe UI", 10))
        self.output_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 10))
        
        output_btn = self.create_button(output_frame, "Browse", self.select_output_folder)
        output_btn.grid(row=0, column=1)
        
        files_content.columnconfigure(0, weight=1)
        
        # === Options Section ===
        options_frame = self.create_section_frame(main_frame, "Processing Options")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        options_content = tk.Frame(options_frame, bg='#2d2d2d')
        options_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Checkbox
        self.overwrite_check = tk.Checkbutton(
            options_content, 
            text="Allow overwriting existing files",
            variable=self.overwrite_var,
            bg='#2d2d2d', fg='#ffffff', selectcolor='#404040',
            font=("Segoe UI", 10), activebackground='#2d2d2d', activeforeground='#ffffff'
        )
        self.overwrite_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))
        
        # Options en ligne
        tk.Label(options_content, text="Demucs Model:", 
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.model_combo = ttk.Combobox(
            options_content, 
            textvariable=self.model_var,
            values=["htdemucs_6s", "htdemucs", "htdemucs_ft", "mdx_extra", "mdx"],
            state="readonly",
            width=15,
            font=("Segoe UI", 9)
        )
        self.model_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        tk.Label(options_content, text="Device:", 
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        
        self.device_combo = ttk.Combobox(
            options_content,
            textvariable=self.device_var,
            values=["auto", "cpu", "cuda"],
            state="readonly",
            width=15,
            font=("Segoe UI", 9)
        )
        self.device_combo.grid(row=1, column=3, sticky=tk.W)
        
        tk.Label(options_content, text="Number of processes:", 
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').grid(row=2, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        
        self.workers_spin = tk.Spinbox(
            options_content,
            from_=1,
            to=os.cpu_count() * 2,
            textvariable=self.workers_var,
            width=15,
            bg='#404040', fg='#ffffff', insertbackground='#ffffff',
            relief='solid', bd=1, font=("Segoe UI", 9)
        )
        self.workers_spin.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))

        # Vocals reduction
        tk.Label(options_content, text="Vocals Volume %:",
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').grid(row=2, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 10))

        self.vocals_spin = tk.Spinbox(
            options_content,
            from_=0,
            to=100,
            textvariable=self.reduce_vocals_var,
            width=15,
            bg='#404040', fg='#ffffff', insertbackground='#ffffff',
            relief='solid', bd=1, font=("Segoe UI", 9)
        )
        self.vocals_spin.grid(row=2, column=3, sticky=tk.W, pady=(10, 0))

        # === Variant Selection Section ===
        variants_frame = self.create_section_frame(main_frame, "Stem Mix Variants")
        variants_frame.pack(fill=tk.X, pady=(0, 20))

        variants_content = tk.Frame(variants_frame, bg='#2d2d2d')
        variants_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        variant_descriptions = {
            "no_guitar": "No Guitar  (drums, bass, vocals, piano, other)",
            "no_vocals": "No Vocals  (drums, bass, piano, other, guitar)",
            "no_bass": "No Bass  (drums, vocals, piano, other, guitar)",
            "no_guitar_no_bass": "No Guitar + No Bass  (drums, vocals, piano, other)",
            "no_guitar_no_bass_no_vocals": "No Guitar + No Bass + No Vocals  (drums, piano, other)",
            "drums_only": "Drums Only  (drums)",
            "vocals_and_drums": "Vocals + Drums  (vocals, drums)",
        }

        # Two-column layout for checkboxes
        row = 0
        col = 0
        for variant_name, description in variant_descriptions.items():
            cb = tk.Checkbutton(
                variants_content,
                text=description,
                variable=self.variant_vars[variant_name],
                bg='#2d2d2d', fg='#ffffff', selectcolor='#404040',
                font=("Segoe UI", 9), activebackground='#2d2d2d', activeforeground='#ffffff'
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # Select All / Deselect All buttons
        variant_btn_frame = tk.Frame(variants_content, bg='#2d2d2d')
        variant_btn_frame.grid(row=row + 1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        select_all_btn = self.create_button(variant_btn_frame, "Select All", self.select_all_variants)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))

        deselect_all_btn = self.create_button(variant_btn_frame, "Deselect All", self.deselect_all_variants)
        deselect_all_btn.pack(side=tk.LEFT)

        # === Custom Variant Section ===
        custom_frame = self.create_section_frame(main_frame, "Custom Variant Builder")
        custom_frame.pack(fill=tk.X, pady=(0, 20))

        custom_content = tk.Frame(custom_frame, bg='#2d2d2d')
        custom_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Name field
        name_row = tk.Frame(custom_content, bg='#2d2d2d')
        name_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(name_row, text="Name:",
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').pack(side=tk.LEFT, padx=(0, 10))

        self.custom_name_var = tk.StringVar()
        self.custom_name_entry = tk.Entry(name_row, textvariable=self.custom_name_var,
                                          bg='#404040', fg='#ffffff', insertbackground='#ffffff',
                                          relief='solid', bd=1, font=("Segoe UI", 10), width=25)
        self.custom_name_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Stem checkboxes in a row
        stems_row = tk.Frame(custom_content, bg='#2d2d2d')
        stems_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(stems_row, text="Include:",
                font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d').pack(side=tk.LEFT, padx=(0, 10))

        self.custom_stem_vars = {}
        for stem in ["drums", "bass", "vocals", "piano", "guitar", "other"]:
            var = tk.BooleanVar(value=False)
            self.custom_stem_vars[stem] = var
            cb = tk.Checkbutton(stems_row, text=stem, variable=var,
                               bg='#2d2d2d', fg='#ffffff', selectcolor='#404040',
                               font=("Segoe UI", 9), activebackground='#2d2d2d', activeforeground='#ffffff')
            cb.pack(side=tk.LEFT, padx=(0, 10))

        # Add button
        add_row = tk.Frame(custom_content, bg='#2d2d2d')
        add_row.pack(fill=tk.X, pady=(0, 5))

        add_btn = self.create_button(add_row, "Add Custom Variant", self.add_custom_variant)
        add_btn.pack(side=tk.LEFT)

        # List of added custom variants
        self.custom_list_frame = tk.Frame(custom_content, bg='#2d2d2d')
        self.custom_list_frame.pack(fill=tk.X)

        # === Progress Section ===
        progress_frame = self.create_section_frame(main_frame, "Progress")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        progress_content = tk.Frame(progress_frame, bg='#2d2d2d')
        progress_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_content,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style='TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(progress_content, textvariable=self.status_var, 
                                   font=("Segoe UI", 10), fg='#ffffff', bg='#2d2d2d')
        self.status_label.pack(anchor=tk.W)
        
        # === Control Buttons Section ===
        control_frame = tk.Frame(main_frame, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = self.create_accent_button(
            control_frame,
            "Start Processing",
            self.start_processing
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.pause_button = self.create_button(
            control_frame,
            "Pause",
            self.pause_processing,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.cancel_button = self.create_button(
            control_frame,
            "Cancel",
            self.cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT)
        
        # === Logs Section ===
        logs_frame = self.create_section_frame(main_frame, "Activity Log")
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        logs_content = tk.Frame(logs_frame, bg='#2d2d2d')
        logs_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Text area with scrollbar
        log_text_frame = tk.Frame(logs_content, bg='#2d2d2d')
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_text_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#1a1a1a',
            fg='#ffffff',
            insertbackground='#ffffff',
            selectbackground='#0078d4',
            selectforeground='#ffffff',
            font=("Consolas", 9),
            relief='solid',
            bd=1
        )
        
        log_scrollbar = tk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        log_controls = tk.Frame(logs_content, bg='#2d2d2d')
        log_controls.pack(fill=tk.X, pady=(10, 0))
        
        clear_btn = self.create_button(log_controls, "Clear Logs", self.clear_logs)
        clear_btn.pack(side=tk.RIGHT)
    
    def create_section_frame(self, parent, title):
        """Créer un frame de section avec titre."""
        section_frame = tk.Frame(parent, bg='#1e1e1e')
        
        # Titre de la section
        title_frame = tk.Frame(section_frame, bg='#333333', height=35)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text=title, 
                              font=("Segoe UI", 11, "bold"), 
                              fg='#ffffff', bg='#333333')
        title_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        return section_frame
    
    def create_button(self, parent, text, command, state=tk.NORMAL):
        """Créer un bouton avec le style sombre."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg='#404040',
            fg='#ffffff',
            activebackground='#505050',
            activeforeground='#ffffff',
            relief='solid',
            bd=1,
            font=("Segoe UI", 9),
            padx=15,
            pady=5,
            state=state
        )
        return btn
    
    def create_accent_button(self, parent, text, command, state=tk.NORMAL):
        """Créer un bouton accent avec le style sombre."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg='#0078d4',
            fg='#ffffff',
            activebackground='#106ebe',
            activeforeground='#ffffff',
            relief='solid',
            bd=1,
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            state=state
        )
        return btn
    
    def setup_layout(self):
        """Configure layout and styles."""
        # Style for main button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("", 10, "bold"))
    
    def select_input_file(self):
        """Select an input file."""
        filename = filedialog.askopenfilename(
            title="Select a PSARC file",
            filetypes=[("PSARC Files", "*.psarc"), ("All files", "*.*")]
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
    
    def select_all_variants(self):
        """Select all variant checkboxes."""
        for var in self.variant_vars.values():
            var.set(True)

    def deselect_all_variants(self):
        """Deselect all variant checkboxes."""
        for var in self.variant_vars.values():
            var.set(False)

    def add_custom_variant(self):
        """Add a custom variant from the builder fields."""
        name = self.custom_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name for the custom variant.")
            return

        # Sanitize name: replace spaces with underscores, remove special chars
        import re
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()

        stems = [s for s, var in self.custom_stem_vars.items() if var.get()]
        if not stems:
            messagebox.showerror("Error", "Please select at least one stem.")
            return

        # Check for duplicate names
        existing = [n for n, _ in self.custom_variants]
        if name in existing or name in self.variant_vars:
            messagebox.showerror("Error", f"Variant '{name}' already exists.")
            return

        self.custom_variants.append((name, stems))
        self._refresh_custom_list()

        # Clear inputs
        self.custom_name_var.set("")
        for var in self.custom_stem_vars.values():
            var.set(False)

    def remove_custom_variant(self, name):
        """Remove a custom variant by name."""
        self.custom_variants = [(n, s) for n, s in self.custom_variants if n != name]
        self._refresh_custom_list()

    def _refresh_custom_list(self):
        """Redraw the custom variants list."""
        for widget in self.custom_list_frame.winfo_children():
            widget.destroy()

        for name, stems in self.custom_variants:
            row = tk.Frame(self.custom_list_frame, bg='#2d2d2d')
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=f"{name}  ({', '.join(stems)})",
                    font=("Segoe UI", 9), fg='#cccccc', bg='#2d2d2d').pack(side=tk.LEFT, padx=(0, 10))

            remove_btn = tk.Button(row, text="X", command=lambda n=name: self.remove_custom_variant(n),
                                   bg='#602020', fg='#ffffff', activebackground='#803030',
                                   activeforeground='#ffffff', relief='solid', bd=1,
                                   font=("Segoe UI", 8, "bold"), padx=5, pady=0)
            remove_btn.pack(side=tk.LEFT)

    def get_selected_variants(self) -> list:
        """Return list of selected variant names (built-in + custom)."""
        return [name for name, var in self.variant_vars.items() if var.get()] + \
               [name for name, _ in self.custom_variants]

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
            messagebox.showerror("Error", f"Input path does not exist: {input_path}")
            return False

        if not self.get_selected_variants():
            messagebox.showerror("Error", "Please select at least one variant.")
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
        
        self.status_var.set("Initialisation...")
        self.progress_var.set(0)
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_files, daemon=False)  # Not daemon
        self.processing_thread.start()
    
    def pause_processing(self):
        """Pause or resume processing."""
        if self.paused:
            self.paused = False
            self.pause_button.config(text="Pause")
            self.status_var.set("Reprise du traitement...")
            self.message_queue.put(('log', "Traitement repris"))
        else:
            self.paused = True
            self.pause_button.config(text="> Reprendre")
            self.status_var.set("Traitement en pause...")
            self.message_queue.put(('log', "Traitement mis en pause"))
    
    def cancel_processing(self):
        """Cancel current processing."""
        result = messagebox.askyesno("Confirmation", "Are you sure you want to cancel the processing?")
        if result:
            self.cancelled = True
            self.status_var.set("Annulation...")
            self.message_queue.put(('log', "Annulation demandée par l'utilisateur"))
    
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
                device=self.device_var.get(),
                reduce_vocals=self.reduce_vocals_var.get()
            )

            # Register custom variants in VARIANT_CONFIGS
            for name, stems in self.custom_variants:
                VARIANT_CONFIGS[name] = {"suffix": f"_{name}", "include_stems": stems}

            selected_variants = self.get_selected_variants()
            self.message_queue.put(('log', f"Selected variants: {', '.join(selected_variants)}"))
            
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
            
            num_inputs = len(files_to_process)
            num_variants = len(selected_variants)
            total_outputs = num_inputs * num_variants
            self.message_queue.put(('log', f"Processing {num_inputs} file(s) x {num_variants} variant(s) = {total_outputs} expected output(s)"))

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
                self.message_queue.put(('status', f"Processing {psarc_file.name} ({i+1}/{num_inputs}) - {processed_count}/{total_outputs} outputs complete"))
                self.message_queue.put(('progress', (processed_count / total_outputs) * 100))

                try:
                    # File processing
                    results = processor.process_psarc_file(
                        psarc_file,
                        output_path,
                        force=self.overwrite_var.get(),
                        variants=selected_variants
                    )

                    # Check for cancellation after processing
                    if self.cancelled or self.shutdown_requested:
                        break

                    if results:
                        processed_count += len(results)
                        for r in results:
                            self.message_queue.put(('log', f"[OK] Variant created: {r.name}"))
                        self.message_queue.put(('progress', (processed_count / total_outputs) * 100))
                    else:
                        self.message_queue.put(('log', f"[WARN] File skipped: {psarc_file.name}"))

                except Exception as e:
                    self.message_queue.put(('log', f"[ERROR] Error processing {psarc_file.name}: {e}"))
                    # Check for cancellation after error
                    if self.cancelled or self.shutdown_requested:
                        break

            # Processing completed
            if not self.cancelled and not self.shutdown_requested:
                self.message_queue.put(('status', f"Complete! {processed_count}/{total_outputs} outputs produced"))
                self.message_queue.put(('log', f"Processing complete! {processed_count}/{total_outputs} output file(s) produced"))
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
            messagebox.showinfo("Terminé", "Le traitement est terminé !")
    
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
        print("Démarrage de l'interface graphique...")
        
        # Application closing configuration
        def on_closing():
            print("Fermeture de l'application demandée")
            self.logger.info("Application close requested")
            
            if self.processing:
                result = messagebox.askyesno(
                    "Confirmation",
                    "Un traitement est en cours. Voulez-vous vraiment quitter ?"
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
            print("Nettoyage des ressources...")
            self.cleanup()
            
            # Destroy the GUI
            try:
                self.root.quit()
                self.root.destroy()
                print("[OK] Interface fermée proprement")
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
            print("Lancement de la boucle principale tkinter...")
            # Start main loop
            self.root.mainloop()
            print("[OK] Boucle principale terminée")
        except KeyboardInterrupt:
            print("[WARN] Interruption clavier détectée")
            on_closing()
        except Exception as e:
            print(f"[ERROR] Erreur dans la boucle principale: {e}")
            self.logger.error(f"Error in main loop: {e}")
            on_closing()
        finally:
            print("Nettoyage final...")
            self.cleanup()
            # Final force exit as last resort
            try:
                os._exit(0)
            except:
                pass


def main():
    """Main entry point for the graphical interface."""
    
    print("Point d'entrée principal de l'interface graphique")
    
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
            print("[OK] Gestionnaires de signaux configurés")
        except:
            pass
    
    app = None
    try:
        print("Création de l'instance RocksmithGuitarMuteGUI...")
        app = RocksmithGuitarMuteGUI()
        print("[OK] Instance créée avec succès")
        
        print("Lancement de l'application...")
        app.run()
        print("[OK] Application terminée normalement")
        
    except KeyboardInterrupt:
        print("[WARN] Application interrompue par l'utilisateur")
        if app:
            app.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] ERREUR CRITIQUE: {e}")
        print(f"Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Critical Error", f"Error starting application: {e}")
        except:
            print(f"Impossible d'afficher la boîte de dialogue d'erreur")
        if app:
            app.cleanup()
        sys.exit(1)
    finally:
        print("Nettoyage final de l'application...")
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
        
        print("[OK] Nettoyage final terminé")
        
        # Force exit
        try:
            sys.exit(0)
        except:
            os._exit(0)


if __name__ == "__main__":
    main()
