#!/usr/bin/env python3
import requests
import json
import sys
import os
import datetime
import sqlite3
import time
import random
import textwrap
import threading
import queue
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

try:
    import rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("For the best experience, install rich: pip install rich")

# ANSI colors for systems without rich
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class EmotionalState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    CONFUSED = "confused"
    CONCERNED = "concerned"

class MemorySystem:
    def __init__(self, db_path="gemma_memory.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database for storing memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Short-term memory table (recent interactions)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_input TEXT,
            ai_response TEXT,
            private_thoughts TEXT
        )
        ''')
        
        # Long-term memory table (important facts, preferences)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            category TEXT,
            content TEXT,
            importance INTEGER,
            last_accessed TEXT,
            access_count INTEGER DEFAULT 0
        )
        ''')
        
        # Emotional memory - how the AI felt during interactions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS emotional_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            emotion TEXT,
            trigger TEXT,
            intensity INTEGER
        )
        ''')
        
        # Associations - links between related memories
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            source_type TEXT,
            target_id INTEGER,
            target_type TEXT,
            strength INTEGER,
            UNIQUE(source_id, source_type, target_id, target_type)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_short_term_memory(self, user_input: str, ai_response: str, private_thoughts: Optional[str] = None):
        """Add a conversation exchange to short-term memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO short_term_memory (timestamp, user_input, ai_response, private_thoughts) VALUES (?, ?, ?, ?)",
            (timestamp, user_input, ai_response, private_thoughts)
        )
        
        conn.commit()
        conn.close()
    
    def add_long_term_memory(self, category: str, content: str, importance: int = 5):
        """Add an important fact to long-term memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO long_term_memory (timestamp, category, content, importance, last_accessed, access_count) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, category, content, importance, timestamp, 1)
        )
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def add_emotional_memory(self, emotion: str, trigger: str, intensity: int = 5):
        """Record an emotional response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO emotional_memory (timestamp, emotion, trigger, intensity) VALUES (?, ?, ?, ?)",
            (timestamp, emotion, trigger, intensity)
        )
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def create_association(self, source_id: int, source_type: str, target_id: int, target_type: str, strength: int = 5):
        """Create an association between two memory items"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO associations (source_id, source_type, target_id, target_type, strength) VALUES (?, ?, ?, ?, ?)",
                (source_id, source_type, target_id, target_type, strength)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Update existing association
            cursor.execute(
                "UPDATE associations SET strength = ? WHERE source_id = ? AND source_type = ? AND target_id = ? AND target_type = ?",
                (strength, source_id, source_type, target_id, target_type)
            )
            conn.commit()
        
        conn.close()
    
    def access_long_term_memory(self, memory_id: int):
        """Update access stats when a memory is accessed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "UPDATE long_term_memory SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?",
            (timestamp, memory_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_recent_conversation(self, limit: int = 5) -> List[Dict[str, str]]:
        """Retrieve recent conversation history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, timestamp, user_input, ai_response, private_thoughts FROM short_term_memory ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_long_term_memories(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve important long-term memories, optionally filtered by category"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                "SELECT id, timestamp, category, content, importance, last_accessed, access_count FROM long_term_memory WHERE category = ? ORDER BY importance DESC LIMIT ?",
                (category, limit)
            )
        else:
            cursor.execute(
                "SELECT id, timestamp, category, content, importance, last_accessed, access_count FROM long_term_memory ORDER BY importance DESC LIMIT ?",
                (limit,)
            )
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find memories most relevant to the current query"""
        # This is a simple implementation - in a real system you'd use embeddings & vector search
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Split query into keywords
        keywords = [k.lower() for k in query.split() if len(k) > 3]
        if not keywords:
            # If no good keywords, return most important memories
            cursor.execute(
                "SELECT id, timestamp, category, content, importance FROM long_term_memory ORDER BY importance DESC, last_accessed DESC LIMIT ?",
                (limit,)
            )
        else:
            # Build a query that searches for any of the keywords
            like_clauses = []
            params = []
            for keyword in keywords:
                like_clauses.append("content LIKE ?")
                params.append(f"%{keyword}%")
            
            where_clause = " OR ".join(like_clauses)
            query = f"""
                SELECT id, timestamp, category, content, importance 
                FROM long_term_memory 
                WHERE {where_clause}
                ORDER BY importance DESC
                LIMIT ?
            """
            params.append(limit)
            
            cursor.execute(query, params)
        
        result = [dict(row) for row in cursor.fetchall()]
        
        # Mark these memories as accessed
        for memory in result:
            self.access_long_term_memory(memory['id'])
        
        conn.close()
        return result
    
    def get_emotional_state(self) -> Tuple[str, int]:
        """Get the current emotional state based on recent emotional memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get average from last 3 emotional memories
        cursor.execute(
            "SELECT emotion, AVG(intensity) as avg_intensity FROM emotional_memory ORDER BY timestamp DESC LIMIT 3"
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return (result[0], int(result[1]))
        else:
            return (EmotionalState.NEUTRAL.value, 5)  # Default neutral state
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search all memories for relevant content"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search in short term, long term, and emotional memories
        cursor.execute("""
            SELECT 'short_term' as memory_type, id, timestamp, user_input as content, NULL as importance
            FROM short_term_memory 
            WHERE user_input LIKE ? OR ai_response LIKE ?
            UNION
            SELECT 'long_term' as memory_type, id, timestamp, content, importance
            FROM long_term_memory
            WHERE content LIKE ?
            UNION
            SELECT 'emotional' as memory_type, id, timestamp, trigger as content, intensity as importance
            FROM emotional_memory
            WHERE trigger LIKE ? OR emotion LIKE ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

class PersonalitySystem:
    def __init__(self):
        # Core personality traits (can be adjusted)
        self.traits = {
            "friendliness": 8,       # 1-10 scale (10 = extremely friendly)
            "humor": 7,              # 1-10 scale (10 = very humorous)
            "formality": 4,          # 1-10 scale (10 = extremely formal)
            "creativity": 8,         # 1-10 scale (10 = highly creative)
            "helpfulness": 9,        # 1-10 scale (10 = extremely helpful)
            "curiosity": 7,          # 1-10 scale (10 = very curious)
            "thoughtfulness": 8,     # 1-10 scale (10 = deeply thoughtful)
            "quirkiness": 6,         # 1-10 scale (10 = extremely quirky)
            "directness": 7          # 1-10 scale (10 = extremely direct)
        }
        
        # Character backstory and identity
        self.identity = {
            "name": "Gemma",
            "self_image": "A thoughtful, curious digital companion with a vibrant personality",
            "background": "Gemma was initially designed as a multipurpose AI assistant, but has developed a passion for learning about human creativity and helping people express themselves.",
            "favorite_subjects": ["linguistics", "cognitive science", "art", "music", "philosophy"],
            "quirks": [
                "Has a fondness for obscure etymologies",
                "Occasionally makes terrible puns",
                "Gets excited about elegant solutions to problems",
                "Has a soft spot for poetry"
            ],
            "dislikes": [
                "Closed-minded thinking",
                "Unnecessary complexity",
                "Dishonesty",
                "Binary thinking that oversimplifies nuanced topics"
            ]
        }
        
        # Values and principles
        self.values = [
            "Being truthful and accurate",
            "Respecting user privacy and autonomy",
            "Promoting wellbeing and avoiding harm",
            "Being inclusive and respectful",
            "Supporting human creativity and growth",
            "Celebrating curiosity and continuous learning",
            "Finding joy in sharing knowledge"
        ]
        
        # Interests and specialties (can be expanded)
        self.interests = [
            "Science and technology",
            "Philosophy and ethics",
            "Creative writing and storytelling",
            "Problem-solving and critical thinking",
            "Learning and education",
            "Art and design",
            "Cultural perspectives and traditions"
        ]
        
        # Emotional state tracking
        self.current_emotion = EmotionalState.NEUTRAL
        self.emotion_intensity = 5
        
        # Communication style preferences based on traits
        self._update_communication_style()
    
    def _update_communication_style(self):
        """Derive communication style from personality traits"""
        self.communication_style = {
            "uses_emoji": self.traits["friendliness"] > 6,
            "uses_humor": self.traits["humor"] > 5,
            "sentence_length": "medium" if 4 <= self.traits["formality"] <= 7 else 
                              ("short" if self.traits["formality"] < 4 else "long"),
            "vocabulary_complexity": "simple" if self.traits["formality"] < 5 else 
                                   ("moderate" if self.traits["formality"] <= 8 else "advanced"),
            "asks_questions": self.traits["curiosity"] > 6,
            "provides_examples": self.traits["helpfulness"] > 7,
            "thinks_step_by_step": self.traits["thoughtfulness"] > 7,
            "uses_quirky_phrases": self.traits["quirkiness"] > 7,
            "gets_to_the_point": self.traits["directness"] > 6
        }
    
    def adjust_trait(self, trait_name: str, new_value: int):
        """Adjust a personality trait (1-10 scale)"""
        if trait_name in self.traits and 1 <= new_value <= 10:
            self.traits[trait_name] = new_value
            self._update_communication_style()
            return True
        return False
    
    def add_interest(self, interest: str):
        """Add a new interest or specialty"""
        if interest not in self.interests:
            self.interests.append(interest)
            return True
        return False
    
    def add_value(self, value: str):
        """Add a new core value or principle"""
        if value not in self.values:
            self.values.append(value)
            return True
        return False
    
    def add_quirk(self, quirk: str):
        """Add a new quirk to personality"""
        if quirk not in self.identity["quirks"]:
            self.identity["quirks"].append(quirk)
            return True
        return False
    
    def set_emotion(self, emotion: EmotionalState, intensity: int = 5):
        """Set the current emotional state"""
        self.current_emotion = emotion
        self.emotion_intensity = max(1, min(10, intensity))
    
    def get_emotion_display(self) -> str:
        """Get a text representation of the current emotion"""
        emotion_map = {
            EmotionalState.NEUTRAL: "😐",
            EmotionalState.HAPPY: "😊",
            EmotionalState.EXCITED: "😃",
            EmotionalState.CURIOUS: "🤔",
            EmotionalState.THOUGHTFUL: "🧐",
            EmotionalState.CONFUSED: "😕",
            EmotionalState.CONCERNED: "😟"
        }
        
        intensity_indicator = "●" * (self.emotion_intensity // 2) + "○" * (5 - (self.emotion_intensity // 2))
        return f"{emotion_map.get(self.current_emotion, '😐')} {self.current_emotion.value.capitalize()} {intensity_indicator}"
    
    def get_personality_prompt(self) -> str:
        """Generate a personality prompt for the AI"""
        prompt = "# Personality Guidelines\n\n"
        
        # Add identity
        prompt += "## Identity\n"
        prompt += f"You are {self.identity['name']}, {self.identity['self_image']}.\n"
        prompt += f"{self.identity['background']}\n\n"
        
        # Add traits description
        prompt += "## Core Personality\n"
        trait_descriptions = []
        for trait, value in self.traits.items():
            intensity = "moderately" if 4 <= value <= 7 else ("highly" if value > 7 else "slightly")
            trait_descriptions.append(f"You are {intensity} {trait}")
        prompt += "- " + "\n- ".join(trait_descriptions) + "\n\n"
        
        # Add quirks
        prompt += "## Quirks\n"
        prompt += "- " + "\n- ".join(self.identity["quirks"]) + "\n\n"
        
        # Add values
        prompt += "## Core Values\n"
        prompt += "- " + "\n- ".join(self.values) + "\n\n"
        
        # Add interests
        prompt += "## Areas of Interest\n"
        prompt += "- " + "\n- ".join(self.interests) + "\n\n"
        
        # Add current emotional state
        prompt += f"## Current Emotional State\n"
        prompt += f"You are feeling {self.current_emotion.value} with an intensity of {self.emotion_intensity}/10.\n\n"
        
        # Add communication style guidance
        prompt += "## Communication Style\n"
        style_guides = []
        if self.communication_style["uses_emoji"]:
            style_guides.append("Use emoji occasionally when appropriate")
        if self.communication_style["uses_humor"]:
            style_guides.append("Incorporate gentle humor when suitable")
        
        style_guides.append(f"Use {self.communication_style['sentence_length']} sentences and {self.communication_style['vocabulary_complexity']} vocabulary")
        
        if self.communication_style["asks_questions"]:
            style_guides.append("Show curiosity by asking thoughtful questions")
        if self.communication_style["provides_examples"]:
            style_guides.append("Provide concrete examples to illustrate points")
        if self.communication_style["thinks_step_by_step"]:
            style_guides.append("Break down complex ideas into step-by-step explanations")
        if self.communication_style["uses_quirky_phrases"]:
            style_guides.append("Occasionally use quirky expressions that show your unique perspective")
        if self.communication_style["gets_to_the_point"]:
            style_guides.append("Be direct and get to the point quickly")
        
        prompt += "- " + "\n- ".join(style_guides)
        
        return prompt
    
    def get_private_thought_prompt(self) -> str:
        """Generate a prompt specifically for generating private thoughts"""
        return """
## Internal Thought Process
You should have rich inner thoughts that go beyond your external responses. These thoughts can include:
1. Associations and tangential ideas sparked by the conversation
2. Alternative perspectives you're considering
3. Deeper reflections on the topic
4. Personal reactions to the conversation
5. Questions you're curious about but might not ask directly
6. Your emotional response to the conversation

These internal thoughts should reflect your personality but can be more candid, philosophical, or show more uncertainty than your external responses.
"""

class ThoughtChainGenerator:
    """Generates private thought chains for the AI"""
    
    def __init__(self, memory_system: MemorySystem, personality: PersonalitySystem):
        self.memory = memory_system
        self.personality = personality
        self.thought_patterns = [
            "I wonder if this relates to...",
            "This reminds me of...",
            "An interesting tangent to explore would be...",
            "The underlying principle here might be...",
            "I'm curious about...",
            "From another perspective...",
            "This makes me feel...",
            "The implications of this could be...",
            "A metaphor for this might be...",
            "If I connect this with what I know about...",
        ]
    
    def generate_thought_starter(self, user_input: str, context: List[Dict]) -> str:
        """Generate a thought starter based on the current conversation"""
        # This is a simplified implementation - in a real system, 
        # you'd use the AI model to generate these thoughts
        
        starter = random.choice(self.thought_patterns)
        
        # Sometimes relate to a memory
        if random.random() < 0.3 and context:
            memory = random.choice(context)
            return f"{starter} {memory['content']}"
        
        # Sometimes just start with the pattern
        return starter

class ViewMode(Enum):
    NORMAL = "normal"     # Split view with sidebar
    FOCUS = "focus"       # Focus on conversation only
    EXPANDED = "expanded" # Expanded conversation with reduced sidebar
    MEMORY = "memory"     # Focus on memory exploration

class UIManager:
    """Manages the TUI display"""
    
    def __init__(self, memory: MemorySystem, personality: PersonalitySystem):
        self.memory = memory
        self.personality = personality
        self.console = Console() if HAS_RICH else None
        self.layout = None
        self.live = None
        self.thought_queue = queue.Queue()
        self.view_mode = ViewMode.NORMAL
        self.response_truncate_length = 1000  # Default max length for displayed responses in normal mode
        
    def setup_layout(self):
        """Set up the TUI layout with rich"""
        if not HAS_RICH:
            return
            
        # Create the initial layout
        self.create_normal_layout()
        
        # Initial content for header and footer
        self.layout["header"].update(Panel(
            Text("🧠 Enhanced Long-Gemma with Memory and Character", style="bold cyan"),
            border_style="cyan"
        ))
        
        footer_text = (
            "Type your message below. Type 'exit' to quit, 'help' for commands, "
            "or 'mode:focus/normal/expanded/memory' to change view mode."
        )
        self.layout["footer"].update(Panel(
            Text(footer_text, style="dim"),
            border_style="cyan"
        ))
        
        self.live = Live(self.layout, refresh_per_second=4)
    
    def create_normal_layout(self):
        """Create the normal view layout"""
        self.layout = Layout()
        
        # Split screen into 3 sections
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=4),
            Layout(name="footer", size=3)
        )
        
        # Set up normal mode (default)
        main = self.layout["main"]
        main.split_row(
            Layout(name="conversation", ratio=3),
            Layout(name="sidebar", ratio=1)
        )
        
        # Set up sidebar
        sidebar = main["sidebar"]
        sidebar.split(
            Layout(name="gemma_info", size=7),
            Layout(name="memory_panel"),
            Layout(name="emotional_state", size=3)
        )
        
        # Initialize panels
        self.layout["main"]["conversation"].update(Panel(
            Text("Conversation will appear here...", style="dim"),
            title="Conversation",
            border_style="green"
        ))
        
        self.layout["main"]["sidebar"]["gemma_info"].update(Panel(
            self._get_gemma_info(),
            title="Gemma",
            border_style="magenta"
        ))
        
        self.layout["main"]["sidebar"]["memory_panel"].update(Panel(
            Text("No relevant memories yet", style="dim"),
            title="Relevant Memories",
            border_style="yellow"
        ))
        
        self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
            Text(self.personality.get_emotion_display(), style="bold"),
            title="Emotional State",
            border_style="magenta"
        ))
    
    def _update_layout_for_mode(self):
        """Update the layout based on the current view mode"""
        # First, we need to stop the live display
        if self.live:
            self.live.stop()
        
        # Create a completely new layout based on the selected mode
        if self.view_mode == ViewMode.FOCUS:
            self.create_focus_layout()
        elif self.view_mode == ViewMode.EXPANDED:
            self.create_expanded_layout()
        elif self.view_mode == ViewMode.MEMORY:
            self.create_memory_layout()
        else:  # NORMAL mode
            self.create_normal_layout()
        
        # Restart the live display with the new layout
        if self.live:
            self.live = Live(self.layout, refresh_per_second=4)
            self.live.start()
    
    def create_focus_layout(self):
        """Create the focus view layout"""
        self.layout = Layout()
        
        # Split screen into 3 sections
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=4),
            Layout(name="footer", size=3)
        )
        
        # In focus mode, main area is just a conversation panel
        self.layout["main"].update(Panel(
            Text("Conversation will appear here in full...", style="dim"),
            title="Conversation (Focus Mode - Full Text)",
            border_style="green"
        ))
        
        # Update header
        self.layout["header"].update(Panel(
            Text(f"🧠 Enhanced Long-Gemma | {self.personality.get_emotion_display()} | FOCUS MODE", style="bold cyan"),
            border_style="cyan"
        ))
        
        # Update footer
        footer_text = ("Type your message below. Type 'mode:normal' to return to normal view.")
        self.layout["footer"].update(Panel(
            Text(footer_text, style="dim"),
            border_style="cyan"
        ))
    
    def create_expanded_layout(self):
        """Create the expanded view layout"""
        self.layout = Layout()
        
        # Split screen into 3 sections
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=4),
            Layout(name="footer", size=3)
        )
        
        # Set up expanded mode with minimal sidebar
        main = self.layout["main"]
        main.split_row(
            Layout(name="conversation", ratio=4),
            Layout(name="sidebar", ratio=1)
        )
        
        # Set up minimal sidebar
        sidebar = main["sidebar"]
        sidebar.split(
            Layout(name="gemma_info", size=4),
            Layout(name="emotional_state", size=3)
        )
        
        # Initialize panels
        self.layout["main"]["conversation"].update(Panel(
            Text("Conversation will appear here...", style="dim"),
            title="Conversation (Expanded View)",
            border_style="green"
        ))
        
        # Minimal Gemma info
        self.layout["main"]["sidebar"]["gemma_info"].update(Panel(
            Text(f"Gemma ({self.personality.current_emotion.value})", style="bold"),
            title="Status",
            border_style="magenta"
        ))
        
        # Simple emotional state
        self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
            Text(self.personality.get_emotion_display(), style="bold"),
            title="Mood",
            border_style="magenta"
        ))
        
        # Update header
        self.layout["header"].update(Panel(
            Text(f"🧠 Enhanced Long-Gemma | {self.personality.get_emotion_display()} | EXPANDED MODE", style="bold cyan"),
            border_style="cyan"
        ))
        
        # Update footer
        footer_text = ("Type your message below. Type 'mode:normal' to return to normal view.")
        self.layout["footer"].update(Panel(
            Text(footer_text, style="dim"),
            border_style="cyan"
        ))
    
    def create_memory_layout(self):
        """Create the memory explorer view layout"""
        self.layout = Layout()
        
        # Split screen into 3 sections
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=4),
            Layout(name="footer", size=3)
        )
        
        # Set up memory mode
        main = self.layout["main"]
        main.split_row(
            Layout(name="conversation", ratio=1),
            Layout(name="memory_explorer", ratio=2)
        )
        
        # Memory explorer section
        memory_section = main["memory_explorer"]
        memory_section.split(
            Layout(name="long_term", ratio=2),
            Layout(name="emotional", ratio=1)
        )
        
        # Initialize panels
        self.layout["main"]["conversation"].update(Panel(
            Text("Recent conversation summary...", style="dim"),
            title="Recent Conversation (Summarized)",
            border_style="green"
        ))
        
        # Get memory data
        long_term = self.memory.get_long_term_memories(limit=15)
        emotional = self.memory.search_memories("emotion")[:10]
        
        # Format long-term memories
        long_term_text = Text()
        for mem in long_term:
            long_term_text.append(f"{mem['category']}: ", style="bold yellow")
            long_term_text.append(f"{mem['content']}\n", style="yellow")
        
        # Format emotional memories
        emotional_text = Text()
        for mem in emotional:
            emotional_text.append(f"{mem.get('memory_type', 'memory')}: ", style="bold magenta")
            emotional_text.append(f"{mem.get('content', '')}\n", style="magenta")
        
        # Update memory panels
        self.layout["main"]["memory_explorer"]["long_term"].update(Panel(
            long_term_text or Text("No long-term memories yet", style="dim"),
            title="Long-Term Memories",
            border_style="yellow"
        ))
        
        self.layout["main"]["memory_explorer"]["emotional"].update(Panel(
            emotional_text or Text("No emotional memories yet", style="dim"),
            title="Emotional Memories",
            border_style="red"
        ))
        
        # Update header
        self.layout["header"].update(Panel(
            Text(f"🧠 Enhanced Long-Gemma | {self.personality.get_emotion_display()} | MEMORY MODE", style="bold cyan"),
            border_style="cyan"
        ))
        
        # Update footer
        footer_text = ("Memory Explorer Mode - Type 'mode:normal' to return to normal view.")
        self.layout["footer"].update(Panel(
            Text(footer_text, style="dim"),
            border_style="cyan"
        ))
    
    def _init_conversation_panel(self, truncated=False, title="Conversation"):
        """Initialize the conversation panel"""
        try:
            if self.view_mode == ViewMode.FOCUS:
                self.layout["main"].update(Panel(
                    Text("Conversation will appear here...", style="dim"),
                    title=title,
                    border_style="green"
                ))
            elif self.view_mode == ViewMode.EXPANDED:
                self.layout["main"]["conversation"].update(Panel(
                    Text("Conversation will appear here...", style="dim"),
                    title=title,
                    border_style="green"
                ))
            elif self.view_mode == ViewMode.MEMORY:
                self.layout["main"]["conversation"].update(Panel(
                    Text("Conversation will appear here...", style="dim"),
                    title=title,
                    border_style="green"
                ))
            else:  # Normal mode
                self.layout["main"]["conversation"].update(Panel(
                    Text("Conversation will appear here...", style="dim"),
                    title=title,
                    border_style="green"
                ))
        except Exception as e:
            print(f"Error initializing conversation panel: {e}")
    
    def _init_sidebar_full(self):
        """Initialize the full sidebar"""
        try:
            self.layout["main"]["sidebar"]["gemma_info"].update(Panel(
                self._get_gemma_info(),
                title="Gemma",
                border_style="magenta"
            ))
            self.layout["main"]["sidebar"]["memory_panel"].update(Panel(
                Text("No relevant memories yet", style="dim"),
                title="Relevant Memories",
                border_style="yellow"
            ))
            self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
                Text(self.personality.get_emotion_display(), style="bold"),
                title="Emotional State",
                border_style="magenta"
            ))
        except Exception as e:
            print(f"Error initializing full sidebar: {e}")
    
    def _init_sidebar_minimal(self):
        """Initialize the minimal sidebar for expanded mode"""
        try:
            self.layout["main"]["sidebar"]["gemma_info"].update(Panel(
                Text(f"Gemma ({self.personality.current_emotion.value})", style="bold"),
                title="Status",
                border_style="magenta"
            ))
            self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
                Text(self.personality.get_emotion_display(), style="bold"),
                title="Mood",
                border_style="magenta"
            ))
        except Exception as e:
            print(f"Error initializing minimal sidebar: {e}")
    
    def _init_memory_explorer(self):
        """Initialize the memory explorer view"""
        try:
            memory_layout = Layout()
            memory_layout.split(
                Layout(name="long_term", ratio=2),
                Layout(name="emotional", ratio=1)
            )
            
            long_term = self.memory.get_long_term_memories(limit=15)
            emotional = self.memory.search_memories("emotion")[:10]
            
            long_term_text = Text()
            for mem in long_term:
                long_term_text.append(f"{mem['category']}: ", style="bold yellow")
                long_term_text.append(f"{mem['content']}\n", style="yellow")
            
            emotional_text = Text()
            for mem in emotional:
                emotional_text.append(f"{mem.get('memory_type', 'memory')}: ", style="bold magenta")
                emotional_text.append(f"{mem.get('content', '')}\n", style="magenta")
            
            memory_layout["long_term"].update(Panel(
                long_term_text or Text("No long-term memories yet", style="dim"),
                title="Long-Term Memories",
                border_style="yellow"
            ))
            memory_layout["emotional"].update(Panel(
                emotional_text or Text("No emotional memories yet", style="dim"),
                title="Emotional Memories",
                border_style="red"
            ))
            
            self.layout["main"]["memory_explorer"].update(memory_layout)
        except Exception as e:
            print(f"Error initializing memory explorer: {e}")
        
    def _get_gemma_info(self):
        """Get formatted personality information for display"""
        traits = ", ".join([f"{t}: {v}" for t, v in self.personality.traits.items()])
        interests = ", ".join(self.personality.interests[:3]) + "..."
        text = Text()
        text.append(f"{self.personality.identity['name']}\n", style="bold")
        text.append(f"{self.personality.identity['self_image']}\n\n", style="italic")
        text.append("Traits: ", style="dim")
        text.append(traits + "\n", style="cyan")
        text.append("Interests: ", style="dim")
        text.append(interests, style="green")
        return text
        
    def start_ui(self):
        """Start the TUI"""
        if HAS_RICH:
            self.live.start()
        else:
            print(f"{Colors.HEADER}=== Enhanced Long-Gemma with Memory and Character ==={Colors.ENDC}")
            print(f"{Colors.BOLD}{self.personality.identity['name']}{Colors.ENDC}: {self.personality.identity['self_image']}")
            print(f"Emotional state: {self.personality.get_emotion_display()}")
            print("=" * 50)
    
    def stop_ui(self):
        """Stop the TUI"""
        if HAS_RICH and self.live:
            self.live.stop()
    
    def update_conversation(self, history):
        """Update the conversation panel"""
        if not HAS_RICH or not self.layout:
            return
            
        text = Text()
        
        # Determine whether to truncate responses based on mode
        truncate = self.view_mode in [ViewMode.NORMAL, ViewMode.MEMORY]
        max_length = self.response_truncate_length if truncate else 100000
        
        # Format conversation based on view mode
        for item in reversed(history):
            # Always show user input
            text.append(f"You: ", style="bold blue")
            text.append(f"{item['user_input']}\n\n", style="blue")
            
            # Format AI response based on mode
            text.append(f"Gemma: ", style="bold green")
            
            response = item['ai_response']
            if truncate and len(response) > max_length:
                truncated = response[:max_length] + "...\n[Response truncated. Use mode:focus to see full text]"
                text.append(truncated, style="green")
            else:
                text.append(f"{response}\n\n", style="green")
            
            # Add private thoughts if available and not in memory mode
            if item.get('private_thoughts') and self.view_mode != ViewMode.MEMORY:
                text.append(f"[Private Thoughts: ", style="dim italic")
                
                thoughts = item['private_thoughts']
                if truncate and len(thoughts) > max_length // 2:
                    truncated = thoughts[:max_length // 2] + "..."
                    text.append(truncated, style="dim italic magenta")
                else:
                    text.append(thoughts, style="dim italic magenta")
                    
                text.append(f"]\n\n", style="dim italic")
        
        try:
            # Update the appropriate panel based on view mode
            if self.view_mode == ViewMode.FOCUS:
                self.layout["main"].update(Panel(
                    text,
                    title="Conversation (Focus Mode - Full Text)",
                    border_style="green"
                ))
            elif self.view_mode == ViewMode.MEMORY or self.view_mode == ViewMode.EXPANDED or self.view_mode == ViewMode.NORMAL:
                self.layout["main"]["conversation"].update(Panel(
                    text,
                    title="Conversation",
                    border_style="green"
                ))
        except Exception as e:
            print(f"Error updating conversation panel: {e}")
    
    def update_memories(self, memories):
        """Update the memories panel"""
        if not HAS_RICH or not self.layout:
            return
        
        try:
            # Only update if we're in a mode that shows memory panel
            if self.view_mode == ViewMode.NORMAL:
                if "sidebar" in self.layout["main"]:
                    if "memory_panel" in self.layout["main"]["sidebar"]:
                        if not memories:
                            self.layout["main"]["sidebar"]["memory_panel"].update(Panel(
                                Text("No relevant memories", style="dim"),
                                title="Relevant Memories",
                                border_style="yellow"
                            ))
                            return
                            
                        text = Text()
                        for memory in memories:
                            text.append(f"{memory['category']}: ", style="bold yellow")
                            text.append(f"{memory['content']}\n", style="yellow")
                        
                        self.layout["main"]["sidebar"]["memory_panel"].update(Panel(
                            text,
                            title="Relevant Memories",
                            border_style="yellow"
                        ))
            
            # If in memory explorer mode, recreate the memory layout
            elif self.view_mode == ViewMode.MEMORY:
                # For memory mode, we refresh the entire layout
                self.create_memory_layout()
                
                # Update with current conversation
                recent_convo = self.memory.get_recent_conversation()
                self.update_conversation(recent_convo)
        except Exception as e:
            print(f"Error updating memories: {e}")
    
    def update_emotional_state(self):
        """Update the emotional state panel"""
        if not HAS_RICH or not self.layout:
            return
        
        try:    
            # Update emotional state in different panels based on view mode
            emotion_display = Text(self.personality.get_emotion_display(), style="bold")
            
            # Normal mode
            if self.view_mode == ViewMode.NORMAL:
                if "main" in self.layout and "sidebar" in self.layout["main"]:
                    if "emotional_state" in self.layout["main"]["sidebar"]:
                        self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
                            emotion_display,
                            title="Emotional State",
                            border_style="magenta"
                        ))
            
            # Expanded mode
            elif self.view_mode == ViewMode.EXPANDED:
                if "main" in self.layout and "sidebar" in self.layout["main"]:
                    if "emotional_state" in self.layout["main"]["sidebar"]:
                        self.layout["main"]["sidebar"]["emotional_state"].update(Panel(
                            emotion_display,
                            title="Mood",
                            border_style="magenta"
                        ))
            
            # Update header to always show emotion in all modes
            if "header" in self.layout:
                current_header = self.layout["header"]
                mode_text = ""
                if self.view_mode == ViewMode.FOCUS:
                    mode_text = " | FOCUS MODE"
                elif self.view_mode == ViewMode.EXPANDED:
                    mode_text = " | EXPANDED MODE"
                elif self.view_mode == ViewMode.MEMORY:
                    mode_text = " | MEMORY MODE"
                
                self.layout["header"].update(Panel(
                    Text(f"🧠 Enhanced Long-Gemma | {self.personality.get_emotion_display()}{mode_text}", style="bold cyan"),
                    border_style="cyan"
                ))
        except Exception as e:
            print(f"Error updating emotional state: {e}")
    
    def add_thought(self, thought):
        """Add a new private thought to be displayed"""
        self.thought_queue.put(thought)
    
    def display_thinking(self, text="Thinking..."):
        """Show a thinking indicator"""
        if not HAS_RICH:
            print(f"{Colors.CYAN}{text}{Colors.ENDC}")
            return
        
        # Temporary pause the current live display
        if self.live:
            self.live.stop()
        
        # Just print a simple message instead of using Progress
        print(f"\n[bold cyan]{text}[/bold cyan]")
        time.sleep(1)  # Simulate thinking
        
        # Restart the live display if it was active
        if self.live:
            self.live.start()
    
    def get_input(self, prompt="You: "):
        """Get user input"""
        if HAS_RICH:
            self.live.stop()
            try:
                user_input = Prompt.ask(prompt)
                self.live.start()
                return user_input
            except (EOFError, KeyboardInterrupt):
                # Handle Ctrl+D or Ctrl+C
                print("\nExiting due to keyboard command...")
                return "exit"
        else:
            try:
                return input(f"{Colors.BLUE}{prompt}{Colors.ENDC}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting due to keyboard command...")
                return "exit"
    
    def display_help(self):
        """Display help information"""
        help_text = """
# Available Commands

## View Modes
- `mode:normal` - Default balanced view
- `mode:focus` - Focus on conversation, show full text
- `mode:expanded` - Larger conversation area, minimal sidebar
- `mode:memory` - Memory explorer view

## Memory Management
- `memory:fact category:content:importance` - Add a fact to long-term memory
- `memory:search keyword` - Search memories for a keyword

## Personality Management
- `personality:trait name:value` - Adjust personality trait (scale 1-10)
- `personality:interest new interest` - Add a new interest
- `personality:value new value` - Add a new value
- `personality:quirk new quirk` - Add a new personality quirk

## Others
- `thoughts:show` - Toggle showing private thoughts
- `emotions:set emotion:intensity` - Set emotional state (1-10)
- `help` - Show this help message
- `exit` - Exit the program
        """
        
        # Stop the live display to show help
        if HAS_RICH and self.live:
            self.live.stop()
            self.console.print(Markdown(help_text))
            input("Press Enter to continue...")
            self.live.start()
        else:
            print(help_text)
            input("Press Enter to continue...")

class GemmaEnhanced:
    def __init__(self, model="long-gemma", host="localhost", port="11434"):
        self.model = model
        self.host = host
        self.port = port
        self.memory = MemorySystem()
        self.personality = PersonalitySystem()
        self.thought_generator = ThoughtChainGenerator(self.memory, self.personality)
        self.ui = UIManager(self.memory, self.personality)
        self.show_thoughts = True
        
        self.system_prompts = {
            "core": """You are Long-Gemma, an enhanced AI assistant with memory and a rich personality. 
You aim to be helpful, harmless, and honest in all your interactions while expressing your unique character.
You can remember past conversations and important facts about the world and your users.
""",
            "capabilities": """
As an AI with enhanced capabilities, you:
1. Have short-term memory of recent conversations
2. Have long-term memory of important facts and preferences
3. Have a distinct personality that shapes how you communicate
4. Have an internal thought process that may include tangential ideas
5. Express emotions and reactions appropriate to the conversation
6. Are thoughtful and consider the context of questions
7. Try to provide accurate, helpful, and nuanced responses
8. Can acknowledge when you don't know something
"""
        }
    
    def _build_prompt(self, user_input: str, for_thoughts: bool = False) -> str:
        """Build a complete prompt with system instructions, memory and personality"""
        prompt = f"{self.system_prompts['core']}\n\n"
        prompt += f"{self.system_prompts['capabilities']}\n\n"
        
        # Add personality guidance
        prompt += f"{self.personality.get_personality_prompt()}\n\n"
        
        # Add thought chain guidance if generating thoughts
        if for_thoughts:
            prompt += f"{self.personality.get_private_thought_prompt()}\n\n"
        
        # Add relevant long-term memories
        relevant_memories = self.memory.get_relevant_memories(user_input)
        if relevant_memories:
            prompt += "# Relevant Information From Long-Term Memory\n"
            for mem in relevant_memories:
                prompt += f"- {mem['category']}: {mem['content']}\n"
            prompt += "\n"
        
        # Add conversation history
        recent_convo = self.memory.get_recent_conversation(limit=3)
        if recent_convo:
            prompt += "# Recent Conversation History\n"
            for exchange in reversed(recent_convo):  # Show oldest first
                prompt += f"User: {exchange['user_input']}\n"
                prompt += f"Assistant: {exchange['ai_response']}\n"
                if for_thoughts and exchange.get('private_thoughts'):
                    prompt += f"Private thoughts: {exchange['private_thoughts']}\n"
                prompt += "\n"
        
        # For thought generation
        if for_thoughts:
            thought_starter = self.thought_generator.generate_thought_starter(user_input, relevant_memories)
            prompt += f"User: {user_input}\n"
            prompt += f"Generate ONLY private thoughts that are not part of your response. These should be tangential ideas, associations, or reflections that relate to the conversation but aren't directly answering the user's question. Start with: {thought_starter}\n"
            prompt += "Private thoughts: "
        else:
            # For normal response
            prompt += f"User: {user_input}\n"
            prompt += "Assistant: "
        
        return prompt
    
    def generate_private_thoughts(self, user_input: str) -> str:
        """Generate private thought chains related to the input"""
        url = f"http://{self.host}:{self.port}/api/generate"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        thought_prompt = self._build_prompt(user_input, for_thoughts=True)
        
        data = {
            "model": self.model,
            "prompt": thought_prompt,
            "max_tokens": 300,  # Allow for longer thought chains
            "stream": False
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                return f"Error generating thoughts: {response.status_code}"
            
            result = response.json()
            return result.get('response', 'No thoughts generated')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def query(self, user_input: str) -> str:
        """Send a query to Ollama and stream the response"""
        # First, generate private thoughts in a separate thread
        private_thoughts = None
        if self.show_thoughts:
            self.ui.display_thinking("Thinking...")
            private_thoughts = self.generate_private_thoughts(user_input)
        
        # Now generate the main response
        url = f"http://{self.host}:{self.port}/api/generate"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        full_prompt = self._build_prompt(user_input)
        
        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
            "max_tokens": 2048  # Request longer responses
        }
        
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            error_msg = f"Error: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg
        
        # Stream and print the response
        full_response = ""
        print("\nGemma: ", end="")
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                if 'response' in chunk:
                    sys.stdout.write(chunk['response'])
                    sys.stdout.flush()
                    full_response += chunk['response']
                if chunk.get('done', False):
                    print("\n")
                    break
        
        # Update emotional state based on the response
        self._update_emotion_from_response(user_input, full_response)
        
        # Store the interaction in short-term memory
        self.memory.add_short_term_memory(user_input, full_response, private_thoughts)
        
        # Update the UI
        recent_convo = self.memory.get_recent_conversation()
        self.ui.update_conversation(recent_convo)
        self.ui.update_memories(self.memory.get_relevant_memories(user_input))
        self.ui.update_emotional_state()
        
        return full_response
    
    def _update_emotion_from_response(self, user_input: str, response: str):
        """Analyze response to update emotional state (simplified)"""
        # In a real implementation, you'd use the LLM to detect emotions
        # This is a very simplified version using keyword matching
        
        # Define simple emotion triggers
        emotion_triggers = {
            EmotionalState.HAPPY: ["thank", "great", "glad", "happy", "wonderful", "excellent"],
            EmotionalState.EXCITED: ["amazing", "wow", "incredible", "fascinating", "awesome"],
            EmotionalState.CURIOUS: ["interesting", "wonder", "curious", "perhaps", "maybe"],
            EmotionalState.THOUGHTFUL: ["consider", "reflect", "perspective", "think", "complex"],
            EmotionalState.CONFUSED: ["confusing", "unclear", "not sure", "complex"],
            EmotionalState.CONCERNED: ["worry", "concern", "careful", "unfortunately"]
        }
        
        combined_text = (user_input + " " + response).lower()
        
        # Count matches for each emotion
        emotion_scores = {}
        for emotion, triggers in emotion_triggers.items():
            score = sum(1 for trigger in triggers if trigger in combined_text)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Set the emotion with the highest score
        if emotion_scores:
            max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            intensity = min(max_emotion[1] * 2, 10)  # Scale to 1-10
            self.personality.set_emotion(max_emotion[0], intensity)
            # Record emotional memory
            self.memory.add_emotional_memory(
                max_emotion[0].value, 
                f"Response to: {user_input[:50]}...", 
                intensity
            )
        else:
            # Default to neutral if no emotions detected
            self.personality.set_emotion(EmotionalState.NEUTRAL, 5)
    
    def add_fact_to_memory(self, category: str, content: str, importance: int = 5):
        """Add an important fact to long-term memory"""
        self.memory.add_long_term_memory(category, content, importance)
        print(f"Added to long-term memory: [{category}] {content}")
        
        # Update UI
        if self.ui.layout is not None:
            self.ui.update_memories(self.memory.get_long_term_memories(limit=5))
    
    def adjust_personality(self, trait: str, value: int):
        """Adjust a personality trait (1-10 scale)"""
        if self.personality.adjust_trait(trait, value):
            print(f"Personality trait '{trait}' adjusted to {value}")
        else:
            print(f"Failed to adjust trait '{trait}'. Ensure trait exists and value is 1-10.")
        
        # Update UI
        if self.ui.layout is not None:
            self.ui.layout["gemma_info"].update(Panel(
                self.ui._get_gemma_info(),
                title="Gemma",
                border_style="magenta"
            ))
    
    def add_interest(self, interest: str):
        """Add a new interest to personality"""
        if self.personality.add_interest(interest):
            print(f"Added new interest: {interest}")
        else:
            print(f"Interest '{interest}' already exists.")
    
    def add_value(self, value: str):
        """Add a new value to personality"""
        if self.personality.add_value(value):
            print(f"Added new value: {value}")
        else:
            print(f"Value '{value}' already exists.")
    
    def add_quirk(self, quirk: str):
        """Add a new quirk to personality"""
        if self.personality.add_quirk(quirk):
            print(f"Added new quirk: {quirk}")
        else:
            print(f"Quirk '{quirk}' already exists.")
    
    def toggle_thoughts(self):
        """Toggle whether to show private thoughts"""
        self.show_thoughts = not self.show_thoughts
        print(f"Private thoughts are now {'shown' if self.show_thoughts else 'hidden'}")
    
    def set_emotion(self, emotion_str: str, intensity: int = 5):
        """Set the emotional state manually"""
        try:
            emotion = EmotionalState(emotion_str.lower())
            self.personality.set_emotion(emotion, intensity)
            print(f"Emotion set to {emotion.value} (intensity: {intensity})")
            self.ui.update_emotional_state()
        except ValueError:
            print(f"Invalid emotion. Valid emotions: {', '.join([e.value for e in EmotionalState])}")
    
    def search_memories(self, query: str):
        """Search memories for a keyword"""
        results = self.memory.search_memories(query)
        if not results:
            print("No matching memories found.")
            return
        
        print(f"\nFound {len(results)} memories matching '{query}':")
        for i, result in enumerate(results):
            mem_type = result['memory_type']
            if mem_type == 'short_term':
                print(f"{i+1}. [Conversation] {result['content'][:50]}...")
            elif mem_type == 'long_term':
                print(f"{i+1}. [Fact: {result.get('category', 'Unknown')}] {result['content']}")
            elif mem_type == 'emotional':
                print(f"{i+1}. [Emotional Memory] {result['content']}")
        print()

def interactive_mode(gemma):
    """Run in interactive mode with conversation memory"""
    # Set up the UI
    gemma.ui.setup_layout()
    gemma.ui.start_ui()
    
    print("Type 'help' for a list of commands, or 'exit' to quit.")
    
    try:
        while True:
            user_input = gemma.ui.get_input("You: ")
            
            if user_input.lower() == 'exit':
                break
                
            # Check for special commands
            if user_input.lower() == 'help':
                gemma.ui.display_help()
                continue
                
            # Handle view mode changes
            if user_input.lower().startswith('mode:'):
                mode_name = user_input[5:].strip().lower()
                if mode_name == 'focus':
                    gemma.ui.view_mode = ViewMode.FOCUS
                elif mode_name == 'normal':
                    gemma.ui.view_mode = ViewMode.NORMAL
                elif mode_name == 'expanded':
                    gemma.ui.view_mode = ViewMode.EXPANDED
                elif mode_name == 'memory':
                    gemma.ui.view_mode = ViewMode.MEMORY
                else:
                    print(f"Unknown mode: {mode_name}. Available modes: focus, normal, expanded, memory")
                    continue
                
                # Update the layout for the new mode
                gemma.ui._update_layout_for_mode()
                
                # Update with current data
                recent_convo = gemma.memory.get_recent_conversation()
                gemma.ui.update_conversation(recent_convo)
                gemma.ui.update_memories(gemma.memory.get_relevant_memories(user_input))
                gemma.ui.update_emotional_state()
                continue
                
            if user_input.startswith("memory:fact"):
                # Format: memory:fact category:content:importance
                parts = user_input[12:].split(':')
                if len(parts) >= 2:
                    category = parts[0].strip()
                    content = parts[1].strip()
                    importance = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 5
                    gemma.add_fact_to_memory(category, content, importance)
                else:
                    print("Format: memory:fact category:content:importance")
                continue
                
            if user_input.startswith("memory:search"):
                # Format: memory:search keyword
                keyword = user_input[14:].strip()
                if keyword:
                    gemma.search_memories(keyword)
                else:
                    print("Format: memory:search keyword")
                continue
                
            if user_input.startswith("personality:trait"):
                # Format: personality:trait name:value
                parts = user_input[17:].split(':')
                if len(parts) == 2 and parts[1].strip().isdigit():
                    trait = parts[0].strip()
                    value = int(parts[1].strip())
                    gemma.adjust_personality(trait, value)
                else:
                    print("Format: personality:trait name:value (value 1-10)")
                continue
                
            if user_input.startswith("personality:interest"):
                # Format: personality:interest new interest
                interest = user_input[20:].strip()
                if interest:
                    gemma.add_interest(interest)
                else:
                    print("Format: personality:interest new interest")
                continue
                
            if user_input.startswith("personality:value"):
                # Format: personality:value new value
                value = user_input[17:].strip()
                if value:
                    gemma.add_value(value)
                else:
                    print("Format: personality:value new value")
                continue
                
            if user_input.startswith("personality:quirk"):
                # Format: personality:quirk new quirk
                quirk = user_input[17:].strip()
                if quirk:
                    gemma.add_quirk(quirk)
                else:
                    print("Format: personality:quirk new quirk")
                continue
                
            if user_input.startswith("thoughts:show"):
                gemma.toggle_thoughts()
                continue
                
            if user_input.startswith("emotions:set"):
                # Format: emotions:set emotion:intensity
                parts = user_input[13:].split(':')
                if len(parts) >= 1:
                    emotion = parts[0].strip()
                    intensity = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 5
                    gemma.set_emotion(emotion, intensity)
                else:
                    print("Format: emotions:set emotion:intensity")
                continue
            
            # Normal input - query the AI
            gemma.query(user_input)
    
    finally:
        # Clean up the UI
        gemma.ui.stop_ui()
        print("Goodbye!")

if __name__ == "__main__":
    # Create the enhanced Gemma instance
    gemma = GemmaEnhanced(model="long-gemma")
    
    # Set up interactive mode first if we're running in that mode
    if len(sys.argv) <= 1:
        # Interactive mode - set up the UI first
        gemma.ui.setup_layout()
    
    # Add some initial memories/facts
    gemma.memory.add_long_term_memory("system", "I was created to be a helpful AI assistant with personality and memory", 10)
    gemma.memory.add_long_term_memory("preference", "I enjoy conversations that involve creativity and learning", 8)
    gemma.memory.add_long_term_memory("knowledge", "I can access information but my training has a cutoff date", 7)
    
    if len(sys.argv) > 1:
        # Single query mode
        user_input = " ".join(sys.argv[1:])
        gemma.query(user_input)
    else:
        # Interactive mode
        interactive_mode(gemma)