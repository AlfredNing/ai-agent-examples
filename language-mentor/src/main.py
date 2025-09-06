import streamlit as st
from agent.conversation_agent import ConversationAgent
from agent.hotel_checkin_agent import HotelCheckinAgent
from agent.job_interview_agent import JobInterviewAgent
from agent.retening_agent import RentingAgent
from agent.salary_negotiation_agent import SalaryNegotiationAgent
from utils.logger import LOG
from dotenv import load_dotenv

load_dotenv()
import sys
import os

# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到sys.path
# sys.path.append(root_dir)

conversation_agent = ConversationAgent()
hotel_checkin_agent = HotelCheckinAgent()
job_interview_agent = JobInterviewAgent()
renting_agent = RentingAgent()
salary_negotiation_agent = SalaryNegotiationAgent()


# 对话 Agent 处理函数
def handle_conversation(user_input, chat_history):
    LOG.debug(f"[聊天记录]: {chat_history}")
    # bot_message = conversation_agent.chat(user_input)
    bot_message = conversation_agent.chat_with_history(user_input)
    LOG.info(f"[ChatBot]: {bot_message}")
    return bot_message


# 场景 Agent 处理函数，根据选择的场景调用相应的 Agent
def handle_scenario(user_input, history, scenario):
    agents = {
        "求职面试": job_interview_agent,
        "酒店入住": hotel_checkin_agent,
        "薪资谈判": salary_negotiation_agent,
        "租房": renting_agent
    }
    return agents[scenario].respond(user_input)


def main():
    st.title("Language Mentor")

    # 模式选择：通用对话 or 场景对话
    interaction_mode = st.radio(
        "请选择交互模式：",
        ["通用对话", "场景对话"],
        horizontal=True
    )

    if interaction_mode == "通用对话":
        # 通用对话模式：有上下文记忆的连续对话
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []  # 用于存储对话历史

        user_query = st.chat_input(placeholder="请输入您的问题...")

        if user_query:
            # 调用通用对话处理函数
            bot_response = handle_conversation(user_query, st.session_state.chat_history)

            # 更新历史
            st.session_state.chat_history.append(("你", user_query))
            st.session_state.chat_history.append(("助手", bot_response))

        # 展示对话历史
        for role, msg in st.session_state.chat_history:
            st.chat_message(role).write(msg)

    elif interaction_mode == "场景对话":
        # 场景对话模式：选择一个场景再提问
        st.subheader("🎭 选择场景")

        scenario = st.selectbox(
            "请选择一个场景：",
            ["求职面试", "酒店入住", "薪资谈判", "租房"]
        )

        user_query = st.chat_input(placeholder=f"请描述您的{scenario}相关问题...")

        if user_query:
            # 调用场景对话处理函数
            response = handle_scenario(user_query, [], scenario)  # history=[] 暂未使用，可后续扩展
            st.chat_message("你").write(user_query)
            st.chat_message("助手").write(response)


if __name__ == '__main__':
    main()
