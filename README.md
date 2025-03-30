# Windows User Profile Slimmer

A GUI tool to reduce the size of your Windows user profile by relocating large non-system folders and files to a safe location on your C:\ drive, and creating symbolic links to maintain compatibility.

---

## Why Slim Your User Profile?

- **Performance:** Reduces login/logout delays, speeds up roaming profiles, avoids profile corruption.
- **Compatibility:** Prevents profile size limits in managed environments (e.g. Active Directory, Remote Desktop).
- **Storage Management:** Helps manage large folders like `Documents`, `Downloads`, `GitHub`, and large files (> 500 MB).

Large user profiles are one of the reasons that many computers slow down after reaching a certain age. In Windows 11, *many* programs install files directly to your `C:\Users\<Username>` directory. 

---

## How does it work?

The program creates a symbolic link in your user profile and moves the files to a separate directory

---

## Features

- Analyze profile size folder-by-folder
- Move large folders and files to `C:\User_<yourname>`
- Auto-create symlinks so apps work normally
- Supports undo (restores all original folder locations)
- Excludes sensitive system folders and JetBrains/VS Code project configs

---

## How to Check Your Profile Size in Windows 11

1. Press `Win + R`, type:  `%userprofile%`
2. Select all folders (Ctrl+A), right-click → Properties
3. AppData is hidden by default and should be excluded manually
4. This tool automatically excludes `AppData` for you
5. Essentially, your user profile is the size of your `C:\Users\<Username>\` directory minus the size of your `C:\Users\<Username>\AppData` folder.

---

## Disclaimer

>  Use at your own risk. This tool modifies your user folder structure and creates symlinks. Make sure you:
>
> - **Run as Administrator**
> - **Review items carefully before moving**
> - **Back up important data before proceeding**

This program has also only been tested on Windows 11, have not looked into older versions of Windows (10, 8.1, 8, 7, ... etc.).

---

## Environment Creation Using Anaconda 3
```
conda create -n windows-profile-slimmer python=3.12
conda activate windows-profile-slimmer
pip install pyqt5 humanize
```

---

## How to Use

1. Run the tool with Administrator privileges (for example, open Anaconda3 prompt with administrator rights and run the program):
```
python profile_slimmer.py
```
2. Select your user profile folder (C:\Users\YourName)
3. Wait for the scan to complete
4. Check off large folders/files you want to move
5. Click Move Selected and Create Symlinks
6. (Optional) Use Undo to restore everything

### Safe by Design
- AppData, .git, .idea, .vscode, and system folders are auto-excluded
- Symlinks are logged in symlinks.txt in your user profile directory

## Project Structure
```
windows-user-profile-slimmer/
├── profile_slimmer.py       ← Main GUI app
├── README.md                ← This documentation
└── .gitignore               ← Excludes .idea/, .vscode/, etc.
```
