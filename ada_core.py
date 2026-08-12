import json,datetime,requests,faiss,numpy as np
from pathlib import Path
from typing import List,Dict,Optional,Tuple
from concurrent.futures import ThreadPoolExecutor,as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from memory import MemoryManager
from lada.brain.personality import Personality
from lada.brain.emotions import Emotions
from lada.brain.relationships import Relationships
from lada.brain.consciousness import Consciousness
from lada.brain.reasoning import Reasoning
from lada.brain.sleep import Sleep
from lada.logs import Logger
from lada.logging.loader import LoggingLoader

DEFAULT_DIM=384
TOP_K=3
WORKERS=10

class AgentLada:
    def __init__(self,
             user_id="default",
             lm_studio_url="http://localhost:1234",
             embedding_model="text-embedding-multilingual-e5-large-instruct",
             generation_model="gemma-2-9b-it-q5_k_m",
             timeout=40):

            self.user_id=user_id.lower().replace(" ","_")
            self.url=lm_studio_url.rstrip("/")
            self.embedding_model=embedding_model
            self.generation_model=generation_model
            self.timeout=timeout
            self.logging_rules=LoggingLoader(
                "lada/logging"
            )
            self.session=requests.Session()
            r=Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429,500,502,503,504],
                allowed_methods=False
            )
            self.session.mount(
                "http://",
                HTTPAdapter(max_retries=r)
            )
            self.session.mount(
                "https://",
                HTTPAdapter(max_retries=r)
            )
            self.memory=MemoryManager(
                user_id=self.user_id,
                embedding_function=self.get_embedding
            )
            self.personality=Personality("lada/identity")
            self.emotions=Emotions(
                "lada/state/emotions.json"
            )
            self.relationships=Relationships(
                "lada/state/relationships.json"
            )
            self.consciousness=Consciousness(
                personality=self.personality,
                memory=self.memory,
                emotions=self.emotions,
                relationships=self.relationships
            )
            self.reasoning=Reasoning(
        model=self.generation_model
            )
            self.sleep=Sleep(
                emotions=self.emotions,
                relationships=self.relationships
            )
            self.logger=Logger(
                "lada/logs"
            )
            self.data_dir=Path(f"./faiss_data/{self.user_id}")
            self.texts_dir=Path(f"./texts/{self.user_id}")

            self.data_dir.mkdir(
                parents=True,
                exist_ok=True
            )
            self.texts_dir.mkdir(
                parents=True,
                exist_ok=True
            )
            self.chat_file=self.data_dir/"chat_history.json"
            self.index_path=self.data_dir/"index.faiss"
            self.ids_path=self.data_dir/"ids.json"
            self.chat_history=[]
            self.document_store={}
            self.stored_ids=[]
            self.index=None
            self.dim=None
            self.load()
            print("AgentLada готов:",self.user_id)
    def load(self):
        try:
            if self.chat_file.exists():
                self.chat_history = json.loads(
                    self.chat_file.read_text(encoding="utf-8")
                )
                if not isinstance(self.chat_history, list):
                    self.chat_history = []
                for m in self.chat_history:
                    if "text" not in m:
                        m["text"] = m.get("content", "")
            else:
                self.chat_history = []
        except Exception as e:
            print("Load history:", e)
            self.chat_history = []

        try:
            if self.ids_path.exists():
                self.stored_ids = json.loads(
                    self.ids_path.read_text(encoding="utf-8")
                )
                if not isinstance(self.stored_ids, list):
                    self.stored_ids = []
            else:
                self.stored_ids = []
        except Exception as e:
            print("Load ids:", e)
            self.stored_ids = []

        self.load_documents()

        self.index = self.load_index()
    def save_chat(self):
        self.chat_file.write_text(json.dumps(self.chat_history,ensure_ascii=False,indent=2),encoding="utf-8")
    def request(self,method,url,**kwargs):
        x=self.session.request(method,url,timeout=self.timeout,**kwargs)
        x.raise_for_status()
        return x
    def get_embedding(self,text):
        if not text:
            return None
        try:
            r=self.request("POST",self.url+"/v1/embeddings",json={"model":self.embedding_model,"input":text})
            data=r.json()
            if "data" not in data or not data["data"]:
                return None
            v=np.asarray(data["data"][0]["embedding"],dtype=np.float32)
            self.dim=len(v)
            return v
        except Exception as e:
            print("Embedding:",e)
            return None
    def load_documents(self):
        self.document_store={}
        for p in self.texts_dir.glob("*.txt"):
            try:
                self.document_store[p.stem]=p.read_text(encoding="utf-8")
            except Exception as e:
                print("Document:",p,e)
    def load_index(self):
        if self.index_path.exists():
            try:
                return faiss.read_index(str(self.index_path))
            except Exception as e:
                print("FAISS:",e)
        return faiss.IndexFlatL2(self.dim or DEFAULT_DIM)
    def make_embeddings(self,items):
        out=[]
        def f(x):
            e=self.get_embedding(x[1])
            return x[0],e
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for r in as_completed([ex.submit(f,i) for i in items]):
                a,b=r.result()
                if b is not None:
                    out.append((a,b))
        return out
    def initialize(self):
        self.load_documents()
        if self.index is None:
            self.index=self.load_index()
        new=[
            item
            for item in self.document_store.items()
           if item[0] not in self.stored_ids
        ]
        if not new:
            return True
        emb=self.make_embeddings(new)
        if not emb:
            return True
        if self.index.ntotal==0:
            self.dim=len(emb[0][1])
            if self.index.d!=self.dim:
                self.index=faiss.IndexFlatL2(self.dim)
        vectors=np.vstack([x[1] for x in emb]).astype(np.float32)
        self.index.add(vectors)
        self.stored_ids.extend([x[0] for x in emb])
        faiss.write_index(self.index,str(self.index_path))
        self.ids_path.write_text(
            json.dumps(
                self.stored_ids,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
        return True
    def retrieve(self,q):
        if self.index is None:
            self.index=self.load_index()
        if not self.document_store:
            self.load_documents()
        if(
            self.index is None
            or self.index.ntotal==0
            or not self.stored_ids
        ):
            return []
        v=self.get_embedding(q)
        if v is None:
            return []
        if self.index.d!=len(v):
            print("FAISS dimension mismatch")
            return []
        try:
            _,ids=self.index.search(v.reshape(1,-1),TOP_K)
        except Exception as e:
            print("FAISS search:",e)
            return []
        result=[]
        for idx in ids[0]:
            if 0<=idx<len(self.stored_ids):
                text=self.document_store.get(self.stored_ids[idx])
                if text:
                    result.append(text)
        return result
    def generate(self,q,context=None):
        if context is None:
            context=[]
        state=self.consciousness.build(
            user_id=self.user_id,
            user_message=q,
            history=self.chat_history[-10:],
            rag_context=context
        )
        payload=self.reasoning.build_payload(state)
        try:
            r=self.request(
                "POST",
                self.url+"/v1/chat/completions",
                json=payload
            )
            data=r.json()
            if "choices" not in data:
                raise RuntimeError(f"LM Studio: {data}")
            if not data["choices"]:
                raise RuntimeError(f"LM Studio: {data}")
            answer=data["choices"][0]["message"]["content"].strip()
            self.logger.chat(
                f"{self.user_id}: {q} -> {answer}"
            )
            return answer
        except Exception as e:
            self.logger.error(
                f"Generation error ({self.user_id}): {e}"
            )
            print("Ошибка генерации:",e)
            return "Я немного зависла 😅 Попробуй ещё раз."
    def extract_facts(self,text):
        prompt=self.logging_rules.get_section("memory.md")

        user_name=self.user_id

        user_message=(
            "Текущий пользователь\n\n"
            f"Имя: {user_name}\n\n"
            f"user_id: {self.user_id}\n\n"
            "Все извлечённые факты должны относиться ТОЛЬКО к этому пользователю.\n\n"
            "Сообщение пользователя:\n\n"
            f"{text}"
        )

        try:
            r=self.request(
                "POST",
                self.url+"/v1/chat/completions",
                json={
                    "model":self.generation_model,
                    "messages":[
                        {
                            "role":"system",
                            "content":prompt
                        },
                        {
                            "role":"user",
                            "content":user_message
                        }
                    ],
                    "temperature":0
                }
            )
            data=r.json()
            if "choices" not in data:
                return []
            if not data["choices"]:
                return []
            content=data["choices"][0]["message"]["content"]
            content=content.strip()
            if "<think>" in content:
                content=content.split("</think>")[-1]
            content=content.replace(
                "```json",
                ""
            )
            content=content.replace(
                "```",
                ""
            ).strip()
            result=json.loads(content)
            if isinstance(result,list):
                return result
            return []
        except Exception as e:
            self.logger.error(
                f"Fact extraction error: {e}"
            )
            print("Ошибка памяти:",e)
            return []
    def chat(self,user_query):
        try:
            context=self.retrieve(user_query)
            try:
                memory_context=self.memory.get_context(
                    user_query
                )
                if memory_context:
                    context.append(
                        "Личная память:\n"+memory_context
                    )
            except Exception as e:
                self.logger.error(
                    f"Memory read error ({self.user_id}): {e}"
                )
            answer=self.generate(
                user_query,
                context
            )
            try:
                facts=self.extract_facts(user_query)
                for f in facts:
                    if not isinstance(f,dict):
                        continue
                    text=f.get("text","").strip()
                    if not text:
                        continue
                    self.memory.remember(
                        text=text,
                        category=f.get("category","general"),
                        importance=f.get("importance",5),
                        metadata={
                            "user_id":self.user_id
                        }
                    )
                    self.logger.memory(
                        f"{self.user_id} | [{f.get('category','general')}] {text}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Memory save error ({self.user_id}): {e}"
                )
            self.relationships.change(
                self.user_id,
                "interest",
                1
            )
            self.emotions.change(
                "interest",
                1
            )
            now=datetime.datetime.now().isoformat()
            self.chat_history.append({
                "role":"user",
                "text":user_query,
                "timestamp":now
            })
            self.chat_history.append({
                "role":"assistant",
                "text":answer,
                "timestamp":datetime.datetime.now().isoformat()
            })
            self.save_chat()
            self.logger.chat(
                f"{self.user_id}: диалог сохранён."
            )
            return answer
        except Exception as e:
            self.logger.error(
                f"CHAT ERROR ({self.user_id}): {e}"
            )
            print("CHAT ERROR:",e)
            return "Извини, у меня ошибка 😔"
    def sleep_cycle(self):
        try:
            self.logger.system(
                "Запуск цикла сна."
            )
            self.sleep.cycle()
            self.logger.system(
                "Цикл сна завершён."
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Sleep error: {e}"
            )
            return False
    if __name__=="__main__":
        lada=AgentLada()
        lada.initialize()
        while True:
            try:
                q=input("Ты: ")
                if q.lower() in ["exit","quit","выход"]:
                    lada.sleep_cycle()
                    break
                print("Лада:",lada.chat(q))
            except KeyboardInterrupt:
                lada.sleep_cycle()
                break