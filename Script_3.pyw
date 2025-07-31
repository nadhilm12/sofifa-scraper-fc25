# ==================================================================================================
# Script_3.pyw
#
# DESCRIPTION:
# This script creates a User Interface (UI) using Tkinter and ttkbootstrap libraries.
# The UI serves as a "launcher" or control panel to run the two previous scraper scripts
# (Script_1.py and Script_2.py). Users can input team URLs from Sofifa,
# select destination folders, start or stop scraping processes, and view
# real-time process logs.
#
# NOTE:
# This file should be saved with .pyw extension (pythonw.exe) so that when executed,
# the command prompt window (black terminal) doesn't appear, only the UI.
# Make sure Script_1.py and Script_2.py are in the same folder as this script.
# ==================================================================================================


# --------------------------------------------------------------------------------------------------
# SECTION 1: LIBRARY IMPORTS
# Importing all libraries needed for UI and backend functionality.
# --------------------------------------------------------------------------------------------------
import os
import sys
import threading              # For running processes in background to prevent UI "freezing"
import subprocess             # For running external scripts (Script_1.py & Script_2.py)
import tkinter as tk
from tkinter import filedialog, messagebox, ttk # Standard UI components from Tkinter
from tkinter.scrolledtext import ScrolledText # Text widget with scrollbar
from ttkbootstrap import Style # Library for modern Tkinter themes
from ttkbootstrap.constants import * # Constants from ttkbootstrap (e.g., SUCCESS, INFO)
import io                     # For managing I/O streams


# --------------------------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION
# Initial variables and settings that apply throughout the application.
# --------------------------------------------------------------------------------------------------

# Configure standard output to be captured and displayed in UI log.
# This is important to read subprocess output.

#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')   - delete the HASTAG if not in APLICATION form

# Global variables to store currently running subprocesses.
# Needed to stop processes from the "Stop" button.
script1_process = None
script2_process = None


# --------------------------------------------------------------------------------------------------
# SECTION 3: MAIN UI INITIALIZATION (ROOT WINDOW)
# Creating the main application window and applying theme.
# --------------------------------------------------------------------------------------------------
root = tk.Tk()
root.title("Sofifa Scraper 🚀")
root.geometry("1080x700")
root.resizable(True, True) # Window size cannot be changed
style = Style(theme="flatly") # Initial theme (can be changed with dark mode)

# Icon with safe path
ICON_PATH = os.path.join(os.path.dirname(__file__), "logo-app.ico")
if os.path.exists(ICON_PATH):
    root.iconbitmap(ICON_PATH)

# --------------------------------------------------------------------------------------------------
# SECTION 4: LOGIC FUNCTIONS (BACKEND)
# Collection of functions handling all logic behind buttons and UI interactions.
# --------------------------------------------------------------------------------------------------

def log(msg):
    """Display message to log area in UI and automatically scroll to bottom."""
    log_text.config(state='normal')  # Enable edit mode to insert text
    log_text.insert(tk.END, f"{msg}\n")
    log_text.see(tk.END)  # Auto-scroll to last line
    log_text.config(state='disabled') # Disable again to prevent user editing

def browse_folder():
    """Open dialog to select folder and display it in entry box."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder_selected)

def validate_url(url):
    """Validates Sofifa URL format to ensure correct link."""
    return url.startswith("https://sofifa.com/team/") or url.startswith("https://sofifa.com/squad/")

def run_script(script_name, url, output_folder, progressbar, est_label, script_number):
    """
    The core function is to run the scraper script in a separate thread.
    Using threads prevents the UI from becoming unresponsive while the scraping is running.
    """
    global script1_process, script2_process

    url = url.strip()
    # Validate input before running
    if not validate_url(url):
        messagebox.showerror("Invalid URL", "URL must begin with 'https://sofifa.com/team/' or '/squad/'.")
        return
    if not output_folder:
        messagebox.showerror("Folder Not Selected", "Please select the output folder first.")
        return

    # Update UI to indicate process starting
    progressbar.grid()
    progressbar.start(10) # Start progress bar animation
    est_label.config(text="Initiating Process...", foreground="#FF0000")

    def thread_target():
        """This function will be executed inside the thread."""
        nonlocal url # Using url variable from outer scope
        try:
            log(f"\n▶️ Injecting {script_name}...")
            if not url.endswith("/"): url += "/" # Ensure URL ends with slash

            # Command to execute in command line
            command = ["python", script_name, "--url", url, "--output", output_folder]
            log(f"[CMD] {' '.join(command)}")

            # Run subprocess
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,       # Capture standard output
                stderr=subprocess.STDOUT,     # Capture standard error (merge with stdout)
                text=True,                    # Output as text
                encoding='utf-8',             # Specify encoding
                creationflags=subprocess.CREATE_NO_WINDOW # (Windows-only) Hide cmd window
            )

            # Save process object to global variable based on script number
            if script_number == 1:
                globals()['script1_process'] = process
            else:
                globals()['script2_process'] = process

            # Read script output line by line in real-time
            for line in iter(process.stdout.readline, ''):
                log(line.strip())
            
            process.stdout.close()
            return_code = process.wait() # Wait until process completes
            
            if return_code == 0:
                log(f"✅ Process {script_name} Complete and FULLY Operated.")
            else:
                log(f"⚠️ Process {script_name} There is some problems: {return_code}.")

        except FileNotFoundError:
            log(f"❌ ERROR: File '{script_name}' is not exist. Make sure file in the same directory.")
        except Exception as e:
            log(f"❌ ERROR there is problems:  {script_name}: {e}")
        finally:
            # Clean up UI after process completes or fails
            progressbar.stop()
            progressbar.grid_remove() # Hide progress bar
            est_label.config(text="")
            if script_number == 1:
                globals()['script1_process'] = None
            else:
                globals()['script2_process'] = None
    
    # Create and start new thread
    threading.Thread(target=thread_target, daemon=True).start()

def cancel_script(script_number):
    """Terminate the ongoing scraping process."""
    process_to_cancel = script1_process if script_number == 1 else script2_process
    
    if process_to_cancel and process_to_cancel.poll() is None: # Check if process is still running
        process_to_cancel.terminate()
        log(f"⛔ Script {script_number} Stopped by USER.")
    else:
        log(f"⚠️ No Script {script_number} injected  to pe terminated.")

def reset_all():
    """Reset all input and LOG in UI."""
    if messagebox.askokcancel("Reset", "Are you sure to Reset ALL?"):
        url_entry.delete(0, tk.END)
        output_entry.delete(0, tk.END)
        log_text.config(state='normal')
        log_text.delete(1.0, tk.END)
        log_text.config(state='disabled')
        est_label_1.config(text="")
        est_label_2.config(text="")
        progbar1.grid_remove()
        progbar2.grid_remove()

def open_output_folder():
    """Opening output folder in File Explorer."""
    path = output_entry.get()
    if path and os.path.isdir(path):
        os.startfile(path) # This command is cross-platform (Windows, macOS, Linux)
    else:
        messagebox.showwarning("Folder Not Found", "The output folder is invalid or has not been selected.")

def toggle_dark():
    """Change the UI theme between light (flatly) and dark (darkly)."""
    new_theme = "darkly" if style.theme.name == "flatly" else "flatly"
    style.theme_use(new_theme)


# --------------------------------------------------------------------------------------------------
# SECTION 5: UI LAYOUT (WIDGETS)
# Placing all buttons, labels, and input areas into application window using .grid().
# --------------------------------------------------------------------------------------------------

# --- Main Frame ---
# Split window into two parts: left for controls, right for log.
root.columnconfigure(1, weight=1) # Right column can expand
root.rowconfigure(0, weight=1)    # Row can expand vertically

left_frame = ttk.Frame(root, padding=15)
left_frame.grid(row=0, column=0, sticky="ns")

right_frame = ttk.Frame(root, padding=15)
right_frame.grid(row=0, column=1, sticky="nsew")
right_frame.columnconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=1)

# --- Left Frame Content (Input & Controls) ---

# 1. URL & Folder Input
ttk.Label(left_frame, text="🔗 Sofifa Team URL", font="-weight bold").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
url_entry = ttk.Entry(left_frame, width=50)
url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

ttk.Label(left_frame, text="📁 Output Folder", font="-weight bold").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 2))
output_entry = ttk.Entry(left_frame, width=35)
output_entry.grid(row=3, column=0, sticky="ew")
ttk.Button(left_frame, text="Browse...", command=browse_folder, bootstyle="outline").grid(row=3, column=1, sticky="ew", padx=(5, 0))

# Separator
ttk.Separator(left_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")

# 2. Script 1 Controls
ttk.Label(left_frame, text="1. Script for 14 Parameters", font="-weight bold")\
   .grid(row=5, column=0, columnspan=2, sticky="w")

ttk.Label(
    left_frame,
    text=("Parameters: ID, Name, Age, Overall, Potential, Position, Height, "
          "Weight, Pref.Foot, Skill Moves, Weak Foot, Contract, Nationality"),
    wraplength=300, font=("Segoe UI", 9, "italic"), foreground="#CCCCCC"
).grid(row=6, column=0, columnspan=2, sticky="w")

start_btn1 = ttk.Button(
    left_frame, text="▶ Initiate Script 1", bootstyle="success",
    command=lambda: run_script("Script_1.py", url_entry.get(), output_entry.get(),
                               progbar1, est_label_1, 1)
)
start_btn1.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 2))

progbar1 = ttk.Progressbar(
    left_frame, mode='determinate', maximum=100, value=0,
    bootstyle="success-striped"
)
progbar1.grid(row=8, column=0, columnspan=2, sticky="ew", pady=2)
progbar1.grid_remove()

est_label_1 = ttk.Label(left_frame, text="", bootstyle="secondary")
est_label_1.grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 10))


# 3. Script 2 Controls
ttk.Label(left_frame, text="2. Script for 4 Parameters", font="-weight bold")\
   .grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 0))

ttk.Label(
    left_frame, text="Parameters: ID, Name, Value, Wage",
    wraplength=300, font=("Segoe UI", 9, "italic"), foreground="#CCCCCC"
).grid(row=11, column=0, columnspan=2, sticky="w")

start_btn2 = ttk.Button(
    left_frame, text="▶ Initiate Script 2", bootstyle="info",
    command=lambda: run_script("Script_2.py", url_entry.get(), output_entry.get(),
                               progbar2, est_label_2, 2)
)
start_btn2.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(10, 2))

progbar2 = ttk.Progressbar(
    left_frame, mode='determinate', maximum=100, value=0,
    bootstyle="info-striped"
)
progbar2.grid(row=13, column=0, columnspan=2, sticky="ew", pady=2)
progbar2.grid_remove()

est_label_2 = ttk.Label(left_frame, text="", bootstyle="secondary")
est_label_2.grid(row=14, column=0, columnspan=2, sticky="w", pady=(0, 10))


# Separator
ttk.Separator(left_frame, orient='horizontal').grid(row=15, column=0, columnspan=2, pady=20, sticky="ew")

# 4. General Controls (Stop, Reset, etc)
controls_frame = ttk.Frame(left_frame)
controls_frame.grid(row=15, column=0, columnspan=2, sticky="ew")
controls_frame.columnconfigure((0, 1), weight=1)
ttk.Button(controls_frame, text="❌ Stop Script 1", bootstyle="danger-outline", command=lambda: cancel_script(1)).grid(row=0, column=0, sticky="ew", padx=(0, 5))
ttk.Button(controls_frame, text="❌ Stop Script 2", bootstyle="danger-outline", command=lambda: cancel_script(2)).grid(row=0, column=1, sticky="ew", padx=(5, 0))

ttk.Button(left_frame, text="📂 Open Output Folder", command=open_output_folder, bootstyle="secondary").grid(row=16, column=0, columnspan=2, sticky="ew", pady=5)
ttk.Button(left_frame, text="🔄 Reset All", command=reset_all, bootstyle="danger").grid(row=16, column=0, columnspan=2, sticky="ew")

# --- Right Frame Content (Log Output) ---
ttk.Label(right_frame, text="📋 Process Log", font="-weight bold").grid(row=0, column=0, sticky="w")
log_text = ScrolledText(right_frame, wrap=tk.WORD, height=40, state='disabled', relief="solid", bd=1)
log_text.grid(row=1, column=0, sticky="nsew", pady=(5,0))

# --- Bottom Controls (absolute position) ---
# Place dark mode button in bottom left corner
toggle_button = ttk.Button(left_frame, text="🌙 Switch Theme", command=toggle_dark, bootstyle="outline-secondary")
toggle_button.grid(row=20, column=0, columnspan=2, sticky="ew", pady=(50, 0))

def show_guide():
    message = (
        "USER GUIDANCE :\n\n"
        ">>This Script take TIME TO SCRAP so please be patient<<\n"
        "1. Enter the URL of the squad/team page on Sofifa.\n"
        "--> Ex : https://sofifa.com/team/5/chelsea/\n"
        "2. Select the destination folder to save the data.\n"
        "3. Click Start Script 1 to scrape 14 main Parameters.\n"
        "4. Click Start Script 2 to scrape remaining Wage & Value.\n"
        "5. Use the STOP button if you want to stop the process.\n"
        "6. All process logs are displayed on the right side of the screen.\n"
        "7. Run Merger Application for merging this aplication output files."
    )
    messagebox.showinfo("Guidance", message)

guide_btn = ttk.Button(left_frame, text="<<--Guidance-->>", bootstyle="info-outline", command=show_guide)
guide_btn.grid(row=21, column=0, columnspan=2, sticky="ew", pady=(5, 0))

# === FOOTER SECTION ===
footer_frame = ttk.Frame(root)
footer_frame.grid(row=99, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

# Bottom left: Powered by
powered_label = ttk.Label(footer_frame, text="Powered by Python | Open-source | 2025", font=("Segoe UI", 9))
powered_label.pack(side="left")

# Bottom right: Info Button

def show_info():
    messagebox.showinfo(
        "About this Tool",
        "Sofifa Scraper Tool\nCreated by : nadhilm12\n\nThis tool allows you to scrape data from Sofifa for personal modding or research.\nUse responsibly and support open-source projects!\n\nInspired by the work of : Paulv2k4, eshortX and Decoruiz"
    )

info_button = ttk.Button(footer_frame, text="Info", command=show_info)
info_button.pack(side="right")

# === END FOOTER ===
# --------------------------------------------------------------------------------------------------
# SECTION 6: RUN APPLICATION
# Start main Tkinter event loop. UI will appear and wait for user interaction.
# --------------------------------------------------------------------------------------------------
root.mainloop()