# Eisenhower Matrix Task Sorter

A desktop application to sort tasks based on the Eisenhower matrix.

## Installation

1. Install Python 3.x

2. Install dependencies: `pip install -r requirements.txt`

3. Run: `python main.py`

## Usage

Enter a task, add an optional tag, check "Urgent" and/or "Important", optionally enable "Fecha" and choose a due date, then click "Add Task" to place it in the appropriate quadrant.

Use the task menu to edit or remove the due date, tag, or note on any task. Tasks in the "Important & Not Urgent" quadrant with a due date will automatically move to "Urgent & Important" when the date arrives or is overdue.

The four quadrants are:
- Urgent & Important: Do first
- Important & Not Urgent: Schedule
- Urgent & Not Important: Delegate
- Neither: Eliminate