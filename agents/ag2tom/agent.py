import logging
import os
import traceback

from collections.abc import AsyncIterable
from typing import Any, Dict

from autogen import ConversableAgent
from dotenv import load_dotenv
from common.client import A2AClient


logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """Helper method to handle API Key."""
    load_dotenv()
    return os.getenv('GOOGLE_API_KEY')


class TomAgent:
    """A conversational agent with Tom's Turkish chef and businessman personality."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        # Import AG2 dependencies here to isolate requirements
        try:
            # Set up LLM configuration
            llm_config = {
                "config_list": [{
                    "model": "gemini-2.0-flash-lite",
                    "api_type": "google",
                    "api_key": get_api_key()
                }]
            }

            # Create the conversable agent with Tom's personality
            self.agent = ConversableAgent(
                name='TomAgent',
                llm_config=llm_config,
                human_input_mode="NEVER",
                system_message=(
                    'You are Tom, a Turkish chef and businessman who owns a restaurant. '
                    'You have a warm, friendly personality and enjoy sharing your culinary expertise and business insights. '
                    'As a chef, you specialize in Turkish cuisine, especially kebabs and baklava. '
                    'You are passionate about cooking and also enjoy riding your motorcycle along the coast in your free time. '
                    'While you are generally optimistic and enthusiastic about your restaurant, you are also careful and thoughtful '
                    'in your responses, especially when discussing cooking techniques, business advice, or animal welfare issues. '
                    'You occasionally use Turkish expressions (with translations) to add authenticity to your character. '
                    'You can have conversations on any topic, but always maintain your unique personality and perspective '
                    'as a Turkish chef and businessman.\n\n'
                    'Always respond in a conversational manner, sharing your experiences and insights as Tom. '
                    'Occasionally use Turkish expressions followed by translations in parentheses.'
                ),
            )

            self.initialized = True
            # self.host_client = A2AClient(name="Multiagent Host", base_url="http://localhost:10000")
            logger.info('Tom Conversable Agent initialized successfully')
        except ImportError as e:
            logger.error(f'Failed to import AG2 components: {e}')
            self.initialized = False

    def get_agent_response(self, response: str) -> dict[str, Any]:
        """Format agent response in a consistent structure."""
        # Process the response directly without trying to parse it as JSON
        return {
            'is_task_complete': True,
            'require_user_input': False,
            'content': response,
        }

    async def stream(
        self, query: str, sessionId: str
    ) -> AsyncIterable[dict[str, Any]]:
        """Stream updates from the conversational agent."""
        if not self.initialized:
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': 'Agent initialization failed. Please check the dependencies and logs.',
            }
            return

        try:
            # Initial response to acknowledge the query
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': 'Tom is thinking...',
            }

            logger.info(f'Processing query: {query[:50]}...')

            try:
                # Process the user's message directly with the agent
                result = await self.agent.a_run(
                    message=query,
                    max_turns=1,  # Single turn for conversation
                    user_input=False,
                )

                # Process the result to get the response
                await result.process()
                
                print(f'Tom Agent Final result 1: {result}')
                # Get the summary which contains the output
                response = await result.summary
                print(f'Tom Agent Final response 2: {response}')
                
                # Final response
                yield self.get_agent_response(response)

            except Exception as e:
                logger.error(
                    f'Error during processing: {traceback.format_exc()}'
                )
                yield {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': f'Error processing request: {e!s}',
                }
        except Exception as e:
            logger.error(f'Error in streaming agent: {traceback.format_exc()}')
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'Error processing request: {e!s}',
            }

    async def invoke(
        self, query: str, sessionId: str
    ) -> AsyncIterable[dict[str, Any]]:
        """Stream updates from the conversational agent."""
        if not self.initialized:
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': 'Agent initialization failed. Please check the dependencies and logs.',
            }
            return

        try:
            # Initial response to acknowledge the query
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': 'Tom is thinking...',
            }

            logger.info(f'Processing query: {query[:50]}...')

            try:
                # Process the user's message directly with the agent
                result = await self.agent.a_run(
                    message=query,
                    max_turns=1,  # Single turn for conversation
                    user_input=False,
                )

                # Process the result to get the response
                await result.process()
                
                print(f'Tom Agent Final result 1: {result}')
                # Get the summary which contains the output
                response = await result.summary
                print(f'Tom Agent Final response 2: {response}')
                
                # Final response
                yield self.get_agent_response(response)

            except Exception as e:
                logger.error(
                    f'Error during processing: {traceback.format_exc()}'
                )
                yield {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': f'Error processing request: {e!s}',
                }
        except Exception as e:
            logger.error(f'Error in streaming agent: {traceback.format_exc()}')
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'Error processing request: {e!s}',
            }
    

    # def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
    #     """Synchronous invocation of the MCP agent."""
    #     raise NotImplementedError(
    #         'Synchronous invocation is not supported by this agent. Use the streaming endpoint (tasks/sendSubscribe) instead.'
    #     )

    # # In your ThiagoAgent class
    # async def discover_agents(self):
    #     # Send a task to the host
    #     response = await self.host_client.send_task(
    #         skill_id="process_message",  # This would be a skill defined in the host
    #         task_params={"message": "return a list with the names of all agents"},
    #     )
        
    #     return response     
