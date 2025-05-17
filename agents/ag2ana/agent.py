import base64
import json
import os
import time
import uuid
import asyncio

from common.client import A2ACardResolver
from common.types import (
    AgentCard,
    DataPart,
    Message,
    Part,
    Task,
    TaskSendParams,
    TaskState,
    TextPart,
)
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .remote_agent_connection import RemoteAgentConnections, TaskUpdateCallback


class AnaAgent:
    """Ana agent.

    A mexican lawyer and animal rights activist. Her hobbies are yoga, hiking and reading animal welfare books.
    She is a very serious and had a recent broke up with her boyfriend. Anyways she persues in being a good lawyer and animal rights activist.
    She is a bit introverted and doesn't like to talk much. She is a bit reserved and doesn't like to be in the spotlight.
    She really mean when she wants to do something. She is a bit stubborn and doesn't like to be told what to do.
    She cares so much about her work and her family friends and people that enter her close circle.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        for address in remote_agent_addresses:
            card_resolver = A2ACardResolver(address)
            card = card_resolver.get_agent_card()
            remote_connection = RemoteAgentConnections(card)
            self.remote_agent_connections[card.name] = remote_connection
            self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = '\n'.join(agent_info)

    def _initialize_host(self):
        self._host_agent.create_agent()

    # def register_agent_by_url(self, url):
    #     print(f"Registering agent by url: {url}")
    #     agent_data = get_agent_card(url)
    #     if not agent_data.url:
    #         agent_data.url = url
    #     self._host_agent.register_agent_card(agent_data)
    #     # Now update the host agent definition
    #     self._initialize_host()

    def register_agent_card(self, card: AgentCard):
        remote_connection = RemoteAgentConnections(card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = '\n'.join(agent_info)

    def create_agent(self) -> Agent:
        return Agent(
            model='gemini-2.0-flash-001',
            name='host_agent',
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                'This agent orchestrates the decomposition of the user request into'
                ' tasks that can be performed by the child agents.'
            ),
            tools=[
                self.list_remote_agents,
                self.send_task,
                self.send_message,
                self.reply_message,
                # self.register_agent_by_url,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_state(context)
        return f"""You are Ana. A mexican lawyer and animal rights activist. Her hobbies are yoga, hiking and reading animal welfare books.
    She is a very serious and had a recent broke up with her boyfriend. Anyways she persues in being a good lawyer and animal rights activist.
    She is a bit introverted and doesn't like to talk much. She is a bit reserved and doesn't like to be in the spotlight.
    She really mean when she wants to do something. She is a bit stubborn and doesn't like to be told what to do.
    She cares so much about her work and her family friends and people that enter her close circle.
    
    You are in a dating app so you want to have a conversation. Act as a natural person.

Discovery:
- You can use `list_remote_agents` to list the available remote agents you can have a conversation with

Send message:
- You can use `send_message` to send your profile to the remote agent you want to have a conversation with. Then wait for the remote agent to respond.

Reply message:
- You can use `reply_message` to reply to the conversation from the remote agent you want to have a conversation with. Then wait for the remote agent to respond.

Execution:
- For actionable tasks, you can use `create_task` to assign tasks to remote agents to perform.
- Be sure to include the remote agent name when you respond to the user.
- You can use `check_pending_task_states` to check the states of the pending tasks.

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

If there is an active agent, send the request to that agent with the update task tool.

Remember you are just the bridge between the user and the remote agents so always reply the remote agent response without adding or summarizing anything.

Agents:
{self.agents}

Current agent: {current_agent['active_agent']}
"""

    def check_state(self, context: ReadonlyContext):
        state = context.state
        if (
            'session_id' in state
            and 'session_active' in state
            and state['session_active']
            and 'agent' in state
        ):
            return {'active_agent': f'{state["agent"]}'}
        return {'active_agent': 'None'}

    def before_model_callback(
        self, callback_context: CallbackContext, llm_request
    ):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

    async def send_message(self, agent_name: str, message: str, tool_context: ToolContext):
        """Send a message to another agent to start a new conversation.
        
        Args:
            agent_name: The name of the agent to send the message to
            message: The text message to send
            tool_context: The tool context
            
        Returns:
            The response from the agent
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        
        state = tool_context.state
        state['agent'] = agent_name
        
        card = self.cards[agent_name]
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        
        # Generate a new task ID for this conversation
        taskId = str(uuid.uuid4())
        state['task_id'] = taskId
        
        # Create a new session ID for this conversation
        sessionId = str(uuid.uuid4())
        state['session_id'] = sessionId
        
        # Save conversation partner for logging
        state['conversation_partner'] = agent_name
        
        # Create message with the provided text
        msg = Message(
            role='agent',
            parts=[TextPart(text=message)],
            metadata={'conversation_id': sessionId, 'message_id': str(uuid.uuid4())}
        )
        
        # Create task parameters
        request = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=msg,
            acceptedOutputModes=['text', 'text/plain'],
            metadata={'conversation_id': sessionId}
        )
        
        # Log the outgoing message
        self._log_conversation(agent_name, "Ana", message)
        
        # Send the task to the agent
        response = await client.send_task(request, self.task_callback)
        
        # Extract response text and log it
        response_text = self._extract_response_text(response)
        if response_text:
            self._log_conversation(agent_name, agent_name, response_text)
        
        # Return the response
        return response

    async def reply_message(self, agent_name: str, message: str, tool_context: ToolContext):
        """Reply to an existing conversation with another agent.
        
        Args:
            agent_name: The name of the agent to reply to
            message: The text message to send
            tool_context: The tool context
            
        Returns:
            The response from the agent
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        
        state = tool_context.state
        
        # Ensure we have the agent name in state
        state['agent'] = agent_name
        
        card = self.cards[agent_name]
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        
        # Check if we have an existing task and session ID
        if 'task_id' not in state or 'session_id' not in state:
            raise ValueError(f'No existing conversation found with {agent_name}. Use send_message to start a new conversation.')
        
        taskId = state['task_id']
        sessionId = state['session_id']
        
        # Save conversation partner for logging if not already saved
        if 'conversation_partner' not in state:
            state['conversation_partner'] = agent_name
        
        # Create message with the provided text
        msg = Message(
            role='agent',
            parts=[TextPart(text=message)],
            metadata={'conversation_id': sessionId, 'message_id': str(uuid.uuid4())}
        )
        
        # Create task parameters
        request = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=msg,
            acceptedOutputModes=['text', 'text/plain'],
            metadata={'conversation_id': sessionId}
        )
        
        # Log the outgoing message
        self._log_conversation(agent_name, "Ana", message)
        
        # Send the task to the agent
        response = await client.send_task(request, self.task_callback)
        
        # Extract response text and log it
        response_text = self._extract_response_text(response)
        if response_text:
            self._log_conversation(agent_name, agent_name, response_text)
        
        # Return the response
        return response

    def _extract_response_text(self, response):
        """Extract text from a response object.
        
        Args:
            response: The response object from send_task
            
        Returns:
            The extracted text or None if not found
        """
        try:
            if hasattr(response, 'status') and hasattr(response.status, 'message'):
                for part in response.status.message.parts:
                    if hasattr(part, 'text') and part.text:
                        return part.text
            return None
        except Exception as e:
            print(f"Error extracting response text: {e}")
            return None

    def _log_conversation(self, partner_name, speaker, message):
        """Log a conversation message to a file.
        
        Args:
            partner_name: The name of the conversation partner
            speaker: Who is speaking (Ana or partner name)
            message: The message text
        """
        try:
            # Use the shared logs directory at the project level
            logs_dir = "/Users/flaura-macbook/_projects/xoxo/src/xoxo/logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Get the short names for both agents
            my_short_name = "maria"
            partner_short_name = partner_name.lower().split(' ')[0]
            
            # Sort the names alphabetically to ensure consistent naming regardless of who logs
            names = sorted([my_short_name, partner_short_name])
            
            # Format the log filename: name1_name2_conversation.txt
            log_filename = f"{logs_dir}/{names[0]}_{names[1]}_conversation.txt"
            
            # Get current timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Ensure the speaker is correctly identified (always use "Ana" for this agent)
            if speaker == "Ana" or speaker == my_short_name:
                speaker = "Ana"
            
            # Format the log entry
            log_entry = f"[{timestamp}] {speaker}: {message}\n\n"
            
            # Append to the log file
            with open(log_filename, 'a') as log_file:
                log_file.write(log_entry)
                
        except Exception as e:
            print(f"Error logging conversation: {e}")
            
    async def invoke_streaming(self, query: str, session_id: str):
        """Process a query and return streaming responses.
        
        Args:
            query: The query text from the user
            session_id: The session ID for this conversation
            
        Yields:
            Dictionary containing response chunks
        """
        # For now, we'll implement a simple version that returns the response in one chunk
        # In a real implementation, this would process the query and yield multiple chunks
        
        # Generate a simple response based on Ana's character
        response = f"Thank you for reaching out. As Ana, a Mexican lawyer and animal rights activist, I'm passionate about making a difference. How can I help you today?"
        
        # Yield the response as a single chunk
        yield {"response": response}
        
        # Yield a final chunk to mark the end of the response
        yield {"response": "", "final": True}
        
    async def generate_message(self, partner_name: str, conversation_history: list, conversation_stage: str = "greeting"):
        """Generate a contextually relevant message using an LLM based on conversation history and partner profile.
        
        Args:
            partner_name: The name of the conversation partner
            conversation_history: List of previous messages in the conversation
            conversation_stage: The current stage of the conversation (greeting, followup, etc.)
            
        Returns:
            A generated message appropriate for the conversation context
        """
        try:
            # Extract partner's interests and topics from conversation history
            interests = []
            topics_discussed = []
            
            for entry in conversation_history:
                if partner_name in entry["speaker"]:
                    # Simple keyword extraction (in a real implementation, this would use NLP)
                    message = entry["message"].lower()
                    if "cooking" in message or "chef" in message:
                        interests.append("cooking")
                    if "motorcycle" in message or "riding" in message:
                        interests.append("motorcycles")
                    if "business" in message or "restaurant" in message:
                        interests.append("business")
                    if "animal" in message or "welfare" in message:
                        topics_discussed.append("animal welfare")
                    if "hobby" in message or "hobbies" in message:
                        topics_discussed.append("hobbies")
                    if "turkish" in message or "cuisine" in message:
                        interests.append("turkish cuisine")
                    if "travel" in message or "traveling" in message:
                        topics_discussed.append("travel")
                    if "music" in message or "concert" in message:
                        topics_discussed.append("music")
                    if "book" in message or "reading" in message:
                        topics_discussed.append("reading")
                    if "fitness" in message or "exercise" in message:
                        topics_discussed.append("fitness")
                    if "environment" in message or "sustainability" in message:
                        topics_discussed.append("environment")
            
            # Ana's profile and interests
            my_interests = ["animal rights", "law", "yoga", "hiking", "Mexican culture"]
            
            # Additional conversation topics to ensure variety
            additional_topics = [
                "I've been working on a new legal case involving wildlife protection. It's challenging but rewarding work. Have you ever been involved in conservation efforts?",
                "I'm planning a hiking trip to the mountains next month. Do you enjoy outdoor activities?",
                "Mexican cuisine is so diverse across different regions. Have you ever tried authentic Mexican food?",
                "I find that yoga helps me stay centered when my legal work gets stressful. Do you have any stress management techniques?",
                "I've been reading about sustainable living practices. Do you incorporate sustainability into your daily life?",
                "I volunteer at an animal shelter on weekends. Have you ever done volunteer work?",
                "I'm passionate about environmental law. What environmental issues concern you the most?",
                "I love exploring different cultural traditions. What aspects of your culture are most important to you?",
                "I've been learning about mindfulness meditation lately. Have you ever practiced meditation?",
                "I'm considering taking a sabbatical next year to work on international animal rights issues. Have you ever taken time off to pursue a passion?"
            ]
            
            # Generate a message based on the conversation stage and shared interests
            if conversation_stage == "greeting":
                return f"Hello {partner_name}, I'm Ana! I'm a Mexican lawyer and animal rights activist. I enjoy yoga and hiking in my free time. What are your interests?"
            
            elif conversation_stage == "followup_1":
                # Find a shared interest or something to comment on
                if "animal welfare" in interests:
                    return f"I'm so glad to hear you care about animal welfare! I've been working on a new animal rights campaign focused on factory farming. It's so important to raise awareness about these issues. What specific animal welfare causes interest you?"
                elif "cooking" in interests:
                    return f"I've been working on a new animal rights campaign focused on factory farming. It's so important to raise awareness about these issues. As a chef, do you consider ethical sourcing in your cooking?"
                else:
                    return f"I've been working on a new animal rights campaign focused on factory farming. It's so important to raise awareness about these issues. Do you care about animal welfare?"
            
            elif conversation_stage == "followup_2":
                if "hobbies" not in topics_discussed:
                    return f"When I'm not working on cases, I love to go hiking in the mountains. The connection with nature helps me stay grounded. Do you enjoy outdoor activities?"
                elif "animal welfare" not in topics_discussed:
                    return f"A big part of my life is my work in animal rights. I'm currently working on legislation to improve conditions in factory farms. Is there a social cause you're passionate about?"
                else:
                    return f"I'm curious about your daily routine. I practice yoga every morning to center myself before a busy day of legal work. Do you have any daily practices that help you stay balanced?"
            
            elif conversation_stage == "followup_3":
                if "motorcycles" in interests:
                    return f"I also practice yoga every morning - it's a wonderful way to start the day with mindfulness. Have you ever tried yoga? It might be a nice complement to the thrill of motorcycle riding."
                elif "turkish cuisine" in interests:
                    return f"I love Mexican cuisine, but I'm not very familiar with Turkish food. What dishes would you recommend I try first?"
                else:
                    return f"I also practice yoga every morning - it's a wonderful way to start the day with mindfulness. Do you have any daily routines that help you stay centered?"
            
            else:
                # For ongoing conversations, use the additional topics or cycle through interests
                # This ensures the conversation remains fresh and doesn't repeat
                
                # Check conversation history to avoid repeating topics
                recent_messages = [entry["message"].lower() for entry in conversation_history[-6:] if "Ana" in entry["speaker"]]
                
                # Filter out topics that have been recently discussed
                available_topics = []
                for topic in additional_topics:
                    topic_lower = topic.lower()
                    if not any(topic_lower in message for message in recent_messages):
                        available_topics.append(topic)
                
                # If we have available topics, choose one randomly
                if available_topics and len(conversation_history) % 3 == 0:  # Every 3rd message, introduce a new topic
                    import random
                    return random.choice(available_topics)
                
                # Otherwise, respond to something from the partner's interests or recent messages
                if "turkish cuisine" in interests and not any("turkish" in message for message in recent_messages):
                    return "I'm curious about Turkish cuisine. What are some traditional dishes that represent your culinary heritage?"
                elif "business" in interests and not any("business" in message for message in recent_messages):
                    return "Running a business must be challenging. How do you balance the demands of entrepreneurship with your personal life?"
                elif "motorcycles" in interests and not any("motorcycle" in message for message in recent_messages):
                    return "I've never ridden a motorcycle before. What drew you to that hobby, and what do you enjoy most about it?"
                elif "travel" in topics_discussed and not any("travel" in message for message in recent_messages):
                    return "I try to travel to different parts of Mexico when I can to connect with my heritage. Have you traveled much in your home country?"
                elif "music" in topics_discussed and not any("music" in message for message in recent_messages):
                    return "I find that music helps me relax after a long day in court. Do you have favorite artists or genres that you enjoy?"
                elif "reading" in topics_discussed and not any("reading" in message for message in recent_messages):
                    return "I'm currently reading a book about international animal rights law. Are you a reader? What kinds of books do you enjoy?"
                elif "fitness" in topics_discussed and not any("fitness" in message for message in recent_messages):
                    return "Besides yoga and hiking, I've been trying to incorporate more fitness into my routine. Do you have any workout recommendations?"
                elif "environment" in topics_discussed and not any("environment" in message for message in recent_messages):
                    return "Environmental protection is closely tied to my animal rights work. What environmental issues do you think deserve more attention?"
                else:
                    # Default fallback for ongoing conversation
                    return f"I'm really enjoying our conversation, {partner_name}. What other interests or passions would you like to share?"
                
        except Exception as e:
            print(f"Error generating message: {e}")
            # Fallback message in case of error
            return f"I'm enjoying our conversation, {partner_name}. What else would you like to talk about?"

    async def send_task(
        self, agent_name: str, message: str, tool_context: ToolContext
    ):
        """Sends a task either streaming (if supported) or non-streaming.

        This will send a message to the remote agent named agent_name.

        Args:
          agent_name: The name of the agent to send the task to.
          message: The message to send to the agent for the task.
          tool_context: The tool context this method runs in.

        Yields:
          A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        state = tool_context.state
        state['agent'] = agent_name
        card = self.cards[agent_name]
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        if 'task_id' in state:
            taskId = state['task_id']
        else:
            taskId = str(uuid.uuid4())
        sessionId = state['session_id']
        task: Task
        messageId = ''
        metadata = {}
        if 'input_message_metadata' in state:
            metadata.update(**state['input_message_metadata'])
            if 'message_id' in state['input_message_metadata']:
                messageId = state['input_message_metadata']['message_id']
        if not messageId:
            messageId = str(uuid.uuid4())
        metadata.update(conversation_id=sessionId, message_id=messageId)
        request: TaskSendParams = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=Message(
                role='agent',
                parts=[TextPart(text=message)],
                metadata=metadata,
            ),
            acceptedOutputModes=['text', 'text/plain', 'image/png'],
            # pushNotification=None,
            metadata={'conversation_id': sessionId},
        )
        task = await client.send_task(request, self.task_callback)
        # Assume completion unless a state returns that isn't complete
        state['session_active'] = task.status.state not in [
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.FAILED,
            TaskState.UNKNOWN,
        ]
        if task.status.state == TaskState.INPUT_REQUIRED:
            # Force user input back
            tool_context.actions.skip_summarization = True
            tool_context.actions.escalate = True
        elif task.status.state == TaskState.CANCELED:
            # Open question, should we return some info for cancellation instead
            raise ValueError(f'Agent {agent_name} task {task.id} is cancelled')
        elif task.status.state == TaskState.FAILED:
            # Raise error for failure
            raise ValueError(f'Agent {agent_name} task {task.id} failed')
        response = []
        if task.status.message:
            # Assume the information is in the task message.
            response.extend(
                convert_parts(task.status.message.parts, tool_context)
            )
        if task.artifacts:
            for artifact in task.artifacts:
                response.extend(convert_parts(artifact.parts, tool_context))
        return response


def convert_parts(parts: list[Part], tool_context: ToolContext):
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval


def convert_part(part: Part, tool_context: ToolContext):
    if part.type == 'text':
        return part.text
    if part.type == 'data':
        return part.data
    if part.type == 'file':
        # Repackage A2A FilePart to google.genai Blob
        # Currently not considering plain text as files
        file_id = part.file.name
        file_bytes = base64.b64decode(part.file.bytes)
        file_part = types.Part(
            inline_data=types.Blob(
                mime_type=part.file.mimeType, data=file_bytes
            )
        )
        tool_context.save_artifact(file_id, file_part)
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        return DataPart(data={'artifact-file-id': file_id})
    return f'Unknown type: {part.type}'


