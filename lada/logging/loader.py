from pathlib import Path

class LoggingLoader:

    FILES=[
        "memory.md",
        "chat.md",
        "brain.md",
        "system.md"
    ]

    def __init__(self,logging_path="lada/logging"):
        self.logging_path=Path(logging_path)
        self.sections={}
        self.prompt=""
        self.reload()

    def reload(self):
        self.sections.clear()

        for filename in self.FILES:

            path=self.logging_path/filename

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

            text=self.sections.get(
                filename,
                ""
            ).strip()

            if not text:
                continue

            title=filename.replace(
                ".md",
                ""
            ).upper()

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
    def get(self,name):
        if not name.endswith(".md"):
            name=name+".md"
        return self.sections.get(name,"")
    def __str__(self):
        return self.prompt