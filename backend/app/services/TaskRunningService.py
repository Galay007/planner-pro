from ..repositories.TaskRunningRepository import TaskRunningRepository
from ..models.TaskRunningModel import TaskRunning, RunningStatusEnum, TriggerModeEnum
from ..models.TaskModel import Task, InRunningEnum, TaskStatusEnum
from datetime import datetime
from ..utils.DatetimeUtils import DateTimeUtils
from ..repositories.TaskRepository import TaskRepository
from cronsim import CronSim
import logging
from pathlib import Path
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TaskRunningService:
    taskRunningRepository: TaskRunningRepository
    taskRepository: TaskRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskRunningRepository = TaskRunningRepository(db)
        self.taskRepository = TaskRepository(db)

    def create_task_run(self, taskRunning: TaskRunning):
        self.taskRunningRepository.create(taskRunning)

    def update_in_running_status(self, task: Task, new_status: InRunningEnum):
        if task.task_deps_id is None:
            task.in_running = new_status.value
            task.change_dt = DateTimeUtils.local_with_micr()
        self.taskRepository.update_task(task)

    def update_task_status_off(self, task: Task, new_status: TaskStatusEnum):
        task.status = new_status.value
        task.on_control = "off"
        task.change_dt = DateTimeUtils.local_with_micr()
        self.taskRepository.update_task(task)

    def has_parent(self, task_deps_id: int) -> bool:
        task = self.taskRepository.get_task_by_task_id_short(task_deps_id)
        return True if task else False

    def validate_cheduled_tasks_for_adding(self, current_dt: datetime) -> list[Task]:
        tasks = self.taskRepository.get_all_tasks()
        validated_tasks_for_adding = []

        for task in tasks:
            if task.status == TaskStatusEnum.RUNNING:
                logger.debug(f'Task id {task.task_id} is now running')
                continue

            if task.task_props is None:
                if task.on_control == 'on': 
                    logger.warning(f'Task id {task.task_id} has no properties to be "ON"')
                    self.update_task_status_off(task, TaskStatusEnum.NOT_ACTIVE)
                continue

            valid_dates = True if task.task_props.from_dt <= current_dt and task.task_props.until_dt >= current_dt else False
            valid_cron = self.is_cron_valid(task.task_props.cron_expression, task.task_id)
            valid_is_added = True if task.in_running == InRunningEnum.ADDED  else False
            valid_to_clean = True if task.in_running == InRunningEnum.TO_CLEAN  else False
            valid_storage_path = self.is_path_valid(task.task_props.storage_path, task.task_id)
            valid_in_future = True if task.task_props.until_dt >= current_dt else False
            valid_connection = True if task.task_props.connection_id is not None else False

            if task.on_control == "on" and task.task_deps_id is None:
                if  valid_dates and valid_cron and not valid_to_clean and not valid_is_added and valid_connection and valid_storage_path \
                    or (valid_is_added and
                                 task.added_running_dt and task.added_running_dt.date() < current_dt.date()):
           
                    validated_tasks_for_adding.append(task) 
                        

                elif valid_in_future and valid_cron and not valid_is_added  and valid_storage_path and valid_connection:
                    pass # не добавляем, но оставляем вкл и ждем, т.к. время еще не наступило

                elif not valid_dates or not valid_cron or valid_to_clean or not valid_storage_path or not valid_connection:

                    logger.warning(f'Task id {task.task_id} can not be "ON" due to invalid params for running')
                    task.added_running_dt = None
                    self.update_task_status_off(task, TaskStatusEnum.NOT_ACTIVE)
                    self.update_in_running_status(task, InRunningEnum.TO_CLEAN)
                    

            if task.on_control == "on" and task.task_deps_id is not None:

                valid_parent = True if self.has_parent(task.task_deps_id) else False

                if not valid_parent or not valid_in_future or valid_cron or not valid_storage_path or not valid_connection: # если valid_cron == True, то это ошибка для depended task
                    logger.warning(f'Depended task id {task.task_id} can not be "ON" due to invalid params')
                    task.added_running_dt = None
                    self.update_task_status_off(task, TaskStatusEnum.NOT_ACTIVE)
                    
        
        return validated_tasks_for_adding

    def clean_scheduled_tasks(self, current_dt: datetime) -> None:
        tasks = self.taskRepository.get_all_tasks()

        for task in tasks:
            valid_is_cleared = True if task.in_running == InRunningEnum.CLEARED  else False
            valid_is_not_active = True if task.status == TaskStatusEnum.NOT_ACTIVE  else False

            if task.on_control == "off" and task.task_deps_id is None and (not valid_is_cleared or not valid_is_not_active):
                self.taskRunningRepository.delete_by_task_id(task.task_id, current_dt)
                task.added_running_dt = None
                self.update_task_status_off(task, TaskStatusEnum.NOT_ACTIVE)
                self.update_in_running_status(task, InRunningEnum.CLEARED)
                logger.info(f'Unrunnings of task id {task.task_id} were cleaned for {current_dt.date()} due to turn off')


    def refresh_runnings(self):
        current_dt = datetime.now()

        self.clean_scheduled_tasks(current_dt)
        valid_tasks_list = self.validate_cheduled_tasks_for_adding(current_dt)

        if len(valid_tasks_list) == 0:
            return


        for task in valid_tasks_list:
            isRunningsSaved = False

            base_fields  = dict(
                task_uid = task.task_uid,
                task_id = task.task_id,
                parent_id = task.task_deps_id,
                trigger_mode = TriggerModeEnum.SCHEDULED.value,
                notifications = task.notifications,
                email = task.task_props.email,
                tg_chat_id = task.task_props.tg_chat_id,
                storage_path = task.task_props.storage_path,
                created_dt = DateTimeUtils.local_wo_microsec(),
                status = RunningStatusEnum.PENDING.value
            )

            cron_expr = task.task_props.cron_expression

            today_executions = self.get_today_executions(cron_expr, current_dt)
            
            if len(today_executions) > 0:
                
                for row_execute in today_executions:
                    new_run = TaskRunning(**base_fields)
                    new_run.schedule_dt = row_execute
                    self.create_task_run(new_run)
                
                isRunningsSaved = True
            
            if isRunningsSaved:
                task.added_running_dt = current_dt
                task.status = TaskStatusEnum.ACTIVE.value
                self.update_in_running_status(task, InRunningEnum.ADDED)
                logger.info(f'Task id {task.task_id} was added for runnings')
                
    
    def is_cron_valid(self, expr: str, task_id: int) -> bool:
        try:
            CronSim(expr, datetime.now())
            return True
        except Exception as e:
            logger.error(f'Task id {task_id} has invalid cron expression {expr}')
            return False

    
    def is_path_valid(self, path: str, task_id: int) -> bool:     
        try:
            path_folder = Path(path)
            if path_folder.exists():
                return True
            else:
                return False
        except Exception:
            logger.error(f'Task id {task_id} has invalid path storage {path}')
            return False

    def get_today_executions(self, cron_expr: str, today_dt: datetime) -> list[datetime]:
        cs = CronSim(cron_expr, today_dt)

        today_executions = []
        for _ in range(1440):  # 1440 минут — 24 часа
            dt = next(cs)

            if dt.date() == today_dt.date():
                today_executions.append(dt)

        return today_executions

    


