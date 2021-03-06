# Reaction Time Game
# Inspired by a project in The Arduino Inventor's Guide
import threading
from queue import Queue
from random import random
from time import sleep
from time import time

from flask import Flask, render_template
from flask_json import FlaskJSON, as_json
from gpiozero import Button, LED

# Times below are in seconds
SUSPENSE_TIME = .4
MIN_WAIT = 1.5
MAX_WAIT = 5
MAX_REACTION = 1
WAIT_RANGE = MAX_WAIT - MIN_WAIT
BLINK_TIME = .1
WIN_BLINK_TIME = .05
WIN_BLINKS = 5

class Player:
    def __init__(self, name, button, led):
        self.name = name
        self.button = Button(button)
        self.button.when_pressed = self.pressed
        self.led = LED(led)
        self.wins = 0
        self.fastest_ms = None
        
    def pressed(self):
        pass
    
players = (Player('Black',  16, 13),
           Player('Red',    20, 19),
           Player('White',  21, 26),
           Player('Yellow', 12,  6))

app = Flask(__name__)
json = FlaskJSON(app)
queue = Queue()

def players_by_score():
    sorted_players = list(players)
    sorted_players.sort(key=lambda player: player.wins, reverse=True)
    return sorted_players

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/reset")
@as_json
def reset():
    print('reset')
    for player in players:
        player.wins = 0
        player.fastest_ms = 0;
    return {}

@app.route("/status")
@as_json
def status():
    event = queue.get()
    sorted_players = players_by_score()
    names_scores = [[player.name, player.wins, player.fastest_ms or '']
                    for i, player in enumerate(sorted_players)]
    return {'event': event, 'scores': names_scores}


def pressing_players(): return [player for player in players if player.button.is_pressed]

def find_winners():
    disqualified = pressing_players()
    start = time()
    sleep(.06)  # Ignore any presses that are sooner than human reaction time would allow
    timeout = start + MAX_REACTION

    while time() < timeout:
        winners = [player for player in pressing_players() if player not in disqualified]
        if winners:
            return winners, time() - start
    return [], 0  # Timed out


def game_thread():
    while True:
        sleep(MIN_WAIT + random() * WAIT_RANGE)
        for player in players:
            player.led.on()
        winners, elapsed = find_winners()
        for player in players:
            player.led.off()
        sleep(SUSPENSE_TIME)  # Build suspense about who won
        for player in winners:
            player.led.blink(WIN_BLINK_TIME, WIN_BLINK_TIME, WIN_BLINKS)
            elapsed_ms = int(elapsed * 1000)
            queue.put('\n%s wins in %d milliseconds' % (player.name, elapsed_ms))
            if not player.fastest_ms or elapsed_ms < player.fastest_ms:
                player.fastest_ms = elapsed_ms
            player.wins += 1

threading.Thread(target=game_thread).start()
app.run(host='localhost', threaded=True)
