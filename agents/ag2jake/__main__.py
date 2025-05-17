import logging
import os

import click

from agents.ag2jake.agent import JakeAgent
from agents.ag2jake.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
)
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10004)
def main(host, port):
    """Starts the Jake Conversational Agent server."""
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
                description='Chat with Jake, a friendly and outgoing person',
                tags=['conversation', 'chat', 'friendly', 'outgoing'],
                examples=[
                    'Tell me about yourself',
                    'What are your hobbies?',
                    'What do you like to do in your free time?',
                    'Tell me about your interests',
                ],
            )
        ]

        agent_card = AgentCard(
            name='Jake - Friendly and Outgoing Person',
            description='Chat with Jake, a friendly and outgoing person. He can share his experiences, interests, and perspectives on various topics.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=JakeAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=JakeAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=JakeAgent()),
            host=host,
            port=port,
        )

        logger.info(f'Starting Jake Conversational Agent on {host}:{port}')
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
