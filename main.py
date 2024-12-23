import sys
import vlc
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QPushButton, QFileDialog, QHBoxLayout, QLabel,
                           QSlider, QMenuBar, QMenu, QStatusBar, QAction, QInputDialog, 
                           QLineEdit, QMessageBox, QToolBar, QComboBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap
from playlist_viewer import PlaylistViewer

class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Media Player")
        self.setGeometry(100, 100, 800, 600)

        # Set the application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C0A1A;
                color: #FFFFFF;
            }
            QMenuBar {
                background-color: #4A0D2A;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #7A1745;
            }
            QMenu {
                background-color: #4A0D2A;
                color: #FFFFFF;
                border: 1px solid #7A1745;
            }
            QMenu::item:selected {
                background-color: #7A1745;
            }
            QToolBar {
                background-color: #4A0D2A;
                border: none;
                spacing: 10px;
                padding: 5px;
            }
            QComboBox {
                background-color: #7A1745;
                color: #FFFFFF;
                border: 1px solid #B01E53;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QComboBox:hover {
                background-color: #B01E53;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
                margin-right: 5px;
            }
            QPushButton {
                background-color: #7A1745;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 60px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #B01E53;
            }
            QSlider::groove:horizontal {
                background: #4A0D2A;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #B01E53;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #D62564;
            }
            QStatusBar {
                background-color: #4A0D2A;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        # Create playlist viewer
        self.playlist_viewer = PlaylistViewer()
        self.playlist_viewer.channel_selected.connect(self.play_channel)

        # Set window icon
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "logo.svg")
        self.setWindowIcon(QIcon(icon_path))

        # Create VLC instance and media player
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create toolbar
        self.create_toolbar()

        # Create video widget
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_widget, 1)  # Add stretch factor

        # Create controls layout
        self.controls_layout = QHBoxLayout()
        
        # Play button
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause)
        self.controls_layout.addWidget(self.play_button)

        # Fullscreen button
        self.fullscreen_button = QPushButton("⛶")  # Unicode symbol for fullscreen
        self.fullscreen_button.setToolTip("Toggle Fullscreen (F11)")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.controls_layout.addWidget(self.fullscreen_button)

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # Volume label
        self.volume_label = QLabel("Volume: 50%")
        self.volume_label.setMinimumWidth(80)
        
        self.controls_layout.addWidget(self.volume_label)
        self.controls_layout.addWidget(self.volume_slider)

        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        self.controls_layout.addWidget(self.time_label)

        # Time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMaximum(1000)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.controls_layout.addWidget(self.time_slider)

        self.layout.addLayout(self.controls_layout)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Timer for updating the time slider
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

        # Setup fullscreen handling
        self.is_fullscreen = False
        self.video_widget.mouseDoubleClickEvent = self.handle_double_click
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()

        self.is_playing = False
        self.setup_ui()

    def create_toolbar(self):
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(self.toolbar)

        # Add category selector
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Live TV", "Movies", "Series", "Sports", "News", "Kids", "Music"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        self.toolbar.addWidget(self.category_combo)

        # Add channel/content selector
        self.content_combo = QComboBox()
        self.content_combo.setMinimumWidth(200)
        self.content_combo.currentTextChanged.connect(self.on_content_selected)
        self.toolbar.addWidget(self.content_combo)

        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        # Create logo container
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(5)

        # Add logo
        logo_label = QLabel()
        pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.svg"))
        scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_layout.addWidget(logo_label)

        # Add name label with custom styling
        name_label = QLabel("ABU-ALEEN")
        name_label.setStyleSheet("""
            QLabel {
                color: #D62564;
                font-size: 14px;
                font-weight: bold;
                font-family: Arial;
                padding-right: 10px;
            }
        """)
        logo_layout.addWidget(name_label)

        self.toolbar.addWidget(logo_container)

    def on_category_changed(self, category):
        # Clear current content combo
        self.content_combo.clear()
        
        # Get items from playlist viewer for the selected category
        if hasattr(self.playlist_viewer, 'categories') and category in self.playlist_viewer.categories:
            category_item = self.playlist_viewer.categories[category]
            for i in range(category_item.childCount()):
                item = category_item.child(i)
                self.content_combo.addItem(item.text(0))

    def on_content_selected(self, content):
        # Play the selected content if it exists in the channels dictionary
        if content in self.playlist_viewer.channels:
            url = self.playlist_viewer.channels[content]
            self.play_channel(url, content)

    def setup_shortcuts(self):
        # F11 for fullscreen
        self.shortcut_f11 = QAction(self)
        self.shortcut_f11.setShortcut("F11")
        self.shortcut_f11.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.shortcut_f11)

        # Escape to exit fullscreen
        self.shortcut_esc = QAction(self)
        self.shortcut_esc.setShortcut("Esc")
        self.shortcut_esc.triggered.connect(self.exit_fullscreen)
        self.addAction(self.shortcut_esc)

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen()
            self.menuBar().hide()
            self.statusBar.hide()
            self.is_fullscreen = True
            self.fullscreen_button.setText("⧉")  # Change symbol when in fullscreen
        else:
            self.exit_fullscreen()

    def exit_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.menuBar().show()
            self.statusBar.show()
            self.is_fullscreen = False
            self.fullscreen_button.setText("⛶")

    def handle_double_click(self, event):
        self.toggle_fullscreen()

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Open local file action
        open_action = QAction("Open File", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Open URL action
        open_url_action = QAction("Open URL", self)
        open_url_action.setShortcut("Ctrl+U")
        open_url_action.triggered.connect(self.open_url)
        file_menu.addAction(open_url_action)
        
        # Open IPTV stream action
        open_stream_action = QAction("Open IPTV Stream", self)
        open_stream_action.setShortcut("Ctrl+I")
        open_stream_action.triggered.connect(self.open_stream)
        file_menu.addAction(open_stream_action)

        # Browse IPTV Channels action
        browse_channels_action = QAction("Browse IPTV Channels", self)
        browse_channels_action.setShortcut("Ctrl+B")
        browse_channels_action.triggered.connect(self.show_playlist_viewer)
        file_menu.addAction(browse_channels_action)
        
        # Add separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Subtitle menu
        subtitle_menu = menubar.addMenu("Subtitles")
        
        # Load subtitle file action
        load_subtitle_action = QAction("Load Subtitle", self)
        load_subtitle_action.triggered.connect(self.load_subtitle)
        subtitle_menu.addAction(load_subtitle_action)

    def show_playlist_viewer(self):
        self.playlist_viewer.show()

    def play_channel(self, url, name):
        media = self.instance.media_new(url)
        self.mediaplayer.set_media(media)
        self.play_pause()
        self.statusBar.showMessage(f"Playing: {name}")

    def open_url(self):
        url, ok = QInputDialog.getText(self, 'Open URL',
                                     'Enter video URL:', QLineEdit.Normal)
        if ok and url:
            media = self.instance.media_new(url)
            self.mediaplayer.set_media(media)
            self.play_pause()
            self.statusBar.showMessage(f"Playing URL: {url}")

    def open_stream(self):
        url, ok = QInputDialog.getText(self, 'Open IPTV Stream',
                                     'Enter IPTV stream URL (m3u/m3u8):', QLineEdit.Normal)
        if ok and url:
            if url.lower().endswith(('.m3u', '.m3u8')):
                media = self.instance.media_new(url)
                self.mediaplayer.set_media(media)
                self.play_pause()
                self.statusBar.showMessage(f"Playing IPTV Stream: {url}")
            else:
                QMessageBox.warning(self, "Invalid Format",
                                  "Please enter a valid M3U/M3U8 playlist URL")

    def open_file(self):
        dialog = QFileDialog()
        filename, _ = dialog.getOpenFileName(self, "Open Video",
                                           "",
                                           "Video Files (*.mp4 *.avi *.mkv *.mov);;IPTV Playlists (*.m3u *.m3u8);;All Files (*.*)")
        if filename:
            media = self.instance.media_new(filename)
            self.mediaplayer.set_media(media)
            self.play_pause()
            self.statusBar.showMessage(f"Playing: {filename}")

    def setup_ui(self):
        if sys.platform.startswith('linux'):  # for Linux
            self.mediaplayer.set_xwindow(int(self.video_widget.winId()))
        elif sys.platform == "win32":  # for Windows
            self.mediaplayer.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform == "darwin":  # for macOS
            self.mediaplayer.set_nsobject(int(self.video_widget.winId()))

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.play_button.setText("Play")
            self.is_playing = False
            self.timer.stop()
        else:
            if self.mediaplayer.play() == -1:
                self.open_file()
                return
            self.mediaplayer.play()
            self.play_button.setText("Pause")
            self.is_playing = True
            self.timer.start()

    def load_subtitle(self):
        dialog = QFileDialog()
        filename, _ = dialog.getOpenFileName(self, "Open Subtitle",
                                           "",
                                           "Subtitle Files (*.srt *.ass *.ssa);;All Files (*.*)")
        if filename:
            self.mediaplayer.video_set_subtitle_file(filename)
            self.statusBar.showMessage(f"Loaded subtitles: {filename}")

    def set_volume(self):
        volume = self.volume_slider.value()
        self.mediaplayer.audio_set_volume(volume)
        self.volume_label.setText(f"Volume: {volume}%")

    def set_position(self):
        pos = self.time_slider.value()
        self.mediaplayer.set_position(pos / 1000.0)

    def update_ui(self):
        media_pos = int(self.mediaplayer.get_position() * 1000)
        self.time_slider.setValue(media_pos)
        
        # Update time display
        if self.mediaplayer.is_playing():
            time_current = self.mediaplayer.get_time() // 1000  # Current time in seconds
            duration = self.mediaplayer.get_length() // 1000    # Total length in seconds
            
            current_str = f"{time_current//60:02d}:{time_current%60:02d}"
            total_str = f"{duration//60:02d}:{duration%60:02d}"
            self.time_label.setText(f"{current_str} / {total_str}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec_())
