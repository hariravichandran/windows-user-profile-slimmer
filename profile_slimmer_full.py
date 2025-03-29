import sys
import os
import shutil
import humanize
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QFileDialog, QLabel,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

EXCLUDED_FOLDERS = {'AppData', 'MicrosoftEdgeBackups', 'OneDrive', 'Favorites', 'Saved Games', 'Searches'}
SIZE_THRESHOLD_MB = 500

class FolderEntry:
    def __init__(self, path: Path, size_bytes: int):
        self.path = path
        self.size_bytes = size_bytes
        self.should_move = size_bytes >= SIZE_THRESHOLD_MB * 1024 * 1024

    @property
    def size_human(self):
        return humanize.naturalsize(self.size_bytes, binary=True)

    @property
    def name(self):
        return self.path.name

class FolderScanner(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, int)

    def __init__(self, user_profile_path):
        super().__init__()
        self.user_profile_path = Path(user_profile_path)

    def run(self):
        entries = []
        all_items = [item for item in self.user_profile_path.iterdir()
                     if item.is_dir() and item.name not in EXCLUDED_FOLDERS and not item.is_symlink()]

        total = len(all_items)
        profile_size = 0

        for idx, folder in enumerate(all_items):
            try:
                size = self.get_folder_size(folder)
                profile_size += size
                entries.append(FolderEntry(folder, size))
            except Exception as e:
                print(f"Failed to scan {folder}: {e}")
            self.progress.emit(int((idx + 1) / total * 100))

        self.finished.emit(entries, profile_size)

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
        self.resize(850, 650)
        self.user_profile = None
        self.entries = []

        layout = QVBoxLayout(self)

        self.profile_label = QLabel("User Profile: Not selected")
        layout.addWidget(self.profile_label)

        self.pick_btn = QPushButton("Select User Profile Folder")
        self.pick_btn.clicked.connect(self.select_user_profile)
        layout.addWidget(self.pick_btn)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Move?", "Folder", "Size", "Will Save"])
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.move_btn = QPushButton("Move Selected and Create Symlinks")
        self.move_btn.clicked.connect(self.move_selected_folders)
        self.move_btn.setEnabled(False)
        btn_layout.addWidget(self.move_btn)

        self.undo_btn = QPushButton("Undo Last Move")
        self.undo_btn.clicked.connect(self.undo_symlinks)
        self.undo_btn.setEnabled(False)
        btn_layout.addWidget(self.undo_btn)

        self.downloads_btn = QPushButton("Move Individual Files from Downloads")
        self.downloads_btn.clicked.connect(self.move_downloads_files)
        btn_layout.addWidget(self.downloads_btn)

        layout.addLayout(btn_layout)

    def select_user_profile(self):
        folder = QFileDialog.getExistingDirectory(self, "Select User Profile Folder", "C:/Users")
        if folder:
            self.user_profile = Path(folder)
            self.profile_label.setText(f"User Profile: {folder}")
            self.start_scan()

    def start_scan(self):
        self.entries = []
        self.table.setRowCount(0)
        self.status_label.setText("Scanning...")
        self.progress.setValue(0)
        self.move_btn.setEnabled(False)
        self.undo_btn.setEnabled(True)

        self.scanner = FolderScanner(self.user_profile)
        self.scanner.progress.connect(self.progress.setValue)
        self.scanner.finished.connect(self.display_results)
        self.scanner.start()

    def display_results(self, entries, profile_size):
        self.entries = entries
        self.status_label.setText(f"Total Profile Size (excluding AppData): {humanize.naturalsize(profile_size, binary=True)}")
        self.table.setRowCount(len(entries))

        for i, entry in enumerate(entries):
            checkbox = QCheckBox()
            checkbox.setChecked(entry.should_move)
            self.table.setCellWidget(i, 0, checkbox)
            self.table.setItem(i, 1, QTableWidgetItem(str(entry.path)))
            self.table.setItem(i, 2, QTableWidgetItem(entry.size_human))
            self.table.setItem(i, 3, QTableWidgetItem(entry.size_human if entry.should_move else "—"))

        self.move_btn.setEnabled(True)

    def move_selected_folders(self):
        if not self.user_profile:
            return

        username = self.user_profile.name
        relocate_base = Path(f"C:/User_{username}")
        relocate_base.mkdir(parents=True, exist_ok=True)
        symlink_log = self.user_profile / "symlinks.txt"
        log_lines = []

        total_to_move = sum(1 for row in range(self.table.rowCount()) if self.table.cellWidget(row, 0).isChecked())
        moved_count = 0
        self.progress.setValue(0)

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not checkbox.isChecked():
                continue

            folder_path = Path(self.table.item(row, 1).text())
            target_path = relocate_base / folder_path.name

            try:
                if not folder_path.exists():
                    continue
                shutil.move(str(folder_path), str(target_path))
                os.symlink(str(target_path), str(folder_path), target_is_directory=True)
                log_lines.append(f"{folder_path} --> {target_path}")
                moved_count += 1
                self.progress.setValue(int((moved_count / total_to_move) * 100))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to move {folder_path}:{str(e)}")

        with open(symlink_log, "a") as f:
            f.write("\n".join(log_lines) + "\n")

        self.status_label.setText(f"✅ {moved_count} folder(s) moved and symlinked.")
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

        symlink_log.unlink()  # Delete the log after undo
        self.status_label.setText(f"🔁 Restored {restored} folder(s).")
        self.start_scan()

    def move_downloads_files(self):
        downloads_path = self.user_profile / "Downloads"
        if not downloads_path.exists():
            QMessageBox.information(self, "Downloads", "Downloads folder not found.")
            return

        relocate_base = Path(f"C:/User_{self.user_profile.name}/Downloads")
        relocate_base.mkdir(parents=True, exist_ok=True)
        files = list(downloads_path.glob("*"))

        moved = 0
        for file in files:
            if file.is_file():
                try:
                    shutil.move(str(file), str(relocate_base / file.name))
                    moved += 1
                except Exception as e:
                    print(f"Could not move {file}: {e}")

        self.status_label.setText(f"📁 Moved {moved} files from Downloads.")
        self.start_scan()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfileSlimmer()
    window.show()
    sys.exit(app.exec_())
