import streamlit as st
from ada_core import AgentLada
from user_manager import UserManager

def main():
    st.set_page_config(page_title="Лада",page_icon="🤖",layout="centered")
    st.title("🤖 Лада: AI Агент с памятью")
    if "user_manager" not in st.session_state:
        st.session_state.user_manager=UserManager()
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        tab1,tab2=st.tabs(["🔑 Вход","📝 Регистрация"])
        with tab1:
            st.subheader("Вход в систему")
            username=st.text_input("Имя пользователя",key="login_username")
            password=st.text_input("Пароль",type="password",key="login_password")
            if st.button("Войти",type="primary"):
                if username and password:
                    user_id,message=st.session_state.user_manager.login_user(username,password)
                    if user_id:
                        st.session_state.user_id=user_id
                        st.session_state.username=username
                        st.session_state.ada=AgentLada(user_id=user_id)
                        st.success(f"Добро пожаловать, {username}!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Заполните все поля")
        with tab2:
            st.subheader("Регистрация")
            new_username=st.text_input("Имя пользователя",key="reg_username")
            new_password=st.text_input("Пароль",type="password",key="reg_password")
            confirm_password=st.text_input("Повторите пароль",type="password",key="reg_confirm")
            if st.button("Зарегистрироваться",type="primary"):
                if new_username and new_password:
                    if new_password!=confirm_password:
                        st.error("Пароли не совпадают")
                    else:
                        user_id,message=st.session_state.user_manager.register_user(new_username,new_password)
                        if user_id:
                            st.success(f"Регистрация успешна! Теперь войдите под именем {new_username}")
                        else:
                            st.error(message)
                else:
                    st.warning("Заполните все поля")
        return
    ada=st.session_state.ada
    username=st.session_state.get("username",st.session_state.user_id)
    st.sidebar.success(f"👤 {username}")
    if st.sidebar.button("Выйти из аккаунта"):
        st.session_state.user_id=None
        st.session_state.ada=None
        st.rerun()
    if "setup_done" not in st.session_state:
        with st.spinner("🚀 Инициализация личной памяти..."):
            success=ada.initialize()
            if success:
                st.session_state.setup_done=True
            else:
                st.error("Ошибка инициализации")
                return
    if "messages" not in st.session_state:
        st.session_state.messages=[]
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt:=st.chat_input("Напишите сообщение Ладе..."):
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Лада думает..."):
            try:
                response=ada.chat(prompt)
            except Exception as e:
                response=f"❌ Ошибка: {str(e)}"
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role":"assistant","content":response})

if __name__=="__main__":
    main()