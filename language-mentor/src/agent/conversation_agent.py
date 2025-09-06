from .base_scenario_agent import ScenarioAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from utils.logger import LOG
import os

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    获取指定会话ID的聊天历史。如果该会话ID不存在，则创建一个新的聊天历史实例。

    参数:
        session_id (str): 会话的唯一标识符

    返回:
        BaseChatMessageHistory: 对应会话的聊天历史对象
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


class ConversationAgent:
    """
       对话代理类，负责处理与用户的对话。
    """

    def __init__(self):
        super().__init__()
        self.name = "Conversation Agent"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(current_dir, '..', 'prompts')
        prompts_file_path = os.path.join(prompts_dir, 'conversation_prompts.txt')

        with open(prompts_file_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read().strip()

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        llm = ChatOpenAI(model='qwen-max', max_tokens=8192, temperature=0.8)
        self.chatbot = self.prompt | llm

        # 将聊天机器人与消息历史记录关联起来
        self.chatbot_with_history = RunnableWithMessageHistory(self.chatbot, get_session_history)

        # 保持配置属性
        self.config = {"configurable": {"session_id": "abc123"}}

    def chat(self, user_input):
        """
        处理用户输入并产生回复
        :param user_input:用户输入信息
        :return: 代理生成的回复内容
        """
        response = self.chatbot.invoke(
            [HumanMessage(content=user_input)]
        )

    def chat_with_history(self, user_input):
        """
          处理用户输入并生成包含聊天历史的回复，同时记录日志。
        :param user_input:用户输入信息
        :return: 代理生成的回复内容
        """
        response = self.chatbot_with_history.invoke(
            [HumanMessage(content=user_input)],
            self.config
        )
        LOG.debug(response)
        return response.content
