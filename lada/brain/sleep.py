import json
from pathlib import Path
from datetime import datetime

class Sleep:
    def __init__(
        self,
        emotions=None,
        relationships=None,
        logs_path="lada/logs"
    ):
        self.emotions=emotions
        self.relationships=relationships
        self.logs_path=Path(logs_path)
        self.logs_path.mkdir(parents=True,exist_ok=True)
        self.log_file=self.logs_path/"sleep.log"

    def cycle(self):
        if self.emotions:
            self._normalize_emotions()

        if self.relationships:
            self._normalize_relationships()

        self._write_log("Sleep cycle completed.")

    def _normalize_emotions(self):
        state=self.emotions.get()

        for key in [
            "happiness",
            "trust",
            "interest"
        ]:
            value=state.get(key,50)

            if value>50:
                self.emotions.change(key,-1)

            elif value<50:
                self.emotions.change(key,1)

        for key in [
            "irritation",
            "sadness",
            "stress"
        ]:
            value=state.get(key,0)

            if value>0:
                self.emotions.change(key,-1)

    def _normalize_relationships(self):
        data=self.relationships.data

        for user_id in data:
            relation=data[user_id]

            for key in relation:
                value=relation[key]

                if key=="attachment":
                    continue

                if value>50:
                    relation[key]=max(50,value-1)

                elif value<50:
                    relation[key]=min(50,value+1)

        self.relationships.save()

    def _write_log(self,text):
        with open(
            self.log_file,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(
                f"[{datetime.now().isoformat(timespec='seconds')}] {text}\n"
            )