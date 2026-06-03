#!/usr/bin/env python3
"""
Development Assistant V2 - Main Entry Point
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(__file__))

from core.loop import main_loop

if __name__ == "__main__":
    print("=" * 60)
    print("Development Assistant V2")
    print("System zarządzania projektami i monitorowania")
    print("- Obsidian & Todoist Integration")
    print("=" * 60)
    print("\nNaciśnij Ctrl+C aby zatrzymać system\n")
    
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\nSystem zatrzymany.")
    except Exception as e:
        print(f"\n\nWystąpił błąd: {e}")
        sys.exit(1)