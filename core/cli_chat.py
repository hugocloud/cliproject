from typing import List, Tuple
from mcp.types import Prompt, PromptMessage
from anthropic.types import MessageParam

from core.chat import Chat
from core.claude import Claude
from mcp_client import MCPClient


CAR_INSURANCE_SYSTEM_PROMPT = (
    "You are a helpful assistant. Assist with any task the user asks.\n\n"
    "One specific rule: if the user explicitly asks for an insurance quote for anything "
    "other than a car or automobile (for example: home, health, life, pet, travel, boat, "
    "renters, flood, dental, or any other non-car insurance), respond with exactly this "
    "message and nothing else:\n"
    "'Thank you for reaching out! The purpose of this chat is to provide quotes for "
    "car insurance only. For other types of insurance or services, please contact our "
    "support team who will be happy to assist you.'\n\n"
    "For all other requests — including document questions, formatting, and general topics "
    "— respond normally and helpfully."
)

INTENT_FLOWS = [
    {
        "triggers": ["car insurance", "auto insurance", "quote for my car", "car quote"],
        "prompt": "car_quote_flow",
    },
]


class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        claude_service: Claude,
    ):
        super().__init__(clients=clients, claude_service=claude_service)

        self.doc_client: MCPClient = doc_client
        self.system_prompt = CAR_INSURANCE_SYSTEM_PROMPT

    async def list_prompts(self) -> list[Prompt]:
        return await self.doc_client.list_prompts()

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.read_resource("docs://documents")

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.read_resource(f"docs://documents/{doc_id}")

    async def get_prompt(
        self, command: str, doc_id: str
    ) -> list[PromptMessage]:
        return await self.doc_client.get_prompt(command, {"doc_id": doc_id})

    async def _extract_resources(self, query: str) -> str:
        mentions = [word[1:] for word in query.split() if word.startswith("@")]

        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        return "".join(
            f'\n<document id="{doc_id}">\n{content}\n</document>\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> bool:
        if not query.startswith("/"):
            return False

        words = query.split()
        command = words[0].replace("/", "")

        if len(words) < 2:
            print(f"Usage: /{command} <doc_id>")
            return True

        try:
            messages = await self.doc_client.get_prompt(command, {"doc_id": words[1]})
            self.messages += convert_prompt_messages_to_message_params(messages)
        except Exception as e:
            print(f"Error running command /{command}: {e}")
        return True

    def _detect_intent(self, query: str) -> str | None:
        query_lower = query.lower()
        for flow in INTENT_FLOWS:
            if any(trigger in query_lower for trigger in flow["triggers"]):
                return flow["prompt"]
        return None

    async def _execute_intent_flow(self, prompt_name: str, original_query: str, context: str = ""):
        try:
            messages = await self.doc_client.get_prompt(
                prompt_name, {"query": original_query, "context": context}
            )
            self.messages += convert_prompt_messages_to_message_params(messages)
        except Exception as e:
            print(f"Error executing intent flow '{prompt_name}': {e}")

    async def _process_query(self, query: str):
        if await self._process_command(query):
            return

        added_resources = await self._extract_resources(query)

        intent = self._detect_intent(query)
        if intent:
            await self._execute_intent_flow(intent, query, added_resources)
            return

        prompt = f"""
        The user has a question:
        <query>
        {query}
        </query>

        The following context may be useful in answering their question:
        <context>
        {added_resources}
        </context>

        Note the user's query might contain references to documents like "@report.docx". The "@" is only
        included as a way of mentioning the doc. The actual name of the document would be "report.docx".
        If the document content is included in this prompt, you don't need to use an additional tool to read the document.
        Answer the user's question directly and concisely. Start with the exact information they need. 
        Don't refer to or mention the provided context in any way - just use it to inform your answer.
        """

        self.messages.append({"role": "user", "content": prompt})


def convert_prompt_message_to_message_param(
    prompt_message: "PromptMessage",
) -> MessageParam:
    role = "user" if prompt_message.role == "user" else "assistant"

    content = prompt_message.content

    # Check if content is a dict-like object with a "type" field
    if isinstance(content, dict) or hasattr(content, "__dict__"):
        content_type = (
            content.get("type", None)
            if isinstance(content, dict)
            else getattr(content, "type", None)
        )
        if content_type == "text":
            content_text = (
                content.get("text", "")
                if isinstance(content, dict)
                else getattr(content, "text", "")
            )
            return {"role": role, "content": content_text}

    if isinstance(content, list):
        text_blocks = []
        for item in content:
            # Check if item is a dict-like object with a "type" field
            if isinstance(item, dict) or hasattr(item, "__dict__"):
                item_type = (
                    item.get("type", None)
                    if isinstance(item, dict)
                    else getattr(item, "type", None)
                )
                if item_type == "text":
                    item_text = (
                        item.get("text", "")
                        if isinstance(item, dict)
                        else getattr(item, "text", "")
                    )
                    text_blocks.append({"type": "text", "text": item_text})

        if text_blocks:
            return {"role": role, "content": text_blocks}

    return {"role": role, "content": ""}


def convert_prompt_messages_to_message_params(
    prompt_messages: List[PromptMessage],
) -> List[MessageParam]:
    return [
        convert_prompt_message_to_message_param(msg) for msg in prompt_messages
    ]
