#!/usr/bin/env python3
"""
Towarzysz V9 - Main Entry Point
"""

import sys
sys.dont_write_bytecode = True
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(__file__))

from core.loop import main_loop

if __name__ == "__main__":
    print("=" * 60)
    print("Towarzysz V9")
    print("System zarządzania projektami i monitorowania")
    print("- Obsidian & Todoist Integration")
    print("=" * 60)
    print("\nNaciśnij Ctrl+C aby zatrzymać system\n")
    
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--once", action="store_true")
        args = parser.parse_args()
        main_loop(max_cycles=1 if args.once else None)
    except KeyboardInterrupt:
        print("\n\nSystem zatrzymany.")
    except Exception as e:
        print(f"\n\nWystąpił błąd: {e}")
        sys.exit(1)
