#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 19:40:03 2023

@author: marcelaygabriela
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 10
NPED = 1
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    
    def __init__(self):
        
        self.ncars_north = Value('i',0)
        self.ncars_south = Value('i',0)
        self.nped = Value('i',0)
        self.mutex = Lock()
        self.no_north_cars = Condition(self.mutex)
        self.no_south_cars = Condition(self.mutex)
        self.no_ped = Condition(self.mutex)
    
    def north_cars(self):
        return self.ncar_south.value == 0 and self.nped.value==0 
    
    def southh_cars(self):
        return self.ncar_north.value == 0 and self.nped.value==0 
    def ped(self):
        return self.ncar_south.value == 0 and self.ncar_north.value==0 
    
    def wants_enter_car(self, direction: int) -> None:
        
        if direction == 0 :
            self.mutex.acquire()
            self.no_south_cars.wait_for(self.are_no_south_cars)
            self.no_ped.wait_for(self.are_no_ped)
            self.ncars_north.value += 1
            self.mutex.release()
        else:
            self.mutex.acquire()
            self.no_north_cars.wait_for(self.are_no_north_cars)
            self.no_ped.wait_for(self.are_no_ped)
            self.ncars_south.value += 1
            self.mutex.release()  
            
            
    def leaves_car(self, direction: int) -> None:
        
        if direction == 0:
            self.mutex.acquire() 
            self.ncars_north.value -= 1
            if self.ncars_north.value==0:
                self.no_north_cars.notify()
            self.mutex.release()
        else:
            self.mutex.acquire() 
            self.ncars_south.value -= 1
            if self.ncars_south.value==0:
                self.no_south_cars.notify()
            self.mutex.release()
    
    def wants_enter_pedestrian(self) -> None:
        
        self.mutex.acquire()
        self.no_north_cars.wait_for(self.are_no_north_cars)
        self.no_south_cars.wait_for(self.are_no_south_cars)
        self.nped.value +=1
        self.mutex.release()
        
    def leaves_pedestrian(self) -> None:
        
        self.mutex.acquire()
        self.nped.value -=1
        if self.nped.value==0:
                self.no_ped.notify()
        self.no_ped.notify()
        self.mutex.release()

    def __repr__(self) -> str:
        return f"M<cn:{self.ncars_north.value},cs:{self.ncars_south.value},\
            p:{self.nped.value}>"

def delay_car_north() -> None:
    time.sleep(0.5)

def delay_car_south() -> None:
    time.sleep(0.5)

def delay_pedestrian() -> None:
    time.sleep(1.0)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()

#mqtt
        
        
