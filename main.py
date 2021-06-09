##!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import gui
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5.QtCore import QTimer, QSize, Qt
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor
import pygame
from mutagen import File, MutagenError
import resources


class Exx(QMainWindow, gui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.initPygame()
        self.initButtonSignal()
        self.initButtonIcon()
        self.slider_signal_init()
        self.launchAlbumCover()
        self.initLabel()
        self.mute_val = False
        self.state_playing = None

    def initUI(self):
        self.setWindowTitle('Music player v0.99')
        self.setWindowIcon(QIcon(':/sourse/pass.jpg'))
        self.setAcceptDrops(True)
        self.label_name_song.setWordWrap(True)
        self.progress_bar.setMinimum(1)

    def initPygame(self):
        pygame.init()
        pygame.mixer.init()

    def initButtonSignal(self):
        self.button_play.clicked.connect(self.playingEvent)
        self.button_stop.clicked.connect(self.stop)
        self.button_open.clicked.connect(self.browseFolder)
        self.button_next.clicked.connect(self.nextSong)
        self.button_prev.clicked.connect(self.prevSong)

        self.button_play.setEnabled(False)
        self.button_stop.setEnabled(False)
        self.button_next.setEnabled(False)
        self.button_prev.setEnabled(False)

    def initButtonIcon(self):
        self.button_play.setIcon(QIcon(':/sourse/play.png'))
        self.button_play.setIconSize(QSize(30, 30))
        self.button_stop.setIcon(QIcon(':/sourse/stop.png'))
        self.button_stop.setIconSize(QSize(20, 20))
        self.button_open.setIcon(QIcon(':/sourse/open.png'))
        self.button_open.setIconSize(QSize(25, 25))
        self.button_next.setIcon(QIcon(':/sourse/next.png'))
        self.button_next.setIconSize(QSize(25, 25))
        self.button_prev.setIcon(QIcon(':/sourse/prev.png'))
        self.button_prev.setIconSize(QSize(25, 25))

    def initLabel(self):
        self.label_pic_volume.labelClicked.connect(self.mute)
        self.label_vol_value.setText('50')
        self.setLabelTimeUp(0)
        self.label_total_time.setText(self.formatTime(0))
        self.setVolume()
        self.label_name_song.setText('Ready to play music')

    def slider_signal_init(self):
        self.progress_bar.sliderClicked.connect(
            lambda: self.setPlaybackPosition(self.progress_bar.value()))
        self.progress_bar.setEnabled(False)
        self.slider_volume.valueChanged.connect(
            self.setVolume)
        self.slider_volume.sliderMoved.connect(
            self.setVolume)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            value = [url.path().lstrip('/') for url in event.mimeData().urls()]
            self.initListFile(value)

    def initMusic(self, value):
        self.button_play.setIcon(QIcon(':/sourse/pause.png'))
        self.name_song = value
        try:
            pygame.mixer.music.load(self.name_song)
            pygame.mixer.music.play()
        except pygame.error as err:
            print(err)
            self.getAlbumCover()
            self.label_name_song.setText('Unsupported format')
            if self.state_playing is not None:
                self.stop()
            self.button_play.setEnabled(False)
            self.label_total_time.setText(self.formatTime(0))
        else:
            self.setProgressBar()  # ползунок на начало
            self.setLabelTimeUp(0)
            self.getLength(self.name_song)
            self.getNameSong(self.name_song)

            # громкость звука перед началом проигрывания
            self.setVolume()

            # отображение обложки
            self.getAlbumCover(self.name_song)

            self.button_play.setEnabled(True)
            self.button_stop.setEnabled(True)
            self.progress_bar.setEnabled(True)

            self.time_mus = 0
            self.setProgressBarTimer()
            self.setMusicTimer()

            self.label_total_time.setText(self.formatTime(self.length))

            self.state_playing = 'play'

    def getAlbumCover(self, song=None):
        try:
            file = File(song)
            artwork = file.tags['APIC:']
        except (KeyError, TypeError, MutagenError):
            self.launchAlbumCover()
        else:
            pixmap = QPixmap()
            pixmap.loadFromData(artwork.data)
            self.label_album_cover.setPixmap(
                pixmap.scaled(
                    500,
                    500,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation))

    def launchAlbumCover(self):
        self.label_album_cover.setPixmap(QPixmap(
            ':/sourse/pass.jpg').scaled(
                500,
                500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation))

    def getNameSong(self, song=None):
        try:
            file = File(song, easy=True)
            title = file['title'][0]
            artist = file['artist'][0]
        except (MutagenError, KeyError):
            value = self.name_song.split(sep='/')[-1].split('.mp3')[0]
        else:
            value = f'{title} - {artist}'
        self.label_name_song.setText(value)

    def getLength(self, song=None):
        try:
            file = File(song)
        except MutagenError as err:
            print(err)
        else:
            self.length = file.info.length

    def playingEvent(self):
        if self.state_playing in (None, 'stop'):
            self.initMusic(self.name_song)
            self.state_playing = 'play'
        elif self.state_playing == 'play':
            pygame.mixer.music.pause()
            self.state_playing = 'pause'
            self.button_play.setIcon(QIcon(':/sourse/play.png'))
            self.tmr0.stop()
            self.tmr1.stop()
        elif self.state_playing == 'pause':
            pygame.mixer.music.unpause()
            self.state_playing = 'play'
            self.button_play.setIcon(QIcon(':/sourse/pause.png'))
            self.setProgressBarTimer()
            self.setMusicTimer()

    def stop(self):
        pygame.mixer.music.stop()
        self.state_playing = 'stop'
        self.setLabelTimeUp(0)
        self.setProgressBar()
        self.setProgressBarTimer('stop')
        self.setMusicTimer('stop')
        self.button_play.setIcon(QIcon(':/sourse/play.png'))
        self.progress_bar.setEnabled(False)

    def formatTime(self, n):
        n = round(n)
        h = n // 3600
        m = n // 60 % 60
        s = n % 60
        if s < 10 and h == 0:
            return f"{m}:{s:0>2}"
        if h == 0:
            return f"{m}:{s}"
        if s < 10:
            return f"{h}:{m}:{s:0>2}"
        else:
            return f"{h}:{m}:{s}"

    def setLabelTimeUp(self, value):
        self.label_time_up.setText(self.formatTime(value))

    def browseFolder(self):
        before_directory = QFileDialog.getOpenFileNames(
            self, None, None, "*.mp3")[0]

        # исключение диалогового окна без импортированных файлов
        if bool(before_directory) is True:
            self.initListFile(before_directory)

    def initListFile(self, value):
        self.directory = value
        if len(self.directory) > 1:
            self.button_next.setEnabled(True)
            self.button_prev.setEnabled(True)
        else:
            self.button_next.setEnabled(False)
            self.button_prev.setEnabled(False)
        self.position_playlist = 0
        self.getPositionTracklist()
        self.name_song = self.directory[0]
        self.initMusic(self.name_song)

    def nextSong(self):
        try:
            self.name_song = self.directory[self.position_playlist + 1]
        except IndexError:
            True
        else:
            self.position_playlist += 1
            self.initMusic(self.name_song)
            self.getPositionTracklist()

    def prevSong(self):
        if self.position_playlist < 1:
            True
        else:
            self.name_song = self.directory[self.position_playlist - 1]
            self.position_playlist -= 1
            self.initMusic(self.name_song)
            self.getPositionTracklist()

    def getPositionTracklist(self):
        self.label_tracklist_info.setText(
            f'{self.position_playlist+1} of {len(self.directory)}')

    def setVolume(self):
        volume = self.slider_volume.value()
        self.label_vol_value.setText(f'{volume}')
        if volume == 0:
            val = ':/sourse/volume_0.png'
        elif 1 <= volume <= 30:
            val = ':/sourse/volume_1-30.png'
        elif 31 <= volume <= 65:
            val = ':/sourse/volume_31-65.png'
        elif 66 <= volume <= 100:
            val = ':/sourse/volume_66-100.png'
        if volume != 0:
            self.mute_val = False
        pic_vol = QPixmap(val)
        self.label_pic_volume.setPixmap(
            pic_vol.scaled(
                30,
                20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        pygame.mixer.music.set_volume(volume / 100)

    def mute(self):
        if self.mute_val is False:
            self.vol_val_before = self.slider_volume.value()
            self.slider_volume.setValue(0)
            self.mute_val = True
        else:
            self.slider_volume.setValue(self.vol_val_before)
            self.mute_val = False
        self.setVolume()

    def setProgressBarTimer(self, val=None):
        if val == 'stop':
            self.tmr0.stop()
        else:
            self.tmr0 = QTimer()
            self.tmr0.timeout.connect(lambda: self.setProgressBar(
                self.progress_bar.value()))
            self.tmr0.start(round(self.length * 10))

    def setMusicTimer(self, val=None):
        if val == 'stop':
            self.tmr1.stop()
        else:
            self.tmr1 = QTimer()
            self.tmr1.timeout.connect(self.musicCountDown)
            self.tmr1.start(10)

    def setProgressBar(self, position=0):
        position += 1
        self.progress_bar.setValue(position)

    def musicCountDown(self):
        '''отсчет времени от начала музыки'''
        self.time_mus += 1
        if self.time_mus >= self.length * 100:
            self.time_mus = 0
            if len(self.directory) > 1 and (self.position_playlist + 1
                                            != len(self.directory)):
                self.nextSong()
            else:
                self.stop()
        if self.time_mus % 100 == 0:
            self.setLabelTimeUp(self.time_mus // 100)

    def setPlaybackPosition(self, value):
        if self.progress_bar.isEnabled() is True:
            time = self.length / 100 * value
            self.time_mus = round(time * 100)
            try:
                pygame.mixer.music.set_pos(time)
            except pygame.error:
                self.label_name_song.setText('codec error')
                self.stop()
            self.setLabelTimeUp(self.time_mus // 100)

    def closeEvent(self, event):
        pygame.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Highlight, QColor(200, 200, 150).lighter())
    app.setPalette(palette)
    window = Exx()
    window.setFixedSize(500, 591)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
