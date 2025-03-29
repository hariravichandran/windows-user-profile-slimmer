# windows-user-profile-slimmer
A handy tool that reduces the user profile

✅ What This Tool Does:
A. Choose a user profile folder (C:\Users\...)

B. Scan the profile (excluding AppData and risky/system folders) with a progress bar

C. Show a UI listing:

Folder name

Size

Estimated size to save

Checkbox to mark for relocation

Total profile size (excluding AppData)

D. Move selected folders to:

php-template
Copy
Edit
C:\User_<username>\<folder>
and create symlinks back to the original location.

E. Log all moved folders and symlinks into:

php-template
Copy
Edit
<original_user_profile>\symlinks.txt
F. Includes smart error handling, progress indicator, and auto-skipping unsafe folders

🐍 Install Requirements
bash
Copy
Edit
pip install pyqt5 humanize
▶️ How to Run
Save the file as: profile_slimmer_full.py

Run it as Administrator:

bash
Copy
Edit
python profile_slimmer_full.py



````


conda create -n windows-profile-slimmer python=3.12

`conda activate windows-profile-slimmer`

pip install pyqt5 humanize

