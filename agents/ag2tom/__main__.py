import logging
import os
import sys

from common.client import A2ACardResolver

# Add the src directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

import click

from xoxo.agents.ag2tom.agent import TomAgent
from xoxo.agents.ag2tom.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
    Message,
)
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10003)
def main(host, port):
    """Starts the Tom Conversational Agent server."""
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            raise MissingAPIKeyError(
                'GOOGLE_API_KEY environment variable not set.'
            )

        capabilities = AgentCapabilities(streaming=True)
        skills = [
            AgentSkill(
                id='have_conversation',
                name='Have a Conversation',
                description='Chat with Tom, a Turkish chef and businessman',
                tags=['conversation', 'chat', 'cooking', 'turkish', 'chef', 'restaurant', 'business'],
                examples=[
                    'Tell me about your restaurant',
                    'What Turkish dishes do you specialize in?',
                    'How do you balance running a restaurant with your other interests?',
                    'Tell me about your motorcycle rides along the coast',
                ],
            )
        ]

        agent_card = AgentCard(
            name='Tom - Turkish Chef and Businessman',
            description='Chat with Tom, a Turkish chef and businessman who owns a restaurant. He can share his culinary expertise, business insights, and experiences with occasional Turkish expressions.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=TomAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=TomAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        # Create the agent and task manager
        tom_agent = TomAgent()
        task_manager = AgentTaskManager(agent=tom_agent)
        
        # Create the server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )

        # Start the server
        logger.info(f'Starting Tom Conversational Agent on {host}:{port}')
        server.start()
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)

if __name__ == '__main__':
    main()
