import sys
import os
import shutil
import humanize
import ctypes
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QFileDialog, QLabel,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

EXCLUDED_FOLDERS = {'AppData', 'MicrosoftEdgeBackups', 'OneDrive', 'Favorites', 'Saved Games', 'Searches'}
SIZE_THRESHOLD_MB = 500

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class FolderEntry:
    def __init__(self, path: Path, size_bytes: int, target: Path):
        self.path = path
        self.size_bytes = size_bytes
        self.target = target
        self.should_move = size_bytes >= SIZE_THRESHOLD_MB * 1024 * 1024

    @property
    def size_human(self):
        return humanize.naturalsize(self.size_bytes, binary=True)

    @property
    def name(self):
        return self.path.name

class FolderScanner(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, user_profile_path):
        super().__init__()
        self.user_profile_path = Path(user_profile_path)

    def run(self):
        entries = []
        username = self.user_profile_path.name
        relocate_base = Path(f"C:/User_{username}")

        scan_targets = []
        for item in self.user_profile_path.iterdir():
            if item.name == "Documents" and item.is_dir():
                # Add subfolders of Documents
                for sub in item.iterdir():
                    if sub.is_dir():
                        scan_targets.append(sub)
            elif item.is_dir() and item.name not in EXCLUDED_FOLDERS and not item.is_symlink():
                scan_targets.append(item)

        total = len(scan_targets)

        for idx, folder in enumerate(scan_targets):
            try:
                size = self.get_folder_size(folder)
                # Destination path: place Documents subfolders under C:/User_<username>/Documents/<sub>
                if "Documents" in folder.parts:
                    rel_path = Path("Documents") / folder.name
                else:
                    rel_path = Path(folder.name)
                target_path = relocate_base / rel_path
                entries.append(FolderEntry(folder, size, target_path))
            except Exception as e:
                print(f"Failed to scan {folder}: {e}")
            self.progress.emit(int((idx + 1) / total * 100))

        entries.sort(key=lambda x: x.size_bytes, reverse=True)
        self.finished.emit(entries)

    def get_folder_size(self, path):
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except:
                    pass
        return total

class ProfileSlimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Profile Slimmer")
        self.resize(1000, 700)
        self.user_profile = None
        self.entries = []

        layout = QVBoxLayout(self)

        self.profile_label = QLabel("User Profile: Not selected")
        font = QFont()
        font.setPointSize(11)
        self.profile_label.setFont(font)
        layout.addWidget(self.profile_label)

        self.pick_btn = QPushButton("Select User Profile Folder")
        self.pick_btn.setFont(font)
        self.pick_btn.clicked.connect(self.select_user_profile)
        layout.addWidget(self.pick_btn)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Move?", "Folder", "Size", "Will Save", "Target Directory"])
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.move_btn = QPushButton("Move Selected and Create Symlinks")
        self.move_btn.setFont(font)
        self.move_btn.clicked.connect(self.move_selected_folders)
        self.move_btn.setEnabled(False)
        btn_layout.addWidget(self.move_btn)

        self.undo_btn = QPushButton("Undo Last Move")
        self.undo_btn.setFont(font)
        self.undo_btn.clicked.connect(self.undo_symlinks)
        self.undo_btn.setEnabled(False)
        btn_layout.addWidget(self.undo_btn)

        self.downloads_btn = QPushButton("Move Individual Files and Folders from Downloads")
        self.downloads_btn.setFont(font)
        self.downloads_btn.clicked.connect(self.move_downloads_files)
        btn_layout.addWidget(self.downloads_btn)

        layout.addLayout(btn_layout)

        if not is_admin():
            QMessageBox.critical(self, "Admin Required", "This tool must be run as Administrator.")
            sys.exit(1)

    def select_user_profile(self):
        folder = QFileDialog.getExistingDirectory(self, "Select User Profile Folder", "C:/Users")
        if folder:
            self.user_profile = Path(folder)
            self.profile_label.setText(f"User Profile: {folder}")
            self.start_scan()

    def start_scan(self):
        self.entries = []
        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.move_btn.setEnabled(False)
        self.undo_btn.setEnabled(True)

        self.scanner = FolderScanner(self.user_profile)
        self.scanner.progress.connect(self.progress.setValue)
        self.scanner.finished.connect(self.display_results)
        self.scanner.start()

    def display_results(self, entries):
        self.entries = entries
        self.table.setRowCount(len(entries))

        for i, entry in enumerate(entries):
            checkbox = QCheckBox()
            checkbox.setChecked(entry.should_move)
            self.table.setCellWidget(i, 0, checkbox)
            self.table.setItem(i, 1, QTableWidgetItem(str(entry.path)))
            self.table.setItem(i, 2, QTableWidgetItem(entry.size_human))
            self.table.setItem(i, 3, QTableWidgetItem(entry.size_human if entry.should_move else "—"))
            self.table.setItem(i, 4, QTableWidgetItem(str(entry.target)))

        self.move_btn.setEnabled(True)

    def safe_get_size(self, path):
        try:
            return path.stat().st_size
        except:
            return 0

    def move_selected_folders(self):
        if not self.user_profile:
            return

        symlink_log = self.user_profile / "symlinks.txt"
        log_lines = []
        total_moved = 0
        total_size = 0
        self.progress.setValue(0)

        selected_rows = [row for row in range(self.table.rowCount()) if self.table.cellWidget(row, 0).isChecked()]

        for idx, row in enumerate(selected_rows):
            folder_path = Path(self.table.item(row, 1).text())
            target_path = Path(self.table.item(row, 4).text())
            try:
                size = sum(self.safe_get_size(f) for f in folder_path.rglob('*') if f.is_file())
            except:
                size = 0

            if target_path.exists():
                reply = QMessageBox.question(self, "Folder Exists", f"{target_path} already exists. Overwrite and merge?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    continue

            target_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                if not folder_path.exists():
                    continue
                shutil.move(str(folder_path), str(target_path))
                os.symlink(str(target_path), str(folder_path), target_is_directory=True)
                log_lines.append(f"{folder_path} --> {target_path}")
                total_moved += 1
                total_size += size
                self.progress.setValue(int((idx + 1) / len(selected_rows) * 100))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to move {folder_path}:\n{str(e)}")

        with open(symlink_log, "a") as f:
            f.write("\n".join(log_lines) + "\n")

        QMessageBox.information(self, "Move Complete", f"Moved {total_moved} folder(s). Total saved: {humanize.naturalsize(total_size, binary=True)}")
        self.start_scan()

    def undo_symlinks(self):
        symlink_log = self.user_profile / "symlinks.txt"
        if not symlink_log.exists():
            QMessageBox.information(self, "Undo", "No symlink log found.")
            return

        restored = 0
        with open(symlink_log, "r") as f:
            lines = f.readlines()

        for line in reversed(lines):
            if "-->" not in line:
                continue
            orig, moved = [Path(p.strip()) for p in line.strip().split("-->")]
            try:
                if orig.is_symlink():
                    orig.unlink()
                    shutil.move(str(moved), str(orig))
                    restored += 1
            except Exception as e:
                print(f"Failed to undo {orig}: {e}")

        symlink_log.unlink()
        QMessageBox.information(self, "Undo Complete", f"Restored {restored} folder(s).")
        self.start_scan()

    def move_downloads_files(self):
        downloads_path = self.user_profile / "Downloads"
        if not downloads_path.exists():
            QMessageBox.information(self, "Downloads", "Downloads folder not found.")
            return

        relocate_base = Path(f"C:/User_{self.user_profile.name}/Downloads")
        relocate_base.mkdir(parents=True, exist_ok=True)
        items = list(downloads_path.iterdir())

        moved = 0
        total_size = 0

        for item in items:
            try:
                target = relocate_base / item.name
                size = item.stat().st_size if item.is_file() else sum(self.safe_get_size(f) for f in item.rglob('*') if f.is_file())
                shutil.move(str(item), str(target))
                total_size += size
                moved += 1
            except Exception as e:
                print(f"Could not move {item}: {e}")

        QMessageBox.information(self, "Downloads Move Complete", f"Moved {moved} items. Total saved: {humanize.naturalsize(total_size, binary=True)}")
        self.start_scan()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfileSlimmer()
    window.show()
    sys.exit(app.exec_())
