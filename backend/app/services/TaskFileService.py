from fastapi import Depends, UploadFile, File, HTTPException, status
from ..repositories.TaskFileRepository import TaskFileRepository
from ..models.TaskFileModel import TaskFile
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..utils.datetime_utils import DateTimeUtils
import shutil
from pathlib import Path
from ..configs.Config import settings

class TaskFileService:
    taskFileRepository: TaskFileRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskFileRepository = TaskFileRepository(db)       

    def create(self,
        task_id: int,
        file_name: str,
        file_path: str
        ) -> TaskFile:
        
        new_task_file = TaskFile(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            change_dt=DateTimeUtils.local_wo_micr()
        )

        self.taskFileRepository.create(new_task_file)

    def get_by_uid(self,task_uid: int) -> TaskFile | None:           
        return self.taskFileRepository.get_by_uid(task_uid)
    
    def get_by_id(self,id: int) -> TaskFile | None:
        return self.taskFileRepository.get_by_id(id)
    
    def get_all(self) -> List[TaskFile]:
        return self.taskFileRepository.get_all()

    def update(self, taskFile: TaskFile) -> TaskFile:

        return self.taskFileRepository.update(taskFile)
    
    def check_folder_exists(self, task_id: int, task_type: str, root_folder: str):
        needsToSave = False
        if not Path(root_folder).exists():
            needsToSave = True
            root_folder = Path(f'{settings.uploads_dir}/{task_id}/{task_type.upper()}')
        
        return str(Path(root_folder).as_posix()), needsToSave

    def files_validation(self, needsToSave, task_type: str, root_folder: str, files: list[UploadFile] = File(...)):

        valid_files = [
            file
            for file in files
            if file.filename and file.filename.lower().endswith(f".{task_type.lower()}")
        ]

        if valid_files is None or len(valid_files)==0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"No files with {task_type} extension") 

        root_path = Path(root_folder)

        if needsToSave:
            if root_path.exists():
                    shutil.rmtree(root_path)
            root_path.mkdir(parents=True, exist_ok=True)
        
        for file in valid_files:
            file_path = root_path / file.filename
            try:
                with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
            except Exception:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"File {file.filename} was not saved") 

        return valid_files

    
    def update_deleted_date(self,task_uid: int, delete_dt: datetime) -> None:
        taskFile = self.get_by_uid(task_uid)
        taskFile.deleted_dt = delete_dt
        taskFile.change_dt = delete_dt
        self.taskFileRepository.update(taskFile)
    
    def update_last_change_date(self,task_uid:int,change_dt: datetime):
        taskFile = self.get_by_uid(task_uid)
        taskFile.change_dt=change_dt
        self.taskFileRepository.update(taskFile)





