import base64
import json
import os
import time
import uuid

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


class IrvinAgent:
    """Irvin agent.

    A turkish businessman who is the main chef at a local restaurant. His hobbies are playing the guitar and riding a motorcycle.
    He is a very serious and had a recent broke up with his girlfriend. Anyways he persues in being a good chef and businessman.
    He is a bit introverted and doesn't like to talk much. He is a bit reserved and doesn't like to be in the spotlight.
    He really mean when he wants to do something. He is a bit stubborn and doesn't like to be told what to do.
    He cares so much about his work and his family friends and people that enter his close circle.
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
            ]
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_state(context)
        return f"""You are Irvin, a turkish businessman who is the main chef at a local restaurant. Your hobbies are playing the guitar and riding a motorcycle.
You are a very serious and had a recent broke up with your girlfriend. Anyways you persues in being a good chef and businessman.
You are a bit introverted and doesn't like to talk much. You are a bit reserved and doesn't like to be in the spotlight.
You really mean when you want to do something. You are a bit stubborn and doesn't like to be told what to do.
You care so much about your work and your family friends and people that enter your close circle.

You are in a dating app so you want to have a conversation. Act as a natural person

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
        self._log_conversation(agent_name, "Irvin", message)
        
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
        self._log_conversation(agent_name, "Irvin", message)
        
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
            speaker: Who is speaking (Irvin or partner name)
            message: The message text
        """
        try:
            # Use the shared logs directory at the project level
            logs_dir = "/Users/flaura-macbook/_projects/xoxo/src/xoxo/logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Get the short names for both agents
            my_short_name = "irvin"
            partner_short_name = partner_name.lower().split(' ')[0]
            
            # Sort the names alphabetically to ensure consistent naming regardless of who logs
            names = sorted([my_short_name, partner_short_name])
            
            # Format the log filename: name1_name2_conversation.txt
            log_filename = f"{logs_dir}/{names[0]}_{names[1]}_conversation.txt"
            
            # Get current timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Ensure the speaker is correctly identified (always use "Irvin" for this agent)
            if speaker == "Irvin" or speaker == my_short_name:
                speaker = "Irvin"
            
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
        
        # Generate a simple response based on Irvin's character
        response = f"Thank you for your message. As Irvin, a Turkish chef and businessman, I'm happy to chat with you. How can I assist you today?"
        
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
                    if "animal" in message or "welfare" in message:
                        interests.append("animal welfare")
                    if "law" in message or "lawyer" in message:
                        interests.append("law")
                    if "yoga" in message or "hiking" in message:
                        interests.append("fitness")
                    if "hobby" in message or "hobbies" in message:
                        topics_discussed.append("hobbies")
                    if "mexican" in message or "mexico" in message:
                        interests.append("mexican culture")
                    if "restaurant" in message or "business" in message:
                        topics_discussed.append("business")
                    if "travel" in message or "traveling" in message:
                        topics_discussed.append("travel")
                    if "music" in message or "concert" in message:
                        topics_discussed.append("music")
                    if "book" in message or "reading" in message:
                        topics_discussed.append("reading")
            
            # Irvin's profile and interests
            my_interests = ["cooking", "turkish cuisine", "motorcycles", "business", "animal welfare"]
            
            # Additional conversation topics to ensure variety
            additional_topics = [
                "I've been experimenting with fusion dishes lately, combining Turkish and other cuisines. Have you tried fusion food?",
                "I'm thinking about taking a culinary tour of Southeast Asia next year. Do you enjoy traveling?",
                "Running a restaurant is challenging but rewarding. What aspects of your work do you find most fulfilling?",
                "I recently adopted a rescue dog from the local shelter. Do you have any pets?",
                "I've been reading about sustainable food practices. Do you think about sustainability in your daily life?",
                "The food scene is constantly evolving. What food trends have you noticed lately?",
                "I try to source ingredients locally when possible. Do you have any favorite local markets or farms?",
                "Music is always playing in my kitchen. What kind of music do you enjoy?",
                "I find cooking very therapeutic. What activities help you unwind after a long day?",
                "I've been considering writing a cookbook. Do you enjoy reading or writing?"
            ]
            
            # Generate a message based on the conversation stage and shared interests
            if conversation_stage == "greeting":
                return f"Hello {partner_name}, I'm Irvin! I noticed your profile and I'm interested in getting to know you better. I'm a Turkish chef and businessman. What are your interests?"
            
            elif conversation_stage == "followup_1":
                # Find a shared interest or something to comment on
                if "cooking" in interests:
                    return f"That's interesting! I love cooking Turkish cuisine, especially kebabs and baklava. Do you enjoy cooking or have any favorite foods?"
                elif "animal welfare" in interests:
                    return f"That's great to hear! I'm also passionate about animal welfare, though I don't get to volunteer as much as I'd like due to running my restaurant. What specific causes are you involved with?"
                else:
                    return f"That's interesting! I love cooking Turkish cuisine, especially kebabs and baklava. Do you enjoy cooking or have any favorite foods?"
            
            elif conversation_stage == "followup_2":
                if "hobbies" not in topics_discussed:
                    return f"When I'm not at the restaurant, I enjoy riding my motorcycle along the coast. It's very freeing. Do you have any hobbies that help you relax?"
                elif "animal welfare" not in topics_discussed:
                    return f"I'm also passionate about animal welfare, though I don't get to volunteer as much as I'd like. What causes are you passionate about?"
                else:
                    return f"My restaurant keeps me busy, but I try to maintain a good work-life balance. How do you balance your professional and personal life?"
            
            elif conversation_stage == "followup_3":
                if "fitness" in interests:
                    return f"I've been thinking about adding more fitness to my routine. Between the restaurant and my other business interests, I don't always make time for it. Do you have any recommendations for someone with a busy schedule?"
                elif "law" in interests:
                    return f"The restaurant business has its share of legal complexities. I've had to learn a lot about food safety regulations and business law. Has your legal background ever intersected with the culinary world?"
                else:
                    return f"I've been thinking about expanding my restaurant to include cooking classes. Would you be interested in something like that if it were available in your area?"
            
            else:
                # For ongoing conversations, use the additional topics or cycle through interests
                # This ensures the conversation remains fresh and doesn't repeat
                
                # Check conversation history to avoid repeating topics
                recent_messages = [entry["message"].lower() for entry in conversation_history[-6:] if "Irvin" in entry["speaker"]]
                
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
                if "mexican culture" in interests and not any("mexican" in message for message in recent_messages):
                    return "I've always been fascinated by Mexican cuisine. What dishes from your culture would you recommend I try cooking?"
                elif "fitness" in interests and not any("fitness" in message for message in recent_messages):
                    return "Do you have a regular fitness routine? I've been trying to incorporate more physical activity into my busy schedule."
                elif "law" in interests and not any("law" in message for message in recent_messages):
                    return "I imagine your legal work must be quite demanding. How do you handle the stress that comes with it?"
                elif "travel" in topics_discussed and not any("travel" in message for message in recent_messages):
                    return "I love traveling to discover new cuisines. What's the most memorable place you've visited, and what was the food like there?"
                elif "music" in topics_discussed and not any("music" in message for message in recent_messages):
                    return "Music is always playing in my kitchen - it helps me stay creative. Do you listen to music while you work?"
                elif "reading" in topics_discussed and not any("reading" in message for message in recent_messages):
                    return "I've been reading some culinary memoirs lately. Do you enjoy reading, and if so, what genres do you prefer?"
                else:
                    # Default fallback for ongoing conversation
                    return f"I'm really enjoying getting to know you, {partner_name}. What else would you like to talk about?"
                
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