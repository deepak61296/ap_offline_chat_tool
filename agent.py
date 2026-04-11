#!/usr/bin/env python3
"""
ArduPilot AI - Standalone Agent CLI
This is a rich terminal interface for the ArduPilot AI Backend.
It connects to the local API server and provides an immersive copilot experience.
"""

import os
import sys
import time
import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from backend.config import API_HOST, API_PORT, BACKEND_VERSION

console = Console()
API_CLIENT_HOST = "127.0.0.1" if API_HOST == "0.0.0.0" else API_HOST
API_URL = f"http://{API_CLIENT_HOST}:{API_PORT}"

def check_server():
    """Wait for the API server to be ready and fetch status."""
    with console.status("[bold blue]Waiting for AI Backend server to start...[/bold blue]"):
        for _ in range(10):
            try:
                # We check /status to get the actual operation_mode
                resp = requests.get(f"{API_URL}/status", timeout=2)
                if resp.status_code == 200:
                    return resp.json()
            except requests.exceptions.RequestException:
                time.sleep(1)
    return None

def show_welcome(server_status):
    """Display the welcome banner."""
    console.clear()
    
    # Check what mode the server is actually running in!
    op_mode = server_status.get("operation_mode", "integrated")
    is_standalone_active = (op_mode == "standalone")
    model = server_status.get("default_model", "unknown")
    mavlink = server_status.get("mavlink", {})
    mav_status = "connected" if mavlink.get("connected") else mavlink.get("state", "disconnected")
    mav_endpoint = mavlink.get("connection_string") or "not configured"
    telemetry_health = mavlink.get("telemetry_health", "missing")
    
    banner = f"""
[bold cyan]ArduPilot AI Agent[/bold cyan] v{BACKEND_VERSION}
[dim]Standalone MAVLink Copilot Interface[/dim]

[yellow]Mode:[/yellow] {'[bold green]True Standalone (PyMAVLink execution)[/bold green]' if is_standalone_active else '[bold magenta]Integrated (QGC execution)[/bold magenta]'}
[yellow]Model:[/yellow] {model}
[yellow]MAVLink:[/yellow] {mav_status}
[yellow]Endpoint:[/yellow] {mav_endpoint}
[yellow]Telemetry:[/yellow] {telemetry_health}
[yellow]Commands:[/yellow] Type natural language to control the drone (e.g., 'arm and takeoff to 15m')
[yellow]System:[/yellow] Type 'exit' or 'quit' to close.
"""
    console.print(Panel(banner, border_style="cyan"))
    return is_standalone_active

def chat_loop(server_status):
    """Main interactive loop."""
    is_standalone_active = show_welcome(server_status)
    
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold green]Agent[/bold green] [dim]>[/dim]")
            
            if user_input.lower() in ('exit', 'quit'):
                console.print("[dim]Shutting down Agent CLI...[/dim]")
                break
                
            if not user_input.strip():
                continue
                
            # Send to backend
            with console.status("[bold cyan]Agent is thinking...[/bold cyan]"):
                payload = {
                    "message": user_input,
                    "mode": "agent" 
                }
                response = requests.post(f"{API_URL}/chat", json=payload, timeout=60)
                
            data = response.json()
            ai_text = data.get('response', '')

            if response.status_code == 200:
                console.print("\n[bold blue]AI Copilot[/bold blue]")
                console.print(Panel(Markdown(ai_text), border_style="blue"))
                _print_execution_status(data)
                
                # In standalone mode, the backend already executed things.
                # We can just show if any commands were generated.
                cmds = data.get('commands') or ([data.get('command')] if data.get('command') else [])
                if cmds and not is_standalone_active:
                    console.print(f"[dim yellow]Warning: {len(cmds)} commands returned in compatibility mode. A GCS executor would need to run them.[/dim yellow]")
            else:
                console.print(f"[bold red]Error from server:[/bold red] HTTP {response.status_code}")
                console.print(Panel(Markdown(ai_text or data.get('error') or 'Unknown error'), border_style="red"))
                _print_execution_status(data)
                    
        except KeyboardInterrupt:
            break
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Connection lost to AI Backend server![/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


def _print_execution_status(data):
    if data.get("interaction_type") != "command":
        return

    parse_source = data.get("parse_source") or "none"
    connection = data.get("connection_state") or "unknown"
    success = data.get("execution_success")
    attempted = data.get("execution_attempted")
    error = data.get("execution_error")

    if success:
        style = "green"
        title = "Execution OK"
    elif attempted:
        style = "red"
        title = "Execution Failed"
    else:
        style = "yellow"
        title = "Execution Blocked"

    lines = [
        f"Parse source: {parse_source}",
        f"Connection: {connection}",
        f"Attempted: {attempted}",
        f"Success: {success}",
    ]
    if error:
        lines.append(f"Error: {error}")

    for step in data.get("step_results") or []:
        lines.append(f"- {step.get('command')}: {'OK' if step.get('success') else 'FAILED'} ({step.get('message')})")

    console.print(Panel("\n".join(lines), title=title, border_style=style))

if __name__ == "__main__":
    server_status = check_server()
    if not server_status:
        console.print(f"[bold red]Failed to connect to API server at {API_URL}[/bold red]")
        console.print("[dim]Is the backend running? Try starting it with 'python run_server.py --standalone'[/dim]")
        sys.exit(1)
        
    # Extract standalone mode from server status
    op_mode = server_status.get("operation_mode", "integrated")
    is_standalone_active = (op_mode == "standalone")
    
    chat_loop(server_status)
