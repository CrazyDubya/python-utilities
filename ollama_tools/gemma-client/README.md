# Enhanced Long-Gemma

A sophisticated interactive interface for the Long-Gemma LLM through Ollama, featuring:

![Enhanced Long-Gemma TUI](https://i.imgur.com/NcxCv8M.png)

## Features

- 🧠 **Advanced Memory System**
  - Short-term conversation history
  - Long-term persistent memory for facts and preferences
  - Emotional memory tracking
  - Memory associations and relevance tracking

- 🎭 **Rich Personality Framework**
  - Configurable personality traits affecting response style
  - Character backstory and identity
  - Dynamic emotional states that change with conversation
  - Quirks and preferences that shape interactions

- 💭 **Private Thought Chains**
  - Internal thought processes displayed alongside responses
  - Tangential ideas and associations
  - Shows Gemma's "thinking" beyond direct answers

- 📊 **Beautiful TUI Interface**
  - Split-panel design showing conversation and memory
  - Real-time emotional state display
  - Personality profile view
  - Relevant memory display

## Getting Started

### Prerequisites

- Python 3.6+
- Ollama with long-gemma model installed
- Ollama server running on localhost:11434
- Rich library for TUI (optional but recommended): `pip install rich`

### Usage

```bash
# Install rich for the best experience
pip install rich

# Run in interactive mode with TUI
./gemma_enhanced.py

# Run with a single query (without interactive mode)
./gemma_enhanced.py "Tell me about quantum computing"
```

## Interactive Commands

The system supports many special commands:

### Memory Management

```
memory:fact category:content:importance   # Add a fact to long-term memory
memory:search keyword                     # Search memories for a keyword
```

Example:
```
memory:fact user_preference:Likes science fiction books:8
memory:search science
```

### Personality Management

```
personality:trait name:value      # Adjust personality trait (scale 1-10)
personality:interest new interest # Add a new interest
personality:value new value       # Add a new value
personality:quirk new quirk       # Add a new personality quirk
```

Examples:
```
personality:trait humor:9
personality:quirk Obsessed with unusual metaphors
```

### Emotional State

```
emotions:set emotion:intensity    # Set emotional state (scale 1-10)
```

Supported emotions: neutral, happy, excited, curious, thoughtful, confused, concerned

Example:
```
emotions:set excited:8
```

### Thought Process

```
thoughts:show                     # Toggle showing private thoughts
```

## Personality System

The personality framework includes:

- **Identity**: Character backstory, self-image, and preferences
- **Traits**: Configurable parameters (1-10 scale) affecting response style
  - Friendliness, humor, formality, creativity, helpfulness, etc.
- **Quirks**: Unique characteristics that give Gemma personality
- **Values**: Core principles and ethics
- **Emotional States**: Dynamic moods that shift during conversation

## Architecture

- **MemorySystem**: SQLite database storing different types of memories
- **PersonalitySystem**: Manages traits, identity, and communication style
- **ThoughtChainGenerator**: Creates private thought processes
- **UIManager**: Handles the rich TUI interface
- **GemmaEnhanced**: Main class coordinating all components

## License

MIT