from langchain.agents import create_agent
from agent_app.model.factory import chat_model
from agent_app.utils.prompt_loader import load_system_prompts
from agent_app.agent.tools import agent_tools
from agent_app.agent.tools.agent_tools import (query_knowledge_base, get_files_meta, read_file_chunks, list_files,
                                     rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fetch_external_data, fill_context_for_report)
from agent_app.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from agent_app.utils.temp_file_service import get_temp_file_service


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[query_knowledge_base, get_files_meta, read_file_chunks, list_files,
                   rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )
        self.temp_file_service = get_temp_file_service()

    def execute_stream(
        self,
        query: str,
        conversation_id: int,
        uploaded_filename: str | None = None,
        session_file_id: str | None = None,
    ):
        context = {"report": False}
        if session_file_id and uploaded_filename:
            temp_file_content = self.temp_file_service.read_file_content(conversation_id, session_file_id, uploaded_filename)
            context["temp_file_prompt"] = (
                f"临时文档《{uploaded_filename}》仅对当前对话有效，新对话不应再引用。用户提到“这个文档”“该文档”时默认指它。\n"
                f"文档内容：\n{temp_file_content}"
            )
        elif uploaded_filename:
            context["temp_file_prompt"] = (
                f"最近上传了文件《{uploaded_filename}》，用户提到“这个文档”时默认指它。"
            )

        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        user_query = query.strip()
        emitted_text = ""
        for chunk in self.agent.stream(input_dict, stream_mode="values", context=context):
            latest_message = chunk["messages"][-1]
            if not hasattr(latest_message, "content") or not latest_message.content:
                continue
            content = latest_message.content.strip()
            # 过滤掉用户消息本身（首条消息在 LangChain 中会被记录为 ToolMessage）
            if content == user_query:
                continue
            # 仅输出增量，避免整段重刷导致重复
            if content.startswith(emitted_text):
                delta = content[len(emitted_text):]
                if delta:
                    emitted_text = content
                    yield delta
            else:
                emitted_text = content
                yield content

    def sync_knowledge_file(self, filepath: str) -> dict:
        """将单个文件同步到知识库，返回 sync_file 结果"""
        result = agent_tools.rag.sync_file(filepath)
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[query_knowledge_base, get_files_meta, read_file_chunks, list_files,
                   rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )
        return result


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)