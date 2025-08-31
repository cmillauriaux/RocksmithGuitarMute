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

# Import main module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rocksmith_guitar_mute import RocksmithGuitarMute, setup_logging


class RocksmithGuitarMuteGUI:
    """Interface graphique pour RockSmith Guitar Mute."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RockSmith Guitar Mute - Interface Graphique")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)
        self.model_var = tk.StringVar(value="htdemucs_6s")
        self.device_var = tk.StringVar(value="auto")
        self.workers_var = tk.IntVar(value=os.cpu_count())
        
        # État du traitement
        self.processing = False
        self.paused = False
        self.cancelled = False
        self.processor = None
        self.processing_thread = None
        
        # Queue pour la communication entre threads
        self.message_queue = queue.Queue()
        
        # Configuration du logging
        self.setup_gui_logging()
        
        # Création de l'interface
        self.create_widgets()
        self.setup_layout()
        
        # Démarrage du monitoring des messages
        self.check_queue()
    
    def setup_gui_logging(self):
        """Configure le logging pour l'interface graphique."""
        # Logger pour l'interface
        self.logger = logging.getLogger("GUI")
        self.logger.setLevel(logging.INFO)
        
        # Handler personnalisé pour envoyer les logs vers la GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, message_queue):
                super().__init__()
                self.message_queue = message_queue
            
            def emit(self, record):
                msg = self.format(record)
                self.message_queue.put(('log', msg))
        
        gui_handler = GUILogHandler(self.message_queue)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Ajouter le handler au logger principal
        root_logger = logging.getLogger()
        root_logger.addHandler(gui_handler)
    
    def create_widgets(self):
        """Crée tous les widgets de l'interface."""
        
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === Section Sélection des fichiers ===
        files_frame = ttk.LabelFrame(main_frame, text="Sélection des fichiers", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Entrée/Sortie
        ttk.Label(files_frame, text="Fichier/Dossier d'entrée:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        input_frame = ttk.Frame(files_frame)
        input_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=2)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_path, width=60)
        self.input_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(input_frame, text="Fichier", command=self.select_input_file).grid(row=0, column=1, padx=2)
        ttk.Button(input_frame, text="Dossier", command=self.select_input_folder).grid(row=0, column=2, padx=2)
        
        ttk.Label(files_frame, text="Dossier de sortie:").grid(row=2, column=0, sticky=tk.W, pady=(10, 2))
        
        output_frame = ttk.Frame(files_frame)
        output_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=2)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=60)
        self.output_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(output_frame, text="Parcourir", command=self.select_output_folder).grid(row=0, column=1)
        
        files_frame.columnconfigure(0, weight=1)
        
        # === Section Options ===
        options_frame = ttk.LabelFrame(main_frame, text="Options de traitement", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkbox pour écraser les fichiers
        self.overwrite_check = ttk.Checkbutton(
            options_frame, 
            text="Autoriser l'écrasement des fichiers existants",
            variable=self.overwrite_var
        )
        self.overwrite_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Modèle Demucs
        ttk.Label(options_frame, text="Modèle Demucs:").grid(row=1, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            options_frame, 
            textvariable=self.model_var,
            values=["htdemucs_6s", "htdemucs", "htdemucs_ft", "mdx_extra", "mdx"],
            state="readonly",
            width=20
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Device
        ttk.Label(options_frame, text="Périphérique:").grid(row=2, column=0, sticky=tk.W, pady=2)
        device_combo = ttk.Combobox(
            options_frame,
            textvariable=self.device_var,
            values=["auto", "cpu", "cuda"],
            state="readonly",
            width=20
        )
        device_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Nombre de workers
        ttk.Label(options_frame, text="Nombre de processus:").grid(row=3, column=0, sticky=tk.W, pady=2)
        workers_spin = ttk.Spinbox(
            options_frame,
            from_=1,
            to=os.cpu_count() * 2,
            textvariable=self.workers_var,
            width=20
        )
        workers_spin.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # === Section Progression ===
        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Barre de progression
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Label de statut
        self.status_var = tk.StringVar(value="Prêt")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        # === Section Boutons de contrôle ===
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame,
            text="Démarrer le traitement",
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
            text="Annuler",
            command=self.cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # === Section Logs ===
        logs_frame = ttk.LabelFrame(main_frame, text="Journal d'activité", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        # Zone de texte avec scrollbar
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
        
        # Bouton pour effacer les logs
        ttk.Button(logs_frame, text="Effacer les logs", command=self.clear_logs).pack(anchor=tk.E, pady=(5, 0))
    
    def setup_layout(self):
        """Configure la disposition et les styles."""
        # Style pour le bouton principal
        style = ttk.Style()
        style.configure("Accent.TButton", font=("", 10, "bold"))
    
    def select_input_file(self):
        """Sélectionne un fichier d'entrée."""
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier PSARC",
            filetypes=[("Fichiers PSARC", "*.psarc"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
    
    def select_input_folder(self):
        """Sélectionne un dossier d'entrée."""
        folder = filedialog.askdirectory(title="Sélectionner un dossier contenant des fichiers PSARC")
        if folder:
            self.input_path.set(folder)
    
    def select_output_folder(self):
        """Sélectionne le dossier de sortie."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if folder:
            self.output_path.set(folder)
    
    def validate_inputs(self) -> bool:
        """Valide les entrées utilisateur."""
        if not self.input_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier ou dossier d'entrée.")
            return False
        
        if not self.output_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sortie.")
            return False
        
        input_path = Path(self.input_path.get())
        if not input_path.exists():
            messagebox.showerror("Erreur", f"Le chemin d'entrée n'existe pas: {input_path}")
            return False
        
        return True
    
    def start_processing(self):
        """Démarre le traitement en arrière-plan."""
        if not self.validate_inputs():
            return
        
        # Vérification des fichiers existants si nécessaire
        if not self.overwrite_var.get():
            input_path = Path(self.input_path.get())
            output_path = Path(self.output_path.get())
            
            if input_path.is_file():
                output_file = output_path / input_path.name
                if output_file.exists():
                    result = messagebox.askyesno(
                        "Fichier existant",
                        f"Le fichier {output_file.name} existe déjà. Voulez-vous le remplacer?"
                    )
                    if not result:
                        return
            else:
                # Vérifier s'il y a des fichiers qui seraient écrasés
                psarc_files = list(input_path.glob("*.psarc"))
                existing_files = [f for f in psarc_files if (output_path / f.name).exists()]
                
                if existing_files:
                    result = messagebox.askyesno(
                        "Fichiers existants",
                        f"{len(existing_files)} fichier(s) existe(nt) déjà dans le dossier de sortie. "
                        "Voulez-vous les remplacer?"
                    )
                    if not result:
                        return
        
        # Mise à jour de l'interface
        self.processing = True
        self.paused = False
        self.cancelled = False
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.NORMAL)
        
        self.status_var.set("Initialisation...")
        self.progress_var.set(0)
        
        # Démarrage du thread de traitement
        self.processing_thread = threading.Thread(target=self.process_files, daemon=True)
        self.processing_thread.start()
    
    def pause_processing(self):
        """Met en pause ou reprend le traitement."""
        if self.paused:
            self.paused = False
            self.pause_button.config(text="Pause")
            self.status_var.set("Reprise du traitement...")
            self.message_queue.put(('log', "Traitement repris"))
        else:
            self.paused = True
            self.pause_button.config(text="Reprendre")
            self.status_var.set("Traitement en pause...")
            self.message_queue.put(('log', "Traitement mis en pause"))
    
    def cancel_processing(self):
        """Annule le traitement en cours."""
        result = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir annuler le traitement?")
        if result:
            self.cancelled = True
            self.status_var.set("Annulation en cours...")
            self.message_queue.put(('log', "Annulation demandée par l'utilisateur"))
    
    def process_files(self):
        """Traite les fichiers en arrière-plan."""
        try:
            # Configuration du logging pour ce thread
            setup_logging(verbose=True)
            
            # Initialisation du processeur
            self.message_queue.put(('log', f"Initialisation avec le modèle {self.model_var.get()}"))
            self.message_queue.put(('status', "Initialisation du processeur..."))
            
            processor = RocksmithGuitarMute(
                demucs_model=self.model_var.get(),
                device=self.device_var.get()
            )
            
            input_path = Path(self.input_path.get())
            output_path = Path(self.output_path.get())
            
            # Déterminer les fichiers à traiter
            if input_path.is_file():
                files_to_process = [input_path] if input_path.suffix.lower() == '.psarc' else []
            else:
                files_to_process = list(input_path.glob("*.psarc"))
            
            if not files_to_process:
                self.message_queue.put(('log', "Aucun fichier PSARC trouvé"))
                self.message_queue.put(('status', "Aucun fichier à traiter"))
                return
            
            total_files = len(files_to_process)
            self.message_queue.put(('log', f"Traitement de {total_files} fichier(s)"))
            
            processed_count = 0
            
            for i, psarc_file in enumerate(files_to_process):
                if self.cancelled:
                    self.message_queue.put(('log', "Traitement annulé"))
                    break
                
                # Gestion de la pause
                while self.paused and not self.cancelled:
                    threading.Event().wait(0.1)
                
                if self.cancelled:
                    break
                
                # Mise à jour du statut
                self.message_queue.put(('status', f"Traitement de {psarc_file.name} ({i+1}/{total_files})"))
                self.message_queue.put(('progress', (i / total_files) * 100))
                
                try:
                    # Traitement du fichier
                    result = processor.process_psarc_file(
                        psarc_file,
                        output_path,
                        force=self.overwrite_var.get()
                    )
                    
                    if result:
                        processed_count += 1
                        self.message_queue.put(('log', f"✓ Fichier traité avec succès: {result.name}"))
                    else:
                        self.message_queue.put(('log', f"⚠ Fichier ignoré: {psarc_file.name}"))
                
                except Exception as e:
                    self.message_queue.put(('log', f"✗ Erreur lors du traitement de {psarc_file.name}: {e}"))
                
                # Mise à jour de la progression
                self.message_queue.put(('progress', ((i + 1) / total_files) * 100))
            
            # Traitement terminé
            if not self.cancelled:
                self.message_queue.put(('status', f"Traitement terminé - {processed_count}/{total_files} fichiers traités"))
                self.message_queue.put(('log', f"Traitement terminé avec succès! {processed_count} fichier(s) traité(s)"))
                self.message_queue.put(('progress', 100))
            
        except Exception as e:
            self.message_queue.put(('log', f"Erreur critique: {e}"))
            self.message_queue.put(('status', "Erreur lors du traitement"))
        
        finally:
            # Réinitialisation de l'interface
            self.message_queue.put(('processing_done', None))
    
    def check_queue(self):
        """Vérifie la queue des messages et met à jour l'interface."""
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
        
        # Programmer la prochaine vérification
        self.root.after(100, self.check_queue)
    
    def add_log_message(self, message: str):
        """Ajoute un message au journal d'activité."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_logs(self):
        """Efface le journal d'activité."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def processing_finished(self):
        """Appelée quand le traitement est terminé."""
        self.processing = False
        self.paused = False
        self.cancelled = False
        
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pause")
        self.cancel_button.config(state=tk.DISABLED)
        
        if not self.cancelled:
            messagebox.showinfo("Terminé", "Le traitement est terminé!")
    
    def run(self):
        """Lance l'interface graphique."""
        # Configuration de la fermeture de l'application
        def on_closing():
            if self.processing:
                result = messagebox.askyesno(
                    "Confirmation",
                    "Un traitement est en cours. Voulez-vous vraiment quitter?"
                )
                if not result:
                    return
                self.cancelled = True
            
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Démarrage de la boucle principale
        self.root.mainloop()


def main():
    """Point d'entrée principal pour l'interface graphique."""
    try:
        app = RocksmithGuitarMuteGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Erreur critique", f"Erreur lors du démarrage de l'application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
