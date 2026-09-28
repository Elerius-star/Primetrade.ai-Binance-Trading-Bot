#!/usr/bin/env python3
"""
Binance Futures Trading Bot - CLI Interface
"""

import click
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv
import os

from bot.client import BinanceFuturesClient
from bot.orders import OrderManager
from bot.validators import OrderValidator
from bot.logging_config import logger

load_dotenv()
console = Console()

class TradingBotCLI:
    def __init__(self):
        self.client = None
        self.order_manager = None
        self.validator = OrderValidator()
        
    def initialize_client(self):
        """Initialize the Binance client"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Connecting to Binance...", total=None)
                self.client = BinanceFuturesClient()
                self.order_manager = OrderManager(self.client)
            
            console.print("[green]✓ Connected to Binance Futures Testnet[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to connect: {e}[/red]")
            logger.error(f"Initialization failed: {e}")
            return False
    
    def display_welcome(self):
        """Display welcome banner"""
        welcome_text = """
╔══════════════════════════════════════════════╗
║     BINANCE FUTURES TRADING BOT v1.0        ║
║           Testnet Environment               ║
╚══════════════════════════════════════════════╝
        """
        console.print(Panel(welcome_text, style="bold cyan"))
    
    def place_order_interactive(self):
        """Interactive order placement"""
        console.print("\n[bold yellow]📊 Order Placement[/bold yellow]\n")
        
        # Get symbol
        symbol = Prompt.ask(
            "Enter symbol",
            choices=OrderValidator.VALID_SYMBOLS,
            default="BTCUSDT"
        )
        
        # Get side
        side = Prompt.ask(
            "Select side",
            choices=OrderValidator.VALID_SIDES,
            default="BUY"
        )
        
        # Get order type
        order_type = Prompt.ask(
            "Select order type",
            choices=OrderValidator.VALID_ORDER_TYPES,
            default="MARKET"
        )
        
        # Get quantity
        while True:
            quantity = Prompt.ask("Enter quantity")
            valid, result = OrderValidator.validate_quantity(quantity, symbol)
            if valid:
                quantity = result
                break
            console.print(f"[red]{result}[/red]")
        
        # Get price for limit orders
        price = None
        if order_type == "LIMIT":
            while True:
                price_input = Prompt.ask("Enter limit price")
                valid, result = OrderValidator.validate_price(price_input)
                if valid:
                    price = result
                    break
                console.print(f"[red]{result}[/red]")
        
        # Display order summary
        self.display_order_summary(symbol, side, order_type, quantity, price)
        
        # Confirm order
        if not Confirm.ask("\n[bold]Place this order?[/bold]"):
            console.print("[yellow]Order cancelled[/yellow]")
            return
        
        # Place order
        self.execute_order(symbol, side, order_type, quantity, price)
    
    def display_order_summary(self, symbol, side, order_type, quantity, price=None):
        """Display order summary"""
        table = Table(title="Order Summary", style="bold")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Symbol", symbol)
        table.add_row("Side", f"[{'green' if side == 'BUY' else 'red'}]{side}[/{'green' if side == 'BUY' else 'red'}]")
        table.add_row("Type", order_type)
        table.add_row("Quantity", str(quantity))
        if price:
            table.add_row("Price", f"${price:,.2f}")
        
        console.print(table)
    
    def execute_order(self, symbol, side, order_type, quantity, price=None):
        """Execute the order"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Placing order...", total=None)
                
                if order_type == "MARKET":
                    result = self.order_manager.place_market_order(symbol, side, quantity)
                else:
                    result = self.order_manager.place_limit_order(symbol, side, quantity, price)
            
            if result['success']:
                self.display_order_result(result)
                logger.info(f"Order placed successfully: {result}")
            else:
                console.print(f"[red]✗ Order failed: {result.get('error', 'Unknown error')}[/red]")
                logger.error(f"Order failed: {result}")
                
        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            logger.error(f"Unexpected error in execute_order: {e}", exc_info=True)
    
    def display_order_result(self, result):
        """Display order result"""
        table = Table(title="✅ Order Result", style="bold green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Order ID", str(result.get('order_id', 'N/A')))
        table.add_row("Status", result.get('status', 'N/A'))
        table.add_row("Executed Quantity", result.get('executed_qty', '0'))
        
        if 'avg_price' in result and result['avg_price']:
            table.add_row("Average Price", f"${float(result['avg_price']):,.2f}")
        elif 'price' in result:
            table.add_row("Price", f"${float(result['price']):,.2f}")
        
        console.print(table)
    
    def get_account_info(self):
        """Display account information"""
        try:
            account_info = self.client.get_account_info()
            
            table = Table(title="📈 Account Information", style="bold blue")
            table.add_column("Asset", style="cyan")
            table.add_column("Balance", style="white")
            table.add_column("Available", style="white")
            
            for asset in account_info.get('assets', []):
                if float(asset.get('walletBalance', 0)) > 0:
                    table.add_row(
                        asset['asset'],
                        f"${float(asset['walletBalance']):,.2f}",
                        f"${float(asset['availableBalance']):,.2f}"
                    )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Failed to get account info: {e}[/red]")
            logger.error(f"Account info error: {e}")

@click.command()
@click.option('--symbol', help='Trading symbol (e.g., BTCUSDT)')
@click.option('--side', type=click.Choice(['BUY', 'SELL']), help='Order side')
@click.option('--type', 'order_type', type=click.Choice(['MARKET', 'LIMIT']), help='Order type')
@click.option('--quantity', type=float, help='Order quantity')
@click.option('--price', type=float, help='Limit price (required for LIMIT orders)')
@click.option('--interactive', is_flag=True, help='Run in interactive mode')
def main(symbol, side, order_type, quantity, price, interactive):
    """Binance Futures Trading Bot - CLI Entry Point"""
    
    bot = TradingBotCLI()
    bot.display_welcome()
    
    # Initialize client
    if not bot.initialize_client():
        sys.exit(1)
    
    if interactive or all(v is None for v in [symbol, side, order_type, quantity]):
        # Interactive mode
        while True:
            console.print("\n[bold]Available Commands:[/bold]")
            console.print("1. Place Order")
            console.print("2. View Account Info")
            console.print("3. Exit")
            
            choice = Prompt.ask("Select option", choices=["1", "2", "3"])
            
            if choice == "1":
                bot.place_order_interactive()
            elif choice == "2":
                bot.get_account_info()
            else:
                console.print("[yellow]Goodbye![/yellow]")
                break
    else:
        # Command line mode
        try:
            # Validate inputs
            valid, symbol = OrderValidator.validate_symbol(symbol)
            if not valid:
                raise ValueError(symbol)
            
            valid, side = OrderValidator.validate_side(side)
            if not valid:
                raise ValueError(side)
            
            valid, order_type = OrderValidator.validate_order_type(order_type)
            if not valid:
                raise ValueError(order_type)
            
            valid, quantity = OrderValidator.validate_quantity(str(quantity), symbol)
            if not valid:
                raise ValueError(quantity)
            
            if order_type == "LIMIT":
                if not price:
                    raise ValueError("Price is required for LIMIT orders")
                valid, price = OrderValidator.validate_price(str(price))
                if not valid:
                    raise ValueError(price)
            
            # Execute order
            if order_type == "MARKET":
                result = bot.order_manager.place_market_order(symbol, side, quantity)
            else:
                result = bot.order_manager.place_limit_order(symbol, side, quantity, price)
            
            if result['success']:
                bot.display_order_result(result)
            else:
                console.print(f"[red]Order failed: {result.get('error')}[/red]")
                sys.exit(1)
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

if __name__ == "__main__":
    main()