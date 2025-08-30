from typing import Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import ChatMessage, BaseMessage, AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pathlib import Path
import pprint

load_dotenv()

llm = ChatOpenAI(model='qwen-max')


class AgentState(Dict):
    # 用户输入
    user_input: str
    # llm解析的参数
    params: Optional[Dict[str, Any]]
    # 生成的目录结构
    structure: Optional[list[dict[str, Any]]]
    # 生成的文件内容
    files: Optional[Dict[str, str]]
    # 最终整合输出的内容
    output: Optional[str]


def start(state: AgentState) -> AgentState:
    return {"user_input": state["user_input"]}


def parse_input(state: AgentState) -> AgentState:
    user_input = state["user_input"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
         你是一个专业的 Java 项目脚手架生成助手。
         请根据用户描述，提取以下结构化信息，并以合法的 JSON 格式输出（不要任何多余文字）：
        - projectName: 项目名称， 如 "generate-project-code
        - jdkVersion: jdk版本,如 "8" 或 "11" 或 "17
        - build_tool: 构建工具，如 "maven" 或 "gradle"
        - framework: 使用的框架，如 "spring_boot" 或 "none"
        - modules: 项目包含的模块列表，如 ["api", "service", "repository"]
        - needs: 用户需要的功能，如 ["rest_controller", "unit_test", "docker"]
        - company_package: 项目的公司包名，例如 "com.nq" 或 "org.example"。如果没有明确提到，请使用默认值 "com.nq"
    
         请确保字段正确，格式为：{{"build_tool": "...", "framework": "...", "modules": [], "needs": []}}
        """),
        ("human", "{user_input}")
    ])

    parser = JsonOutputParser()

    chain = prompt | llm | parser

    try:
        result = chain.invoke({"user_input": user_input})
        print("解析结果: ", result)
        return {"params": result}
    except Exception as e:
        print("[fallback] 使用默认参数:", e)
        return {
            "params": {
                "projectName": "generate-code-project",
                "jdkVersion": "17",
                "build_tool": "maven",
                "framework": "spring_boot",
                "modules": ["api", "service", "repository"],
                "needs": ["rest_controller", "unit_test", "docker"],
                "company_package": "com.nq"
            }
        }


def generate_struct(state: AgentState) -> AgentState:
    params = state["params"]
    print("[节点] generate_structure: LLM 生成目录结构")

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
       根据以下参数生成项目名称{params['projectName']},
       公司包名：{params['company_package']}
       生成Java 项目目录结构，输出 JSON 列表，每项为：
        {{{{"type": "dir"|"file", "path": "相对路径"}}}}
      参数：
      - projectName: {params['projectName']}
      - build_tool: {params['build_tool']}
      - framework: {params['framework']}
      - modules: {params['modules']}
      - needs: {params['needs']}
      - jdkVersion: {params['jdkVersion']}

      只输出 JSON 列表，例如：
                  [{{{{"type": "dir", "path": "src/main/java"}}}}, {{{{"type": "file", "path": "pom.xml"}}}}]
        
        
      """),
        ("human", "请输出结构。")
    ])

    parser = JsonOutputParser()
    chain = prompt | llm | parser
    try:
        result = chain.invoke({})
        print("[结构结果]", result)
        return {"structure": result, "params": params}
    except Exception as e:
        print("[fallback] 使用默认结构:", e)
        return {
            "params": params,
            "structure": [
                {"type": "dir", "path": "src/main/java/com/example"},
                {"type": "dir", "path": "src/test/java/com/example"},
                {"type": "file", "path": "pom.xml"},
                {"type": "file", "path": "Dockerfile"}
            ]
        }


def generate_files(state: AgentState) -> AgentState:
    params = state["params"]
    print("[节点] generate_files: LLM 生成文件内容")

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
    你是一个专业的java项目助手，确保生成的项目能够一键导入启动。
    
    根据以下项目参数，生成该项目所需要的关键文件。
    项目名称为：{params['projectName']} 
    项目包为: {params['company_package']}
    项目参数:
    - build_tool: {params['build_tool']}
    - framework: {params['framework']}
    - modules: {params['modules']}
    - needs: {params['needs']}
    - jdkVersion: {params['jdkVersion']}
    - company_package: {params['company_package']}
    - projectName: {params['projectName']}
    
    请生成一个 JSON 对象，其中：
    - key 为文件的相对路径，例如："pom.xml"、"src/main/java/com/example/Application.java"
    - value 为该文件的具体内容（字符串）
    
    请确保输出的是一个合法的、格式正确的 JSON 对象，例如：
    {{{{
      "pom.xml": "<project>...</project>",
      "src/main/java/com/example/Application.java": "package com.example...",
      "src/test/java/com/example/HelloControllerTest.java": "@Test public void ..."
    }}}}
    
    不要包含任何 Markdown、代码块、```
    或者 ### 文件名: 这类文本。
    只输出一个 JSON 对象，不要任何额外的解释文字。
    
    切记，只能根据项目名生成单个项目的框架
    """),
        ("human", "请生成")
    ])

    parser = JsonOutputParser()
    chain = prompt | llm | parser
    try:
        result = chain.invoke({})
        return {"files": result, "params": params}
    except Exception as e:
        print("[fallback] 文件生成失败:", e)
        return {"files": {}, "params": params}


def write_to_disk(state: AgentState) -> AgentState:
    structure = state["structure"]
    files = state.get("files")
    projectName = state["params"]['projectName']
    print("files:", files)

    if not structure or not files:
        return {"output": "⚠️ 未生成结构或文件，跳过写入。"}
    base_dir = "generate_project" if projectName is None else projectName

    project_path = Path(base_dir)

    if project_path.exists():
        import shutil
        shutil.rmtree(project_path)

    project_path.mkdir(exist_ok=True)
    print(f"[写入] 创建项目目录: {project_path}")

    for item in structure:
        if item["type"] == "dir":
            p = project_path / item["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.mkdir(exist_ok=True)
            print(f"[目录] {p}")

    for fname, content in files.items():
        p = project_path / fname
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print(f"[文件] {p} ({len(content)} 字符)")

    return {
        "output": f"✅ 项目已生成到本地文件夹：{project_path.absolute()}"
    }


def generate_output(state: AgentState) -> AgentState:
    output = state.get("output", "📦 项目已生成（无详细输出）")
    return {"output": output}


def builder_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("start", start)
    workflow.add_node("parse_input", parse_input)
    workflow.add_node("generate_structure", generate_struct)
    workflow.add_node("generate_files", generate_files)
    workflow.add_node("write_to_disk", write_to_disk)
    workflow.add_node("generate_output", generate_output)

    workflow.add_edge(START, "start")
    workflow.add_edge("start", "parse_input")
    workflow.add_edge("parse_input", "generate_structure")
    workflow.add_edge("generate_structure", "generate_files")
    workflow.add_edge("generate_files", "write_to_disk")
    workflow.add_edge("write_to_disk", "generate_output")
    workflow.add_edge("generate_output", END)
    return workflow.compile()


if __name__ == '__main__':

    app = builder_workflow()

    graph_png = app.get_graph().draw_mermaid_png()
    with open("single-generate-code-agent.png", "wb") as f:
        f.write(graph_png)

    user_input = """
    帮我创建一个 Spring Boot + Maven  的 Java17 项目,
    项目名称为agent-generate-code
    公司设置为com.microsoft，
    包含 REST API 层、Service 层、Repository 层，还要有单元测试和 Docker 支持。
    """
    state = {"user_input": user_input}
    print("\n🚀 开始运行 Java 项目生成 Agent（含本地磁盘写入）...\n")

    for event in app.stream(state):
        for node, output in event.items():
            print(f"【节点 {node}】输出:")
            pprint.pprint(output)
    print("\n✅ 工作流执行完毕！")
