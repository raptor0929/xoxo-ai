import asyncio
import logging
import traceback
import sys
import os

# Add the parent directory to sys.path to make imports work
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from collections.abc import AsyncIterable

from common.server import utils
from common.server.task_manager import InMemoryTaskManager
from common.types import (
    Artifact,
    InternalError,
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from .agent import AnaAgent


logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    """Task manager for Ana conversational agent."""

    def __init__(self, agent: AnaAgent):
        super().__init__()
        self.agent = agent

    # -------------------------------------------------------------
    # Public API methods
    # -------------------------------------------------------------

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handle synchronous task requests.

        This method processes one-time task requests and returns a complete response.
        Unlike streaming tasks, this waits for the full agent response before returning.
        """
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        await self.upsert_task(request.params)
        # Update task store to WORKING state (return value not used)
        await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )

        task_send_params: TaskSendParams = request.params
        query = self._extract_user_query(task_send_params)

        try:
            agent_response = self.agent.invoke(
                query, task_send_params.sessionId
            )
            return await self._handle_send_task(request, agent_response)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            return SendTaskResponse(
                id=request.id,
                error=InternalError(
                    message=f'Error during on_send_task: {e!s}'
                ),
            )

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """Handle streaming task requests with SSE subscription.

        This method initiates a streaming task and returns incremental updates
        to the client as they become available. It uses Server-Sent Events (SSE)
        to push updates to the client as the agent generates them.
        """
        try:
            error = self._validate_request(request)
            if error:
                return error

            await self.upsert_task(request.params)

            task_send_params: TaskSendParams = request.params
            sse_event_queue = await self.setup_sse_consumer(
                task_send_params.id, False
            )

            asyncio.create_task(self._handle_send_task_streaming(request))

            return self.dequeue_events_for_sse(
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f'Error in SSE stream: {e}')
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while streaming the response'
                ),
            )

    # -------------------------------------------------------------
    # Agent response handlers
    # -------------------------------------------------------------

    async def _handle_send_task(
        self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """Handle the 'tasks/send' JSON-RPC method by processing agent response.

        This method processes the synchronous (one-time) response from the agent,
        transforms it into the appropriate task status and artifacts, and
        returns a complete SendTaskResponse.
        """
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id

        # Create a message with the agent's response
        message = Message(
            role='assistant',
            parts=[TextPart(text=agent_response['response'])],
        )

        # Create an artifact with the response
        artifact = Artifact(
            parts=[TextPart(text=agent_response['response'])],
            index=0,
            append=False,
        )

        # Update task store (return value not used)
        task_status = TaskStatus(
            state=TaskState.COMPLETED, message=message
        )
        await self.update_store(task_id, task_status, [artifact])

        # Return the response
        return SendTaskResponse(
            id=request.id,
            result=utils.task_with_artifacts(
                task_id,
                task_send_params.sessionId,
                task_status,
                [artifact],
                [task_send_params.message],
            ),
        )

    async def _handle_send_task_streaming(
        self, request: SendTaskStreamingRequest
    ) -> None:
        """Handle the 'tasks/sendSubscribe' JSON-RPC method for streaming responses.

        This method processes streaming responses from the agent incrementally,
        converting each chunk into appropriate SSE events for real-time client updates.
        It handles different agent response states (working, input required, completed)
        and generates both status update and artifact events.
        """
        task_send_params: TaskSendParams = request.params
        query = self._extract_user_query(task_send_params)

        try:
            # First send WORKING status update
            logger.info(
                f'Sending initial WORKING status for task {task_send_params.id}'
            )
            task_status = TaskStatus(state=TaskState.WORKING)
            await self.update_store(task_send_params.id, task_status, None)
            task_update_event = TaskStatusUpdateEvent(
                id=task_send_params.id, status=task_status
            )
            await self.enqueue_events_for_sse(
                task_send_params.id, task_update_event
            )

            # Invoke agent and process response
            async for chunk in self.agent.invoke_streaming(
                query, task_send_params.sessionId
            ):
                # Process each chunk from the agent
                parts = [TextPart(text=chunk['response'])]
                message = Message(role='agent', parts=parts)
                artifact = None
                task_state = TaskState.WORKING
                end_stream = False

                if chunk.get('final', False):
                    # Check if we need user input
                    if chunk.get('input_required', False):
                        task_state = TaskState.INPUT_REQUIRED
                        end_stream = True
                        logger.info('Sending INPUT_REQUIRED status update (final)')
                    else:
                        # Task completed - completed state with artifact
                        task_state = TaskState.COMPLETED
                        artifact = Artifact(parts=parts, index=0, append=False)
                        end_stream = True
                        logger.info(
                            'Sending COMPLETED status with artifact (final)'
                        )

                # Update task store (return value not used)
                task_status = TaskStatus(state=task_state, message=message)
                await self.update_store(
                    task_send_params.id,
                    task_status,
                    None if artifact is None else [artifact],
                )

                # First send artifact if we have one
                if artifact:
                    logger.info(
                        f'Sending artifact event for task {task_send_params.id}'
                    )
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=task_send_params.id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        task_send_params.id, task_artifact_update_event
                    )

                # Then send status update
                logger.info(
                    f'Sending status update for task {task_send_params.id}, state={task_state}, final={end_stream}'
                )
                task_update_event = TaskStatusUpdateEvent(
                    id=task_send_params.id, status=task_status, final=end_stream
                )
                await self.enqueue_events_for_sse(
                    task_send_params.id, task_update_event
                )

        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            logger.error(traceback.format_exc())
            await self.enqueue_events_for_sse(
                task_send_params.id,
                InternalError(
                    message=f'An error occurred while streaming the response: {e}'
                ),
            )

    # -------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------

    def _validate_request(
        self, request: SendTaskRequest | SendTaskStreamingRequest
    ) -> JSONRPCResponse | None:
        """Validate task request parameters for compatibility with agent capabilities.

        Ensures that the client's requested output modalities are compatible with
        what the agent can provide.

        Returns:
            JSONRPCResponse with an error if validation fails, None otherwise.
        """
        task_send_params: TaskSendParams = request.params
        # Define supported content types for AnaAgent
        SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
        
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes,
            SUPPORTED_CONTENT_TYPES,
        ):
            logger.warning(
                'Unsupported output mode. Received %s, Support %s',
                task_send_params.acceptedOutputModes,
                SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        return None

    def _extract_user_query(self, task_send_params: TaskSendParams) -> str:
        """Extract the user's text query from the task parameters.

        Extracts and returns the text content from the first part of the user's message.
        Currently only supports text parts.

        Args:
            task_send_params: The parameters of the task containing the user's message.

        Returns:
            str: The extracted text query.

        Raises:
            ValueError: If the message part is not a TextPart.
        """
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text
