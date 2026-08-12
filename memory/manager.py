from typing import Optional
from .storage import MemoryStorage
from .models import Fact
from difflib import SequenceMatcher

class MemoryManager:
    def __init__(self,user_id:str,embedding_function=None):
        self.storage=MemoryStorage(user_id)
        self.embedding_function=embedding_function
    SINGLE_VALUE_CATEGORIES={
        "profile",
        "name",
        "age",
        "gender",
        "city",
        "country",
        "location",
        "profession",
        "work"
    }
    def _find_similar_fact(self,text:str,threshold:float=0.88):
        text=text.lower().strip()
        best_fact=None
        best_score=0.0
        for fact in self.all_facts():
            score=SequenceMatcher(
                None,
                text,
                fact["text"].lower()
            ).ratio()
            if score>best_score:
                best_score=score
                best_fact=fact
        if best_score>=threshold:
            return best_fact
        return None
    def remember(
        self,
        text:str,
        category:str="general",
        importance:int=5,
        metadata=None
    ):
        text=text.strip()
        if not text:
            return None
        similar=self._find_similar_fact(text)
        if similar:
            return similar
        if category in self.SINGLE_VALUE_CATEGORIES:
            rows=self.storage.get_by_category(category)
            if rows:
                row=rows[0]
                fact=Fact.from_dict({
                    "id":row[0],
                    "text":row[1],
                    "category":row[2],
                    "importance":row[3],
                    "created":row[4],
                    "updated":row[5],
                    "last_used":row[6],
                    "used":row[7],
                    "embedding":None,
                    "metadata":{}
                })
                fact.text=text
                fact.importance=importance
                if self.embedding_function:
                    try:
                        fact.embedding=self.embedding_function(text)
                    except Exception:
                        pass
                self.storage.update_fact(fact)
                return fact
        fact=Fact(
            text=text,
            category=category,
            importance=importance,
            metadata=metadata or {}
        )
        if self.embedding_function:
            try:
                fact.embedding=self.embedding_function(text)
            except Exception:
                pass
        self.storage.insert_fact(fact)
        return fact

    # =====================================================
    # Получить все факты
    # =====================================================

    def all_facts(self):
        rows=self.storage.get_all()
        facts=[]
        for row in rows:
            facts.append({
            "id":row[0],
                "text":row[1],
                "category":row[2],
                "importance":row[3],
                "created":row[4],
                "updated":row[5],
                "last_used":row[6],
                "used":row[7]
           })
        return facts
    def search(
        self,
        query:str,
        limit:int=5
    ):
        query=query.lower().strip()
        facts=self.all_facts()
        if not query:
            facts.sort(
                key=lambda x:(
                    x["importance"],
                    x["used"]
                ),
                reverse=True
            )
            return facts[:limit]
        result=[]
        for fact in facts:
            text=fact["text"].lower()
            if query in text:
                result.append((1.0,fact))
                continue
            score=SequenceMatcher(
                None,
                query,
                text
            ).ratio()
            if score>=0.35:
                result.append((score,fact))
        result.sort(
            key=lambda x:(
                x[0],
                x[1]["importance"],
                x[1]["used"]
            ),
            reverse=True
        )
        return [x[1] for x in result[:limit]]
    def get_context(
        self,
        query:str,
        limit:int=5
    )->str:
        facts=self.search(query,limit)
        if not facts:
            return ""
        context=[]
        for fact in facts:
            context.append(
                f"- {fact['text']}"
            )
        return "\n".join(context)
    def forget(self,fact_id:str):
        self.storage.delete(fact_id)
    def close(self):
        self.storage.close()