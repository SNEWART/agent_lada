from datetime import datetime

class Consciousness:
    def __init__(
        self,
        personality,
        memory=None,
        emotions=None,
        relationships=None
    ):
        self.personality=personality
        self.memory=memory
        self.emotions=emotions
        self.relationships=relationships
    def build(
        self,
        user_id,
        user_message,
        history=None,
        rag_context=None
    ):
        history=history or []
        rag_context=rag_context or []
        personality=self.personality.get_prompt()
        memory=""
        if self.memory:
            try:
                memory=self.memory.get_context(user_message)
            except Exception:
                memory=""
        emotions={}
        if self.emotions:
            emotions=self.emotions.get()
        relationships={}
        if self.relationships:
            relationships=self.relationships.get(user_id)
        formatted_history=[]
        for message in history:
            role=message.get("role")
            content=message.get(
                "content",
                message.get("text","")
            )
            if role and content:
                formatted_history.append({
                    "role":role,
                    "content":content
                })
        return{
            "time":datetime.now().isoformat(timespec="seconds"),
            "user_id":user_id,
            "personality":personality,
            "memory":memory,
            "rag":rag_context,
            "emotions":emotions,
            "relationships":relationships,
            "history":formatted_history,
            "message":user_message
        }

    def summary(self,state):
        return{
            "history":len(state.get("history",[])),
            "memory":bool(state.get("memory")),
            "documents":len(state.get("rag",[])),
            "emotions":len(state.get("emotions",{})),
            "relationships":len(state.get("relationships",{}))
        }