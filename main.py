#!/usr/bin/env python3
"""
ArduPilot Offline Chat Tool - Main Interface
Connects FunctionGemma with PyMAVLink drone control
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from src.drone_functions import DroneController, DRONE_FUNCTIONS
from src.qwen_interface import Qwen25Interface as FunctionGemmaInterface

console = Console()


class ArduPilotChatTool:
    """Main chat interface for ArduPilot drone control"""
    
    def __init__(self, connection_string: str = 'udp:127.0.0.1:14550', model_name: str = 'qwen2.5:3b'):
        """
        Initialize chat tool
        
        Args:
            connection_string: MAVLink connection string
            model_name: Ollama model name (default: qwen2.5:3b)
        """
        self.drone = DroneController(connection_string)
        self.gemma = FunctionGemmaInterface(model_name)
        self.running = False
        self.model_name = model_name
        
    def connect_drone(self) -> bool:
        """Connect to drone/SITL"""
        console.print("\n[bold cyan]🔌 Connecting to drone...[/bold cyan]")
        return self.drone.connect()
    
    def execute_function(self, function_name: str, arguments: dict) -> dict:
        """
        Execute a drone function
        
        Args:
            function_name: Name of function to call
            arguments: Function arguments
        
        Returns:
            Result dictionary from function execution
        """
        console.print(f"\n[bold yellow][EXECUTING] {function_name}({arguments})[/bold yellow]")
        
        try:
            # Get the function from DroneController
            func = getattr(self.drone, function_name)
            
            # Call with unpacked arguments
            if arguments:
                result = func(**arguments)
            else:
                result = func()
            
            # Print result
            if result.get("status") == "success":
                console.print(f"[bold green][SUCCESS] {result.get('message', 'Success')}[/bold green]")
            else:
                console.print(f"[bold red][ERROR] {result.get('message', 'Failed')}[/bold red]")
            
            return result
            
        except Exception as e:
            error_result = {"status": "error", "message": f"Execution failed: {str(e)}"}
            console.print(f"[bold red][ERROR] {error_result['message']}[/bold red]")
            return error_result
    
    def process_query(self, user_input: str):
        """
        Process user query through FunctionGemma and execute functions
        
        Args:
            user_input: User's natural language command
        """
        # Query FunctionGemma
        response = self.gemma.query(user_input)
        
        if response['type'] == 'function_calls':
            # Execute each function call
            for call in response['calls']:
                func_name = call['name']
                arguments = call['arguments']
                
                # Execute function
                result = self.execute_function(func_name, arguments)
                
                # Send result back to FunctionGemma for natural language response
                final_response = self.gemma.add_tool_result(func_name, result)
                console.print(f"\n[bold blue]Assistant:[/bold blue] {final_response}")
                
        elif response['type'] == 'text':
            # Just a text response
            console.print(f"\n[bold blue]Assistant:[/bold blue] {response['content']}")
            
        elif response['type'] == 'error':
            console.print(f"\n[bold red][ERROR][/bold red] {response['message']}")
    
    def show_welcome(self):
        """Show welcome banner"""
        welcome_text = f"""
[bold cyan]╔═══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                                                           ║[/bold cyan]
[bold cyan]║     🚁 ArduPilot AI Assistant - Qwen 2.5 (96% Accuracy)   ║[/bold cyan]
[bold cyan]║                                                           ║[/bold cyan]
[bold cyan]║        Natural language drone control - Fully offline!    ║[/bold cyan]
[bold cyan]║        Powered by Qwen 2.5 (3B parameters)                ║[/bold cyan]
[bold cyan]║                                                           ║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════════╝[/bold cyan]

[bold white]Model:[/bold white] {self.gemma.model_name}
[bold white]Mode:[/bold white] SITL (ArduPilot Software-in-the-Loop)

[dim]Natural language commands:[/dim]
  • "arm the drone and takeoff to 15 meters"
  • "check battery status"
  • "where am I?"
  • "return to launch"

[dim]Special commands:[/dim]
  [bold]/help[/bold] or [bold]/h[/bold]    - Show available functions
  [bold]/status[/bold] or [bold]/s[/bold]  - Get drone status
  [bold]/reset[/bold] or [bold]/r[/bold]   - Clear conversation history
  [bold]/quit[/bold] or [bold]/q[/bold]    - Exit application
"""
        console.print(Panel(welcome_text, border_style="cyan"))
    
    def show_help(self):
        """Show available drone functions"""
        table = Table(title="📋 Available Drone Functions", border_style="cyan")
        table.add_column("Function", style="bold yellow")
        table.add_column("Description", style="white")
        table.add_column("Parameters", style="dim")
        
        for func_name, func_def in DRONE_FUNCTIONS.items():
            params = ", ".join([f"{k}: {v['type']}" for k, v in func_def['parameters'].items()])
            if not params:
                params = "None"
            table.add_row(func_name, func_def['description'], params)
        
        console.print(table)
    
    def show_status(self):
        """Show drone status"""
        console.print("\n[bold cyan][STATUS] Getting drone status...[/bold cyan]")
        
        # Get position
        pos = self.drone.get_position()
        if pos.get("status") == "success":
            console.print(f"[green]Position:[/green] Lat={pos['latitude']:.6f}, Lon={pos['longitude']:.6f}, Alt={pos['altitude']:.2f}m")
        
        # Get battery
        batt = self.drone.get_battery()
        if batt.get("status") == "success":
            console.print(f"[green]Battery:[/green] {batt['voltage']:.2f}V, {batt['current']:.2f}A, {batt['remaining']}%")
    
    def run(self):
        """Main chat loop"""
        self.show_welcome()
        
        # Connect to drone
        if not self.connect_drone():
            console.print("[bold red][ERROR] Failed to connect to drone. Exiting.[/bold red]")
            return
        
        console.print("\n[bold green]Ready! Type your command or /help for assistance.[/bold green]\n")
        
        self.running = True
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    cmd = user_input.lower()
                    
                    # Quit commands
                    if cmd in ['/quit', '/exit', '/q']:
                        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                        self.running = False
                        break
                    
                    # Help commands
                    elif cmd in ['/help', '/h']:
                        self.show_help()
                    
                    # Status commands
                    elif cmd in ['/status', '/s']:
                        self.show_status()
                    
                    # Reset commands
                    elif cmd in ['/reset', '/r']:
                        self.gemma.reset_conversation()
                        console.print("[green]Conversation reset[/green]")
                    
                    else:
                        console.print(f"[red][ERROR] Unknown command: {user_input}[/red]")
                        console.print("[dim]Type /help or /h for available commands[/dim]")
                else:
                    # Process natural language query
                    self.process_query(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]👋 Interrupted. Goodbye![/bold yellow]")
                self.running = False
                break
            except Exception as e:
                console.print(f"\n[bold red][ERROR][/bold red] {str(e)}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ArduPilot AI Assistant - Natural language drone control with FunctionGemma',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Connect to default SITL
  %(prog)s -c tcp:127.0.0.1:5760             # Connect to specific port
  %(prog)s -m ardupilot-stage1 -v            # Use specific model with verbose output
        """
    )
    
    parser.add_argument(
        '--connection', '-c',
        default='udp:127.0.0.1:14550',
        help='MAVLink connection string (default: udp:127.0.0.1:14550)'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='qwen2.5:3b',
        help='Ollama model name. Options: qwen2.5:3b (default, 96%% accuracy), gemma3:4b, ardupilot-stage1 (legacy)'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available Ollama models and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output for debugging'
    )
    
    args = parser.parse_args()
    
    # List available models if requested
    if args.list_models:
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            console.print("\n[bold cyan]Available Ollama Models:[/bold cyan]")
            console.print(result.stdout)
            console.print("\n[bold green]Recommended for ArduPilot:[/bold green]")
            console.print("  • qwen2.5:3b (default) - 96% accuracy, 2.5s response")
            console.print("  • gemma3:4b - 96% accuracy, 4.5s response")
            console.print("  • ardupilot-stage1 (legacy) - 85% accuracy, 0.4s response")
            return
        except Exception as e:
            console.print(f"[red]Error listing models: {e}[/red]")
            return
    
    # Set verbose mode
    if args.verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    
    # Validate model selection
    console.print(f"\n[bold cyan]Selected Model:[/bold cyan] {args.model}")
    
    # Create and run chat tool with selected model
    chat_tool = ArduPilotChatTool(connection_string=args.connection, model_name=args.model)
    chat_tool.run()


if __name__ == "__main__":
    main()
