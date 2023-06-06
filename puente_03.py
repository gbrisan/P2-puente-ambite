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
        self.ncar_north = Value('i', 0) #número de coches dirección norte en el puente
        self.ncar_south = Value('i', 0) #número de coches dirección sur en el puento
        self.nped = Value('i', 0) #número de peatones en el puente
        self.ncar_waiting_north = Value('i',0) #número de coches esperando en dir norte
        self.ncar_waiting_south = Value('i',0) #número de coches esperando en dir sur
        self.nped_waiting = Value('i',0) #número de peatones esperando
        self.turn = Value('i',0)
        #turn 0 coches norte
        #turn 1 coches sur
        #turn 2 peatones
        self.can_north_cars=Condition(self.mutex)
        self.can_south_cars=Condition(self.mutex)
        self.can_ped=Condition(self.mutex)
 
    def north_cars(self):
        '''
        Para que un coche con dirección norte pueda acceder al puente se tienen
        que cumplir las siguientes condiciones:
            1) No hay coches dirección sur ni peatones en el puente
            2) El turno actual es el 0 o no hay coches en dirección sur ni peatones
               esperando
        '''
        return self.ncar_south.value == 0 and self.nped.value==0 and\
            (self.turn.value == 0 or (self.ncar_waiting_south.value == 0 and\
            self.nped_waiting.value == 0))
            
    def south_cars(self):
        '''
        Para que un coche con dirección sur pueda acceder al puente se tienen
        que cumplir las siguientes condiciones:
            1) No hay coches dirección norte ni peatones en el puente
            2) El turno actual es el 1 o no hay coches en dirección norte ni 
                peatonesesperando
        '''
        return self.ncar_north.value == 0 and self.nped.value==0 and\
                                        (self.turn.value == 1 or\
                                           (self.ncar_waiting_north.value == 0 and\
                                           self.nped_waiting.value == 0))
    def ped(self):
        '''
        Para que un peatón pueda acceder al puente se tienenque cumplir las 
        siguientes condiciones:
            1) No hay coches  en el puente
            2) El turno actual es el 2 o no hay coches esperando
        '''
        return self.ncar_north.value == 0 and self.ncar_south.value==0 and\
            (self.turn.value == 2 or(self.ncar_waiting_north.value == 0 and\
                                           self.ncar_waiting_south.value == 0))
       

    def wants_enter_car(self, direction: int) -> None:
        '''
        ENTRADA AL PUENTE: COCHES
        
        Si un coche quiere entrar se distingue entre dos casos: si va en dir
        sur o si va en dir norte.
        
        Supongamos que la dirección del coche es norte (0), es análogo para sur.
        
        En un primer momento, el contador de coches en dirección norte esperando 
        aumenta en una unidad y el coche se va a quedar esperando hasta que su 
        condición de entrada se cumpla.
        
        Una vez se verifique su condición de entrada, el coche se quita de la
        lista de espera mientras que el número de coches en el puente en dirección
        norte aumentará en una unidad.
        
        De este modo se cumple que el número de coche esperando y de coches
        en el puente es siempre mayor o igual que cero
        '''
        
        self.mutex.acquire()
        if direction == 0 :
            
            self.ncar_waiting_north.value += 1
            self.can_north_cars.wait_for(self.north_cars)
            self.ncar_waiting_north.value -=1
            self.ncar_north.value += 1
                
                
        elif direction == 1 :
                
            self.ncar_waiting_south.value += 1
            self.can_south_cars.wait_for(self.south_cars)
            self.ncar_waiting_south.value -=1
            self.ncar_south.value += 1
                
        self.mutex.release()
                  

    def leaves_car(self, direction: int) -> None:
        '''
        SALIDA DEL PUENTE: COCHES
        
        Al igual que en la entrada se van a distinguir dos posibilidades: que
        el coche circule en dirección norte o sur.
        
        Supongamos que circula en dirección norte(0), análogo para sur.
        
        En primer lugar el número de coches en dirección norte que ocupan el 
        puente desciende en una unidad.
        
        Posteriormente se comprueba si hay coches en dirección sur esperando.
        En ese caso, el turno pasa a ser 1 y se comprueba si ya no hay coches
        en dirección norte, si no hay se avisa a los coches en dirección sur
        que querían entrar y estaban bloqueados.
        
        Si no hay coches en dirección sur esperando pero hay peatones, entonces
        el turno pasa a 2 y se comprueba que no queden coches en dirección norte
        que bloqueen la entrada de los peatones. Si no los hay, se avisa a los
        peatones que estaban en espera.
        
        Si no hay no peatones ni coches en dirección sur esperando, el turno 
        es 0
        '''
        
        self.mutex.acquire()
        if direction == 0:
             
            self.ncar_north.value -= 1
            if self.ncar_waiting_south.value != 0:
                self.turn.value = 1
                if self.ncar_north.value == 0:
                    self.can_south_cars.notify_all()
                    
            elif self.nped_waiting.value != 0:
                self.turn.value = 2
                if self.ncar_north.value==0:
                    self.can_ped.notify_all()
            else:
                self.turn.value = 0
            
        elif direction == 1:
            self.ncar_south.value -= 1
            
            if self.nped_waiting.value != 0:
                self.turn.value = 2
                if self.ncar_south.value == 0:
                    self.can_ped.notify_all()
                    
            elif self.ncar_waiting_north.value != 0:
                self.turn.value = 0
                if self.ncar_south.value == 0:
                    self.can_north_cars.notify_all() 
                else:
                    self.turn.value = 1
                
        self.mutex.release()
            

    def wants_enter_pedestrian(self) -> None:
        '''
        ENTRADA AL PUENTE: PEATONES
        
        Cuando un peatón quiere entrar al puente.
        En un primer momento, el contador de peatones esperando 
        aumenta en una unidad y el peatón se va a quedar bloqueado hasta que su 
        condición de entrada se cumpla.
        Una vez se verifique su condición de entrada, el peatón se quita de la
        lista de espera mientras que el número de peatones en el puente en dirección
        norte aumentará en una unidad
        
        De este modo se cumple que el número de peatones esperando y de peatones
        en el puente es siempre mayor o igual que cero
        '''
        
        self.mutex.acquire()
        self.nped_waiting.value += 1
        self.can_ped.wait_for(self.ped)
        self.nped_waiting.value -=1
        self.nped.value +=1
        self.mutex.release()
        
    def leaves_pedestrian(self) -> None:
        '''
        SALIDA DEL PUENTE: PEATONES
        
        En primer lugar el número de peatones que ocupan el puente desciende en 
        una unidad. Como esta funcións e ejecuta después de la de entrada, el 
        número de peatones en el puente es mayor que cero por lo que al restarle
        1, el número seguirá siedo mayor o igaul que 1.
        
        Posteriormente se comprueba si hay coches en dirección norte esperando.
        En ese caso, el turno pasa a ser 0 y se comprueba si ya no hay peatones,
        si no hay se avisa a los coches que querían entrar y estaban bloqueados.
        
        Si no hay coches en dirección norte esperando pero hay en dirección sur,
        entonces el turno pasa a 1 y se comprueba que no queden peatones en el 
        puente que bloqueen la entrada de los coches. Si no los hay, se avisa a los
        coches que estaban en espera.
        
        Si no hay no peatones ni coches en dirección sur esperando, el turno 
        es 2
        '''
        
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
        else:
            self.turn.value == 2
                
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
    '''
    Con esta función se generan los peatones
    '''
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
    '''
    Con esta función se generan los coches
    '''
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
