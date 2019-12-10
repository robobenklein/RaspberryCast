
import youtube_dl
import os
import threading
import logging
import json

from omxplayer.player import OMXPlayer, OMXPlayerDeadError

from helpers import return_direct_media_url

log = logging.getLogger("RubusCast")
logger = log

class PlaybackItem(object):
    """Class for singular video"""
    def __init__(self, url):
        self.title = None
        self.user_input_url = url
        self.direct_media_url, self.ytdl_result = return_direct_media_url(self.user_input_url)
        if self.ytdl_result is not None:
            # attempt to get more info like title, etc
            try:
                self.title = self.ytdl_result['title']
                logger.info("Video Title: {}".format(
                    self.title
                ))
                self.thumbnail_url = self.ytdl_result['thumbnail']
            except KeyError as e:
                logger.debug(e)
        else:
            logger.warn("No metadata for URL: {}".format(
                self.direct_media_url
            ))

    def get_direct_url(self):
        return self.direct_media_url

    def get_title(self):
        if self.title is not None:
            return self.title
        else:
            return "No Title Available"

    def __str__(self):
        return "<PlaybackItem user_url='{}' title='{}'>".format(
            self.user_input_url,
            self.title
        )

class PlaybackController(object):
    def __init__(self):
        self.player = None
        self.queue = []
        self.current_playbackitem = None
        self.volume = 1.0

    def _on_omxplayer_exit(self, player, exit_status):
        log.info("OMXPlayer exit: {}".format(
            exit_status
        ))

    def _new_player(self):
        """Creates a new player by popping from queue."""
        log.info("Creating new OMXplayer.")
        if self.player is not None:
            self.player.quit()
        if self.current_playbackitem is None:
            if len(self.queue) == 0:
                raise ValueError("Nothing to play.")
            else:
                self.current_playbackitem = self.queue.pop(0)
        log.info("Creating player for video: {}".format(self.current_playbackitem))
        self.player = OMXPlayer(self.current_playbackitem.get_direct_url())
        self.player.set_volume(self.volume)
        self.player.exitEvent.subscribe(self._on_omxplayer_exit)

    def add_single_url(self, url):
        n_item = PlaybackItem(url)
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

    def change_volume(self, increment):
        self.volume += increment
        if self.volume < 0.0:
            self.volume = 0.0
        elif self.volume > 1.0:
            self.volume = 1.0
        if self.player is not None:
            self.player.set_volume(self.volume)

    def get_volume(self):
        if self.player is not None:
            return self.player.volume()
        else:
            return self.volume

    def get_status(self):
        if self.player is None:
            return "Stopped"
        try:
            return self.player.playback_status()
        except OMXPlayerDeadError:
            log.error("OMXPlayer is dead.")
            self.player = None
            return "Stopped"

    def shutdown(self):
        self.stop()
