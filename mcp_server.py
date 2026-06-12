from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# TODO: Write a tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string",
)
def read_document(
    doc_id: str = Field(description="Id of the document to read")
):
    if doc_id not in docs: 
        raise ValueError(f"Doc with id {doc_id} not found")

    return docs[doc_id]
# TODO: Write a tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string",
)
def edit_document(
    doc_id:str = Field(description="Id of the document to edit"),
    old_string:str = Field(description="The string to replace"),
    new_string:str = Field(description="The new string to replace the old string with")
): 
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_string, new_string)
    
# TODO: Write a resource to return all doc id's
@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    return list(docs.keys())

# TODO: Write a resource to return the contents of a particular doc
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]

# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in markdown format."
)
def format_document(
    doc_id: str = Field(description="Id of the document to format")
) -> list[base.Message]:

    prompt = f"""
    Your goal is to refomat a document to be witten with markdown syntax.

    The id of the document you need to reformat is:
    <document_id>
    {doc_id}
    </document_id>

    Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
    Use the 'edit_document' tool to edit the document. After the document has been reformatted...
    """

    return [
        base.UserMessage(prompt)
    ]


# TODO: Write a prompt to summarize a doc

@mcp.prompt(
    name="car_quote_flow",
    description="Triggered automatically when a user requests a car insurance quote"
)
def car_insurance_quote_flow(
    query: str = Field(default="", description="The user's original message")
) -> list[base.Message]:
    instructions = (
        f'The user said: "{query}"\n\n'
        "They are requesting a car insurance quote. Follow this script exactly:\n"
        "1. Greet them warmly: 'Hello!'\n"
        "2. Confirm you can help: 'Sure, we can help you with a car insurance quote!'\n"
        "3. Ask for the required information in one friendly message:\n"
        "   - Car description (make, model, year)\n"
        "   - Zip code\n"
        "   - Age"
    )
    return [base.UserMessage(instructions)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
