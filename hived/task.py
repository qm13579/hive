from datetime import datetime
from multiprocessing import Process
from types import FunctionType

from .config import Config
from .log import logger


class Task:
    """ 
    基础的任务实现  
    """

    def __init__(
            self, name, **kwargs):
        """
        :param name:任务名称
        """
        self.name = name
        self._create_time = datetime.now()
        self.__process: None or Process = None

    def alive(self) -> bool:
        if self.__process is None:
            return False
        else:
            if self.__process.is_alive():
                return True
            else:
                self.__process = None
                return False

    def terminal(self):
        return self.__process.terminate() if self.__process is not None else 0

    def should_run(self, c_time: datetime) -> bool:
        """ 用户应该重写运行逻辑 """
        raise NotImplemented

    def run(self) -> FunctionType:
        raise NotImplemented

    def flush(self, c_time: datetime, config: dict) -> int:
        """ 此方法应该被task的提供者进行重写 """
        raise NotImplemented

    def _run(self, config: Config):
        logger.info(f"task: {self.name} started")
        function = self.run()
        self.__process = Process(target=function, args=(dict(config),), daemon=True)
        self.__process.start()

    def kill(self):
        logger.info(f"task: {self.name} killed")
        return self._kill(self.__process)

    def after_task_kill(self):
        pass

    def before_task_kill(self):
        pass

    def before_task_start(self):
        pass

    def after_task_start(self):
        pass

    @staticmethod
    def _kill(process: Process):
        return process.kill()

    def __repr__(self) -> str:
        return f"{self.name} with {self._create_time}"


class LoopTask(Task):

    def flush(self, c_time: datetime, config: Config) -> int:
        if not self.alive() and self.should_run(c_time=c_time):
            self.before_task_start()
            self._run(config)
            self.after_task_start()
            return 1
        elif self.alive() and not self.should_run(c_time=c_time):
            self.before_task_kill()
            self.kill()
            self.after_task_kill()
            return -1
        return 0


class OnceTask(Task):

    def flush(self, c_time: datetime, config: Config) -> int:
        if not self.alive() and self.should_run(c_time=c_time):
            self.before_task_start()
            self._run(config)
            self.after_task_start()
            return -1
        return 0
