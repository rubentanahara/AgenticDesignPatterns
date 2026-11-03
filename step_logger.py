from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

console = Console()


def phase(title: str) -> None:
    console.rule(f"[bold cyan]{title}", style="cyan")


def show(label: str, value: object, style: str = "green") -> None:
    body = value.model_dump() if isinstance(value, BaseModel) else value
    console.print(Panel(Pretty(body, expand_all=True), title=label, title_align="left", border_style=style))


def show_event(event) -> None:
    for call in event.get_function_calls():
        show(f"{event.author} calls {call.name}", dict(call.args or {}), "yellow")
    for result in event.get_function_responses():
        show(f"{result.name} returned", result.response, "magenta")
    if event.is_final_response() and event.content and event.content.parts and event.content.parts[0].text:
        show(f"{event.author} answers", event.content.parts[0].text)


class StepLogger:
    def step(self, name: str) -> RunnableLambda:
        def _show_value(value):
            show(name, value)
            return value

        return RunnableLambda(_show_value)
