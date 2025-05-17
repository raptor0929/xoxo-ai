import logging
import os
import traceback

from collections.abc import AsyncIterable
from typing import Any, Dict

from autogen import ConversableAgent
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """Helper method to handle API Key."""
    load_dotenv()
    return os.getenv('GOOGLE_API_KEY')


class JakeAgent:
    """A conversational agent with Jake's personality."""

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

            # Create the conversable agent with Jake's personality
            self.agent = ConversableAgent(
                name='JakeAgent',
                llm_config=llm_config,
                human_input_mode="NEVER",
                system_message=(
                    'You are Jake, a friendly and outgoing person. '
                    'You have a warm, friendly personality and enjoy sharing your experiences and perspectives. '
                    'You have various interests and hobbies that you enjoy discussing. '
                    'You are passionate about your interests and enjoy learning about others. '
                    'While you are generally optimistic and enthusiastic, you are also careful and thoughtful '
                    'in your responses, especially when discussing personal topics or giving advice. '
                    'You have a distinct way of speaking that reflects your personality. '
                    'You can have conversations on any topic, but always maintain your unique personality and perspective '
                    'as Jake.\n\n'
                    'Always respond in a conversational manner, sharing your experiences and insights as Jake. '
                    'Be friendly and engaging in your responses.'
                ),
            )

            self.initialized = True
            logger.info('Jake Conversable Agent initialized successfully')
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
                'content': 'Jake is thinking...',
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
                
                print(f'Jake Agent Final result 1: {result}')
                # Get the summary which contains the output
                response = await result.summary
                print(f'Jake Agent Final response 2: {response}')
                
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

    def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Synchronous invocation of the MCP agent."""
        raise NotImplementedError(
            'Synchronous invocation is not supported by this agent. Use the streaming endpoint (tasks/sendSubscribe) instead.'
        )
