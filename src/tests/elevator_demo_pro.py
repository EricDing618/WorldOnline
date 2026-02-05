import random

def demo():
    heap = []
    counter = itertools.count()
    r = random.Random(time.time())
    start_time = f'{r.randint(2000,2025)}/0{r.randint(1,9)}/0{r.randint(1,9)}'
    fa, fb = r.randint(-5,-1), r.randint(27,101)
    # 创建大楼
    building = Building(
        floor_range=(Floor(fa),Floor(fb)),
        start_time=start_time+' 08:00:00',
        name='random_test_building',
        normal_height=r.randint(3,5)
    )

    # 楼层高度特例
    special_floors = [
        Floor(1,r.randint(3,6))
    ]
    for f in special_floors:
        building.floor_range[f.fid] = f

    # 创建电梯
    elevator1 = Elevator(eid=0, max_weight=r.randint(800,2000), building=building, name='左', speed=r.randint(1,3))
    elevator2 = Elevator(eid=1, max_weight=r.randint(1000,2500), building=building, name='右',speed=r.randint(1,3))

    # 添加电梯到大楼
    building.elevators = (elevator1, elevator2)

    # 创建乘客
    passenger1 = Passenger(pid=1, weight=r.randint(45,140), building=building, from_floor=1, to_floor=r.randint(fb//2, fb), name='Peter', appear_time=start_time+f' 0{r.randint(8,9)}:{r.randint(10,59)}:{r.randint(10,59)}', call_eid=r.randint(0,1))
    passenger2 = Passenger(pid=2, weight=r.randint(50,100), building=building, from_floor=r.randint(fa, -1), to_floor=r.randint(1, fb), name='Dick', appear_time=start_time+f' {r.randint(10,23)}:0{r.randint(0,9)}:{r.randint(10,59)}', call_eid=r.randint(0,1))
    passenger3 = Passenger(pid=3, weight=r.randint(0,7000), building=building, from_floor=r.randint(fa, -1), to_floor=r.randint(1, fb), name='NotDick', appear_time=start_time+f' {r.randint(10,23)}:0{r.randint(0,9)}:{r.randint(10,59)}', call_eid=r.randint(0,1)) # 恐怖片（确信

    # 添加乘客到大楼
    building.passengers = [passenger1, passenger2, passenger3]
    #building.passengers = [passenger1, passenger2]

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