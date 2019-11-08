
import youtube_dl
import os
import threading
import logging
import json

from omxplayer.player import OMXPlayer

from process import return_full_url

log = logging.getLogger("RubusCast")

class PlaybackController(object):
    def __init__(self):
        self.player = None
        self.queue = []
        self.volume = 9.0

    def _new_player(self, src):
        if self.player is not None:
            self.player.quit()
        self.player = OMXPlayer(src)

    def add_single_url(self, url):
        # Ignore errors in case of error in long playlists
        ydl = youtube_dl.YoutubeDL({
            'logger': log,
            'noplaylist': True,
            'ignoreerrors': True,
        })
        # Downloading youtube-dl infos. We just want to extract the info
        with ydl:
            result = ydl.extract_info(url, download=False)

        if result is None:
            log.error("Failed to get source file from url: " + str(url))
            return False

        if 'entries' in result:  # Can be a playlist or a list of videos
            video = result['entries'][0]
        else:
            video = result  # Just a video

        if "youtu" in url:
            log.debug("YouTube video.")
            for fid in ('22', '18', '36', '17'):
                for i in video['formats']:
                    if i['format_id'] == fid:
                        log.debug(
                            'CASTING: Playing highest video quality ' +
                            i['format_note'] + '(' + fid + ').'
                        )
                        self.queue.append(i['url'])
        elif "vimeo" in url:
            log.debug("Vimeo video.")
            self.queue.append(video['url'])
        else:
            log.debug('''Video not from Youtube or Vimeo.''')
            self.queue.append(video['url'])

        return True


    def play(self):
        if self.get_status() == "Playing":
            log.debug("Playback already playing.")
            return
        if self.player is None and len(self.queue) > 0:
            self._new_player(self.queue[0])
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
        return self.player.playback_status()

    def shutdown(self):
        self.stop()
