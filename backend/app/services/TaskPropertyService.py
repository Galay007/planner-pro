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


        root_path, needsToSave = self.taskFileService.check_folder_exists(task_id, task_type, root_folder)

        new_property = TaskProperty(
            task_id=task_id,
            from_dt=from_dt,
            until_dt=until_dt,
            connection_id=connection_id,
            cron_expression=cron_expression,
            task_type=task_type,
            storage_path=root_path,
            email=email,
            tg_chat_id=tg_chat_id,
            change_dt=DateTimeUtils.local_wo_micr()
        )

        self.taskPropertyRepository.create(new_property)

        valid_files = self.taskFileService.files_validation(needsToSave, task_type, root_path, files)

        for file in valid_files:
            file_path = f'{root_path}/{file.filename}'
            self.taskFileService.create(task_id, file.filename, file_path)

        return new_property


    def get_by_name(self,name: str) -> TaskProperty | None:
                 
        return self.connectionRepository.get(name)
    
    def delete(self,connection: TaskProperty) -> None:
        return self.connectionRepository.delete(connection)
    
    def get_all(self) -> List[TaskProperty]:
        return self.connectionRepository.get_all()
