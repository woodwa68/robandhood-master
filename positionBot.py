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


refreshInterval = 300


class ProcessPlotter(object):
    def __init__(self):

        self.data = {}
      
        self.stock = 'SPY'
        self.positions = [];

    def terminate(self):
        plt.close('all')

  

    def call_back(self):
        
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                self.terminate()
                return False
 
                
            else:
                self.stock = command['symbol']

                if (self.stock in self.b1.items()) == False:
                    self.b1.add_items(command['symbol']);            
                self.positions.append(command['symbol'])
                self.data[command['symbol']] = command;
              
                self.pipe.send('ADDED')

                # elif ((command['symbol'] in self.b1.items()) == True and command['remove']== True):
                #     self.b1.remove_items(command['symbol'])
            
              
                #     self.data[command['symbol']] = {};
                #     self.pipe.send('REMOVED')
        
                

        for item in self.positions:

            bid = float( self.b1.get(item,'BID',check_indx=False));
            ask = float( self.b1.get(item,'ASK',check_indx=False));
            priceBeforeRound = Decimal((bid+ask)/2.0)
            priceBeforeRound = float(round(priceBeforeRound, 2))
       

            if(self.data[item] != 'empty'  and priceBeforeRound != 0 and (float(self.data[item]['avgPrice']) - priceBeforeRound > 0.11)):
                print('stop-loss-trigger')
                self.data[item]['price'] = bid - .05
                self.socketIO.emit('getinfo', self.data[item])
             
            
              
                self.positions.remove(item);
                self.data[item] = 'empty';

    


       
        return True

    def __call__(self, pipe):
        print('starting plotter...')
        tosdb.init(dllpath="C:/TOSDataBridge-master/bin/Release/Win32/tos-databridge-0.9-x86.dll")
        b1 = tosdb.TOSDB_DataBlock(50, True);
        
        b1.add_topics('CUSTOM19')
        b1.add_topics('Last');

        b1.add_topics('ASK');
        
        b1.add_topics('BID');
   
        self.b1 = b1;
        self.positions = [];
        for item in b1.items():
            self.data = {};


        self.pipe = pipe
        self.fig, self.ax = plt.subplots(1,1, sharex=False)
        self.fig.set_size_inches((1,1))
        self.fig.tight_layout()
        
        self.socketIO = sio('localhost', 5000,  wait_for_connection=False)
        timer = self.fig.canvas.new_timer(interval=refreshInterval)
        timer.add_callback(self.call_back)
        timer.start()
        
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
          
            send(line)
            return recv()




def main():

    pl = NBPlot()

    app = Flask(__name__)

    socketio = SocketIO(app)



    @socketio.on('ADD_POSITION')
    def addSymbol(message):
        print(message)
      
        pl.plot(message)

    @socketio.on('REMOVE_POSITION')
    def removeSymbol(message):
        print(message)   
        pl.plot(message)


    socketio.run(app, port=5002)

if __name__ == '__main__':
    main()
