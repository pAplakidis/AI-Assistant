from constants import *
from message_bus import MessageBus

class ToolExecutor:
  def __init__(self, bus: MessageBus, model=MISTRAL_INSTRUCT):
    self.bus = bus
    self.model = model

  def execute(self, tool_name, args):
    pass

  # TODO: like research previously did, use the model to decide which tools to use and in what order, then execute them and feed results back to the model until we have a final answer or code to execute
  def tool_executor_loop(self):
    pass
