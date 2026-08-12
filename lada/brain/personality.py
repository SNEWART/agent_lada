from pathlib import Path

class Personality:
    FILES=[
        "core.md",
        "self.md",
        "persona.md",
        "psychology.md",
        "speech.md",
        "worldview.md",
        "biography.md"
    ]

    def __init__(self,identity_path="lada/identity"):
        self.identity_path=Path(identity_path)
        self.sections={}
        self.prompt=""
        self.reload()

    def reload(self):
        self.sections.clear()
        for filename in self.FILES:
            path=self.identity_path/filename
            if path.exists():
                self.sections[filename]=path.read_text(
                    encoding="utf-8"
                ).strip()
            else:
                self.sections[filename]=""
        self.prompt=self._build_prompt()

    def _build_prompt(self):
        parts=[]
        for filename in self.FILES:
            text=self.sections.get(filename,"").strip()
            if not text:
                continue
            title=filename.replace(".md","").upper()
            parts.append(
                f"===== {title} =====\n{text}"
            )
        return "\n\n".join(parts)

    def get_prompt(self):
        return self.prompt

    def get_section(self,name):
        return self.sections.get(name,"")

    def summary(self):
        return{
            "files":len(self.sections),
            "loaded":[
                name
                for name,text in self.sections.items()
                if text
            ]
        }

    def __str__(self):
        return self.prompt