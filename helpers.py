
import youtube_dl
import os
import threading
import logging
import json
log = logging.getLogger("RubusCast")
logger = log

def return_direct_media_url(url):
    """Get the raw media url from a web url."""
    logger.debug("Getting direct_media_url for: " + url)

    if ((url[-4:] in (".avi", ".mkv", ".mp4", ".mp3")) or
            (".googlevideo.com/" in url)):
        logger.debug('Direct video URL, no need to use youtube-dl.')
        return url, None

    ydl = youtube_dl.YoutubeDL({
        'logger': logger,
        'noplaylist': True,
        'ignoreerrors': True,
    })  # Ignore errors in case of error in long playlists
    with ydl:  # Downloading youtube-dl infos. We just want to extract the info
        result = ydl.extract_info(url, download=False)

    if result is None:
        raise ValueError("URL <{}> could not be resolved.".format(
            url
        ))

    # logger.debug(result)

    if 'entries' in result:  # Can be a playlist or a list of videos
        video = result['entries'][0]
    else:
        video = result  # Just a video

    if "youtu" in url:
        logger.debug('''CASTING: Youtube link detected.
Extracting url in maximal quality.''')
        for fid in ('22', '18', '36', '17'):
            for i in video['formats']:
                if i['format_id'] == fid:
                    logger.debug(
                        'CASTING: Playing highest video quality ' +
                        i['format_note'] + '(' + fid + ').'
                    )
                    return i['url'], result
    else:
        logger.debug('''Video not from Youtube, extracting url in maximal quality.''')
        try:
            return video['url'], result
        except KeyError as e:
            log.warn("Error returning video URL:")
            log.warn(e)
            raise e
