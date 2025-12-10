from Supervisor import Supervisor

class BigBoss():
    def __init__(self):
        self.supervisor = Supervisor()

    def get_field_size(self):
        self.field_size = self.supervisor.get_field_size()

    def get_robot_data(self):
        self.robot_data = self.supervisor.get_robot_data()
    
    def get_breakstone_mask(self):
        self.breakstone_mask = self.supervisor.get_breakstone_mask()

    def get_command(self):
        pass

    def send_command(self):
        pass

    def get_agent_positions(self):
        pass

    def create_logic(self):
        pass