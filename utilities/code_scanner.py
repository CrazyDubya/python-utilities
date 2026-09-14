
import os
from pathlib import Path
import sqlite3
import json

def scan_directory(start_path: str = ".") -> str:
    """Scan directory and create a representation of all relevant files and their contents"""
    output = []

    # Supported file extensions and specific file types
    supported_files = ['.py', '.db', '.ipynb', 'requirements.txt', 'config.ini']

    for root, dirs, files in os.walk(start_path):
        for file in files:
            filepath = os.path.join(root, file)
            ext = Path(file).suffix

            if ext in supported_files or file in supported_files:
                output.append(f"\n{'='*80}")
                output.append(f"FILE: {filepath}")
                output.append(f"{'='*80}")

                # Process SQLite databases
                if ext == '.db':
                    try:
                        conn = sqlite3.connect(filepath)
                        cursor = conn.cursor()
                        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        for table in tables:
                            output.append(table[0])
                        conn.close()
                    except Exception as e:
                        output.append(f"Error reading database: {e}")

                # Process Jupyter Notebooks
                elif ext == '.ipynb':
                    try:
                        with open(filepath, 'r', encoding='utf-8') as nb_file:
                            notebook = json.load(nb_file)
                            for cell in notebook.get('cells', []):
                                if cell['cell_type'] == 'markdown':
                                    output.append("\n".join(cell.get('source', [])))
                                elif cell['cell_type'] == 'code':
                                    output.append("CODE:")
                                    output.append("\n".join(cell.get('source', [])))
                    except Exception as e:
                        output.append(f"Error reading notebook: {e}")

                # Process other text-based files
                else:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as text_file:
                            output.append(text_file.read())
                    except Exception as e:
                        output.append(f"Error reading file: {e}")

    return "\n".join(output)

if __name__ == "__main__":
    print(scan_directory("."))
