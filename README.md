# Windows User Profile Slimmer

A GUI tool to reduce the size of your Windows user profile by relocating large non-system folders and files to a safe location on your C:\ drive, and creating symbolic links to maintain compatibility.

---

## Why Slim Your User Profile?

- **Performance:** Reduces login/logout delays, speeds up roaming profiles, avoids profile corruption.
- **Compatibility:** Prevents profile size limits in managed environments (e.g. Active Directory, Remote Desktop).
- **Storage Management:** Helps manage large folders like `Documents`, `Downloads`, `GitHub`, and large files (> 500 MB).

Large user profiles are one of the reasons that many Windows 11 computers slow down after reaching a certain age. In Windows 11, *many* programs install files directly to your `C:\Users\<Username>` directory. If you are not careful, user profiles can easily exceed 100 GB. Ideally, a small user profile of only a few gigabytes is one of the hallmarks of a fast Windows machine.

This program removes many of the manual steps (for example, figuring out which files/folders take the most space, creating brand new folders in the C:\ drive, creating the symbolic links as needed).

---

## How does it work?

The program creates a symbolic link in your user profile and moves the files to a separate directory. For example, assuming your username is `Hari` and you want to move the installation of Anaconda 3 (for which each new environment eats into your user profile on Windows!):

1. We first move the files over from the User Profile Directory to a directory that we create on the C:\ drive (So `C:\User_<Username>`):
```
move "C:\Users\Hari\anaconda3" "C:\User_Hari\anaconda3"
```

2. Remove the read-only permissions that are automatically added on the directory:
```
attrib -r "C:\User_Hari\anaconda3" /S /D
```

3. Create a symbolic link that links the original user folder location in the User Profile to the new folder that we moved the files to:
```
mklink /D "C:\Users\Hari\anaconda3" "C:\User_Hari\anaconda3"
```

The advantage of the symbolic link approach is that it allows us to continue to use the default directories on the user profile while also allowing us to not deal with programs constantly adding more data to the user profile and it growing out of control. As another real-world example, suppose you want to install LM Studio and run some different LLM models locally. By default, every model you download locally is added to your user profile. Before you know it, you've added 30+ GB to your user profile after downloading a few models, significantly slowing down your machine.

---

## Features

- Analyze profile size folder-by-folder
- Move large folders and files to `C:\User_<yourname>`
- Auto-create symlinks so apps work normally
- Supports undo (restores all original folder locations)
- Excludes sensitive system folders and JetBrains/VS Code project configs

---

## How to Check Your User Profile Size in Windows 11

1. Press `Win + R`, type:  `%userprofile%`
2. Select all folders (Ctrl+A), right-click → Properties
3. AppData is hidden by default and should be excluded manually
4. This tool automatically excludes `AppData` for you
5. Essentially, your user profile is the size of your `C:\Users\<Username>\` directory minus the size of your `C:\Users\<Username>\AppData` folder.
6. If your user profile size is greater than say, 20 GB, it can cause performance issues for your machine, especially on older machines and machines with limited storage. Ideally, we'd like it to be as small as possible and only contain the bare essential files for the best performance, so say < 5 GB.
7. A good, free program that allows you to get a relatively precise file/folder breakdown for your machine is WinDirStat (https://windirstat.net). You can use it to get a more precise view of how large the user profile is.

---

## Disclaimer

Use at your own risk. This tool modifies your user folder structure and creates symlinks. Make sure you:
- **Run as Administrator**
- **Review items carefully before moving**
- **Back up important data before proceeding**

This program has also only been tested on Windows 11, have not looked into older versions of Windows (10, 8.1, 8, 7, ... etc.).

It's possible (but not likely!) that a Windows Update might adjust/remove the symbolic links. In that case, remember that `symlinks.txt` is stored in your User Profile Directory and has the list of all the symlinks that have been made.

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
5. Click Move Selected and Create Symlinks (symlinks are stored in symlinks.txt)
6. (Optional) Use Undo to restore everything

### Safe by Design
- AppData, .git, .idea, .vscode, and system folders are auto-excluded
- Symlinks are logged in symlinks.txt in your user profile directory (`C:\Users\<Username>`)

## Project Structure
```
windows-user-profile-slimmer/
├── profile_slimmer.py       ← Main GUI app
├── README.md                ← This documentation
└── .gitignore               ← Excludes .idea/, .vscode/, etc.
```

### Contributing
We welcome contributions of all kinds! Whether you're fixing a bug, improving the UI, suggesting a new feature, or just reporting a problem — you're helping make this tool better for everyone.

#### Ways You Can Help
- Report issues — Found a bug or unexpected behavior? Open an issue
- Suggest a feature — Is there something you'd like the tool to do? Let us know!
- Submit a pull request — Add enhancements, refactor code, or improve documentation
- Improve documentation — Even fixing typos or adding usage examples helps

#### Guidelines
- Please keep your contributions focused and scoped to one feature or fix per pull request
- Include a clear explanation of what was changed and why
- Be respectful and constructive — we're here to collaborate

#### Contact
Have questions, feedback, or want to share your use case? Feel free to:
- Start a discussion in Issues
- Tag your fork on GitHub — we'd love to see how you use the tool!

#### Star the Project
If you find this tool useful, consider starring the repo — it helps more people discover it!
