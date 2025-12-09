class Robot:
    '''
    Docstring for Robot
    Робот это база для всех остальных агентов
    '''
    def __init__(self, motor_power, id):
        self.charge = self.get_charge()
        self.motor_power = motor_power
        self.flag_is_move = False
        self.id = id

    def get_charge(self):
        pass

    def move(self):
        pass

    def check_is_wall(self):
        pass

    def get_command(self):
        # command = BigBoss().get_command(id)

        # if command == "move":
        #     self.move()
        
        # elif command == "stop":
        #     self.move()
        
        # return command
        pass
    
    def check_is_wall(self):
        pass

    def check_charged(self):
        pass


class Loader(Robot):
    def __init__(self, motor_power, id, bucket_is_up=False, workload=False):
        super().__init__(motor_power, id)
        self.bucket_is_up = bucket_is_up
        self.workload = workload

    def control_bucket(self):
        pass

    # def get_command(self):
    #     command = super().get_command()

    #     if command == "Поднять ковш":
    #         self.control_bucket()

class Samosval(Robot):
    def __init__(self, motor_power, id, truck_is_up=False, workload=False):
        super().__init__(motor_power, id)
        self.truck_is_up = truck_is_up
        self.workload = workload
    
    def load_truck(self):
        pass

    def control_truck(self):
        pass

class Buldozer(Robot):
    def __init__(self, motor_power, id, blade_is_up=True):
        super().__init__(motor_power, id)
        self.blade_is_up = blade_is_up
    
    def control_blade(self):
        pass