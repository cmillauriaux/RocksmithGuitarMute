#!/usr/bin/env python3
"""
Emergency shutdown script for RockSmith Guitar Mute
Use this if the application doesn't close properly
"""

import sys
import psutil
import time

def force_kill_rocksmith_processes():
    """Force kill all RockSmith Guitar Mute related processes."""
    print("Searching for RockSmith Guitar Mute processes...")
    
    killed_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            name = proc.info['name']
            pid = proc.info['pid']
            
            # Check if process is related to RockSmith Guitar Mute
            is_rocksmith_process = False
            
            if cmdline:
                cmdline_str = ' '.join(str(arg) for arg in cmdline).lower()
                if any(keyword in cmdline_str for keyword in [
                    'rocksmith', 'guitar_mute', 'gui_main', 'launch_gui',
                    'demucs', 'audio2wem'
                ]):
                    is_rocksmith_process = True
            
            # Also check process name
            if any(keyword in name.lower() for keyword in [
                'rocksmith', 'guitar', 'demucs'
            ]):
                is_rocksmith_process = True
            
            if is_rocksmith_process:
                print(f"Found process: PID {pid} - {name}")
                print(f"  Command: {cmdline}")
                
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    
                    # Wait for graceful termination
                    try:
                        process.wait(timeout=5)
                        print(f"  ✅ Terminated gracefully")
                    except psutil.TimeoutExpired:
                        # Force kill if necessary
                        process.kill()
                        print(f"  ⚡ Force killed")
                    
                    killed_processes.append((pid, name))
                    
                except psutil.NoSuchProcess:
                    print(f"  ℹ️  Process already terminated")
                except psutil.AccessDenied:
                    print(f"  ❌ Access denied - cannot kill process")
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return killed_processes

def main():
    print("=" * 60)
    print("ROCKSMITH GUITAR MUTE - EMERGENCY SHUTDOWN")
    print("=" * 60)
    print("This script will force kill all RockSmith Guitar Mute processes")
    print("Use this only if the application doesn't close normally")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    killed = force_kill_rocksmith_processes()
    
    if killed:
        print(f"\n✅ Killed {len(killed)} processes:")
        for pid, name in killed:
            print(f"  - PID {pid}: {name}")
    else:
        print("\nℹ️  No RockSmith Guitar Mute processes found")
    
    # Wait and check again
    print("\nWaiting 3 seconds and checking again...")
    time.sleep(3)
    
    remaining = force_kill_rocksmith_processes()
    if remaining:
        print(f"⚠️  {len(remaining)} processes still running after cleanup")
    else:
        print("🎉 All processes successfully terminated")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
