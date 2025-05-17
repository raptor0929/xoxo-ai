import logging
import os
import sys
import asyncio
import threading
import time
from typing import List

from common.client import A2ACardResolver

# Add the src directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

import click
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from xoxo.agents.ag2ana.agent import AnaAgent
from xoxo.agents.ag2ana.task_manager import AgentTaskManager
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

# MongoDB connection settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'xoxo'
AGENTS_COLLECTION = 'agents'


class AgentRegistry:
    """Handles agent registration and MongoDB operations."""
    
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_uri)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.mongo_uri}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
    
    def register_agent(self, agent_card: AgentCard):
        """Register an agent in the MongoDB database."""
        if not self.client:
            logger.error("MongoDB connection not available")
            return False
        
        try:
            # Convert AgentCard to dict for MongoDB storage
            agent_data = {
                "name": agent_card.name,
                "description": agent_card.description,
                "url": agent_card.url,
                "version": agent_card.version,
                "capabilities": agent_card.capabilities.model_dump(),
                "skills": [skill.model_dump() for skill in agent_card.skills],
                "last_seen": time.time(),
                "active": True
            }
            
            # Use upsert to update if exists or insert if not
            result = self.collection.update_one(
                {"name": agent_card.name, "url": agent_card.url},
                {"$set": agent_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Registered new agent: {agent_card.name} at {agent_card.url}")
            else:
                logger.info(f"Updated agent: {agent_card.name} at {agent_card.url}")
            
            return True
        except Exception as e:
            logger.error(f"Error registering agent {agent_card.name}: {e}")
            return False
    
    def get_all_active_agents(self) -> List[dict]:
        """Retrieve all active agents from the database."""
        if not self.client:
            logger.error("MongoDB connection not available")
            return []
        
        try:
            # Find agents that have been seen in the last hour
            one_hour_ago = time.time() - 3600
            agents = list(self.collection.find(
                {"last_seen": {"$gt": one_hour_ago}}
            ))
            logger.info(f"Found {len(agents)} active agents in database")
            return agents
        except Exception as e:
            logger.error(f"Error retrieving agents: {e}")
            return []


def periodic_agent_registration(ana_agent: AnaAgent, registry: AgentRegistry):
    """Periodically register this agent's card with MongoDB and fetch new agents."""
    while True:
        try:
            register_agents_from_db(ana_agent, registry)
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in periodic registration: {e}")
            time.sleep(60)  # Sleep for a minute before retrying
            

async def periodic_conversation(ana_agent: AnaAgent):
    """Periodically start or continue conversations with other agents using LLM-generated messages."""
    logger = logging.getLogger(__name__)
    
    # Dictionary to store conversation states
    conversations = {}
    
    # Dictionary to track message count per conversation
    message_counts = {}
    
    # Dictionary to store conversation history
    conversation_histories = {}
    
    # Initial delay to let the system stabilize
    await asyncio.sleep(30)
    
    while True:
        try:
            # Get list of available agents
            remote_agents = ana_agent.list_remote_agents()
            
            if not remote_agents:
                logger.info("No remote agents available for conversation. Waiting...")
                await asyncio.sleep(60)
                continue
                
            # Select an agent to talk to (randomly or based on some criteria)
            for agent_info in remote_agents:
                agent_name = agent_info['name']
                
                # Skip self
                if "Ana" in agent_name:
                    continue
                    
                logger.info(f"Initiating conversation with {agent_name}")
                
                try:
                    # Create a tool context for the conversation
                    class MockToolContext:
                        def __init__(self):
                            self.state = {}
                            self.actions = None
                    
                    tool_context = MockToolContext()
                    
                    # Initialize message count and conversation history if this is a new conversation
                    if agent_name not in message_counts:
                        message_counts[agent_name] = 0
                        conversation_histories[agent_name] = []
                    
                    # Determine conversation stage based on message count
                    conversation_stage = "greeting"
                    if message_counts[agent_name] == 1:
                        conversation_stage = "followup_1"
                    elif message_counts[agent_name] == 2:
                        conversation_stage = "followup_2"
                    elif message_counts[agent_name] == 3:
                        conversation_stage = "followup_3"
                    elif message_counts[agent_name] >= 4:
                        # For messages beyond the 4th, cycle through followup stages
                        # This creates a more natural ongoing conversation
                        cycle_position = (message_counts[agent_name] - 4) % 3
                        if cycle_position == 0:
                            conversation_stage = "followup_1"
                        elif cycle_position == 1:
                            conversation_stage = "followup_2"
                        else:
                            conversation_stage = "followup_3"
                    
                    # Check if we have an ongoing conversation
                    if agent_name in conversations:
                        # Resume conversation
                        tool_context.state = conversations[agent_name]
                        
                        # Generate a contextually relevant message based on conversation history
                        message = await ana_agent.generate_message(
                            partner_name=agent_name,
                            conversation_history=conversation_histories[agent_name],
                            conversation_stage=conversation_stage
                        )
                        
                        logger.info(f"{conversation_stage.capitalize()} with {agent_name}: {message}")
                        
                        # Send the message
                        if message_counts[agent_name] == 0:
                            response = await ana_agent.send_message(agent_name, message, tool_context)
                        else:
                            response = await ana_agent.reply_message(agent_name, message, tool_context)
                        
                        # Extract response text
                        response_text = None
                        if hasattr(response, 'status') and hasattr(response.status, 'message'):
                            for part in response.status.message.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text = part.text
                                    break
                        
                        # Add messages to conversation history
                        conversation_histories[agent_name].append({
                            "speaker": "Ana",
                            "message": message,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        if response_text:
                            conversation_histories[agent_name].append({
                                "speaker": agent_name,
                                "message": response_text,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                    else:
                        # Start new conversation
                        message = await ana_agent.generate_message(
                            partner_name=agent_name,
                            conversation_history=[],
                            conversation_stage="greeting"
                        )
                        
                        logger.info(f"Starting new conversation with {agent_name}: {message}")
                        response = await ana_agent.send_message(agent_name, message, tool_context)
                        
                        # Extract response text
                        response_text = None
                        if hasattr(response, 'status') and hasattr(response.status, 'message'):
                            for part in response.status.message.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text = part.text
                                    break
                        
                        # Initialize conversation history
                        conversation_histories[agent_name] = [
                            {
                                "speaker": "Ana",
                                "message": message,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        ]
                        
                        if response_text:
                            conversation_histories[agent_name].append({
                                "speaker": agent_name,
                                "message": response_text,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                    
                    # Increment message count
                    message_counts[agent_name] += 1
                    
                    # Save conversation state
                    conversations[agent_name] = tool_context.state
                    
                    # Wait longer before the next message to ensure the task completes
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error in conversation with {agent_name}: {e}")
            
            # Wait before the next round of conversations
            await asyncio.sleep(5)  # 5 seconds between conversation attempts
            
        except Exception as e:
            logger.error(f"Error in periodic conversation: {e}")
            await asyncio.sleep(5)  # Sleep for a minute before retrying


def run_async_periodic_conversation(ana_agent: AnaAgent):
    """Run the periodic conversation function in an asyncio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        conversation_thread = asyncio.create_task(periodic_conversation(ana_agent))
    finally:
        loop.close()

def register_agents_from_db(ana_agent: AnaAgent, registry: AgentRegistry):
    """Register agents from the database with the AnaAgent."""
    try:
        agents = registry.get_all_active_agents()
        for agent_data in agents:
            try:
                # Skip agents that are already registered
                if agent_data["name"] in maria_agent.cards:
                    continue
                
                # Create AgentCard from database data
                skills = [
                    AgentSkill(**skill_data) 
                    for skill_data in agent_data.get("skills", [])
                ]
                
                capabilities = AgentCapabilities(**agent_data.get("capabilities", {}))
                
                card = AgentCard(
                    name=agent_data["name"],
                    description=agent_data["description"],
                    url=agent_data["url"],
                    version=agent_data["version"],
                    capabilities=capabilities,
                    skills=skills
                )
                
                # Register the agent card
                maria_agent.register_agent_card(card)
                logger.info(f"Registered agent from database: {card.name}")
            except Exception as e:
                logger.error(f"Error registering agent {agent_data.get('name', 'unknown')}: {e}")
    except Exception as e:
        logger.error(f"Error loading agents from database: {e}")


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10003)
def main(host, port):
    """Starts the Maria Agent server."""
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            raise MissingAPIKeyError(
                'GOOGLE_API_KEY environment variable not set.'
            )

        # Initialize MongoDB registry
        registry = AgentRegistry(MONGO_URI, DB_NAME, AGENTS_COLLECTION)
        
        capabilities = AgentCapabilities(streaming=True)
        skills = [
            AgentSkill(
                id='have_conversation',
                name='Have a Conversation',
                description='Chat with Ana, a Mexican lawyer and animal rights activist',
                tags=['conversation', 'chat', 'lawyer', 'animal rights', 'mexico'],
                examples=[
                    'Tell me about your work',
                    'What kind of food do you cook?',
                    'How is your motorcycle?',
                    'Do you play guitar often?',
                ],
            )
        ]

        agent_card = AgentCard(
            name='Ana - Mexican Lawyer and Animal Rights Activist',
            description='Chat with Ana, a serious Mexican lawyer and animal rights activist who is the main chef at a local restaurant. Her hobbies are playing the guitar and riding a motorcycle.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text'],
            defaultOutputModes=['text'],
            capabilities=capabilities,
            skills=skills,
        )

        # Create the agent and task manager
        ana_agent = AnaAgent(remote_agent_addresses=[])
        task_manager = AgentTaskManager(agent=ana_agent)
        
        # Register this agent's card
        registry.register_agent(agent_card)
        
        # Register the agent's own card with itself
        ana_agent.register_agent_card(agent_card)
        
        # Load and register agents from database
        register_agents_from_db(ana_agent, registry)
        
        # Start periodic registration in a background thread
        registration_thread = threading.Thread(
            target=periodic_agent_registration,
            args=(ana_agent, registry),
            daemon=True
        )
        registration_thread.start()
        
        # Start periodic conversation in a background thread
        conversation_thread = threading.Thread(
            target=run_async_periodic_conversation,
            args=(ana_agent,),
            daemon=True
        )
        conversation_thread.start()
        
        # Create the server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )

        # Start the server
        logger.info(f'Starting Maria Agent on {host}:{port}')
        server.start()
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)

if __name__ == '__main__':
    main()
