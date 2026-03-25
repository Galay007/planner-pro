from fastapi import Depends, UploadFile, File
from ..repositories.TaskPropertyRepository import TaskPropertyRepository
from ..models.TaskPropertiesModel import TaskProperty
from typing import List
from datetime import datetime
from ..utils.datetime_utils import DateTimeUtils
from .TaskFileService import TaskFileService


class TaskPropertyService:
    taskPropertyRepository: TaskPropertyRepository
    taskFileService: TaskFileService

    def __init__(
        self, taskPropertyRepository: TaskPropertyRepository = Depends()
    ) -> None:
        self.taskPropertyRepository = taskPropertyRepository
        self.taskFileService = TaskFileService(self.taskPropertyRepository.get_db())

    def create(self,
        task_id: int,
        from_dt: datetime,
        until_dt: datetime,
        connection_id: int,
        cron_expression: str | None,
        task_type: str,
        email: str | None,
        tg_chat_id: str | None,
        root_folder: str,
        files: list[UploadFile] = File(...)
        ) -> TaskProperty:


        storage_path, needsToSave = self.taskFileService.check_folder_exists(task_id, task_type, root_folder)

        # from pathlib import Path
        # original_path = str(Path(root_folder).as_posix())

        new_property = TaskProperty(
            task_id=task_id,
            from_dt=from_dt,
            until_dt=until_dt,
            connection_id=connection_id,
            cron_expression=cron_expression,
            task_type=task_type,
            original_path=root_folder,
            storage_path=storage_path,
            email=email,
            tg_chat_id=tg_chat_id,
            change_dt=DateTimeUtils.local_wo_micr()
        )

        self.taskPropertyRepository.create(new_property)

        valid_files = self.taskFileService.files_validation_and_save(needsToSave, task_type, storage_path, files)

        for file in valid_files:
            file_path = f'{storage_path}\{file.filename}'
            self.taskFileService.create(task_id, file.filename, file_path)

        return new_property


    def get_by_id(self,task_id: int) -> TaskProperty | None:
                 
        return self.taskPropertyRepository.get(task_id)
    
    
    def get_all(self) -> List[TaskProperty]:
        return self.taskPropertyRepository.get_all()
    
    def update(self, taskProperty: TaskProperty, files: list[UploadFile], new_root_folder: str, new_task_type: str) -> TaskProperty:

        if files:
            self.taskFileService.delete_files(taskProperty.task_id, taskProperty.task_type)
            root_path, needsToSave = self.taskFileService.check_folder_exists(taskProperty.task_id, new_task_type, new_root_folder)
            valid_files = self.taskFileService.files_validation_and_save(needsToSave, new_task_type, root_path, files)

            for file in valid_files:
                file_path = f'{root_path}\{file.filename}'
                self.taskFileService.update(taskProperty.task_id, file.filename, file_path)
            
            taskProperty.storage_path = root_path

        taskProperty.task_type = new_task_type
        taskProperty.change_dt = DateTimeUtils.local_wo_micr()
        
        return self.taskPropertyRepository.update(taskProperty)
