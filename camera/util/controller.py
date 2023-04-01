from typing import Dict
import multiprocessing as mtp


def create_worker_process(process_name, execute_fn, params=None):
    controller = PController.get_instance()
    while controller.get_status(process_name=process_name):
        pass
    controller.kill_process(process_name=process_name, force=True)
    controller.add_process(process_name=process_name,
                           execute_fn=execute_fn,
                           params=params)
    print("Create worker process: {}".format(process_name))
    return


class PController(object):
    __instance = None

    @staticmethod
    def get_instance():
        if not PController.__instance:
            PController()
        return PController.__instance

    def __init__(self):
        if PController.__instance:
            raise Exception("NOT ALLOW TO INITIALIZE")
        else:
            self.processes: Dict[str, mtp.Process] = {}
            PController.__instance = self

    def add_process(self, process_name: str, execute_fn, params=None):
        if process_name in self.processes:
            raise Exception("Process is Duplicated")
        if params:
            self.processes[process_name] = mtp.Process(target=execute_fn, args=params, name=process_name)
        else:
            self.processes[process_name] = mtp.Process(target=execute_fn, name=process_name)
        self.processes[process_name].start()

    def update_process(self, process_name: str, execute_fn, params=None):
        self.kill_process(process_name)
        self.add_process(process_name, execute_fn, params)

    def kill_process(self, process_name: str, force=False):
        if process_name not in self.processes:
            if not force:
                raise Exception("Process is not existed")
            return
        self.processes[process_name].terminate()
        self.processes.pop(process_name)

    def get_status(self, process_name):
        if process_name not in self.processes:
            return False
        return self.processes[process_name].is_alive()

    def get_process_id(self, process_name):
        if process_name not in self.processes:
            return -1
        return self.processes[process_name].pid
