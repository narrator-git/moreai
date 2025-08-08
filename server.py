from flask import Flask, render_template, request, jsonify
from more import getresponse, createlog
from waitress import serve
from datetime import datetime
import os
import threading
import time

app = Flask(__name__)

def midnight_checker():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            with open("previd.txt") as p:
                previd = p.read()
            if previd:
                createlog(previd)
        time.sleep(60)

# Запускаем проверку полночи в отдельном потоке
midnight_thread = threading.Thread(target=midnight_checker, daemon=True)
midnight_thread.start()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/chat')
def getresp():
    usertext = request.args.get('usertext')
    if usertext:
        getresponse(usertext)

    with open("chathistory.txt") as c:
        history = [line.split("%") for line in c.read().split("\n") if line]

    # Если AJAX-запрос, возвращаем json
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(history=history)

    # Иначе рендерим страницу
    return render_template("chat.html", history=history)

@app.route('/journal')
def journal():
    with open("journal.txt") as j:
        journ = j.read()
    return render_template('journal.html', journal=journ)

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)