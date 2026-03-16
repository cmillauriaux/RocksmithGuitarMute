#!/usr/bin/env python3
"""
RockSmith Guitar Mute - A tool for removing guitar tracks from Rocksmith 2014 PSARC files

This program:
1. Unpacks Rocksmith 2014 PSARC files using Rocksmith2014.NET
2. Extracts audio files from the Rocksmith format
3. Uses Demucs AI to separate guitar from other instruments
4. Replaces the original audio with the processed backing track
5. Repacks the modified PSARC file

Usage:
    python rocksmith_guitar_mute.py <input_path> <output_dir> [options]
    
Where:
    input_path: Path to a PSARC file or directory containing PSARC files
    output_dir: Directory where processed files will be saved
"""

# Fix for PyInstaller stdout/stderr issues
import sys
import io
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

import argparse
import asyncio
import logging
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torchaudio
import soundfile as sf
import numpy as np


def find_project_root() -> Path:
    """
    Find the project root directory by looking for key files.
    Works from any subdirectory of the project.
    """
    current = Path(__file__).parent.resolve()
    
    # Look for characteristic files that indicate the project root
    markers = ['rs-utils', 'demucs', 'requirements.txt', 'setup.py']
    
    while current != current.parent:  # Stop at filesystem root
        if all((current / marker).exists() for marker in markers[:2]):  # rs-utils and demucs are essential
            return current
        current = current.parent
    
    # Fallback: assume current directory is project root
    return Path(__file__).parent.resolve()


def patch_subprocess_for_silence():
    """Patch subprocess module to ensure all calls are silent on Windows."""
    if sys.platform == "win32":
        import subprocess
        original_run = subprocess.run
        original_popen = subprocess.Popen
        original_call = subprocess.call
        
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
            
        def silent_call(*args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return original_call(*args, **kwargs)
        
        subprocess.run = silent_run
        subprocess.Popen = silent_popen
        subprocess.call = silent_call

# Demucs imports
try:
    import demucs.separate
    import shlex
except ImportError:
    print("Error: Demucs is not installed. Please install it with: pip install demucs")
    sys.exit(1)

# rsrtools imports for PSARC handling
try:
    sys.path.insert(0, str(Path("rsrtools/src").resolve()))
    from rsrtools.files.welder import Welder
except ImportError:
    print("Error: rsrtools is not available. Please clone the rsrtools repository.")
    sys.exit(1)


VARIANT_CONFIGS = {
    "no_vocals": {"suffix": "_no_vocals", "include_stems": ["drums", "bass", "piano", "other", "guitar"]},
    "drums_only": {"suffix": "_drums_only", "include_stems": ["drums"]},
    "no_guitar": {"suffix": "_no_guitar", "include_stems": ["drums", "bass", "vocals", "piano", "other"]},
    "no_bass": {"suffix": "_no_bass", "include_stems": ["drums", "vocals", "piano", "other", "guitar"]},
    "no_guitar_no_bass": {"suffix": "_no_guitar_no_bass", "include_stems": ["drums", "vocals", "piano", "other"]},
    "vocals_and_drums": {"suffix": "_vocals_and_drums", "include_stems": ["vocals", "drums"]},
    "no_guitar_no_bass_no_vocals": {"suffix": "_no_guitar_no_bass_no_vocals", "include_stems": ["drums", "piano", "other"]},
}
ALL_STEMS = ["drums", "bass", "vocals", "piano", "guitar", "other"]
DEFAULT_VARIANTS = ["no_guitar"]
ALL_VARIANTS = list(VARIANT_CONFIGS.keys())


def parse_custom_variant(spec: str) -> tuple:
    """Parse a custom variant spec like 'my_mix:drums,vocals,piano'.

    Returns (name, config_dict) or raises ValueError.
    """
    if ":" not in spec:
        raise ValueError(f"Custom variant must be in 'name:stem1,stem2,...' format, got: {spec}")
    name, stems_str = spec.split(":", 1)
    name = name.strip()
    if not name:
        raise ValueError("Custom variant name cannot be empty")
    stems = [s.strip() for s in stems_str.split(",") if s.strip()]
    invalid = [s for s in stems if s not in ALL_STEMS]
    if invalid:
        raise ValueError(f"Unknown stems: {invalid}. Valid stems: {ALL_STEMS}")
    if not stems:
        raise ValueError("Custom variant must include at least one stem")
    return name, {"suffix": f"_{name}", "include_stems": stems}


class RocksmithGuitarMute:
    """Main class for processing Rocksmith PSARC files to remove guitar tracks."""
    
    def __init__(self, demucs_model: str = "htdemucs_6s", device: str = "auto", reduce_vocals: int = 100):
        """
        Initialize the processor.
        
        Args:
            demucs_model: Demucs model to use for source separation
            device: Device to use for processing ("cpu", "cuda", or "auto")
            reduce_vocals: Vocals volume reduction percentage (0-100, 100 = original volume)
        """
        # Apply subprocess patches for silent operation
        patch_subprocess_for_silence()
        
        self.demucs_model = demucs_model
        self.device = self._get_device(device)
        self.reduce_vocals = reduce_vocals
        self.logger = logging.getLogger(__name__)
        
        # Find project root for tool paths
        self.project_root = find_project_root()
        self.logger.debug(f"Project root detected at: {self.project_root}")
        
        self.logger.info(f"Initialized RocksmithGuitarMute with model {demucs_model} on {self.device}")
    
    def _get_device(self, device: str) -> str:
        """Determine the best device to use for processing."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def _load_audio_file(self, audio_path: Path) -> Tuple[torch.Tensor, int]:
        """
        Load audio file with appropriate backend based on file extension.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple of (audio_tensor, sample_rate)
        """
        file_ext = audio_path.suffix.lower()
        
        if file_ext in ['.ogg', '.flac']:
            # Use soundfile for OGG and FLAC files
            data, sr = sf.read(str(audio_path))
            
            # Convert to torch tensor
            if len(data.shape) == 1:
                # Mono to stereo
                audio = torch.from_numpy(data).float().unsqueeze(0)
            else:
                # Multi-channel, transpose to (channels, samples)
                audio = torch.from_numpy(data.T).float()
            
            return audio, sr
        
        else:
            # Use torchaudio for WAV and other formats
            return torchaudio.load(str(audio_path))
    
    def _run_dotnet_command(self, args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """
        Run a .NET command and return the result.
        
        Args:
            args: Command arguments
            cwd: Working directory for the command
            
        Returns:
            Completed process result
        """
        cmd = ["dotnet", "run", "--project", "Rocksmith2014.NET/samples/MiscTools"] + args
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        if result.returncode != 0:
            self.logger.error(f"Command failed with return code {result.returncode}")
            self.logger.error(f"STDOUT: {result.stdout}")
            self.logger.error(f"STDERR: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        
        return result
    
    def unpack_psarc(self, psarc_path: Path, extract_dir: Path) -> None:
        """
        Unpack a PSARC file using rsrtools welder.
        
        Args:
            psarc_path: Path to the PSARC file
            extract_dir: Directory to extract files to
        """
        self.logger.info(f"Unpacking PSARC: {psarc_path}")
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure we have absolute paths
        psarc_path = psarc_path.resolve()
        extract_dir = extract_dir.resolve()
        
        # Change to extract directory for unpacking
        original_cwd = Path.cwd()
        try:
            os.chdir(extract_dir)
            
            # Use rsrtools welder to unpack PSARC
            with Welder(psarc_path, mode="r") as psarc:
                psarc.unpack()
                
                # Count files for logging
                file_count = sum(1 for _ in psarc)
                self.logger.info(f"Successfully extracted {file_count} files from {psarc_path.name}")
                
        finally:
            os.chdir(original_cwd)
    
    def find_audio_files(self, extract_dir: Path) -> List[Path]:
        """
        Find audio files in the extracted PSARC directory.
        
        Args:
            extract_dir: Directory containing extracted PSARC files
            
        Returns:
            List of audio file paths
        """
        audio_extensions = ['.wem', '.ogg', '.wav', '.flac']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(extract_dir.rglob(f"*{ext}"))
        
        self.logger.info(f"Found {len(audio_files)} audio files")
        for audio_file in audio_files:
            self.logger.debug(f"  - {audio_file.name} ({audio_file.suffix})")
        
        return audio_files
    
    def convert_wem_to_wav(self, wem_path: Path, output_path: Path) -> None:
        """
        Convert WEM file to WAV using Rocksmith2014.NET tools.
        
        Args:
            wem_path: Path to the WEM file
            output_path: Path for the output WAV file
        """
        self.logger.info(f"Converting WEM to WAV: {wem_path.name}")
        
        # Use ww2ogg and revorb tools from rs-utils
        rs_utils_bin = self.project_root / "rs-utils/bin"
        ww2ogg = rs_utils_bin / "ww2ogg.exe"
        revorb = rs_utils_bin / "revorb.exe"
        packed_codebooks = self.project_root / "rs-utils/share/packed_codebooks.bin"
        
        # Convert WEM to OGG
        temp_ogg = output_path.with_suffix('.ogg')
        
        subprocess.run(
            [str(ww2ogg), str(wem_path), "-o", str(temp_ogg), "--pcb", str(packed_codebooks)], 
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        # Try revorb for better compatibility
        try:
            subprocess.run(
                [str(revorb), str(temp_ogg)], 
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            self.logger.info("revorb processing completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"revorb failed (code {e.returncode}), continuing with ww2ogg output")
        
        # Convert OGG to WAV using soundfile (more robust for converted OGG files)
        try:
            audio_data, sr = sf.read(str(temp_ogg))
            # Convert to tensor and ensure correct shape
            if len(audio_data.shape) == 1:
                audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)  # Add channel dimension
            else:
                audio_tensor = torch.from_numpy(audio_data.T)  # Transpose for correct channel order
            
            torchaudio.save(str(output_path), audio_tensor, sr)
            self.logger.info(f"Successfully converted WEM to WAV: {output_path.name}")
        except Exception as e:
            self.logger.error(f"Failed to load OGG with soundfile: {e}")
            # Fallback: try with torchaudio
            try:
                audio, sr = torchaudio.load(str(temp_ogg))
                torchaudio.save(str(output_path), audio, sr)
                self.logger.info(f"Successfully converted with torchaudio fallback: {output_path.name}")
            except Exception as e2:
                self.logger.error(f"Both soundfile and torchaudio failed: {e2}")
                raise
        
        # Clean up temporary OGG
        temp_ogg.unlink()
    
    def separate_stems(self, audio_path: Path, temp_dir: Path) -> Tuple[Dict[str, torch.Tensor], int]:
        """
        Run Demucs source separation on an audio file.

        Args:
            audio_path: Path to the input audio file
            temp_dir: Directory for Demucs output (caller manages cleanup)

        Returns:
            Tuple of (stems_dict, sample_rate)
        """
        self.logger.info(f"Running Demucs source separation: {audio_path.name}")

        # Build demucs command arguments
        args = [
            "--name", self.demucs_model,
            "--device", self.device,
            "--out", str(temp_dir),
            str(audio_path)
        ]

        self.logger.debug(f"Running demucs with args: {args}")

        # Run demucs separation with proper stdout/stderr handling for PyInstaller
        import sys
        import io
        import contextlib

        # Create safe stdout/stderr if they are None (PyInstaller issue)
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()

        # Capture output to prevent PyInstaller issues
        captured_output = io.StringIO()
        captured_error = io.StringIO()

        with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(captured_error):
            try:
                demucs.separate.main(args)
            except SystemExit as e:
                # demucs.separate.main may call sys.exit(), which is normal
                if e.code != 0:
                    self.logger.error(f"Demucs processing failed with exit code: {e.code}")
                    self.logger.error(f"Demucs stderr: {captured_error.getvalue()}")
                    raise RuntimeError(f"Demucs processing failed")

        # Log captured output for debugging
        output_str = captured_output.getvalue()
        error_str = captured_error.getvalue()
        if output_str:
            self.logger.debug(f"Demucs stdout: {output_str}")
        if error_str:
            self.logger.debug(f"Demucs stderr: {error_str}")

        # Find the separated stems directory
        stems_dir = temp_dir / self.demucs_model / audio_path.stem

        if not stems_dir.exists():
            raise FileNotFoundError(f"Demucs output directory not found: {stems_dir}")

        # Load separated stems
        stems = {}
        sr = None
        for stem_file in stems_dir.glob("*.wav"):
            stem_name = stem_file.stem
            audio, current_sr = torchaudio.load(str(stem_file))
            stems[stem_name] = audio
            if sr is None:
                sr = current_sr
            self.logger.debug(f"Loaded stem: {stem_name}")

        if not stems:
            raise FileNotFoundError(f"No audio stems found in: {stems_dir}")

        if sr is None:
            raise ValueError("Could not determine sample rate from audio files")

        self.logger.info(f"Separated into {len(stems)} stems: {', '.join(stems.keys())}")
        return stems, sr

    def mix_stems(self, stems: Dict[str, torch.Tensor], sr: int,
                  include_stems: list, output_path: Path,
                  reduce_vocals: int = 100) -> None:
        """
        Mix selected stems into a single audio file.

        Args:
            stems: Dictionary of stem_name -> audio tensor
            sr: Sample rate
            include_stems: List of stem names to include in the mix
            output_path: Path for the output audio file
            reduce_vocals: Vocals volume percentage (0-100)
        """
        selected = []
        for stem_name in include_stems:
            if stem_name in stems:
                audio = stems[stem_name]
                # Apply vocals reduction if needed
                if stem_name == 'vocals' and reduce_vocals < 100:
                    factor = reduce_vocals / 100.0
                    audio = audio * factor
                    self.logger.debug(f"Applied vocals reduction: {reduce_vocals}%")
                selected.append(audio)
                self.logger.debug(f"Including stem: {stem_name}")
            else:
                self.logger.warning(
                    f"Stem '{stem_name}' not available from model '{self.demucs_model}'. "
                    f"Available stems: {list(stems.keys())}. "
                    f"Use 'htdemucs_6s' model for guitar/piano separation."
                )

        if not selected:
            raise ValueError(f"No matching stems found for: {include_stems}")

        mixed = torch.stack(selected).sum(dim=0)
        torchaudio.save(str(output_path), mixed, sr)
        self.logger.debug(f"Mixed track saved: {output_path}")

    def remove_guitar_track(self, audio_path: Path, output_path: Path, save_guitar: bool = False) -> None:
        """
        Remove guitar track from audio using Demucs.
        Backward-compatible wrapper around separate_stems() and mix_stems().
        """
        temp_dir = output_path.parent / "demucs_temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            stems, sr = self.separate_stems(audio_path, temp_dir)

            # Determine which stems to include (exclude guitar)
            if self.demucs_model == "htdemucs_6s":
                include = [s for s in stems if s != 'guitar']
            else:
                include = [s for s in stems if s != 'other']

            self.mix_stems(stems, sr, include, output_path, self.reduce_vocals)

            if save_guitar:
                guitar_stem = 'guitar' if self.demucs_model == "htdemucs_6s" else 'other'
                if guitar_stem in stems:
                    guitar_path = output_path.with_name(f"{output_path.stem}_guitar{output_path.suffix}")
                    torchaudio.save(str(guitar_path), stems[guitar_stem], sr)
                    self.logger.info(f"Guitar track saved: {guitar_path}")
        finally:
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def convert_wav_to_wem(self, wav_path: Path, wem_path: Path) -> None:
        """
        Convert WAV file to WEM format using rs-utils audio2wem.
        
        Args:
            wav_path: Path to the WAV file
            wem_path: Path for the output WEM file
        """
        self.logger.info(f"Converting WAV to WEM: {wav_path.name}")
        
        # Use our Python version of audio2wem for Windows compatibility
        audio2wem_script = self.project_root / "audio2wem_windows.py"
        
        if not audio2wem_script.exists():
            self.logger.error("audio2wem_windows.py script not found")
            raise RuntimeError("WEM conversion failed: audio2wem_windows.py not found")
        
        # Import and use the conversion function directly
        try:
            sys.path.insert(0, str(self.project_root))
            from audio2wem_windows import convert_audio_to_wem
            
            self.logger.info(f"Converting {wav_path.name} to WEM format...")
            success = convert_audio_to_wem(wav_path, wem_path)
            
            if success:
                self.logger.info(f"Successfully converted to WEM: {wem_path.name}")
            else:
                raise RuntimeError("WEM conversion failed: audio2wem_windows returned False")
                
        except ImportError as e:
            self.logger.error(f"Failed to import audio2wem_windows: {e}")
            raise RuntimeError(f"WEM conversion failed: {e}")
        except Exception as e:
            self.logger.error(f"WEM conversion failed: {e}")
            raise RuntimeError(f"WEM conversion failed: {e}")
    
    def repack_psarc(self, extract_dir: Path, output_psarc: Path) -> None:
        """
        Repack the modified files into a new PSARC using rsrtools welder.
        
        Args:
            extract_dir: Directory containing the modified files  
            output_psarc: Path for the output PSARC file
        """
        self.logger.info(f"Repacking PSARC: {output_psarc}")
        
        # Find the extracted directory (should be the only directory in extract_dir)
        extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if not extracted_dirs:
            raise ValueError(f"No extracted directory found in {extract_dir}")
        
        source_dir = extracted_dirs[0]  # Should be something like "2minutes_p"
        
        # Ensure output directory exists
        output_psarc.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove .psarc extension from output path for welder
        output_dir = output_psarc.parent / output_psarc.stem
        
        # Copy source directory to the target location for packing
        if output_dir.exists():
            shutil.rmtree(output_dir)
        shutil.copytree(source_dir, output_dir)
        
        try:
            # Use rsrtools welder to pack PSARC
            with Welder(output_dir, mode="w") as psarc:
                pass  # The packing happens in the constructor
                
            self.logger.info(f"Successfully repacked PSARC: {output_psarc}")
            
            # Move the created PSARC to the final destination
            created_psarc = output_dir.parent / f"{output_dir.name}.psarc"
            if created_psarc != output_psarc:
                shutil.move(str(created_psarc), str(output_psarc))
                
        finally:
            # Clean up temporary directory
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def _make_variant_unique(self, variant_dir: Path, variant_name: str) -> None:
        """
        Build a fresh PSARC directory for this variant with correctly-named files
        from the start, so all internal references are consistent.

        Instead of renaming files in-place (which breaks some tools), this method:
        1. Reads the original extracted directory
        2. Creates a new directory structure with the variant key in all filenames
        3. Copies files to their new locations
        4. Updates all metadata (manifests, HSAN, xblock, aggregategraph) with
           consistent references matching the new filenames
        5. Updates BNK prefetch DATA to match the remixed audio
        """
        import uuid
        import json
        import struct

        config = VARIANT_CONFIGS[variant_name]

        # Find the top-level song directory (there should be exactly one)
        song_dirs = [d for d in variant_dir.iterdir() if d.is_dir()]
        if not song_dirs:
            self.logger.warning("No song directory found in variant dir, skipping uniqueness")
            return
        song_dir = song_dirs[0]

        # Detect the original DLC key from manifest JSON
        original_key_mixed = None
        manifest_files = list(song_dir.rglob("*.json"))
        if manifest_files:
            data = json.loads(manifest_files[0].read_text(encoding="utf-8"))
            for entry in data.get("Entries", {}).values():
                attrs = entry.get("Attributes", {})
                if "DLCKey" in attrs:
                    original_key_mixed = attrs["DLCKey"]
                    break

        if not original_key_mixed:
            self.logger.warning("Could not detect DLC key, skipping uniqueness")
            return

        original_key_lower = original_key_mixed.lower()
        new_key_mixed = f"{original_key_mixed}{config['suffix'].title().replace('_', '')}"
        new_key_lower = new_key_mixed.lower()

        # Human-readable label for SongName
        variant_display = variant_name.replace("_", " ").title()

        self.logger.info(f"Making variant unique: {original_key_mixed} -> {new_key_mixed}")

        # Build a single PID mapping from original PID -> new PID, shared across
        # manifest JSONs and HSAN so cross-references stay consistent.
        pid_mapping = {}
        for json_file in song_dir.rglob("*.json"):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            for entry_id in data.get("Entries", {}):
                if entry_id not in pid_mapping:
                    pid_mapping[entry_id] = uuid.uuid4().hex.upper()

        # Create new song directory with the variant key name
        new_song_dir = variant_dir / song_dir.name  # keep PSARC stem for Welder
        # We'll rebuild in-place by processing each file

        # Step 1: Copy all files to new locations with updated names.
        # Build a mapping of old_relative_path -> new_relative_path
        file_mapping = {}  # {old_path: new_path}
        for item in sorted(song_dir.rglob("*")):
            if not item.is_file():
                continue
            rel = item.relative_to(song_dir)
            rel_str = str(rel).replace("\\", "/")

            # Replace key in path components
            new_rel_str = rel_str.replace(original_key_lower, new_key_lower)
            file_mapping[rel] = Path(new_rel_str)

        # Create a temporary new directory, copy files with new names
        new_dir = variant_dir / f"{song_dir.name}__new"
        for old_rel, new_rel in file_mapping.items():
            src = song_dir / old_rel
            dst = new_dir / new_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Replace old directory with new one
        shutil.rmtree(song_dir)
        new_dir.rename(song_dir)

        # Step 2: Update JSON manifest files
        for json_file in song_dir.rglob("*.json"):
            data = json.loads(json_file.read_text(encoding="utf-8"))

            new_entries = {}
            for entry_id, entry in data.get("Entries", {}).items():
                attrs = entry.get("Attributes", {})
                new_pid = pid_mapping.get(entry_id, uuid.uuid4().hex.upper())

                if "DLCKey" in attrs:
                    attrs["DLCKey"] = new_key_mixed
                if "SongKey" in attrs:
                    attrs["SongKey"] = new_key_mixed
                if "PersistentID" in attrs:
                    attrs["PersistentID"] = new_pid
                if "SongName" in attrs:
                    attrs["SongName"] = f"{attrs['SongName']} ({variant_display})"
                if "FullName" in attrs:
                    attrs["FullName"] = attrs["FullName"].replace(original_key_mixed, new_key_mixed)

                # Update SongBank/PreviewBankPath to match new filenames
                for bank_field in ("SongBank", "PreviewBankPath"):
                    if bank_field in attrs and isinstance(attrs[bank_field], str):
                        attrs[bank_field] = attrs[bank_field].replace(original_key_lower, new_key_lower)

                # Update URN-style references to match new file paths.
                # Skip SongEvent — it references the Wwise event name baked into the
                # .bnk HIRC section; changing it would silence the audio.
                for key, val in attrs.items():
                    if isinstance(val, str) and val.startswith("urn:") and original_key_lower in val:
                        attrs[key] = val.replace(original_key_lower, new_key_lower)

                entry["Attributes"] = attrs
                new_entries[new_pid] = entry

            data["Entries"] = new_entries
            json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Step 3: Update HSAN files with same PID mapping
        for hsan_file in song_dir.rglob("*.hsan"):
            data = json.loads(hsan_file.read_text(encoding="utf-8"))

            new_entries = {}
            for entry_id, entry in data.get("Entries", {}).items():
                new_pid = pid_mapping.get(entry_id, uuid.uuid4().hex.upper())
                attrs = entry.get("Attributes", {})

                if "DLCKey" in attrs:
                    attrs["DLCKey"] = new_key_mixed
                if "SongKey" in attrs:
                    attrs["SongKey"] = new_key_mixed
                if "PersistentID" in attrs:
                    attrs["PersistentID"] = new_pid
                if "SongName" in attrs and attrs["SongName"]:
                    attrs["SongName"] = f"{attrs['SongName']} ({variant_display})"
                if "FullName" in attrs:
                    attrs["FullName"] = attrs["FullName"].replace(original_key_mixed, new_key_mixed)

                for bank_field in ("SongBank", "PreviewBankPath"):
                    if bank_field in attrs and isinstance(attrs[bank_field], str):
                        attrs[bank_field] = attrs[bank_field].replace(original_key_lower, new_key_lower)

                for key, val in attrs.items():
                    if isinstance(val, str) and val.startswith("urn:") and original_key_lower in val:
                        attrs[key] = val.replace(original_key_lower, new_key_lower)

                entry["Attributes"] = attrs
                new_entries[new_pid] = entry

            data["Entries"] = new_entries
            hsan_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Step 4: Update xblock XML — references already match new filenames
        for xblock_file in song_dir.rglob("*.xblock"):
            text = xblock_file.read_bytes().decode("utf-8-sig")
            text = text.replace(original_key_lower, new_key_lower)
            text = text.replace(original_key_mixed, new_key_mixed)
            xblock_file.write_text(text, encoding="utf-8-sig")

        # Step 5: Update aggregategraph .nt — references already match new filenames
        for nt_file in song_dir.rglob("*.nt"):
            text = nt_file.read_bytes().decode("utf-8-sig")
            text = text.replace(original_key_lower, new_key_lower)
            nt_file.write_text(text, encoding="utf-8-sig")

        # Step 6: Rename WEM files to new media IDs so they don't collide
        # with the original PSARC's audio when both are loaded in Rocksmith.
        import hashlib
        wem_id_mapping = {}  # {old_id_str: new_id_str}
        audio_dir = None
        for wem_file in song_dir.rglob("*.wem"):
            audio_dir = wem_file.parent
            old_id = wem_file.stem
            # Generate a deterministic new ID from the variant name + old ID
            hash_input = f"{new_key_lower}_{old_id}".encode()
            new_id = str(int(hashlib.md5(hash_input).hexdigest()[:8], 16))
            wem_id_mapping[old_id] = new_id
            new_wem_path = wem_file.parent / f"{new_id}.wem"
            wem_file.rename(new_wem_path)
            self.logger.info(f"Renamed WEM: {old_id}.wem -> {new_id}.wem")

        # Step 7: Update BNK files — replace ALL occurrences of old media IDs
        # (DIDX, HIRC sound objects, etc.) and update prefetch DATA.
        for bnk_file in song_dir.rglob("*.bnk"):
            bnk_data = bytearray(bnk_file.read_bytes())

            # First pass: find DIDX entries and DATA section for prefetch update
            didx_entries = []  # [(old_media_id, offset_in_data, size)]
            data_section_offset = None
            pos = 0
            while pos < len(bnk_data) - 8:
                tag = bnk_data[pos:pos+4].decode('ascii', errors='replace')
                chunk_len = struct.unpack_from('<I', bnk_data, pos+4)[0]
                if tag == 'DIDX':
                    n_entries = chunk_len // 12
                    for i in range(n_entries):
                        entry_pos = pos + 8 + i * 12
                        mid = struct.unpack_from('<I', bnk_data, entry_pos)[0]
                        offset = struct.unpack_from('<I', bnk_data, entry_pos + 4)[0]
                        size = struct.unpack_from('<I', bnk_data, entry_pos + 8)[0]
                        didx_entries.append((mid, offset, size))
                elif tag == 'DATA':
                    data_section_offset = pos + 8
                pos += 8 + chunk_len

            # Binary find-and-replace of all old media IDs with new ones
            # throughout the entire BNK (covers DIDX, HIRC, and any other refs)
            for old_id_str, new_id_str in wem_id_mapping.items():
                old_bytes = struct.pack('<I', int(old_id_str))
                new_bytes = struct.pack('<I', int(new_id_str))
                search_pos = 0
                while True:
                    idx = bnk_data.find(old_bytes, search_pos)
                    if idx == -1:
                        break
                    # Don't replace inside the DATA section (raw audio)
                    if data_section_offset is not None:
                        data_end = data_section_offset
                        for _, off, sz in didx_entries:
                            end = data_section_offset + off + sz
                            if end > data_end:
                                data_end = end
                        if data_section_offset <= idx < data_end:
                            search_pos = idx + 4
                            continue
                    bnk_data[idx:idx+4] = new_bytes
                    search_pos = idx + 4

            # Update prefetch DATA from the renamed WEM files
            if didx_entries and data_section_offset is not None:
                for old_mid, offset, size in didx_entries:
                    wem_id = wem_id_mapping.get(str(old_mid), str(old_mid))
                    wem_path = bnk_file.parent / f"{wem_id}.wem"
                    if wem_path.exists():
                        new_wem_bytes = wem_path.read_bytes()
                        prefetch_bytes = new_wem_bytes[:size]
                        if len(prefetch_bytes) == size:
                            start = data_section_offset + offset
                            bnk_data[start:start+size] = prefetch_bytes

            bnk_file.write_bytes(bytes(bnk_data))

        self.logger.info(f"Variant uniqueness applied: {variant_name}")

    def _get_variant_output_path(self, psarc_path: Path, output_dir: Path, variant: str) -> Path:
        """Get the output path for a specific variant of a PSARC file."""
        suffix = VARIANT_CONFIGS[variant]["suffix"]
        stem = psarc_path.stem
        # Rocksmith only loads PSARCs ending in a platform suffix (_p, _m, _ps4, _xb1).
        # Strip it, insert the variant suffix, then restore it so the file is recognized.
        platform_suffixes = ("_p", "_m", "_ps4", "_xb1", "_ps3")
        platform = ""
        for ps in platform_suffixes:
            if stem.endswith(ps):
                stem = stem[: -len(ps)]
                platform = ps
                break
        return output_dir / f"{stem}{suffix}{platform}.psarc"

    def _output_exists(self, psarc_path: Path, output_dir: Path, variants: Optional[list] = None) -> bool:
        """
        Check if all variant output files already exist.

        Args:
            psarc_path: Path to the input PSARC file
            output_dir: Directory for output files
            variants: List of variant names to check (defaults to DEFAULT_VARIANTS)

        Returns:
            True if ALL variant output files already exist
        """
        if variants is None:
            variants = DEFAULT_VARIANTS
        return all(
            self._get_variant_output_path(psarc_path, output_dir, v).exists()
            for v in variants
        )

    def process_psarc_file(self, psarc_path: Path, output_dir: Path,
                           force: bool = False,
                           variants: Optional[list] = None) -> List[Path]:
        """
        Process a single PSARC file to produce one or more stem-mix variants.

        Args:
            psarc_path: Path to the input PSARC file
            output_dir: Directory for output files
            force: If True, process even if output files exist
            variants: List of variant names to produce (defaults to DEFAULT_VARIANTS)

        Returns:
            List of paths to the processed PSARC files
        """
        if variants is None:
            variants = DEFAULT_VARIANTS

        self.logger.info(f"Starting PSARC processing: {psarc_path}")
        self.logger.info(f"Variants to produce: {', '.join(variants)}")
        self.logger.debug(f"Input file size: {psarc_path.stat().st_size} bytes")

        # Warn if model may not support required stems
        six_stem_models = {"htdemucs_6s"}
        if self.demucs_model not in six_stem_models:
            needs_6s = set()
            for v in variants:
                config = VARIANT_CONFIGS[v]
                for s in config["include_stems"]:
                    if s in ("guitar", "piano"):
                        needs_6s.add(s)
            if needs_6s:
                self.logger.warning(
                    f"Model '{self.demucs_model}' does not separate {needs_6s} as individual stems. "
                    f"Variants referencing these stems will produce incorrect results. "
                    f"Use 'htdemucs_6s' for proper guitar/piano separation."
                )

        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if all outputs already exist
        if not force and self._output_exists(psarc_path, output_dir, variants):
            outputs = [self._get_variant_output_path(psarc_path, output_dir, v) for v in variants]
            self.logger.info(f"All variant outputs already exist, skipping")
            return outputs

        produced = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "extracted"
            demucs_dir = temp_path / "demucs_out"
            demucs_dir.mkdir()

            try:
                # Step 1: Unpack PSARC (once)
                self.unpack_psarc(psarc_path, extract_dir)

                # Step 2: Find audio files
                audio_files = self.find_audio_files(extract_dir)

                # Step 3: Separate stems for each audio file (once — the expensive step)
                # Store: {audio_file_path: (stems_dict, sample_rate, original_suffix)}
                separated = {}
                for audio_file in audio_files:
                    if audio_file.suffix.lower() == '.wem':
                        wav_file = audio_file.with_suffix('.wav')
                        self.convert_wem_to_wav(audio_file, wav_file)
                        stems, sr = self.separate_stems(wav_file, demucs_dir)
                        separated[audio_file] = (stems, sr, '.wem')
                        wav_file.unlink(missing_ok=True)
                    elif audio_file.suffix.lower() in ['.ogg', '.wav']:
                        stems, sr = self.separate_stems(audio_file, demucs_dir)
                        separated[audio_file] = (stems, sr, audio_file.suffix.lower())

                # Step 4: For each variant, mix stems, replace audio, repack
                for variant_name in variants:
                    config = VARIANT_CONFIGS[variant_name]
                    output_psarc = self._get_variant_output_path(psarc_path, output_dir, variant_name)

                    # Skip if this specific variant already exists (unless force)
                    if not force and output_psarc.exists():
                        self.logger.info(f"Variant already exists, skipping: {output_psarc.name}")
                        produced.append(output_psarc)
                        continue

                    self.logger.info(f"Building variant: {variant_name} ({config['suffix']})")

                    # Copy the extracted directory for this variant
                    variant_dir = temp_path / f"variant_{variant_name}"
                    shutil.copytree(extract_dir, variant_dir)

                    # Mix and replace each audio file
                    for original_audio, (stems, sr, orig_suffix) in separated.items():
                        # Compute relative path from extract_dir to find corresponding file in variant_dir
                        rel_path = original_audio.relative_to(extract_dir)
                        variant_audio = variant_dir / rel_path

                        # Mix stems for this variant
                        mixed_wav = variant_audio.with_name(f"{variant_audio.stem}_mixed.wav")
                        self.mix_stems(stems, sr, config["include_stems"], mixed_wav, self.reduce_vocals)

                        if orig_suffix == '.wem':
                            # Convert mixed WAV back to WEM, replacing the original
                            self.convert_wav_to_wem(mixed_wav, variant_audio)
                            mixed_wav.unlink(missing_ok=True)
                        else:
                            # Replace original with mixed version
                            shutil.move(mixed_wav, variant_audio)

                    # Make this variant's metadata unique so it doesn't collide in Rocksmith
                    self._make_variant_unique(variant_dir, variant_name)

                    # Repack this variant
                    self.repack_psarc(variant_dir, output_psarc)
                    produced.append(output_psarc)
                    self.logger.info(f"Variant complete: {output_psarc.name}")

                    # Clean up variant directory
                    shutil.rmtree(variant_dir, ignore_errors=True)

            except Exception as e:
                self.logger.error(f"Error processing {psarc_path}: {e}")
                raise

        return produced
    
    def process_input(self, input_path: Path, output_dir: Path,
                      max_workers: Optional[int] = None, force: bool = False,
                      variants: Optional[list] = None) -> List[Path]:
        """
        Process input path (file or directory) and return list of processed files.
        Uses parallel processing to maximize performance.

        Args:
            input_path: Path to input file or directory
            output_dir: Directory for output files
            max_workers: Maximum number of parallel workers (default: number of CPU cores)
            force: If True, process even if output file exists
            variants: List of variant names to produce

        Returns:
            List of processed PSARC file paths
        """
        if variants is None:
            variants = DEFAULT_VARIANTS

        processed_files = []

        # Determine max workers (default to number of CPU cores)
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()

        self.logger.info(f"Using {max_workers} parallel workers for processing")

        if input_path.is_file():
            if input_path.suffix.lower() == '.psarc':
                results = self.process_psarc_file(input_path, output_dir, force=force, variants=variants)
                processed_files.extend(results)
            else:
                self.logger.warning(f"Skipping non-PSARC file: {input_path}")

        elif input_path.is_dir():
            psarc_files = list(input_path.glob("*.psarc"))
            self.logger.info(f"Found {len(psarc_files)} PSARC files in directory")

            if not psarc_files:
                self.logger.warning("No PSARC files found in directory")
                return processed_files

            # Filter files that need processing (skip existing unless force=True)
            files_to_process = []
            for psarc_file in psarc_files:
                if force or not self._output_exists(psarc_file, output_dir, variants):
                    files_to_process.append(psarc_file)
                else:
                    existing = [self._get_variant_output_path(psarc_file, output_dir, v) for v in variants]
                    processed_files.extend(existing)
                    self.logger.info(f"All variants already exist, skipping: {psarc_file.name}")

            self.logger.info(f"Processing {len(files_to_process)} files ({len(psarc_files) - len(files_to_process)} skipped)")

            if files_to_process:
                # Prepare arguments for parallel processing
                process_args = [
                    (psarc_file, output_dir, self.demucs_model, self.device, force, self.reduce_vocals, variants)
                    for psarc_file in files_to_process
                ]

                # Use ProcessPoolExecutor for CPU-bound tasks
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    future_to_file = {
                        executor.submit(process_single_psarc_worker, args): args[0]
                        for args in process_args
                    }

                    for future in as_completed(future_to_file):
                        psarc_file = future_to_file[future]
                        try:
                            result = future.result()
                            if result:
                                processed_files.extend(result)
                                for r in result:
                                    self.logger.info(f"Successfully processed: {r}")
                            else:
                                self.logger.error(f"Failed to process: {psarc_file}")
                        except Exception as e:
                            self.logger.error(f"Exception processing {psarc_file}: {e}")

        else:
            raise ValueError(f"Input path does not exist: {input_path}")

        return processed_files


def process_single_psarc_worker(args_tuple) -> Optional[List[Path]]:
    """
    Worker function for parallel processing of PSARC files.

    Args:
        args_tuple: Tuple containing (psarc_path, output_dir, demucs_model, device, force, reduce_vocals, variants)

    Returns:
        List of paths to processed files or None if failed
    """
    psarc_path, output_dir, demucs_model, device, force, reduce_vocals, variants = args_tuple

    try:
        processor = RocksmithGuitarMute(demucs_model=demucs_model, device=device, reduce_vocals=reduce_vocals)
        return processor.process_psarc_file(psarc_path, output_dir, force=force, variants=variants)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to process {psarc_path}: {e}")
        return None


def setup_logging(verbose: bool = False, log_file: str = None) -> None:
    """Setup logging configuration with detailed diagnostic logging."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Determine log file path
    if log_file is None:
        # If running as executable, place log next to executable
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            exe_path = Path(sys.executable)
            log_file = exe_path.with_suffix('.log')
        else:
            # Running as script
            log_file = Path('rocksmith_guitar_mute.log')
    else:
        log_file = Path(log_file)
    
    # Create detailed formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler with detailed logging (always DEBUG level)
    try:
        file_handler = logging.FileHandler(str(log_file), mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        handlers.append(file_handler)
        print(f"Detailed logging enabled: {log_file}")
    except Exception as e:
        print(f"Warning: Could not create log file {log_file}: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Always DEBUG for file logging
        handlers=handlers,
        force=True
    )
    
    # Log system information at startup
    _log_system_info(log_file)


def _log_system_info(log_file: Path) -> None:
    """Log detailed system information for diagnostic purposes."""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("ROCKSMITH GUITAR MUTE - SYSTEM DIAGNOSTIC LOG")
    logger.info("=" * 80)
    
    # Basic system info
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    
    # PyInstaller info
    if getattr(sys, 'frozen', False):
        logger.info("Running as PyInstaller executable")
        logger.info(f"Executable path: {sys.executable}")
        logger.info(f"Bundled path: {getattr(sys, '_MEIPASS', 'Not available')}")
    else:
        logger.info("Running as Python script")
        logger.info(f"Script path: {__file__}")
    
    # Environment variables
    logger.info("Environment variables:")
    for key in ['PATH', 'PYTHONPATH', 'HOME', 'USERPROFILE', 'TEMP', 'TMP']:
        value = os.environ.get(key, 'Not set')
        logger.info(f"  {key}: {value}")
    
    # Working directory
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Python path
    logger.info("Python sys.path:")
    for i, path in enumerate(sys.path):
        logger.info(f"  [{i}]: {path}")
    
    # Memory info
    try:
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Total memory: {memory.total / (1024**3):.2f} GB")
        logger.info(f"Available memory: {memory.available / (1024**3):.2f} GB")
        logger.info(f"Memory usage: {memory.percent}%")
    except ImportError:
        logger.info("psutil not available - memory info not logged")
    
    # Check critical libraries
    logger.info("Checking critical libraries:")
    critical_libs = [
        ('torch', 'PyTorch for AI processing'),
        ('torchaudio', 'TorchAudio for audio processing'),
        ('demucs', 'Demucs for source separation'),
        ('soundfile', 'SoundFile for audio I/O'),
        ('numpy', 'NumPy for numerical processing'),
        ('rsrtools', 'RSRTools for PSARC handling'),
    ]
    
    for lib_name, description in critical_libs:
        try:
            lib = __import__(lib_name)
            version = getattr(lib, '__version__', 'Unknown version')
            location = getattr(lib, '__file__', 'Unknown location')
            logger.info(f"  [OK] {lib_name} ({description}): v{version}")
            logger.debug(f"     Location: {location}")
        except ImportError as e:
            logger.error(f"  [MISSING] {lib_name} ({description}): MISSING - {e}")
        except Exception as e:
            logger.warning(f"  [WARN] {lib_name} ({description}): ERROR - {e}")
    
    # PyTorch specific info
    try:
        import torch
        logger.info("PyTorch configuration:")
        logger.info(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"  CUDA version: {torch.version.cuda}")
            logger.info(f"  GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                logger.info(f"    GPU {i}: {gpu_name}")
        logger.info(f"  CPU threads: {torch.get_num_threads()}")
    except Exception as e:
        logger.error(f"Error getting PyTorch info: {e}")
    
    # Demucs models info
    try:
        import demucs.pretrained
        import io
        import contextlib
        logger.info("Checking Demucs models:")
        models_to_check = ['htdemucs_6s', 'htdemucs', 'mdx_extra_q']
        for model_name in models_to_check:
            try:
                # Capture output to prevent PyInstaller stdout/stderr issues
                captured_output = io.StringIO()
                captured_error = io.StringIO()
                
                with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(captured_error):
                    model = demucs.pretrained.get_model(model_name)
                logger.info(f"  [OK] {model_name}: Available")
            except Exception as e:
                logger.warning(f"  [WARN] {model_name}: Not available - {e}")
    except Exception as e:
        logger.error(f"Error checking Demucs models: {e}")
    
    # File system info
    logger.info("File system information:")
    try:
        project_root = find_project_root()
        logger.info(f"Project root: {project_root}")
        
        # Check for key directories/files
        key_paths = [
            'rs-utils',
            'rsrtools',
            'demucs',
            'gui',
            'input',
            'output',
            'requirements.txt'
        ]
        
        for path_name in key_paths:
            full_path = project_root / path_name
            if full_path.exists():
                if full_path.is_dir():
                    try:
                        file_count = len(list(full_path.iterdir()))
                        logger.info(f"  [OK] {path_name}/: Directory exists ({file_count} items)")
                    except:
                        logger.info(f"  [OK] {path_name}/: Directory exists (cannot count items)")
                else:
                    size = full_path.stat().st_size
                    logger.info(f"  [OK] {path_name}: File exists ({size} bytes)")
            else:
                logger.warning(f"  [MISSING] {path_name}: Missing")
                
    except Exception as e:
        logger.error(f"Error checking file system: {e}")
    
    logger.info("=" * 80)
    logger.info("END OF SYSTEM DIAGNOSTIC")
    logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Remove guitar tracks from Rocksmith 2014 PSARC files using AI source separation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python rocksmith_guitar_mute.py sample/2minutes_p.psarc output/
  
  # Process directory with parallel processing (uses all CPU cores)
  python rocksmith_guitar_mute.py input_directory/ output/
  
  # Process with specific model and device
  python rocksmith_guitar_mute.py song.psarc output/ --model htdemucs --device cuda
  
  # Force reprocessing with 4 workers
  python rocksmith_guitar_mute.py input_directory/ output/ --force --workers 4
  
  # Reduce vocals to 50% volume
  python rocksmith_guitar_mute.py song.psarc output/ --reduce-vocals 50
  
  # Mute vocals completely
  python rocksmith_guitar_mute.py song.psarc output/ --reduce-vocals 0
  
  # Skip existing files (default behavior)
  python rocksmith_guitar_mute.py input_directory/ output/ --workers 8
        """
    )
    
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to PSARC file or directory containing PSARC files"
    )
    
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where processed files will be saved"
    )
    
    parser.add_argument(
        "--model",
        default="htdemucs_6s",
        help="Demucs model to use for source separation (default: htdemucs_6s)"
    )
    
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device to use for processing (default: auto)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Process files even if output already exists"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Number of parallel workers (default: number of CPU cores)"
    )
    
    parser.add_argument(
        "--reduce-vocals",
        type=int,
        choices=range(0, 101),
        metavar="[0-100]",
        default=100,
        help="Reduce vocals volume (0 = mute, 100 = original volume, default: 100)"
    )

    parser.add_argument(
        "--variants",
        nargs="+",
        choices=list(VARIANT_CONFIGS.keys()) + ["all"],
        default=None,
        help="Stem mix variants to produce (default: no_guitar). "
             "Use 'all' to produce all variants. "
             "Available: " + ", ".join(VARIANT_CONFIGS.keys())
    )

    parser.add_argument(
        "--custom",
        action="append",
        metavar="NAME:STEMS",
        default=[],
        help="Custom variant as 'name:stem1,stem2,...'. Can be repeated. "
             "Valid stems: " + ", ".join(ALL_STEMS)
    )

    args = parser.parse_args()

    # Parse custom variants and add to VARIANT_CONFIGS
    for spec in args.custom:
        name, config = parse_custom_variant(spec)
        if name in VARIANT_CONFIGS:
            print(f"[WARN] Custom variant '{name}' overrides built-in variant")
        VARIANT_CONFIGS[name] = config

    # Resolve variants
    if args.variants is None and not args.custom:
        args.variants = DEFAULT_VARIANTS
    elif args.variants is None:
        args.variants = []

    if args.variants and "all" in args.variants:
        args.variants = ALL_VARIANTS

    # Add custom variant names to the variants list
    for spec in args.custom:
        name = spec.split(":", 1)[0].strip()
        if name not in args.variants:
            args.variants.append(name)
    
    # Setup logging first thing
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Setup global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    try:
        # Validate inputs
        if not args.input_path.exists():
            logger.error(f"Input path does not exist: {args.input_path}")
            sys.exit(1)
        
        # Initialize processor
        processor = RocksmithGuitarMute(
            demucs_model=args.model,
            device=args.device,
            reduce_vocals=args.reduce_vocals
        )
        
        # Process files
        logger.info("Starting RockSmith Guitar Mute processing...")
        processed_files = processor.process_input(
            args.input_path,
            args.output_dir,
            max_workers=args.workers,
            force=args.force,
            variants=args.variants
        )
        
        # Report results
        logger.info(f"Processing complete! Processed {len(processed_files)} files:")
        for file_path in processed_files:
            logger.info(f"  - {file_path}")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()