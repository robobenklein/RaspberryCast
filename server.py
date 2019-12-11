#!/usr/bin/env python3

import logging
import os
import sys
import json
import shutil
from urllib.request import urlretrieve
from bottle import Bottle, SimpleTemplate, request, response, \
                   template, run, static_file
# from process import launchvideo, queuevideo, playlist, \
#                     setState, getState, setVolume
from omxcontroller import PlaybackController

if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = 'raspberrycast.conf'
with open(config_file) as f:
      config = json.load(f)

# Setting log
logging.basicConfig(
    filename='Rubus.log',
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%m-%d %H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger("RubusCast")

# Creating handler to print messages on stdout
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

if config["new_log"]:
    try:
        os.system("sudo fbi -T 1 --noverbose -a images/ready.jpg")
    except Exception as e:
        log.error(e)

# setState("0")
# logger.info('Server successfully started!')

app = Bottle()
controller = PlaybackController()

SimpleTemplate.defaults["get_url"] = app.get_url


@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'


@app.route('/static/<filename>', name='static')
def server_static(filename):
    return static_file(filename, root='static')


@app.route('/')
@app.route('/remote')
def remote():
    logger.debug('Remote page requested.')
    return template('remote')


@app.route('/stream')
def stream():
    url = request.query['url']
    logger.debug('Received URL to cast: '+ url)

    try:
        if (
                ("youtu" in url and "list=" in url) or
                ("soundcloud" in url and "/sets/" in url)):
            playlist(url, True, config)
        else:
            controller.add_single_url(url)
        if controller.get_status() == "Stopped":
            controller.play()
        return "1"
    except Exception as e:
        logger.exception(e)
        return "0"


@app.route('/queue')
def queue():
    url = request.query['url']

    try:
        if controller.get_status() != "Stopped":
            logger.info('Adding URL to queue: '+url)
            if (
                    ("youtu" in url and "list=" in url) or
                    ("soundcloud" in url and "/sets/" in url)):
                controller.playlist(url)
            else:
                controller.add_single_url(url)
            return "2"
        else:
            logger.info('No video currently playing, playing url : '+url)
            if (("youtu" in url and "list=" in url) or
                ("soundcloud" in url and "/sets/" in url)):
                controller.playlist(url)
            else:
                controller.add_single_url(url)
                controller.play()
            return "1"
    except Exception as e:
        logger.error("Could not enqueue video!")
        logger.exception(e)
        return "0"


@app.route('/video')
def video():
    control = request.query['control']
    if control == "pause":
        logger.info('Command : pause')
        # os.system("echo -n p > /tmp/cmd &")
        controller.playpause()
        return "1"
    elif control == "stop":
        logger.info('Command : stop video')
        # os.system("echo -n q > /tmp/cmd &")
        controller.stop()
        return "1"
    elif control == "next":
        logger.info("Command : next video")
        controller.next_video()
        return "1"
    elif control == "right":
        logger.info('Command : forward')
        # os.system("echo -n $'\x1b\x5b\x43' > /tmp/cmd &")
        controller.seek(30)
        return "1"
    elif control == "left":
        logger.info('Command : backward')
        # os.system("echo -n $'\x1b\x5b\x44' > /tmp/cmd &")
        controller.seek(-30)
        return "1"
    elif control == "longright":
        logger.info('Command : long forward')
        # os.system("echo -n $'\x1b\x5b\x41' > /tmp/cmd &")
        controller.seek(300)
        return "1"
    elif control == "longleft":
        logger.info('Command : long backward')
        # os.system("echo -n $'\x1b\x5b\x42' > /tmp/cmd &")
        controller.seek(-300)
        return "1"

@app.route('/info')
def video():
    control = request.query['attr']
    if control == "title":
        return controller.current_playbackitem.get_title()
    elif control == "volume":
        return controller.get_volume()

@app.route('/sound')
def sound():
    vol = request.query['vol']
    if vol == "more":
        logger.info('REMOTE: Command : Sound ++')
        # os.system("echo -n + > /tmp/cmd &")
        controller.change_volume(0.1)
    elif vol == "less":
        logger.info('REMOTE: Command : Sound --')
        # os.system("echo -n - > /tmp/cmd &")
        controller.change_volume(-0.1)
    logger.info("Current volume: " + str(controller.get_volume()))
    return "1"


@app.route('/shutdown')
def shutdown():
    time = request.query['time']
    if time == "cancel":
        os.system("shutdown -c")
        logger.info("Shutdown canceled.")
        return "1"
    else:
        try:
            time = int(time)
            if (time < 2880 and time >= 0):
                shutdown_command = "shutdown -h +" + str(time) + " &"
                os.system(shutdown_command)
                logger.info("Shutdown should be successfully programmed")
                return "1"
        except:
            logger.error("Error in shutdown command parameter")
            return "0"


@app.route('/running')
def webstate():
    currentState = getState()
    logger.debug("Running state as been asked : " + currentState)
    return currentState

logger.info("Pre-run main file loaded.")
run(app, reloader=False, host='0.0.0.0', debug=True, quiet=True, port=2020)
