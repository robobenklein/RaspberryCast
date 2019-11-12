
import youtube_dl
import os
import threading
import logging
import json

from omxplayer.player import OMXPlayer, OMXPlayerDeadError

from process import return_full_url

log = logging.getLogger("RubusCast")

class PlaybackController(object):
    def __init__(self):
        self.player = None
        self.queue = []
        self.volume = 9.0

    def _new_player(self):
        """Creates a new player by popping from queue."""
        if self.player is not None:
            self.player.quit()
        v = self.queue.pop(0)
        log.info("Creating player for video: {}".format(v))
        self.player = OMXPlayer(v)

    def add_single_url(self, url):
        n_item = return_full_url(url)
        if n_item is not None:
            self.queue.append(n_item)
            return True

        raise ValueError("Could not get URL")

    def playlist(self, url):
        log.info("Adding every videos from playlist to queue.")
        ydl = youtube_dl.YoutubeDL({
            'logger': log,
            'extract_flat': 'in_playlist',
            'ignoreerrors': True,
        })
        with ydl:  # Downloading youtub-dl infos
            result = ydl.extract_info(url, download=False)
            for i in result['entries']:
                logger.info("queuing video")
                if i != result['entries'][0]:
                    self.add_single_url(i['url'])


    def play(self):
        if self.get_status() == "Playing":
            log.debug("Playback already playing.")
            return
        if self.player is None and len(self.queue) > 0:
            self._new_player()
        else:
            log.error("Nothing to play!")

    def stop(self):
        if self.player is not None:
            self.player.stop()
            self.player = None

    def playpause(self):
        if self.player is None:
            log.error("No player running.")
        self.player.play_pause()

    def pause(self):
        if self.get_status() == "Paused":
            log.debug("Playback is already paused.")
            return

    def seek(self, seconds):
        if self.player is None:
            raise Exception("Player is not running")
        self.player.seek(seconds)

    def skip_fwd(self, seconds):
        pass

    def skip_backward(self, seconds):
        pass

    def change_volume(self, increment):
        self.volume += increment
        if self.volume < 0.0:
            self.volume = 0.0
        elif self.volume > 10.0:
            self.volume = 10.0
        if self.player is not None:
            self.player.set_volume(self.volume)

    def get_status(self):
        if self.player is None:
            return "Stopped"
        try:
            return self.player.playback_status()
        except OMXPlayerDeadError:
            self.player = None
            return "Stopped"

    def shutdown(self):
        self.stop()
