from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid

def now():
    return datetime.utcnow().isoformat(timespec="seconds")

@dataclass
class Fact:
    text:str
    category:str="general"
    importance:int=5
    id:str=field(default_factory=lambda:str(uuid.uuid4()))
    created:str=field(default_factory=now)
    updated:str=field(default_factory=now)
    last_used:str=field(default_factory=now)
    used:int=0
    embedding:Optional[list]=field(default=None,repr=False)
    metadata:dict=field(default_factory=dict)
    def touch(self):
        self.used+=1
        self.last_used=now()
        self.updated=self.last_used
    def update_text(self,text:str):
        self.text=text.strip()
        self.updated=now()
    def to_dict(self):
        return asdict(self)
    @classmethod
    def from_dict(cls,data):
        allowed={
            "id",
            "text",
            "category",
            "importance",
            "created",
            "updated",
            "last_used",
            "used",
            "embedding",
            "metadata",
        }
        return cls(
            **{k:v for k,v in data.items() if k in allowed}
        )
    def __post_init__(self):
        self.text=self.text.strip()
        if not self.category:
            self.category="general"
        self.importance=max(1,min(10,int(self.importance)))
        if self.metadata is None:
            self.metadata={}