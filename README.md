# Chess Tournament Maker PT

This is the new and improved official software for managing our school's chess tournaments as of the 2025-2026 school year. It has all the correct matchmaking logic, and is designed to be used on a personal computer (PC) at home to make the pairings while you record the results on a restricted school Chromebook at school.

![Screenshot of the main application window](/screenshots/program.png)

---

## How to use (easiest guide)

For ppl who just want to run the program.

1.  **Go to the [Releases Page](https://github.com/Blue5GD/Chess-Tournament-Maker-PT/releases/tag/latest)**.
2.  Under the "Assets" section of the latest release, click on the `.zip` file to download it.
3.  **Unzip/extract the folder** after downloading.
4.  Open the unzipped folder and double-click the `Chess-Tournament-Maker-PT.exe` file to run the program!

I was able to run the file with no problems, but if your antivirus or computer says it's a virus, you can safely ignore it. It's not a virus, trust me.

---

## For future developers (how to modify the program)

For anyone who wants to fix bugs or add new features to the program in the future.

This project was built with **Python** and the **CustomTkinter** library for the user interface.

### 1. Prerequisites
*   You need [Python](https://www.python.org/downloads/) installed on your computer (this was built with Python 3.13 but any version should work).
*   You need [Git](https://git-scm.com/downloads/) or [GitHub Desktop](https://desktop.github.com/) to access the code.

### 2. Setup
First, get a copy of the source code on your machine.

```bash
# Clone this repository to your computer
git clone https://github.com/Blue5GD/Chess-Tournament-Maker-PT.git

# Navigate into the project directory
cd Chess-Tournament-Maker-PT
```

### 3. Install Dependencies
It is highly recommended to use a virtual environment to keep dependencies separate.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install the required libraries from the requirements.txt file
pip install -r requirements.txt
```

### 4. Run the Program from Source
Once the dependencies are installed, you can run the program directly with Python.

```bash
python Chess-Tournament-Maker-PT.py
```

Now you can edit the `.py` file, and your changes will be reflected the next time you run the script.
