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

import argparse
import asyncio
import logging
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torchaudio
import soundfile as sf
import numpy as np

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


class RocksmithGuitarMute:
    """Main class for processing Rocksmith PSARC files to remove guitar tracks."""
    
    def __init__(self, demucs_model: str = "htdemucs", device: str = "auto"):
        """
        Initialize the processor.
        
        Args:
            demucs_model: Demucs model to use for source separation
            device: Device to use for processing ("cpu", "cuda", or "auto")
        """
        self.demucs_model = demucs_model
        self.device = self._get_device(device)
        self.logger = logging.getLogger(__name__)
        
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
            check=False
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
        rs_utils_bin = Path("rs-utils/bin")
        ww2ogg = rs_utils_bin / "ww2ogg.exe"
        revorb = rs_utils_bin / "revorb.exe"
        packed_codebooks = Path("rs-utils/share/packed_codebooks.bin")
        
        # Convert WEM to OGG
        temp_ogg = output_path.with_suffix('.ogg')
        
        subprocess.run(
            [str(ww2ogg), str(wem_path), "-o", str(temp_ogg), "--pcb", str(packed_codebooks)], 
            check=True
        )
        
        # Try revorb for better compatibility
        try:
            subprocess.run([str(revorb), str(temp_ogg)], check=True)
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
    
    def remove_guitar_track(self, audio_path: Path, output_path: Path) -> None:
        """
        Remove guitar track from audio using Demucs.
        
        Args:
            audio_path: Path to the input audio file
            output_path: Path for the output backing track
        """
        self.logger.info(f"Processing audio with Demucs: {audio_path.name}")
        
        # Create temporary directory for demucs output
        temp_dir = output_path.parent / "demucs_temp"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Build demucs command arguments
            args = [
                "--name", self.demucs_model,
                "--device", self.device,
                "--out", str(temp_dir),
                str(audio_path)
            ]
            
            self.logger.debug(f"Running demucs with args: {args}")
            
            # Run demucs separation
            demucs.separate.main(args)
            
            # Find the separated stems directory
            stems_dir = temp_dir / self.demucs_model / audio_path.stem
            
            if not stems_dir.exists():
                raise FileNotFoundError(f"Demucs output directory not found: {stems_dir}")
            
            # Load separated stems
            stems = {}
            for stem_file in stems_dir.glob("*.wav"):
                stem_name = stem_file.stem
                audio, sr = torchaudio.load(str(stem_file))
                stems[stem_name] = audio
                self.logger.debug(f"Loaded stem: {stem_name}")
            
            # Combine all sources except 'other' (which typically contains guitar)
            backing_stems = []
            exclude_stems = ['other']  # 'other' typically contains guitar/lead instruments
            
            for stem_name, stem_audio in stems.items():
                if stem_name not in exclude_stems:
                    backing_stems.append(stem_audio)
                    self.logger.info(f"Including stem: {stem_name}")
                else:
                    self.logger.info(f"Excluding stem: {stem_name} (contains guitar)")
            
            # Mix the backing tracks
            if backing_stems:
                backing_track = torch.stack(backing_stems).sum(dim=0)
            else:
                # Fallback: use drums + bass + vocals if available
                fallback_stems = ['drums', 'bass', 'vocals']
                backing_track = None
                for stem_name in fallback_stems:
                    if stem_name in stems:
                        if backing_track is None:
                            backing_track = stems[stem_name].clone()
                        else:
                            backing_track += stems[stem_name]
                        self.logger.info(f"Using fallback stem: {stem_name}")
                
                if backing_track is None:
                    raise ValueError("No suitable stems found for backing track")
            
            # Save the backing track
            torchaudio.save(str(output_path), backing_track, sr)
            
            self.logger.info(f"Backing track saved: {output_path}")
            
        finally:
            # Clean up temporary directory
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
        audio2wem_script = Path("audio2wem_windows.py")
        
        if not audio2wem_script.exists():
            self.logger.error("audio2wem_windows.py script not found")
            raise RuntimeError("WEM conversion failed: audio2wem_windows.py not found")
        
        # Import and use the conversion function directly
        try:
            sys.path.insert(0, str(Path.cwd()))
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
    
    def _output_exists(self, psarc_path: Path, output_dir: Path) -> bool:
        """
        Check if the output file already exists.
        
        Args:
            psarc_path: Path to the input PSARC file
            output_dir: Directory for output files
            
        Returns:
            True if output file already exists
        """
        output_psarc = output_dir / psarc_path.name
        return output_psarc.exists()

    def process_psarc_file(self, psarc_path: Path, output_dir: Path, force: bool = False) -> Optional[Path]:
        """
        Process a single PSARC file to remove guitar tracks.
        
        Args:
            psarc_path: Path to the input PSARC file
            output_dir: Directory for output files
            force: If True, process even if output file exists
            
        Returns:
            Path to the processed PSARC file or None if skipped
        """
        self.logger.info(f"Processing PSARC file: {psarc_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_psarc = output_dir / psarc_path.name
        
        # Check if output already exists
        if not force and self._output_exists(psarc_path, output_dir):
            self.logger.info(f"Output file already exists, skipping: {output_psarc}")
            return output_psarc
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "extracted"
            
            try:
                # Step 1: Unpack PSARC
                self.unpack_psarc(psarc_path, extract_dir)
                
                # Step 2: Find and process audio files
                audio_files = self.find_audio_files(extract_dir)
                
                for audio_file in audio_files:
                    if audio_file.suffix.lower() == '.wem':
                        # Convert WEM to WAV for processing
                        wav_file = audio_file.with_suffix('.wav')
                        self.convert_wem_to_wav(audio_file, wav_file)
                        
                        # Remove guitar track
                        processed_wav = wav_file.with_name(f"{wav_file.stem}_processed.wav")
                        self.remove_guitar_track(wav_file, processed_wav)
                        
                        # Convert back to WEM and replace original
                        self.convert_wav_to_wem(processed_wav, audio_file)
                        
                        # Clean up temporary files
                        wav_file.unlink(missing_ok=True)
                        processed_wav.unlink(missing_ok=True)
                    
                    elif audio_file.suffix.lower() in ['.ogg', '.wav']:
                        # Process directly
                        processed_file = audio_file.with_name(f"{audio_file.stem}_processed{audio_file.suffix}")
                        self.remove_guitar_track(audio_file, processed_file)
                        
                        # Replace original with processed version
                        shutil.move(processed_file, audio_file)
                
                # Step 3: Repack PSARC
                self.repack_psarc(extract_dir, output_psarc)
                
            except Exception as e:
                self.logger.error(f"Error processing {psarc_path}: {e}")
                raise
        
        return output_psarc
    
    def process_input(self, input_path: Path, output_dir: Path, max_workers: Optional[int] = None, force: bool = False) -> List[Path]:
        """
        Process input path (file or directory) and return list of processed files.
        Uses parallel processing to maximize performance.
        
        Args:
            input_path: Path to input file or directory
            output_dir: Directory for output files
            max_workers: Maximum number of parallel workers (default: number of CPU cores)
            force: If True, process even if output file exists
            
        Returns:
            List of processed PSARC file paths
        """
        processed_files = []
        
        # Determine max workers (default to number of CPU cores)
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        self.logger.info(f"Using {max_workers} parallel workers for processing")
        
        if input_path.is_file():
            if input_path.suffix.lower() == '.psarc':
                # Single file processing
                processed_file = self.process_psarc_file(input_path, output_dir, force=force)
                if processed_file:
                    processed_files.append(processed_file)
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
                if force or not self._output_exists(psarc_file, output_dir):
                    files_to_process.append(psarc_file)
                else:
                    # File already exists, add to results but don't process
                    existing_file = output_dir / psarc_file.name
                    processed_files.append(existing_file)
                    self.logger.info(f"Output already exists, skipping: {existing_file}")
            
            self.logger.info(f"Processing {len(files_to_process)} files ({len(psarc_files) - len(files_to_process)} skipped)")
            
            if files_to_process:
                # Prepare arguments for parallel processing
                process_args = [
                    (psarc_file, output_dir, self.demucs_model, self.device, force)
                    for psarc_file in files_to_process
                ]
                
                # Use ProcessPoolExecutor for CPU-bound tasks
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_file = {
                        executor.submit(process_single_psarc_worker, args): args[0] 
                        for args in process_args
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_file):
                        psarc_file = future_to_file[future]
                        try:
                            result = future.result()
                            if result:
                                processed_files.append(result)
                                self.logger.info(f"Successfully processed: {result}")
                            else:
                                self.logger.error(f"Failed to process: {psarc_file}")
                        except Exception as e:
                            self.logger.error(f"Exception processing {psarc_file}: {e}")
        
        else:
            raise ValueError(f"Input path does not exist: {input_path}")
        
        return processed_files


def process_single_psarc_worker(args_tuple: Tuple[Path, Path, str, str, bool]) -> Optional[Path]:
    """
    Worker function for parallel processing of PSARC files.
    
    Args:
        args_tuple: Tuple containing (psarc_path, output_dir, demucs_model, device, force)
        
    Returns:
        Path to processed file or None if skipped/failed
    """
    psarc_path, output_dir, demucs_model, device, force = args_tuple
    
    try:
        # Create a new processor instance for this worker
        processor = RocksmithGuitarMute(demucs_model=demucs_model, device=device)
        return processor.process_psarc_file(psarc_path, output_dir, force=force)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to process {psarc_path}: {e}")
        return None


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('rocksmith_guitar_mute.log')
        ]
    )


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
        default="htdemucs",
        help="Demucs model to use for source separation (default: htdemucs)"
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate inputs
        if not args.input_path.exists():
            logger.error(f"Input path does not exist: {args.input_path}")
            sys.exit(1)
        
        # Initialize processor
        processor = RocksmithGuitarMute(
            demucs_model=args.model,
            device=args.device
        )
        
        # Process files
        logger.info("Starting RockSmith Guitar Mute processing...")
        processed_files = processor.process_input(
            args.input_path, 
            args.output_dir, 
            max_workers=args.workers,
            force=args.force
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