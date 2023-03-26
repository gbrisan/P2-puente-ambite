"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value


SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    
    def __init__(self):
        self.mutex = Lock()
        self.ncar_north = Value('i', 0) #número de coches en el puente
        self.ncar_south = Value('i', 0)
        self.nped = Value('i', 0) #número de peatones en el puente
        self.ncar_waiting_north = Value('i',0) #número de coches esperando en dirección norte
        self.ncar_waiting_south = Value('i',0)
        self.nped_waiting = Value('i',0) #número de peatones esperando
        self.turn = Value('i',0)
        #turn 0 for north cars
        #turn 1 for south cars
        #turn 2 for pedestrian
        self.can_north_cars=Condition(self.mutex)
        self.can_south_cars=Condition(self.mutex)
        self.can_ped=Condition(self.mutex)
 
    def north_cars(self):
        return self.ncar_south.value == 0 and self.nped.value==0 and\
            (self.turn.value == 0 or (self.ncar_waiting_south.value == 0 and\
            self.nped_waiting.value == 0))
            
    def south_cars(self):
        return self.ncar_north.value == 0 and self.nped.value==0 and\
                                        (self.turn.value == 1 or\
                                           (self.ncar_waiting_north.value == 0 and\
                                           self.nped_waiting.value == 0))
    def ped(self):
        return self.ncar_north.value == 0 and self.ncar_south.value==0 and\
            (self.turn.value == 2 or(self.ncar_waiting_north.value == 0 and\
                                           self.ncar_waiting_south.value == 0))
       

    def wants_enter_car(self, direction: int) -> None:
        
        if direction == 0 :
            self.mutex.acquire()
            self.ncar_waiting_north.value += 1
            self.can_north_cars.wait_for(self.north_cars)
            self.ncar_waiting_north.value -=1
            self.ncar_north.value += 1
            self.mutex.release()
            
        else:
            self.mutex.acquire()
            self.ncar_waiting_south.value += 1
            self.can_south_cars.wait_for(self.south_cars)
            self.ncar_waiting_south.value -=1
            self.ncar_south.value += 1
            self.mutex.release()  

    def leaves_car(self, direction: int) -> None:
        
        if direction == 0:
            self.mutex.acquire() 
            self.ncar_north.value -= 1
            if self.ncar_waiting_south.value != 0:
                self.turn.value = 1
                if self.ncar_north.value==0:
                    self.can_south_cars.notify_all()
            elif self.nped_waiting.value != 0:
                self.turn.value = 2
                if self.ncar_north.value==0:
                    self.can_ped.notify_all()
            self.mutex.release()
            
        else:
            self.mutex.acquire() 
            self.ncar_south.value -= 1
            
            
            if self.nped_waiting.value != 0:
                self.turn.value = 2
                if self.ncar_south.value == 0:
                    self.can_ped.notify_all()
                    
            elif self.ncar_waiting_north.value != 0:
                self.turn.value = 0
                if self.ncar_south.value == 0:
                    self.can_north_cars.notify_all() 
            self.mutex.release()
            

    def wants_enter_pedestrian(self) -> None:
        
        self.mutex.acquire()
        self.nped_waiting.value += 1
        self.can_ped.wait_for(self.ped)
        self.nped_waiting.value -=1
        self.nped.value +=1
        self.mutex.release()
        
    def leaves_pedestrian(self) -> None:
        
        self.mutex.acquire()
        self.nped.value -=1
        
        if self.ncar_waiting_north.value != 0:
            self.turn.value = 0
            if self.nped.value == 0:
                self.can_north_cars.notify_all()
        elif self.ncar_waiting_south !=0:
            self.turn.value = 1
            if self.nped.value == 0:
                self.can_south_cars.notify_all()
           
                
           
        self.mutex.release()

    def __repr__(self) -> str:
        return f"M<cn:{self.ncar_north.value},cs:{self.ncar_south.value},\
            cwn:{self.ncar_waiting_north.value},\
            cws:{self.ncar_waiting_south.value}, p:{self.nped.value}, \
            pw:{self.nped_waiting.value}, turn:{self.turn.value}>"

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