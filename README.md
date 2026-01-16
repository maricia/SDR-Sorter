# SDR Sorter
Automated SDR ZIP File Processing for Assessment Data Workflows

SDR Sorter is a Python-based desktop application that automates the extraction and classification of SDR ZIP files used in K–12 assessment data workflows. It eliminates manual sorting, reduces errors, and standardizes output for both ODS and TestHound processes.

---

## Problem

Assessment data teams frequently receive SDR ZIP files containing dozens or hundreds of files with inconsistent naming conventions, embedded dates, and multiple assessment types. Manually extracting and sorting these files:

- Is time-consuming and error-prone
- Requires detailed domain knowledge of file naming rules
- Slows down downstream reporting and accountability timelines
- Creates risk when handled by non-technical staff

This manual process often becomes a bottleneck during high-pressure reporting windows.

---

## Solution

SDR Sorter automates the entire workflow.

With a simple graphical interface, users can:
- Select an SDR ZIP file
- Choose an output directory
- Specify whether the files are for **ODS** or **TestHound**
- Run the sorter with a single click

The application applies rule-based logic to extract files, classify them by assessment type, and organize them into standardized folders — no scripting or technical knowledge required.

---

## Screenshots

> *(Add screenshots of the GUI here)*

Suggested screenshots:
- Main application window
- ZIP file selection dialog
- Completed output directory structure

You can add images like this:
```markdown
![SDR Sorter GUI](screenshots/sdr_sorter_gui.png)
 
How It Works

ZIP Extraction
The application extracts all files from the selected SDR ZIP archive.

Workflow Selection
Users choose between ODS or TestHound, which determines the sorting rules applied.

Rule-Based Classification
Files are categorized using domain-specific logic, including:

Assessment type (STAAR 3–8, STAAR EOC, TELPAS, TELPAS Alt)

Special identifiers (e.g., EOC, Alt, ProductionExaminee)

File naming patterns and embedded dates

Standardized Output
Files are placed into clearly labeled folders. Any files that do not match known patterns are placed in an Unsorted folder for review, along with a text file listing those files.

User-Friendly Delivery
The tool is designed to be packaged as a one-click executable so it can be used by non-technical staff without Python installed.

Key Features

GUI-based desktop application (Tkinter)

Supports both ODS and TestHound workflows

Automatically processes any SDR ZIP file

Rule-driven, repeatable, and auditable logic

Handles edge cases and unknown files safely

Designed for real-world operational use

Tech Stack

Python

Tkinter (GUI)

Standard Python libraries for file and ZIP handling

Intended Audience

K–12 data and assessment teams

District analytics and accountability staff

Operations teams handling large assessment data drops

Anyone needing reliable, repeatable file processing without manual effort

Why This Project Exists

This tool was built to solve a real operational problem encountered in district-level data workflows, where automation is often needed but engineering resources are limited. It demonstrates how domain knowledge and software engineering can be combined to deliver practical, high-impact solutions.

Future Enhancements

Configurable rule sets

Logging and run summaries

Expanded packaging and distribution options

Additional workflow support

License
