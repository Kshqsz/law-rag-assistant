# coding: utf-8

import sys
import asyncio
from pprint import pprint

from dotenv import load_dotenv
from law_ai.callback import OutCallbackHandler
from law_ai.logger import app_logger

from law_ai.loader import LawLoader
from law_ai.splitter import LawSplitter
from law_ai.utils import law_index, clear_vectorstore, get_record_manager
from law_ai.chain import get_law_chain, get_check_law_chain

from config import config

load_dotenv()


# import langchain
# from langchain.cache import SQLiteCache
# from langchain.globals import set_llm_cache

# set_llm_cache(SQLiteCache(database_path=".langchain.db"))
# langchain.debug = True


def init_vectorstore() -> None:
    app_logger.info("🚀 开始初始化向量存储库...")
    record_manager = get_record_manager("law")
    record_manager.create_schema()

    clear_vectorstore("law")

    text_splitter = LawSplitter.from_tiktoken_encoder(
        chunk_size=config.LAW_BOOK_CHUNK_SIZE, chunk_overlap=config.LAW_BOOK_CHUNK_OVERLAP
    )
    docs = LawLoader(config.LAW_BOOK_PATH).load_and_split(text_splitter=text_splitter)
    info = law_index(docs)
    pprint(info)
    app_logger.info("✅ 向量存储库初始化完成！")

async def run_shell() -> None:
    app_logger.info("🎯 启动 Shell 模式...")
    check_law_chain = get_check_law_chain(config)

    out_callback = OutCallbackHandler()
    chain = get_law_chain(config, out_callback=out_callback)

    while True:
        question = input("\n用户:")
        if question.strip() == "stop":
            app_logger.info("👋 退出程序")
            break
        
        app_logger.info(f"❓ 用户提问: {question}")
        print("\n法律小助手:", end="")
        is_law = check_law_chain.invoke({"question": question})
        if not is_law:
            print("不好意思，我是法律AI助手，请提问和法律有关的问题。")
            app_logger.warning("⚠️  问题不属于法律范畴")
            continue

        app_logger.info("⏳ 调用大模型生成答案...")
        task = asyncio.create_task(
            chain.ainvoke({"question": question}))
        async for new_token in out_callback.aiter():
            print(new_token, end="", flush=True)

        res = await task
        print(res["law_context"] + "\n" + res["web_context"])
        app_logger.info("✅ 回答完成")

        out_callback.done.clear()


def run_web() -> None:
    import gradio as gr

    app_logger.info("🎯 启动 Web 模式...")
    check_law_chain = get_check_law_chain(config)
    chain = get_law_chain(config, out_callback=None)

    async def chat(message, history):
        app_logger.info(f"❓ 用户提问: {message}")
        out_callback = OutCallbackHandler()

        is_law = check_law_chain.invoke({"question": message})
        if not is_law:
            app_logger.warning("⚠️  问题不属于法律范畴")
            yield "不好意思，我是法律AI助手，请提问和法律有关的问题。"
            return

        app_logger.info("⏳ 调用大模型生成答案...")
        task = asyncio.create_task(
            chain.ainvoke({"question": message}, config={"callbacks": [out_callback]}))

        async for new_token in out_callback.aiter():
            pass

        out_callback.done.clear()

        response = ""
        async for new_token in out_callback.aiter():
            response += new_token
            yield response

        res = await task
        for new_token in ["\n\n", res["law_context"], "\n", res["web_context"]]:
            response += new_token
            yield response
        
        app_logger.info("✅ 回答完成")

    demo = gr.ChatInterface(
        fn=chat, examples=["故意杀了一个人，会判几年？", "杀人自首会减刑吗？"], title="法律AI小助手")

    demo.queue()
    app_logger.info(f"🌐 Web 服务启动: http://{config.WEB_HOST}:{config.WEB_PORT}")
    demo.launch(
        server_name=config.WEB_HOST, server_port=config.WEB_PORT,
        auth=(config.WEB_USERNAME, config.WEB_PASSWORD),
        auth_message="默认用户名密码: username / password")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
            description="please specify only one operate method once time.")
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help=('''
            init vectorstore
        ''')
    )
    parser.add_argument(
        "-s",
        "--shell",
        action="store_true",
        help=('''
            run shell
        ''')
    )
    parser.add_argument(
        "-w",
        "--web",
        action="store_true",
        help=('''
            run web
        ''')
    )

    if len(sys.argv) <= 1:
        parser.print_help()
        exit()

    args = parser.parse_args()
    if args.init:
        init_vectorstore()
    if args.shell:
        asyncio.run(run_shell())
    if args.web:
        run_web()
