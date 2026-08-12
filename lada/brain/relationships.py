import json
from pathlib import Path

class Relationships:
    DEFAULT_RELATION={
        "trust":50,
        "respect":50,
        "sympathy":50,
        "attachment":0,
        "interest":50,
        "irritation":0
    }

    def __init__(self,state_path="lada/state/relationships.json"):
        self.path=Path(state_path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.data={}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data=json.loads(
                    self.path.read_text(encoding="utf-8")
                )
            except Exception:
                self.data={}
        else:
            self.data={}
            self.save()

    def save(self):
        self.path.write_text(
            json.dumps(
                self.data,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

    def exists(self,user_id):
        return user_id in self.data

    def create(self,user_id):
        if user_id not in self.data:
            self.data[user_id]=self.DEFAULT_RELATION.copy()
            self.save()
        return self.data[user_id]

    def get(self,user_id):
        if user_id not in self.data:
            return self.create(user_id)
        return self.data[user_id]

    def set(self,user_id,key,value):
        relation=self.get(user_id)
        relation[key]=value
        self.save()

    def change(self,user_id,key,delta,min_value=0,max_value=100):
        relation=self.get(user_id)
        value=relation.get(key,0)
        if isinstance(value,(int,float)):
            value=max(min_value,min(max_value,value+delta))
            relation[key]=value
            self.save()

    def reset(self,user_id):
        self.data[user_id]=self.DEFAULT_RELATION.copy()
        self.save()

    def remove(self,user_id):
        if user_id in self.data:
            del self.data[user_id]
            self.save()

    def context(self,user_id):
        relation=self.get(user_id)
        return(
            f"Доверие: {relation['trust']}\n"
            f"Уважение: {relation['respect']}\n"
            f"Симпатия: {relation['sympathy']}\n"
            f"Привязанность: {relation['attachment']}\n"
            f"Интерес: {relation['interest']}\n"
            f"Раздражение: {relation['irritation']}"
        )