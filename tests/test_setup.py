#!/usr/bin/env python3
"""Test script to verify setup"""
import sys
from rich.console import Console

console = Console()

def test_ollama():
    console.print("\n[bold cyan]Testing Ollama...[/bold cyan]")
    try:
        import ollama
        console.print("[green]   [PASS] Ollama package installed[/green]")
        models = ollama.list()
        console.print("[green]   [PASS] Ollama running[/green]")
        model_names = [m['name'] for m in models.get('models', [])]
        if any('functiongemma' in n for n in model_names):
            console.print("[green]   [PASS] FunctionGemma found[/green]")
            return True
        else:
            console.print("[yellow]   [WARN]  FunctionGemma not found[/yellow]")
            return False
    except Exception as e:
        console.print(f"[red]   [FAIL] Failed: {e}[/red]")
        return False

def test_pymavlink():
    console.print("\n[bold cyan]Testing PyMAVLink...[/bold cyan]")
    try:
        import pymavlink
        console.print(f"[green]   [PASS] PyMAVLink installed[/green]")
        return True
    except:
        console.print("[red]   [FAIL] PyMAVLink not installed[/red]")
        return False

def test_rich():
    console.print("\n[bold cyan]Testing Rich...[/bold cyan]")
    console.print("[green]   [PASS] Rich installed[/green]")
    return True

def main():
    console.print("[bold yellow]System Check[/bold yellow]\n")
    results = [test_ollama(), test_pymavlink(), test_rich()]
    if all(results):
        console.print("\n[bold green][PASS] All tests passed![/bold green]")
        return 0
    else:
        console.print("\n[bold red][FAIL] Some tests failed[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
