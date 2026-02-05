from typing import Generator

import pprint

def demo():
    heap = []
    counter = itertools.count()
    # 创建大楼
    building = Building(
        floor_range=(Floor(-4),Floor(101)),
        start_time='2023/01/01 08:00:00',
        name='柳京饭店'
    )

    # 楼层高度特例
    special_floors = [
        Floor(1,5)
    ]
    for f in special_floors:
        building.floor_range[f.fid] = f

    # 创建电梯
    elevator1 = Elevator(eid=0, max_weight=1000, building=building, name='左', speed=2.5)
    elevator2 = Elevator(eid=1, max_weight=1000, building=building, name='右',speed=2.5)

    # 添加电梯到大楼
    building.elevators = (elevator1, elevator2)

    # 创建乘客
    passenger1 = Passenger(pid=1, weight=70, building=building, from_floor=1, to_floor=5, name='Peter', appear_time='2023/01/01 08:00:10', call_eid=0)
    passenger2 = Passenger(pid=2, weight=80, building=building, from_floor=2, to_floor=6, name='Dick', appear_time='2023/01/01 08:05:20', call_eid=0)

    # 添加乘客到大楼
    building.passengers = [passenger1, passenger2]

    execute = building.execute('FCFS')
    #pprint.pprint(list(execute),indent=4,depth=4)
    for event in execute:
        heapq.heappush(heap,(event['relative_time'], next(counter), event))

    while heap:
        _time, _count, event = heapq.heappop(heap)
        Translate(event)
        

if __name__ == "__main__":
    from core import *
    from translate import *
    demo()
else:
    from .core import *
    from .translate import *