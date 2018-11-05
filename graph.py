"""
============
Multiprocess
============
Demo of using multiprocessing for generating data in one process and
plotting in another.
Written by Robert Cimrman
"""


import time


import scipy.stats
import numpy as np
import warnings
warnings.simplefilter('ignore', np.RankWarning)
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

# Fixing random state for reproducibility
np.random.seed(19680801)

###############################################################################
#
# Processing Class
# ================
#
# This class plots data it receives from a pipe.
#
refreshInterval = 1


class ProcessPlotter(object):
    def __init__(self):
       
        
           
        self.volumeData2 = {}
        self.priceData = {}
        self.colors = {}
   

        self.stock = 'SPY'
        
        self.x = []
        self.y = []
        self.a = 0;
        self.agg1 = 3; 
        self.agg2 = 15;
        self.agg3 = 30;
        self.aggs = [self.agg1]

        self.agg1Length = 18; 
        self.agg2Length = 10;
        self.agg3Length = 12

        self.aggsLength = [self.agg1Length, self.agg2Length, self.agg3Length]

    def terminate(self):
        plt.close('all')

    # def initialize(self):
    #     snapshot1 = self.b1.stream_snapshot('SPY', 'Volume',date_time=True)
    #     print(snapshot1);
    #     micro, sec, minute, hour, day, month, year = snapshot1[0][1];
        
    #     latestT = time.mktime(datetime.datetime(year, month, day, hour, minute, sec).timetuple()) 
       
        
        
    #     for index in range(1):
    #         print(snapshot1[0][1])
    #         i = 0;
     
    #         ourCurrentFuckingIndex = self.aggsLength[index] -1;
    #         largerVol =  snapshot1[0][0];
           
    #         while True:
    #             micro, sec, minute, hour, day, month, year = snapshot1[i][1]
    #             t = time.mktime(datetime.datetime(year, month, day, hour, minute, sec).timetuple()) 

                

    #             theDateTimeWeAreLookingFor =  latestT - (  (self.aggs[index]*self.aggsLength[index]) -  (ourCurrentFuckingIndex/self.aggsLength[index])*(self.aggs[index]*self.aggsLength[index]));
    #             # print("theDateTimeWeAreLookingFor")
    #             # print(theDateTimeWeAreLookingFor)
    #             # print("currentT")
    #             # print(t)

          
    #             if(ourCurrentFuckingIndex == -1 or  i + 1 >= len(snapshot1) ):
    #                 # print('bye')
    #                 break;
    #             elif(t < theDateTimeWeAreLookingFor ):
    #                 # print('hi')
    #                 self.timeData[item][index].insert(0,ourCurrentFuckingIndex*self.aggs[index])
    #                 ourCurrentFuckingIndex = ourCurrentFuckingIndex - 1;
    #                 smallerVol = snapshot1[i][0];
               
    #                 self.volumeData2[item][index].insert(0,(largerVol - smallerVol));
                    
    #                 largerVol = smallerVol;

    #             i = i +1;
        
         

    def graph(self):
        
        
        item = self.stock;
     
        
       
        Ys = np.diff(np.array(self.volumeData2[item][0]));
        priceChanges = np.diff(np.array(self.priceData[item][0]));

        colors = []

        for price in priceChanges:
            if(price > 0):
                colors.append('g')
            elif(price == 0):
                colors.append('k')
            else:
                colors.append('r')

        

        
        
        YsSorted = Ys;
        YsSorted = list(Ys[-100:])
        #YsSorted.sort();
        Xs = np.array(range(len(YsSorted)))

        colors = colors[-len(YsSorted):]

        
        
    
       
        

        self.ax.clear()
        self.ax.axhline(y=0, color='k')
       
        greenXs = [];
        redXs = [];

        redYs = [];
        greenYs = [];
        if(len(Ys)==0):
            return
        else:
            self.ax.scatter(Xs, YsSorted, c=colors)
            self.ax.plot(Xs, YsSorted, 'k-', linewidth=.5)

            # xIndex = 0;
            # for c in colors:
            #     if(c == 'r'):
            #         redYs.append(int(YsSorted[xIndex]));
            #         redXs.append(xIndex);
            #     elif(c == 'g'):
            #         greenYs.append(int(YsSorted[xIndex]));
            #         greenXs.append(xIndex);
            #     xIndex = xIndex + 1;

            # if(len(greenXs)>2):

           
            #     result = np.polyfit(greenXs, greenYs, 1)

            #     p = np.poly1d(result);
            #     yhat = p(Xs)                         # or [p(z) for z in x]
            #     ybar = np.sum(Ys)/len(Ys)          # or sum(y)/len(y)
            #     ssreg = np.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
            #     sstot = np.sum((Ys - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
            #     rsquared = ssreg / sstot
                  
            #     self.ax.plot(Xs, p(Xs), 'g-')
            #     self.ax.text(Xs[0],Ys[0],rsquared)

            # if(len(redXs)>2):
     
                
 

            #     result = np.polyfit(redXs, redYs, 1)

            #     p = np.poly1d(result);
            #     yhat = p(Xs)                         # or [p(z) for z in x]
            #     ybar = np.sum(Ys)/len(Ys)          # or sum(y)/len(y)
            #     ssreg = np.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
            #     sstot = np.sum((Ys - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
            #     rsquared = ssreg / sstot
                  
            #     self.ax.plot(Xs, p(Xs), 'r-')
            #     self.ax.text(Xs[0],Ys[0],rsquared)


        # else:
        #     self.ax.scatter(Xs, YsSorted,  c= self.colors[item][0] )
            
            # verts = [(Xs[0], 0)] + list(zip(Xs, YsSorted)) + [(Xs[-1], 0)]
            # poly = Polygon(verts, facecolor='0.9', edgecolor='0.0')
            # self.ax[index][1].add_patch(poly) 

            # thirdGraph = self.ax[index][2];
            # #thirdGraph.clear()

            # thirdGraph.axhline(y=0, color='k')
            
            # thirdGraph.plot(Xs, Ys,  'b-' )
            # verts2 = [(Xs[0], 0)] + list(zip(Xs, Ys)) + [(Xs[-1], 0)]
            # poly2 = Polygon(verts2, facecolor='0.9', edgecolor='0.0')
            # thirdGraph.add_patch(poly2) 
            

            # if len(Ys) > self.aggsLength[index]:
            #     #self.timeData[item][index].pop(0)
            #     Ys = np.diff(np.array(self.volumeData2[item][index]))[-self.aggsLength[index]:];
            #     Xs = np.array(range(len(Ys)))

            
            #i.clear();
            #i.scatter(Xs, Ys );
            
            
            
        

         

            #result = np.polyfit(Xs, Ys, 2)

            # p = np.poly1d(result);
            # yhat = p(Xs)                         # or [p(z) for z in x]
            # ybar = np.sum(Ys)/len(Ys)          # or sum(y)/len(y)
            # ssreg = np.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
            # sstot = np.sum((Ys - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
            # rsquared = ssreg / sstot
            
            
           
                       
            # self.ax[index][0].plot(Xs, p(Xs), 'r-')
            # self.ax[index][0].text(Xs[0],Ys[0],rsquared)

            # dprice = np.diff(self.priceData[item][index])
            # v = np.diff(self.volumeData2[item][index]);


            # v_buy = v * scipy.stats.norm.cdf(dprice / dprice.std())
            # v_sell = v - v_buy
            # bvpin = abs (v_sell - v_buy) / v
            # if(len(bvpin) != 0):
            #     self.ax[index][0].text(Xs[-1],Ys[-1],bvpin[-1])
                


    def call_back(self):
        
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                self.terminate()
                return False
            # elif(command.find('GetInfo-')!= -1):
            #     item = command[command.find('-')+1:]
            #     total_frame = self.b1.total_frame(date_time= True, labels=True);
            #     print(total_frame)
            #     info = {
            #         "BID":float(total_frame[item].BID[0]), 
            #         "ASK":float(total_frame[item].ASK[0])
            #         };
            #     print(info)
            #     self.pipe.send(info)
            
            else:
                self.stock = command

                self.ax.clear()
                


                
              


                if (command in self.b1.items()) == False:
                    self.b1.add_items(command)
            
              
                    self.priceData[command] = [[],[],[]]
                    self.volumeData2[command] = [[],[],[]]
                    self.colors[command] = [[],[],[]]
                    self.pipe.send('ADDED')
                   
                
            
                    
                else:
                    self.graph();
                    
                    total_frame = self.b1.total_frame(labels=True);
                    # print(total_frame)
                    # info = {
                    #     "BID":float(total_frame[item].BID[0]), 
                    #     "ASK":float(total_frame[item].ASK[0])
                    #     };
                    # print()
                    self.pipe.send(json.dumps(total_frame))
                    


       
        for item in self.b1.items():

            
            index = 0;
            while index< len(self.aggs):
                
                if ((self.a) % (self.aggs[index]) == 0) == False:
                    index += 1
                    continue
                
          
                
                
                #self.priceData[item][index].append( float(self.b1.get(item,'LAST')));
                vol = float( self.b1.get(item,'VOLUME',check_indx=False));
                last = float( self.b1.get(item,'LAST',check_indx=False));
                if(vol > 0):
                    self.volumeData2[item][index].append(vol);
                    self.priceData[item][index].append(last)

                
                

                




                  

                index += 1
                
                self.graph();

        
                
        self.a += 1
        self.fig.suptitle(self.stock)

        self.fig.canvas.draw()
    


       
        return True

    def __call__(self, pipe):
        print('starting plotter...')
        tosdb.init(dllpath="C:/TOSDataBridge-master/bin/Release/Win32/tos-databridge-0.9-x86.dll")
        b1 = tosdb.TOSDB_DataBlock(50, True);
        b1.add_topics('Volume');
        b1.add_topics('Last');

      

        b1.add_items('SPY')
        self.b1 = b1;

        for item in b1.items():
            self.volumeData2[item] = [[],[],[]];
            self.priceData[item] = [[],[],[]];
            self.colors[item] = [[],[],[]];


        self.pipe = pipe
        self.fig, self.ax = plt.subplots(1, sharex=False)
        #self.fig.set_size_inches((8,8))
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=.95)

        timer = self.fig.canvas.new_timer(interval=refreshInterval*1000)
        timer.add_callback(self.call_back)
        timer.start()
        #self.socketIO = sio('localhost', 5001,  wait_for_connection=False)
        print('...done')
        plt.show()

###############################################################################
#
# Plotting class
# ==============
#
# This class uses multiprocessing to spawn a process to run code from the
# class above. When initialized, it creates a pipe and an instance of
# ``ProcessPlotter`` which will be run in a separate process.
#
# When run from the command line, the parent process sends data to the spawned
# process which is then plotted via the callback function specified in
# ``ProcessPlotter:__call__``.
#


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
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)


    @socketio.on('mymessage')
    def test_message(message):
        print(message)
        pl.plot(message['src'])



    @socketio.on('connect')
    def test_connect():
        emit('my response', {'data': 'Graph Connected'})
        print('Graph Connected.')

    
    

    socketio.run(app, port=5001)
 
    
    

# def add_input(input_queue):
#     while True:
#         input_queue.put(sys.stdin.readline())






    # input_queue = Queue.Queue()

    # input_thread = threading.Thread(target=add_input, args=(input_queue,))
    # input_thread.daemon = True
    # input_thread.start()

    # last_update = time.time()


    


    # while True:

    #     if time.time()-last_update>0.5:
    #         sys.stdout.write(".")
    #         last_update = time.time()

    #     if not input_queue.empty():
    #         line = input_queue.get()
    #         if(len(line) != 0 ):
                




        

    # 
    # while True:
    #     line = sys.stdin.readline();
    #     print(line)
    #     
    


if __name__ == '__main__':
    main()