"""
Task Planner — The Brain of the Agentic Drone Copilot.

Takes a user prompt + telemetry context, asks the LLM to decompose it into
an ordered list of atomic tool calls, and returns a structured task plan.

This module is the ONLY place where the LLM is called for agent mode.
"""

import json
import re
import logging
from typing import Dict, Any, List, Tuple, Optional

import ollama

from backend.config import OLLAMA_NUM_CTX, OLLAMA_NUM_GPU
from backend.prompts import get_agent_prompt
from backend.tools import extract_tool_calls, normalize_tool_call, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


def plan(
    user_message: str,
    model: str,
    telemetry: dict,
    connection_status: str,
    telemetry_section: str,
    conversation_history: Optional[List[Dict]] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Decompose a user prompt into an ordered list of executable commands.
    
    Args:
        user_message: The raw user input ("arm, takeoff 20m, move forward 10m then right 20m")
        model: Ollama model name to use
        telemetry: Raw telemetry dict from QGC/MAVProxy
        connection_status: "CONNECTED to drone" or "NOT CONNECTED"
        telemetry_section: Formatted telemetry string for the prompt
        conversation_history: Optional previous messages for multi-turn context
        
    Returns:
        (ai_text_response, list_of_normalized_commands)
        
        ai_text_response: The human-readable text to display in QGC
        list_of_normalized_commands: Ordered list of {"type": "ARM", "params": {}} dicts
    """
    system_prompt = get_agent_prompt(connection_status, telemetry_section)
    
    # Build message array
    messages = [{'role': 'system', 'content': system_prompt}]
    
    # Add conversation history if provided (for multi-turn)
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({'role': 'user', 'content': user_message})
    
    # Call the LLM
    logger.info(f"Planner: Asking LLM to decompose: '{user_message}'")
    response = ollama.chat(
        model=model,
        messages=messages,
        options={
            'num_ctx': OLLAMA_NUM_CTX,
            'num_gpu': OLLAMA_NUM_GPU,
            'temperature': 0.1,  # Low temp for structured output reliability
        }
    )
    
    raw_response = response['message']['content'].strip()
    logger.info(f"Planner: Raw LLM output ({len(raw_response)} chars)")
    
    # Extract structured tool calls from the JSON block
    clean_text, tool_calls = extract_tool_calls(raw_response)
    
    if not tool_calls:
        # No tools extracted — this is a conversational response (greeting, question, etc.)
        logger.info("Planner: No tool calls found — conversational response")
        return raw_response, []
    
    logger.info(f"Planner: Extracted {len(tool_calls)} tool call(s): {[tc.get('tool', '?') for tc in tool_calls]}")
    
    # Normalize each tool call into our standard command format
    commands = []
    for tc in tool_calls:
        cmd = normalize_tool_call(tc)
        if cmd:
            commands.append(cmd)
        else:
            logger.warning(f"Planner: Could not normalize tool call: {tc}")
    
    logger.info(f"Planner: Normalized {len(commands)} command(s): {[c['type'] for c in commands]}")
    
    return clean_text if clean_text else "Executing commands.", commands


def replan_with_context(
    user_message: str,
    previous_response: str,
    injected_context: str,
    model: str,
    connection_status: str,
    telemetry_section: str,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Re-prompt the LLM with additional context (used for RAG parameter lookup).
    
    This is the "double-hop" agentic loop:
    1. User asks something requiring external knowledge
    2. We do a lookup (param_db, etc.)
    3. We inject the results and re-prompt the LLM
    4. LLM now has the context to make the right tool call
    
    Args:
        user_message: Original user input
        previous_response: What the AI said in the first pass
        injected_context: The RAG/lookup results to inject
        model: Ollama model name
        connection_status: Connection status string
        telemetry_section: Formatted telemetry string
        
    Returns:
        (ai_text_response, list_of_normalized_commands)
    """
    system_prompt = get_agent_prompt(connection_status, telemetry_section)
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_message},
        {'role': 'assistant', 'content': previous_response},
        {'role': 'user', 'content': injected_context},
    ]
    
    logger.info("Planner (Re-plan): Injecting context and re-prompting LLM")
    response = ollama.chat(
        model=model,
        messages=messages,
        options={
            'num_ctx': OLLAMA_NUM_CTX,
            'num_gpu': OLLAMA_NUM_GPU,
            'temperature': 0.1,
        }
    )
    
    raw_response = response['message']['content'].strip()
    clean_text, tool_calls = extract_tool_calls(raw_response)
    
    commands = []
    for tc in tool_calls:
        cmd = normalize_tool_call(tc)
        if cmd:
            commands.append(cmd)
    
    logger.info(f"Planner (Re-plan): Got {len(commands)} command(s) from re-prompt")
    return clean_text if clean_text else raw_response, commands
