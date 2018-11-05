"""
============
Multiprocess
============

Demo of using multiprocessing for generating data in one process and
plotting in another.

Written by Robert Cimrman
"""


import time


import warnings
import sys

import tosdb
import json
from multiprocessing import Process, Pipe

# This example will likely not work with the native OSX backend.
# Uncomment the following lines to use the qt5 backend instead.
#
# import matplotlib
# matplotlib.use('qt5agg')
#
# Alternatively, with Python 3.4+ you may add the line
#

#
# immediately after the ``if __name__ == "__main__"`` check.

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
plt.rcParams.update({'font.size': 8})
from datetime import timedelta
import datetime, time

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from socketIO_client import SocketIO as sio
from decimal import Decimal
from math import floor


refreshInterval = 25


class ProcessPlotter(object):
    def __init__(self):

        self.priceData = {}
        self.stock = 'SPY'

    def terminate(self):
        plt.close('all')

  

    def call_back(self):
        
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                self.terminate()
                return False
 
            
            else:
                self.stock = command

                if (command in self.b1.items()) == False:
                    self.b1.add_items(command)
            
              
                    self.priceData[command] = [[],[],[]]
                    self.pipe.send('ADDED')
        
                else:
                    total_frame = self.b1.total_frame(labels=True);
                    self.pipe.send(json.dumps(total_frame))

        return True

    def __call__(self, pipe):
        print('starting plotter...')
        tosdb.init(dllpath="C:/TOSDataBridge-master/bin/Release/Win32/tos-databridge-0.9-x86.dll")
        b1 = tosdb.TOSDB_DataBlock(50, True);
        
        b1.add_topics('CUSTOM19')
        b1.add_topics('Last');

        b1.add_topics('ASK');
        
        b1.add_topics('BID');
        b1.add_items('SPY')
        self.b1 = b1;

        for item in b1.items():
            self.priceData[item] = [[],[],[]];


        self.pipe = pipe
        self.fig, self.ax = plt.subplots(1,1, sharex=False)
        self.fig.set_size_inches((1,1))
        self.fig.tight_layout()
        

        timer = self.fig.canvas.new_timer(interval=refreshInterval)
        timer.add_callback(self.call_back)
        timer.start()
        self.socketIO = sio('localhost', 5000,  wait_for_connection=False)
        print('...done')
        plt.show()



class NBPlot(object):
    def __init__(self):

        self.plot_pipe, plotter_pipe = Pipe()
        self.plotter = ProcessPlotter()
        self.plot_process = Process(
            target=self.plotter,
            args=(plotter_pipe,)
        )
        self.plot_process.daemon = True
        self.plot_process.start()

    def plot(self, line, finished=False):
        send = self.plot_pipe.send
        recv = self.plot_pipe.recv
      
        if finished:
            send(None)
        else:
          
            send(line.strip())
            return recv()

    def check_for_triggers(self):
        
        command = self.plot_pipe.recv()
        print (command)
        return command;




def main():

    pl = NBPlot()

    app = Flask(__name__)

    socketio = SocketIO(app)


    @socketio.on('GET_BID')
    def getBid(message):
        print(message)

        index = 1
    
        response = json.loads(pl.plot(message['src']))
        response = Decimal(float(response[message['src']][index]) - .05);
        response = float(round(response,2))

        emit('myresponse', {'price': response, 'side':message['side']} )

    @socketio.on('GET_LAST')
    def getLast(message):
        print(message)

        response = json.loads(pl.plot(message['src']))
        
        priceBeforeRound = (float(response[message['src']][0])+float(response[message['src']][1]))/2.0
        priceBeforeRound = Decimal(priceBeforeRound)
        priceBeforeRound = float(round(priceBeforeRound, 2))
        
        if(response[message['src']][2] == "0.05"):
            priceBeforeRound = floor(priceBeforeRound * 20) / 20
            
        print(response)
        emit('myresponse', {'price': priceBeforeRound, 'side' :message['side'],})

    @socketio.on('GET_ASK')
    def getAsk(message):
        print(message)
        
        index = 0
    
        response = json.loads(pl.plot(message['src']))
        response = Decimal(float(response[message['src']][index]) + .05); 
        response = float(round(response,2))

       
        emit('myresponse', {'price': response, 'side':message['side'], 'scalp':message['scalp']})

    @socketio.on('ADD_SYMBOL')
    def addSymbol(message):
        print(message)
      
        pl.plot(message['src'])



    @socketio.on('getinfo')
    def getinfo(message):
        print(message)
        emit('myresponse', message, broadcast=True)
   

    @socketio.on('connect')
    def test_connect():
        emit('my response', {'data': 'Data Bridge Connected'})
        print('Data Bridge Connected.')

    socketio.run(app)

if __name__ == '__main__':
    main()
