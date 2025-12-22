#!/usr/bin/env python3
"""
Demo Mode - Test FunctionGemma without SITL
Simulates drone responses for testing the AI interface
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from drone_functions import DRONE_FUNCTIONS
from function_gemma import FunctionGemmaInterface

console = Console()


class MockDroneController:
    """Mock drone controller for demo mode"""
    
    def __init__(self):
        self.armed = False
        self.mode = "STABILIZE"
        self.altitude = 0
        self.position = {"lat": 28.5355, "lon": 77.3910, "alt": 0}  # Noida
        
    def arm(self):
        self.armed = True
        return {"status": "success", "message": "✈️ Drone armed (simulated)"}
    
    def disarm(self):
        self.armed = False
        return {"status": "success", "message": "🛑 Drone disarmed (simulated)"}
    
    def takeoff(self, altitude):
        if not self.armed:
            return {"status": "error", "message": "Drone must be armed first"}
        self.altitude = altitude
        self.mode = "GUIDED"
        return {
            "status": "success",
            "message": f"🚁 Taking off to {altitude}m (simulated)",
            "altitude": altitude
        }
    
    def land(self):
        self.altitude = 0
        self.mode = "LAND"
        return {"status": "success", "message": "🛬 Landing (simulated)"}
    
    def rtl(self):
        self.mode = "RTL"
        return {"status": "success", "message": "🏠 Returning to launch (simulated)"}
    
    def change_mode(self, mode):
        self.mode = mode
        return {"status": "success", "message": f"🔄 Mode changed to {mode} (simulated)"}
    
    def goto_location(self, lat, lon, alt):
        self.position = {"lat": lat, "lon": lon, "alt": alt}
        self.mode = "GUIDED"
        return {
            "status": "success",
            "message": f"📍 Flying to ({lat:.4f}, {lon:.4f}) at {alt}m (simulated)",
            "latitude": lat,
            "longitude": lon,
            "altitude": alt
        }
    
    def set_speed(self, speed, speed_type="ground"):
        return {
            "status": "success",
            "message": f"⚡ {speed_type.capitalize()} speed set to {speed} m/s (simulated)"
        }
    
    def get_position(self):
        return {
            "status": "success",
            "latitude": self.position["lat"],
            "longitude": self.position["lon"],
            "altitude": self.position["alt"],
            "heading": 90.0
        }
    
    def get_battery(self):
        return {
            "status": "success",
            "voltage": 12.6,
            "current": 8.5,
            "remaining": 87
        }


class DemoMode:
    """Demo mode chat interface"""
    
    def __init__(self):
        self.drone = MockDroneController()
        self.gemma = FunctionGemmaInterface()
        self.running = False
        
    def execute_function(self, function_name: str, arguments: dict):
        """Execute a mock function"""
        console.print(f"\n[bold yellow]⚙️  Executing (DEMO): {function_name}({arguments})[/bold yellow]")
        
        try:
            func = getattr(self.drone, function_name)
            if arguments:
                result = func(**arguments)
            else:
                result = func()
            
            if result.get("status") == "success":
                console.print(f"[bold green]{result.get('message', 'Success')}[/bold green]")
            else:
                console.print(f"[bold red]❌ {result.get('message', 'Failed')}[/bold red]")
            
            return result
            
        except Exception as e:
            error_result = {"status": "error", "message": f"Execution failed: {str(e)}"}
            console.print(f"[bold red]❌ {error_result['message']}[/bold red]")
            return error_result
    
    def process_query(self, user_input: str):
        """Process query with FunctionGemma"""
        response = self.gemma.query(user_input)
        
        if response['type'] == 'function_calls':
            for call in response['calls']:
                result = self.execute_function(call['name'], call['arguments'])
                final_response = self.gemma.add_tool_result(call['name'], result)
                console.print(f"\n[bold blue]🤖 Assistant:[/bold blue] {final_response}")
                
        elif response['type'] == 'text':
            console.print(f"\n[bold blue]🤖 Assistant:[/bold blue] {response['content']}")
            
        elif response['type'] == 'error':
            console.print(f"\n[bold red]❌ Error:[/bold red] {response['message']}")
    
    def show_welcome(self):
        """Show demo welcome"""
        welcome = """
[bold magenta]╔═══════════════════════════════════════════════════════╗[/bold magenta]
[bold magenta]║                                                       ║[/bold magenta]
[bold magenta]║           DEMO MODE - No SITL Required                ║[/bold magenta]
[bold magenta]║        Powered by FunctionGemma (270M)                ║[/bold magenta]
[bold magenta]║                                                       ║[/bold magenta]
[bold magenta]╚═══════════════════════════════════════════════════════╝[/bold magenta]

[bold yellow]⚠️  Running in DEMO mode - all responses are simulated[/bold yellow]
[dim]This mode lets you test FunctionGemma without ArduPilot SITL[/dim]

Try commands like:
  • "take off to 10 meters"
  • "what's my battery status?"
  • "fly to latitude 28.5, longitude 77.0"

Commands:
  [bold]/help[/bold]  - Show functions  [bold]/quit[/bold] - Exit  [bold]/reset[/bold] - Clear history
"""
        console.print(Panel(welcome, border_style="magenta"))
    
    def run(self):
        """Run demo mode"""
        self.show_welcome()
        
        console.print("\n[bold green]✅ Demo mode ready! Type your command.[/bold green]\n")
        
        self.running = True
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    if user_input in ['/quit', '/exit']:
                        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                        break
                    elif user_input == '/reset':
                        self.gemma.reset_conversation()
                        console.print("[green]🔄 Conversation reset[/green]")
                    elif user_input == '/help':
                        from rich.table import Table
                        table = Table(title="Available Functions", border_style="cyan")
                        table.add_column("Function", style="yellow")
                        table.add_column("Description")
                        for fname, fdef in DRONE_FUNCTIONS.items():
                            table.add_row(fname, fdef['description'])
                        console.print(table)
                    else:
                        console.print(f"[red]Unknown command[/red]")
                else:
                    self.process_query(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]👋 Interrupted![/bold yellow]")
                break


if __name__ == "__main__":
    console.print("\n[bold cyan]Starting FunctionGemma Demo Mode...[/bold cyan]")
    console.print("[dim]Testing AI function calling without drone hardware[/dim]\n")
    
    demo = DemoMode()
    demo.run()
