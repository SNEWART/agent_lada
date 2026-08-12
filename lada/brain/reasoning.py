class Reasoning:
    def __init__(
        self,
        model,
        temperature=0.85,
        top_p=0.95,
        max_tokens=2000,
        frequency_penalty=0.15,
        presence_penalty=0.10
    ):
        self.model=model
        self.temperature=temperature
        self.top_p=top_p
        self.max_tokens=max_tokens
        self.frequency_penalty=frequency_penalty
        self.presence_penalty=presence_penalty

    def build_messages(self,state):
        messages=[
            {
                "role":"system",
                "content":state["personality"]
            }
        ]

        history=state.get("history",[])
        if history:
            messages.extend(history)

        context=[]

        if state.get("memory"):
            context.append(
                "[MEMORY]\n"+state["memory"]
            )

        rag=state.get("rag",[])
        if rag:
            context.append(
                "[KNOWLEDGE]\n"+"\n\n".join(rag)
            )

        emotions=state.get("emotions",{})
        if emotions:
            text="\n".join(
                f"{k}: {v}"
                for k,v in emotions.items()
            )
            context.append(
                "[EMOTIONS]\n"+text
            )

        relationships=state.get("relationships",{})
        if relationships:
            text="\n".join(
                f"{k}: {v}"
                for k,v in relationships.items()
            )
            context.append(
                "[RELATIONSHIP]\n"+text
            )

        user_message=state["message"]

        if context:
            user_message=(
                "\n\n".join(context)+
                "\n\n[USER]\n"+
                user_message
            )

        messages.append(
            {
                "role":"user",
                "content":user_message
            }
        )

        return messages

    def build_payload(self,state):
        return{
            "model":self.model,
            "messages":self.build_messages(state),
            "temperature":self.temperature,
            "top_p":self.top_p,
            "max_tokens":self.max_tokens,
            "frequency_penalty":self.frequency_penalty,
            "presence_penalty":self.presence_penalty
        }