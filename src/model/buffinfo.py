class BuffInfo:
    def __init__(self, unit_id, buff_type, duration, num):
        self.unit_id = unit_id
        self.buff_type = buff_type
        self.duration = duration
        self.num = num

    @staticmethod
    def if_unit_buff(state_info, unit_id, buff_id):
        for buff_info in state_info.buff_infos:
            if buff_info.unit_id == unit_id and buff_info.buff_type == buff_id:
                return buff_info

        return None
