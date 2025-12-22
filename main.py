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
from drone_functions import DroneController, DRONE_FUNCTIONS
from function_gemma import FunctionGemmaInterface

console = Console()


class ArduPilotChatTool:
    """Main chat interface for ArduPilot drone control"""
    
    def __init__(self, connection_string: str = 'udp:127.0.0.1:14550'):
        """
        Initialize chat tool
        
        Args:
            connection_string: MAVLink connection string
        """
        self.drone = DroneController(connection_string)
        self.gemma = FunctionGemmaInterface()
        self.running = False
        
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
        console.print(f"\n[bold yellow]⚙️  Executing: {function_name}({arguments})[/bold yellow]")
        
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
                console.print(f"[bold green]✅ {result.get('message', 'Success')}[/bold green]")
            else:
                console.print(f"[bold red]❌ {result.get('message', 'Failed')}[/bold red]")
            
            return result
            
        except Exception as e:
            error_result = {"status": "error", "message": f"Execution failed: {str(e)}"}
            console.print(f"[bold red]❌ {error_result['message']}[/bold red]")
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
                console.print(f"\n[bold blue]🤖 Assistant:[/bold blue] {final_response}")
                
        elif response['type'] == 'text':
            # Just a text response
            console.print(f"\n[bold blue]🤖 Assistant:[/bold blue] {response['content']}")
            
        elif response['type'] == 'error':
            console.print(f"\n[bold red]❌ Error:[/bold red] {response['message']}")
    
    def show_welcome(self):
        """Show welcome banner"""
        welcome_text = """
[bold cyan]╔═══════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                                                       ║[/bold cyan]
[bold cyan]║        ArduPilot Offline Chat Tool v1.0              ║[/bold cyan]
[bold cyan]║        Powered by FunctionGemma (270M)               ║[/bold cyan]
[bold cyan]║                                                       ║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════╝[/bold cyan]

[bold white]Natural language → Function calls → Drone actions[/bold white]

[dim]Commands:[/dim]
  - Natural language: "take off to 10 meters", "land the drone"
  - [bold]/help[/bold]    - Show available functions
  - [bold]/status[/bold]  - Get drone status
  - [bold]/reset[/bold]   - Clear conversation history
  - [bold]/quit[/bold]    - Exit
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
        console.print("\n[bold cyan]📊 Getting drone status...[/bold cyan]")
        
        # Get position
        pos = self.drone.get_position()
        if pos.get("status") == "success":
            console.print(f"[green]📍 Position:[/green] Lat={pos['latitude']:.6f}, Lon={pos['longitude']:.6f}, Alt={pos['altitude']:.2f}m")
        
        # Get battery
        batt = self.drone.get_battery()
        if batt.get("status") == "success":
            console.print(f"[green]🔋 Battery:[/green] {batt['voltage']:.2f}V, {batt['current']:.2f}A, {batt['remaining']}%")
    
    def run(self):
        """Main chat loop"""
        self.show_welcome()
        
        # Connect to drone
        if not self.connect_drone():
            console.print("[bold red]❌ Failed to connect to drone. Exiting.[/bold red]")
            return
        
        console.print("\n[bold green]✅ Ready! Type your command or /help for assistance.[/bold green]\n")
        
        self.running = True
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input == '/quit' or user_input == '/exit':
                        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                        self.running = False
                        break
                    elif user_input == '/help':
                        self.show_help()
                    elif user_input == '/status':
                        self.show_status()
                    elif user_input == '/reset':
                        self.gemma.reset_conversation()
                        console.print("[green]🔄 Conversation reset[/green]")
                    else:
                        console.print(f"[red]Unknown command: {user_input}[/red]")
                else:
                    # Process natural language query
                    self.process_query(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]👋 Interrupted. Goodbye![/bold yellow]")
                self.running = False
                break
            except Exception as e:
                console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ArduPilot Offline Chat Tool with FunctionGemma')
    parser.add_argument('--connection', '-c', 
                       default='udp:127.0.0.1:14550',
                       help='MAVLink connection string (default: udp:127.0.0.1:14550)')
    
    args = parser.parse_args()
    
    # Create and run chat tool
    chat_tool = ArduPilotChatTool(connection_string=args.connection)
    chat_tool.run()


if __name__ == "__main__":
    main()
