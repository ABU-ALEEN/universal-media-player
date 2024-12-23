import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
                           QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
import requests
import m3u8

class PlaylistViewer(QWidget):
    channel_selected = pyqtSignal(str, str)  # Signal to emit channel URL and name

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPTV Playlist Viewer")
        self.resize(800, 600)
        self.setup_ui()
        self.channels = {}  # Dictionary to store channels data

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search channels...")
        self.search_input.textChanged.connect(self.filter_channels)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # URL input and load button
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter M3U/M3U8 playlist URL...")
        url_layout.addWidget(self.url_input)
        
        self.load_button = QPushButton("Load Playlist")
        self.load_button.clicked.connect(self.load_playlist)
        url_layout.addWidget(self.load_button)
        layout.addLayout(url_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        # Channel tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Channels"])
        self.tree.itemDoubleClicked.connect(self.on_channel_selected)
        layout.addWidget(self.tree)

        # Categories
        self.categories = {
            "Live TV": QTreeWidgetItem(self.tree, ["Live TV"]),
            "Movies": QTreeWidgetItem(self.tree, ["Movies"]),
            "Series": QTreeWidgetItem(self.tree, ["Series"]),
            "Sports": QTreeWidgetItem(self.tree, ["Sports"]),
            "News": QTreeWidgetItem(self.tree, ["News"]),
            "Kids": QTreeWidgetItem(self.tree, ["Kids"]),
            "Music": QTreeWidgetItem(self.tree, ["Music"]),
            "Others": QTreeWidgetItem(self.tree, ["Others"])
        }

    def load_playlist(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a playlist URL")
            return

        try:
            self.progress.show()
            self.progress.setRange(0, 0)  # Indeterminate progress
            self.load_button.setEnabled(False)
            
            # Clear existing items
            for category in self.categories.values():
                category.takeChildren()
            self.channels.clear()

            # Download and parse playlist
            response = requests.get(url)
            if not response.ok:
                raise Exception("Failed to download playlist")

            playlist_content = response.text
            channels = self.parse_m3u(playlist_content)

            # Categorize and add channels
            self.categorize_channels(channels)
            
            self.progress.hide()
            self.load_button.setEnabled(True)
            QMessageBox.information(self, "Success", f"Loaded {len(channels)} channels")

        except Exception as e:
            self.progress.hide()
            self.load_button.setEnabled(True)
            QMessageBox.warning(self, "Error", f"Failed to load playlist: {str(e)}")

    def parse_m3u(self, content):
        channels = []
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                # Parse channel info
                info = line[8:].split(',', 1)
                if len(info) > 1:
                    title = info[1]
                    # Get URL from next line
                    if i + 1 < len(lines):
                        url = lines[i + 1].strip()
                        if url and not url.startswith('#'):
                            channels.append({'title': title, 'url': url})
                i += 2
            else:
                i += 1
        return channels

    def categorize_channels(self, channels):
        for channel in channels:
            title = channel['title'].lower()
            url = channel['url']
            
            # Categorize based on keywords
            if any(word in title for word in ['news', 'cnn', 'bbc', 'aljazeera']):
                category = 'News'
            elif any(word in title for word in ['movie', 'film', 'cinema']):
                category = 'Movies'
            elif any(word in title for word in ['series', 'show', 'drama']):
                category = 'Series'
            elif any(word in title for word in ['sport', 'football', 'soccer', 'tennis']):
                category = 'Sports'
            elif any(word in title for word in ['kids', 'child', 'cartoon']):
                category = 'Kids'
            elif any(word in title for word in ['music', 'mtv', 'song']):
                category = 'Music'
            else:
                category = 'Live TV'

            # Add to tree
            item = QTreeWidgetItem(self.categories[category], [channel['title']])
            self.channels[channel['title']] = url

    def filter_channels(self):
        search_text = self.search_input.text().lower()
        for category in self.categories.values():
            for i in range(category.childCount()):
                item = category.child(i)
                item.setHidden(search_text not in item.text(0).lower())

    def on_channel_selected(self, item, column):
        if not item.parent():  # Skip if category is clicked
            return
        
        channel_name = item.text(0)
        if channel_name in self.channels:
            self.channel_selected.emit(self.channels[channel_name], channel_name)
