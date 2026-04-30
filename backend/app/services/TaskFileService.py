from fastapi import Depends, UploadFile, File, HTTPException, status
from ..repositories.TaskFileRepository import TaskFileRepository
from ..models.TaskFileModel import TaskFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..utils.DatetimeUtils import DateTimeUtils
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
            change_dt=DateTimeUtils.local_wo_microsec()
        )

        self.taskFileRepository.create(new_task_file)

    def get_by_uid(self,task_uid: int) -> Optional[TaskFile]:           
        return self.taskFileRepository.get_by_uid(task_uid)
    
    def get_by_id(self, task_id: int) -> List[TaskFile]:
        return self.taskFileRepository.get_by_id(task_id)
    
    def get_all(self) -> List[TaskFile]:
        return self.taskFileRepository.get_all()

    def update(self, task_id: int,
        file_name: str,
        file_path: str
        ) -> TaskFile:

        upd_task_file = TaskFile(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            change_dt=DateTimeUtils.local_wo_microsec()
        )

        return self.taskFileRepository.update(upd_task_file)
    
    def check_folder_exists(self, task_id: int, task_type: str, root_folder: str):
        needsToSave = False
        if not Path(root_folder).exists():
            needsToSave = True
            root_folder = Path(f'{settings.uploads_dir}/{task_id}/{task_type.upper()}')
        
        # return str(Path(root_folder).as_posix()), needsToSave
        return str(root_folder), needsToSave

    def files_validation_and_save(self, needsToSave, task_type: str, root_folder: str, files: list[UploadFile] = File(...)):

        valid_files = [
            file
            for file in files
            if file.filename and file.filename.lower().endswith(f".{task_type.lower()}")
        ]

        if valid_files is None or len(valid_files) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"No files with {task_type} extension") 

        root_path = Path(root_folder)

        if needsToSave:
            self.save_files_on_server(root_path, valid_files)
        else:
            for file in valid_files:
                 if not (Path(root_folder) / file.filename).exists():
                     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Can't find files in existing folder") 

        return valid_files

    def save_files_on_server(self, server_path, valid_files):
        if server_path.exists():
            shutil.rmtree(server_path)
        server_path.mkdir(parents=True, exist_ok=True)
        
        for file in valid_files:
            file_path = server_path / file.filename
            try:
                with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
            except Exception:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"File {file.filename} was not saved") 

    def delete_files(self, task_id: int):
        self.taskFileRepository.delete_by_id(task_id)
        
        server_folder = Path(f'{settings.uploads_dir}/{task_id}')

        if server_folder.exists():
            shutil.rmtree(server_folder)
    






