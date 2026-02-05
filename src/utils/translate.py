try:
    from src.core import Building,Elevator,Passenger,Floor,Tool
except:
    from ..Building.Elevator.core import Building,Elevator,Passenger,Floor,Tool

class ElevatorTranslate:
    def __init__(self, event:dict[str, str|int|Building|Elevator|Passenger|Floor]):
        event_type_:str = event['event_type']
        time_:str = event['time']
        building_:Building = event['building']
        elevator_:Elevator = event['elevator']
        passenger_:Passenger = event['passenger']
        floor_:Floor = event['floor']
        '''if elevator_:
            print(elevator_.is_idle)'''
        match event_type_:
            case 'start':
                print(f"[{time_}] {building_.name}(bid: {building_.bid})模拟开始，楼层范围：{list(building_.floor_range.keys())[0]} ~ {list(building_.floor_range.keys())[-1]}（没有0层）")
            case 'elevator_idle':
                print(f"[{time_}] 电梯 {elevator_.name}(eid: {elevator_.eid}) 空闲")
            case 'elevator_arrive':
                print(f"[{time_}] 电梯 {elevator_.name}(eid: {elevator_.eid}) 到达 {floor_.fid} 层（平均速度：{elevator_.speed} m/s）")
            case 'call_elevator':
                print(f"[{time_}] 乘客 {passenger_.name}(pid: {passenger_.pid}) 在楼层 {floor_.fid} 呼叫电梯 {elevator_.name}(eid: {elevator_.eid})（计划），目标楼层 {passenger_.to_floor}，质量 {passenger_.weight}kg")
            case 'passenger_board':
                print(f"[{time_}] 乘客 {passenger_.name}(pid: {passenger_.pid}) 上电梯 {elevator_.name}(eid: {elevator_.eid})")
            case 'passenger_alight':
                print(f"[{time_}] 乘客 {passenger_.name}(pid: {passenger_.pid}) 下电梯 {elevator_.name}(eid: {elevator_.eid})，到达楼层 {passenger_.to_floor}")
            case 'elevator_outweight':
                print(f"[{time_}] 电梯 {elevator_.name}(eid: {elevator_.eid}) 超载！最大载重 {elevator_.max_weight}kg，乘客{passenger_.name}(pid: {passenger_.pid})无法上电梯")
            case 'end':
                print(f"[{time_}] {building_.name}(bid: {building_.bid})模拟结束，共计运行 {Tool.time_difference_seconds(building_.start_time, time_)} 秒")
            case 'invalid':
                print(f"[{time_}] 无效事件，信息：{event}")
            case _:
                print(f"[{time_}] 未知事件类型: {event_type_}")