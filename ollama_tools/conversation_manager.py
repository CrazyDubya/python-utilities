# llm_toolbox/core/conversation_manager.py

class ConversationManager:
    def __init__(self, ollama_client, data_store):
        self.ollama_client = ollama_client
        self.data_store = data_store
        self.conversations = {}

    async def process_message(self, conversation_id, model, messages, **kwargs):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].extend(messages)
        
        context = kwargs.pop('context', None)
        if context:
            kwargs['context'] = context
        
        response = await self.ollama_client.chat(model, self.conversations[conversation_id], **kwargs)
        
        if isinstance(response, str):
            self.conversations[conversation_id].append({"role": "assistant", "content": response})
        elif isinstance(response, dict) and 'message' in response:
            self.conversations[conversation_id].append(response['message'])
        
        # Store the updated conversation
        self.data_store.save_conversation(conversation_id, self.conversations[conversation_id])
        
        return response

    def get_conversation_context(self, conversation_id):
        return self.conversations.get(conversation_id, [])
