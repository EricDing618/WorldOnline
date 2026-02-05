from __future__ import annotations
from typing import Literal, List, Dict, Any, Optional
import heapq

from src.base import *

class Event(SimCoreBaseObject):
    '''事件基类'''
    def __init__(self, 
                 start_time: str='1970/01/01 00:00:00',
                 building: Building=None
                 ):
        self.start_time = start_time
        self.relative_time = 0
        self.building = building
        self.timeline = Timeline(self.start_time)

    def create_event(self,
                    event_type: Literal['start',
                                        'call_elevator',
                                        'elevator_arrive',
                                        'passenger_board',
                                        'passenger_alight',
                                        'elevator_idle',
                                        'elevator_outweight',
                                        'end',
                                        'invalid']='elevator_idle',
                    elevator: Optional[Elevator]=None,
                    passenger: Optional[Passenger]=None,
                    floor: Optional[Floor]=None,
                    time_host: Optional[Building|Elevator|Passenger|Floor]=None
                    ) -> Dict[str, Any]:
        '''创建并返回单个事件字典'''
        event_data = {
            'event_type': event_type,
            'time': time_host.timeline.current_time if time_host else self.timeline.current_time,
            'building': self.building,
            'elevator': elevator,
            'passenger': passenger,
            'floor': floor,
            'relative_time': Tool.time_difference_seconds(self.start_time, time_host.timeline.current_time) if time_host else 0
        }
        return event_data

class Passenger(SimCoreBaseObject):
    '''乘客'''
    def __init__(self,
                 pid: int,
                 weight: int=70,
                 name: str=None,
                 building: Building=None,
                 appear_time: str='1970/01/01 00:00:00',
                 from_floor: int=1,
                 to_floor: int=10,
                 call_eid: int=0
                 ):
        self.pid = pid
        self.weight = weight
        self.building = building
        self.from_floor = from_floor
        self.to_floor = to_floor
        self.name = name if name else '无名氏'
        self.appear_time = appear_time
        self.timeline = Timeline(self.appear_time)
        self.call_eid = call_eid
        self.on_board = False
        self.is_processed = False  # 标记乘客是否已被处理

        assert Tool.time_difference_seconds(self.building.start_time, self.appear_time) >= 0, "乘客出现时间必须在模拟开始时间之后"
        assert self.call_eid in [i.eid for i in self.building.elevators], f"eid {self.call_eid}不存在"
    
    def __repr__(self):
        return f'Passenger(pid={self.pid}, weight={self.weight}, name={self.name}, from_floor={self.from_floor}, to_floor={self.to_floor})'
    
    def __lt__(self, other):
        """用于堆排序，按出现时间排序"""
        return self.appear_time < other.appear_time

class Floor(SimCoreBaseObject):
    '''楼层，负数表示地下，注意忽略0层'''
    def __init__(self, 
                 fid: int, 
                 height: float=3.0,
                 ):
        self.fid = fid
        self.height = height
        self.timeline = Timeline()
    
    def __repr__(self):
        return f'Floor(fid={self.fid}, height={self.height})'

class Elevator(SimCoreBaseObject):
    '''电梯'''
    def __init__(self, 
                 eid: int=0,
                 name: str='',
                 max_weight: int=1000,
                 building: Building=None,
                 speed: float = 1.0,
                 height: float = 3.0,
                 idle_time: float = 300.0
                 ):
        self.eid = eid
        self.name = name if name else str(eid)
        self.max_weight = max_weight
        self.current_weight = 0
        self.passengers: List[Passenger] = []
        self.building = building
        self.timeline = Timeline(self.building.timeline.current_time)
        self.speed = speed
        self.height = height
        self.current_floor = 1
        self.idle_time = idle_time
        self.last_active_time = self.timeline.current_time
        self.is_idle = True
        self.direction = 1
        self.waiting_passengers: List[Passenger] = []  # 等待服务的乘客
    
    def add_passenger(self, passenger: Passenger) -> bool:
        if self.current_weight + passenger.weight <= self.max_weight:
            self.passengers.append(passenger)
            self.current_weight += passenger.weight
            self.is_idle = False
            passenger.on_board = True
            return True
        return False
    
    def remove_passenger(self, passenger: Passenger) -> bool:
        if passenger in self.passengers:
            if len(self.passengers) == 1:
                self.last_active_time = passenger.timeline.current_time
                self.is_idle = True
            self.passengers.remove(passenger)
            self.current_weight -= passenger.weight
            passenger.on_board = False
            return True
        return False
    
    def add_waiting_passenger(self, passenger: Passenger):
        """添加等待服务的乘客"""
        if passenger not in self.waiting_passengers:
            self.waiting_passengers.append(passenger)
    
    def remove_waiting_passenger(self, passenger: Passenger):
        """移除等待服务的乘客"""
        if passenger in self.waiting_passengers:
            self.waiting_passengers.remove(passenger)
    
    def __repr__(self):
        return f'Elevator(eid={self.eid}, current_floor={self.current_floor}, passengers={len(self.passengers)})'
    
    def __lt__(self, other):
        """用于电梯排序"""
        return self.eid < other.eid

class Building(SimCoreBaseObject):
    '''大楼，控制中心'''
    def __init__(self, 
                 floor_range: tuple[Floor, Floor]=None,
                 elevators: tuple[Elevator]=None,
                 start_time: str='1970/01/01 00:00:00',
                 bid: int=0,
                 name: str='',
                 normal_height: float=3.0
                 ):
        self.start_time = start_time
        self.timeline = Timeline(self.start_time)
        self.t = Tool()
        self.floor_range = {f: Floor(f, normal_height) for f in self.t.myrange(floor_range[0].fid, floor_range[1].fid) if f != 0}
        self.elevators = elevators
        self.passengers: List[Passenger] = []
        self.bid = bid
        self.name = name
        self.eventman = Event(self.start_time, self)
        self.events_list: List[Dict[str, Any]] = []  # 存储所有事件
        self.passenger_queue = []  # 乘客等待队列（最小堆）
        
        assert 0 not in self.floor_range, "楼层范围不能包含0层"
    
    def __repr__(self):
        return f'Building(name={self.name}, floors={len(self.floor_range)}, elevators={len(self.elevators)})'
    
    def add_passenger(self, passenger: Passenger):
        """添加乘客到系统"""
        self.passengers.append(passenger)
        heapq.heappush(self.passenger_queue, (passenger.appear_time, passenger))
    
    def get_parking_floors_optimized(self, total_elevators: int, min_floor: int, max_floor: int) -> List[int]:
        """返回电梯待命楼层列表"""
        if total_elevators == 1:
            return [(min_floor + max_floor) // 2]
        
        parking_floors = []
        parking_floors.append(1)  # 第一部电梯在1楼
        
        if total_elevators == 2:
            valid_floors = [f for f in range(min_floor, max_floor + 1) if f != 0]
            middle_index = len(valid_floors) // 2
            parking_floors.append(valid_floors[middle_index])
        elif total_elevators >= 3:
            parking_floors.append(max_floor)  # 最后一部在最高层
            valid_floors = [f for f in range(min_floor, max_floor + 1) if f != 0]
            for i in range(1, total_elevators - 1):
                position = i / (total_elevators - 1)
                index = round(position * (len(valid_floors) - 1))
                parking_floors.append(valid_floors[index])
        
        return sorted(parking_floors)
    
    def elevator_initpark(self) -> List[Dict[str, Any]]:
        """初始化电梯位置，返回事件列表"""
        events = []
        floor_keys = list(self.floor_range.keys())
        parking_floors = self.get_parking_floors_optimized(
            len(self.elevators), floor_keys[0], floor_keys[-1]
        )
        
        for elevator, current_floor in zip(self.elevators, parking_floors):
            elevator.current_floor = current_floor
            events.append(self.eventman.create_event(
                'elevator_arrive', 
                elevator=elevator, 
                floor=self.floor_range[current_floor],
                time_host=elevator
            ))
            events.append(self.eventman.create_event(
                'elevator_idle',
                elevator=elevator,
                time_host=elevator
            ))
        
        return events
    
    def move_elevator_to_floor(self, elevator: Elevator, target_floor: int, 
                              current_time: str) -> List[Dict[str, Any]]:
        """移动电梯到指定楼层，返回事件列表"""
        events = []
        
        # 计算移动时间
        travel_time = self.t.total_height(
            elevator.current_floor,
            target_floor,
            self.floor_range
        ) / elevator.speed
        
        # 更新电梯时间线
        elevator.timeline.update_from_time(current_time)
        elevator.timeline.update(travel_time)
        
        # 更新电梯位置
        elevator.current_floor = target_floor
        
        # 创建到达事件
        events.append(self.eventman.create_event(
            'elevator_arrive',
            elevator=elevator,
            floor=self.floor_range[target_floor],
            time_host=elevator
        ))
        
        return events
    
    def process_passenger_fcfs(self, passenger: Passenger) -> List[Dict[str, Any]]:
        """按FCFS策略处理单个乘客，返回事件列表"""
        events = []
        
        # 找到指定电梯
        elevator = next((e for e in self.elevators if e.eid == passenger.call_eid), None)
        if not elevator:
            return events
        
        # 更新乘客时间线到出现时间
        passenger.timeline.update_from_time(passenger.appear_time)
        
        # 检查电梯空闲时间
        diff = Tool.time_difference_seconds(elevator.last_active_time, passenger.appear_time)
        if diff >= elevator.idle_time and elevator.is_idle:
            elevator.timeline.update_from_time(passenger.appear_time)
            elevator.timeline.update(elevator.idle_time)
            events.append(self.eventman.create_event(
                'elevator_idle',
                elevator=elevator,
                time_host=elevator
            ))
            elevator.is_idle = False
        
        # 乘客呼叫电梯事件
        events.append(self.eventman.create_event(
            'call_elevator',
            elevator=elevator,
            passenger=passenger,
            floor=self.floor_range[passenger.from_floor],
            time_host=passenger
        ))
        
        # 检查电梯是否超载（预检查）
        if not elevator.add_passenger(passenger):
            # 超重事件
            events.append(self.eventman.create_event(
                'elevator_outweight',
                elevator=elevator,
                passenger=passenger,
                time_host=elevator
            ))
            passenger.is_processed = True
            return events
        
        # 移除预检查增加的重量
        elevator.remove_passenger(passenger)
        
        # 如果电梯不在乘客所在楼层，需要移动
        if elevator.current_floor != passenger.from_floor:
            move_events = self.move_elevator_to_floor(
                elevator, passenger.from_floor, passenger.appear_time
            )
            events.extend(move_events)
        
        # 乘客上电梯
        passenger.timeline.update_from(elevator)
        elevator.add_passenger(passenger)
        events.append(self.eventman.create_event(
            'passenger_board',
            elevator=elevator,
            passenger=passenger,
            floor=self.floor_range[passenger.from_floor],
            time_host=passenger
        ))
        
        # 移动电梯到目标楼层
        move_events = self.move_elevator_to_floor(
            elevator, passenger.to_floor, passenger.timeline.current_time
        )
        events.extend(move_events)
        
        # 乘客下电梯
        events.append(self.eventman.create_event(
            'passenger_alight',
            elevator=elevator,
            passenger=passenger,
            floor=self.floor_range[passenger.to_floor],
            time_host=elevator
        ))
        elevator.remove_passenger(passenger)
        
        passenger.is_processed = True
        return events
    
    def execute(self, method: Literal["FCFS", "SSTF", "LOOK"] = "FCFS") -> List[Dict[str, Any]]:
        """执行电梯调度，返回所有事件列表"""
        self.method = method
        all_events = []
        
        # 开始事件
        all_events.append(self.eventman.create_event('start', time_host=self))
        
        # 电梯初始化待命
        init_events = self.elevator_initpark()
        all_events.extend(init_events)
        
        # 按出现时间排序乘客
        sorted_passengers = sorted(
            self.passengers,
            key=lambda p: Tool.time_difference_seconds(self.start_time, p.appear_time)
        )
        
        # 根据调度方法处理乘客
        if method == "FCFS":
            for passenger in sorted_passengers:
                passenger_events = self.process_passenger_fcfs(passenger)
                all_events.extend(passenger_events)
        
        # 按时间排序所有事件
        all_events.sort(key=lambda e: Tool.time_difference_seconds(
            self.start_time, e['time']
        ))
        
        # 更新相对时间
        for event in all_events:
            event['relative_time'] = Tool.time_difference_seconds(
                self.start_time, event['time']
            )
        
        # 结束事件
        if all_events:
            last_time = all_events[-1]['time']
            self.timeline.update_from_time(last_time)
            all_events.append(self.eventman.create_event('end', time_host=self))
        
        return all_events
    
    def get_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取模拟统计信息"""
        stats = {
            'total_passengers': len(self.passengers),
            'total_events': len(events),
            'processed_passengers': sum(1 for p in self.passengers if p.is_processed),
            'elevator_utilization': {},
            'event_types': {}
        }
        
        # 统计事件类型
        for event in events:
            event_type = event['event_type']
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
        
        # 计算电梯利用率
        for elevator in self.elevators:
            idle_events = stats['event_types'].get('elevator_idle', 0)
            active_events = sum(1 for e in events if e['elevator'] == elevator and 
                              e['event_type'] != 'elevator_idle')
            total_events_for_elevator = idle_events + active_events
            
            if total_events_for_elevator > 0:
                utilization = active_events / total_events_for_elevator
            else:
                utilization = 0.0
            
            stats['elevator_utilization'][elevator.eid] = {
                'utilization': utilization,
                'total_passengers': len(elevator.passengers),
                'current_floor': elevator.current_floor
            }
        
        return stats