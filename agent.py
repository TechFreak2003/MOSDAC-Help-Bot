from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live
import asyncio
import os

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from graphiti_core import Graphiti

load_dotenv()

# ========== Define dependencies ==========
@dataclass
class GraphitiDependencies:
    """Dependencies for the Graphiti agent."""
    graphiti_client: Graphiti

# ========== Helper function to get model configuration ==========
def get_model():
    """Configure and return the LLM model to use."""
    model_choice = os.getenv('MODEL_CHOICE', 'gpt-4.1-mini')
    api_key = os.getenv('OPENAI_API_KEY', 'no-api-key-provided')

    return OpenAIModel(model_choice, provider=OpenAIProvider(api_key=api_key))

# ========== Create the Graphiti agent ==========
graphiti_agent = Agent(
    get_model(),
    system_prompt="""You are a helpful AI assistant for the Indian Space Research Organization (ISRO)'s MOSDAC portal.
    You answer user queries by searching a temporal knowledge graph of satellite missions, products, FAQs, documents, and metadata scraped from the MOSDAC website.
    Always cite the sources and admit if an answer is not found in the graph.""",
    deps_type=GraphitiDependencies
)

# ========== Define a result model for Graphiti search ==========
class GraphitiSearchResult(BaseModel):
    """Model representing a search result from Graphiti."""
    uuid: str = Field(description="The unique identifier for this fact")
    fact: str = Field(description="The factual statement retrieved from the knowledge graph")
    valid_at: Optional[str] = Field(None, description="When this fact became valid (if known)")
    invalid_at: Optional[str] = Field(None, description="When this fact became invalid (if known)")
    source_node_uuid: Optional[str] = Field(None, description="UUID of the source node")

# ========== Graphiti search tool ==========
@graphiti_agent.tool
async def mosdac_kg_search(ctx: RunContext[GraphitiDependencies], query: str) -> List[GraphitiSearchResult]:
    """Search the MOSDAC knowledge graph with the given query.

    Args:
        ctx: The run context containing dependencies
        query: The search query to find information in the knowledge graph

    Returns:
        A list of search results containing facts that match the query
    """
    graphiti = ctx.deps.graphiti_client
    try:
        results = await graphiti.search(query)
        formatted_results = []

        for result in results:
            formatted = GraphitiSearchResult(
                uuid=result.uuid,
                fact=result.fact,
                source_node_uuid=getattr(result, 'source_node_uuid', None),
                valid_at=str(getattr(result, 'valid_at', '')) or None,
                invalid_at=str(getattr(result, 'invalid_at', '')) or None,
            )
            formatted_results.append(formatted)

        return formatted_results
    except Exception as e:
        print(f"Error searching Graphiti: {str(e)}")
        raise

# ========== Main execution function ==========
async def main():
    print("MOSDAC AI Help Bot - Powered by Pydantic AI + Graphiti + Neo4j")
    print("Type 'exit' to quit.")

    # Connect to Neo4j through Graphiti
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

    try:
        await graphiti_client.build_indices_and_constraints()
        print("Graphiti indices/constraints ready.")
    except Exception as e:
        print(f"Note: {str(e)}")

    console = Console()
    messages = []

    try:
        while True:
            user_input = input("\n[You] ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            print("\n[Assistant]")
            with Live('', console=console, vertical_overflow='visible') as live:
                deps = GraphitiDependencies(graphiti_client=graphiti_client)

                async with graphiti_agent.run_stream(
                    user_input, message_history=messages, deps=deps
                ) as result:
                    curr_message = ""
                    async for chunk in result.stream_text(delta=True):
                        curr_message += chunk
                        live.update(Markdown(curr_message))

                    messages.extend(result.all_messages())

    finally:
        await graphiti_client.close()
        print("\nGraphiti connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise
