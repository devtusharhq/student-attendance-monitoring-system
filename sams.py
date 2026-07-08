import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
from datetime import datetime
from tkcalendar import DateEntry # Requires 'pip install tkcalendar'

# --- Configuration ---
ROSTER_FILENAME = "students.csv"
RECORDS_FILENAME = "attendance_records.csv"

 # --- Data Management Functions ---

def _get_roster_from_tree():
    """Helper function to get all students currently in the main Treeview."""
    roster_list = []
    for child_id in tree.get_children():
        values = tree.item(child_id)['values']
        roster_list.append([values[0], values[1]]) # ID and Name
    return roster_list

def _save_roster_to_csv():
    """Saves the current student roster from the Treeview to students.csv."""
    try:
        with open(ROSTER_FILENAME, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Name"])
            writer.writerows(_get_roster_from_tree())
        return True
    except Exception as e:
        messagebox.showerror("Roster Save Error", f"An error occurred: {e}")
        return False

def load_roster():
    """Clears the tree and loads the master student list from students.csv."""
    for item in tree.get_children():
        tree.delete(item)
    
    if not os.path.exists(ROSTER_FILENAME):
        with open(ROSTER_FILENAME, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Name"])
    else:
        with open(ROSTER_FILENAME, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            try:
                next(reader) # Skip header
                for row in reader:
                    tree.insert("", tk.END, values=(row[0], row[1], "Not Marked"))
            except StopIteration:
                pass # File is empty

def save_attendance():
    """Saves the current session's attendance to the records file."""
    session_date = date_entry.get_date().strftime('%Y-%m-%d') # Get date from calendar
    session_time = time_entry.get().strip()
    session_subject = subject_entry.get().strip()

    if not all([session_date, session_time, session_subject]):
        messagebox.showwarning("Input Error", "Please provide Date, Time/Period, and Subject.")
        return

    new_records = []
    for child_id in tree.get_children():
        values = tree.item(child_id)['values']
        new_records.append([session_date, session_time, session_subject, values[0], values[1], values[2]])

    all_other_records = []
    if os.path.exists(RECORDS_FILENAME):
        with open(RECORDS_FILENAME, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            try:
                header = next(reader)
                for row in reader:
                    # Keep records that do not match the current session
                    if not (row[0] == session_date and row[1] == session_time and row[2] == session_subject):
                        all_other_records.append(row)
            except StopIteration:
                pass
    
    try:
        with open(RECORDS_FILENAME, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Time", "Subject", "ID", "Name", "Status"])
            writer.writerows(all_other_records)
            writer.writerows(new_records)
        messagebox.showinfo("Success", f"Attendance for {session_subject} at {session_time} saved!")
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred while saving: {e}")

# --- GUI Action Functions ---

def add_student():
    sid = entry_id.get().strip()
    name = entry_name.get().strip()

    if not sid or not name:
        messagebox.showwarning("Input Error", "Please enter both ID and Name.")
        return

    for child_id in tree.get_children():
        if tree.item(child_id)['values'][0] == sid:
            messagebox.showerror("Error", f"Student ID '{sid}' already exists.")
            return

    tree.insert("", tk.END, values=[sid, name, "Not Marked"])
    entry_id.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    
    if _save_roster_to_csv():
        messagebox.showinfo("Roster Updated", f"Student {name} added to the master roster.")

def delete_student():
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Selection Error", "Please select a student to delete.")
        return
    
    if messagebox.askyesno("Confirm Delete", "This will permanently remove the student(s) from the master roster. Are you sure?"):
        for item in selected_items:
            tree.delete(item)
        _save_roster_to_csv()

def mark_attendance(status):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Selection Error", "Please select student(s) to mark.")
        return

    for item in selected_items:
        values = tree.item(item, 'values')
        tree.item(item, values=(values[0], values[1], status))

# --- Report and View Windows ---

def open_view_window():
    view_window = tk.Toplevel(root)
    view_window.title("View Past Attendance Records")
    view_window.geometry("800x500")
    view_window.configure(bg='#f0f0f0')

    def _update_combos():
        dates, times, subjects = set(), set(), set()
        if os.path.exists(RECORDS_FILENAME):
            with open(RECORDS_FILENAME, 'r', newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                try:
                    next(reader)
                    for row in reader:
                        if len(row) == 6:
                            dates.add(row[0]); times.add(row[1]); subjects.add(row[2])
                except (StopIteration, IndexError): pass
        date_combo['values'] = sorted(list(dates))
        time_combo['values'] = sorted(list(times))
        subject_combo['values'] = sorted(list(subjects))

    def filter_records():
        sel_date, sel_time, sel_subject = date_combo.get(), time_combo.get(), subject_combo.get()
        if not all([sel_date, sel_time, sel_subject]): return
        for item in results_tree.get_children(): results_tree.delete(item)
        with open(RECORDS_FILENAME, 'r', newline='', encoding="utf-8") as file:
            reader = csv.reader(file); next(reader)
            for row in reader:
                if len(row) == 6 and row[0]==sel_date and row[1]==sel_time and row[2]==sel_subject:
                    results_tree.insert("", tk.END, values=(row[3], row[4], row[5]))

    def delete_session_record():
        sel_date, sel_time, sel_subject = date_combo.get(), time_combo.get(), subject_combo.get()
        if not all([sel_date, sel_time, sel_subject]):
            messagebox.showwarning("Selection Error", "Please select a full session to delete."); return
        if not messagebox.askyesno("Confirm Deletion", f"Delete the session for {sel_subject} on {sel_date} at {sel_time}?"): return
        
        updated_records = []
        with open(RECORDS_FILENAME, 'r', newline='', encoding="utf-8") as file:
            reader = csv.reader(file); header = next(reader)
            for row in reader:
                if not (row[0]==sel_date and row[1]==sel_time and row[2]==sel_subject):
                    updated_records.append(row)
        with open(RECORDS_FILENAME, 'w', newline='', encoding="utf-8") as file:
            writer = csv.writer(file); writer.writerow(header); writer.writerows(updated_records)
        
        messagebox.showinfo("Success", "The selected session has been deleted.")
        for item in results_tree.get_children(): results_tree.delete(item)
        _update_combos()

    filter_frame = ttk.Frame(view_window, padding=10); filter_frame.pack(fill=tk.X)
    ttk.Label(filter_frame, text="Date:").pack(side=tk.LEFT, padx=5)
    date_combo = ttk.Combobox(filter_frame, width=12); date_combo.pack(side=tk.LEFT, padx=5)
    ttk.Label(filter_frame, text="Time/Period:").pack(side=tk.LEFT, padx=5)
    time_combo = ttk.Combobox(filter_frame, width=12); time_combo.pack(side=tk.LEFT, padx=5)
    ttk.Label(filter_frame, text="Subject:").pack(side=tk.LEFT, padx=5)
    subject_combo = ttk.Combobox(filter_frame, width=15); subject_combo.pack(side=tk.LEFT, padx=5)
    
    ttk.Button(filter_frame, text="View Attendance", command=filter_records).pack(side=tk.LEFT, padx=10)
    ttk.Button(filter_frame, text="Delete This Session", command=delete_session_record, style='Accent.TButton').pack(side=tk.LEFT, padx=10)

    results_frame = ttk.Frame(view_window, padding=10); results_frame.pack(fill=tk.BOTH, expand=True)
    results_tree = ttk.Treeview(results_frame, columns=("ID", "Name", "Status"), show="headings")
    results_tree.pack(fill=tk.BOTH, expand=True)
    results_tree.heading("ID", text="Student ID"); results_tree.heading("Name", text="Student Name"); results_tree.heading("Status", text="Status")
    _update_combos()

def open_report_window():
    report_window = tk.Toplevel(root)
    report_window.title("Generate Attendance Report")
    report_window.geometry("500x400")
    report_window.configure(bg='#f0f0f0')

    students_map, years = {}, set()
    if os.path.exists(ROSTER_FILENAME):
        with open(ROSTER_FILENAME, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f); next(reader)
            for row in reader: students_map[row[1]] = row[0]
    if os.path.exists(RECORDS_FILENAME):
        with open(RECORDS_FILENAME, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row: years.add(datetime.strptime(row[0], '%Y-%m-%d').year)
    months = {datetime.strptime(str(i), "%m").strftime("%B"): i for i in range(1, 13)}

    def _generate():
        student_name, month_name, year = student_combo.get(), month_combo.get(), year_combo.get()
        if not all([student_name, month_name, year]):
            messagebox.showwarning("Input Error", "Please select student, month, and year."); return
        
        student_id, month_num = students_map.get(student_name), months.get(month_name)
        present, total = 0, 0
        with open(RECORDS_FILENAME, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row:
                    record_date = datetime.strptime(row[0], '%Y-%m-%d')
                    if row[3] == student_id and record_date.month == month_num and record_date.year == int(year):
                        total += 1
                        if row[5] == "Present": present += 1
        percentage = (present / total * 100) if total > 0 else 0
        result_text.config(state='normal'); result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Attendance Report\n----------------------------------\n"
                                   f"Student: {student_name}\nPeriod:  {month_name} {year}\n\n"
                                   f"Attended: {present} out of {total} classes\n"
                                   f"----------------------------------\n"
                                   f"Percentage: {percentage:.2f}%\n")
        result_text.config(state='disabled')
        
    filter_frame = ttk.Frame(report_window, padding=15); filter_frame.pack(fill=tk.X)
    ttk.Label(filter_frame, text="Student:").grid(row=0, column=0, sticky='w', pady=5)
    student_combo = ttk.Combobox(filter_frame, values=sorted(list(students_map.keys()))); student_combo.grid(row=0, column=1, sticky='ew', padx=5)
    ttk.Label(filter_frame, text="Month:").grid(row=1, column=0, sticky='w', pady=5)
    month_combo = ttk.Combobox(filter_frame, values=list(months.keys())); month_combo.grid(row=1, column=1, sticky='ew', padx=5)
    ttk.Label(filter_frame, text="Year:").grid(row=2, column=0, sticky='w', pady=5)
    year_combo = ttk.Combobox(filter_frame, values=sorted(list(years))); year_combo.grid(row=2, column=1, sticky='ew', padx=5)
    filter_frame.columnconfigure(1, weight =1)

    ttk.Button(report_window, text="Generate Report", command=_generate, style='Accent.TButton').pack(pady=10)
    result_text = tk.Text(report_window, height=10, width=50, font=("Courier", 11), state='disabled', bg='#ffffff')
    result_text.pack(pady=10, padx=15, fill=tk.BOTH, expand=True)

# ----------------- GUI Setup -----------------
root = tk.Tk()
root.title("Student Attendance System")
root.geometry("850x700")
root.configure(bg='#eaf2f8')

# --- Styles ---
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#ffffff", rowheight=25, fieldbackground="#ffffff")
style.map('Treeview', background=[('selected', '#347083')])
style.configure("TButton", padding=6, relief="flat", background="#cce7ff", font=('Helvetica', 10))
style.configure('Accent.TButton', foreground='white', background='#0078d7', font=('Helvetica', 10, 'bold'))

# --- Main Frames ---
session_frame = ttk.Frame(root, padding="20 10 20 5"); session_frame.pack(fill=tk.X)
input_frame = ttk.Frame(root, padding="20 5 20 10"); input_frame.pack(fill=tk.X)
list_frame = ttk.Frame(root, padding="20 10 20 10"); list_frame.pack(fill=tk.BOTH, expand=True)
action_frame = ttk.Frame(root, padding="20 10 20 20"); action_frame.pack(fill=tk.X)

# --- Session Frame Widgets ---
ttk.Label(session_frame, text="Date:", font=('Helvetica', 11, 'bold')).grid(row=0, column=0)
date_entry = DateEntry(session_frame, width=12, font=('Helvetica', 10), date_pattern='y-mm-dd')
date_entry.grid(row=0, column=1, padx=(5, 15))

ttk.Label(session_frame, text="Time/Period:", font=('Helvetica', 11, 'bold')).grid(row=0, column=2)
time_entry = ttk.Entry(session_frame, width=15, font=('Helvetica', 11))
time_entry.insert(0, datetime.now().strftime('%H:%M'))
time_entry.grid(row=0, column=3, padx=(5, 15))

ttk.Label(session_frame, text="Subject:", font=('Helvetica', 11, 'bold')).grid(row=0, column=4)
subject_entry = ttk.Entry(session_frame, width=20, font=('Helvetica', 11))
subject_entry.grid(row=0, column=5, padx=5)

# --- Input Frame Widgets ---
ttk.Label(input_frame, text="New Student ID:", font=('Helvetica', 11)).grid(row=0, column=0, pady=5, sticky='w')
entry_id = ttk.Entry(input_frame, width=20, font=('Helvetica', 11))
entry_id.grid(row=0, column=1, padx=5, pady=5)
ttk.Label(input_frame, text="New Student Name:", font=('Helvetica', 11)).grid(row=1, column=0, pady=5, sticky='w')
entry_name = ttk.Entry(input_frame, width=30, font=('Helvetica', 11))
entry_name.grid(row=1, column=1, padx=5, pady=5)
add_button = ttk.Button(input_frame, text="Add Student to Roster", command=add_student)
add_button.grid(row=1, column=2, padx=10, pady=5)

# --- List Frame Widgets ---
tree_scroll = ttk.Scrollbar(list_frame); tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Status"), show="headings", yscrollcommand=tree_scroll.set)
tree.pack(fill=tk.BOTH, expand=True)
tree_scroll.config(command=tree.yview)
tree.heading("ID", text="Student ID"); tree.heading("Name", text="Student Name"); tree.heading("Status", text="Attendance Status")

# --- Action Frame Widgets ---
action_buttons = {
    "Mark Present": lambda: mark_attendance("Present"),
    "Mark Absent": lambda: mark_attendance("Absent"),
    "Delete From Roster": delete_student,
    "View Past Records": open_view_window,
    "Generate Report": open_report_window
}
for text, command in action_buttons.items():
    ttk.Button(action_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
ttk.Button(action_frame, text="Save Attendance", command=save_attendance, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)

# --- Initial Load ---
load_roster()
root.mainloop()
