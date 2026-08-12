import json
from pathlib import Path

class Emotions:
    DEFAULT_STATE={
        "mood":"neutral",
        "happiness":50,
        "trust":50,
        "interest":50,
        "irritation":0,
        "sadness":0,
        "stress":0
    }

    def __init__(self,state_path="lada/state/emotions.json"):
        self.path=Path(state_path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.state={}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.state=json.loads(
                    self.path.read_text(encoding="utf-8")
                )
            except Exception:
                self.state=self.DEFAULT_STATE.copy()
        else:
            self.state=self.DEFAULT_STATE.copy()
            self.save()
        for key,value in self.DEFAULT_STATE.items():
            self.state.setdefault(key,value)

    def save(self):
        self.path.write_text(
            json.dumps(
                self.state,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

    def get(self):
        return dict(self.state)

    def get_value(self,key):
        return self.state.get(key)

    def set(self,key,value):
        self.state[key]=value
        self.save()

    def change(self,key,delta,min_value=0,max_value=100):
        value=self.state.get(key,0)
        if isinstance(value,(int,float)):
            value=max(min_value,min(max_value,value+delta))
            self.state[key]=value
            self.save()

    def set_mood(self,mood):
        self.state["mood"]=mood
        self.save()

    def reset(self):
        self.state=self.DEFAULT_STATE.copy()
        self.save()

    def context(self):
        return(
            f"Настроение: {self.state['mood']}\n"
            f"Счастье: {self.state['happiness']}\n"
            f"Доверие: {self.state['trust']}\n"
            f"Интерес: {self.state['interest']}\n"
            f"Раздражение: {self.state['irritation']}\n"
            f"Грусть: {self.state['sadness']}\n"
            f"Стресс: {self.state['stress']}"
        )