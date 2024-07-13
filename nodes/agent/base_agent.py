from griptape.tools import TaskMemoryClient

# from server import PromptServer
from ...py.griptape_config import get_config
from .agent import gtComfyAgent

default_prompt = "{{ input_string }}"


def get_default_config():
    return get_config("agent_config")


class BaseAgent:
    """
    Create a Griptape Agent
    """

    def __init__(self):
        self.default_prompt = default_prompt
        self.agent = gtComfyAgent()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "agent": (
                    "AGENT",
                    {
                        "forceInput": True,
                    },
                ),
                "config": (
                    "CONFIG",
                    {
                        "forceInput": True,
                    },
                ),
                "tools": ("TOOL_LIST", {"forceInput": True, "INPUT_IS_LIST": True}),
                "rulesets": ("RULESET", {"forceInput": True}),
                "input_string": (
                    "STRING",
                    {
                        "forceInput": True,
                        "dynamicPrompts": True,
                    },
                ),
                "STRING": (
                    "STRING",
                    {"multiline": True, "dynamicPrompts": True},
                ),
            },
        }

    RETURN_TYPES = (
        "STRING",
        "AGENT",
    )
    RETURN_NAMES = (
        "OUTPUT",
        "AGENT",
    )
    FUNCTION = "run"

    OUTPUT_NODE = True

    CATEGORY = "Griptape/Agent"

    # def set_default_config(self):
    #     agent_config = get_config("agent_config")
    #     if agent_config:
    #         self.agent.config = BaseStructureConfig.from_dict(agent_config)

    # def model_check(self):
    #     # There are certain models that can't handle Tools well.
    #     # If this agent is using one of those models AND they have tools supplied, we'll
    #     # warn the user.
    #     simple_models = ["llama3", "mistral", "LLama-3"]
    #     drivers = ["OllamaPromptDriver", "LMStudioPromptDriver"]
    #     agent_prompt_driver_name = self.agent.config.prompt_driver.__class__.__name__
    #     model = self.agent.config.prompt_driver.model
    #     if agent_prompt_driver_name in drivers:
    #         if model == "":
    #             return (model, True)
    #         for simple in simple_models:
    #             if simple in model:
    #                 if len(self.agent.tools) > 0:
    #                     return (model, True)
    #     return (model, False)

    # def model_response(self, model):
    #     if model == "":
    #         return "You have provided a blank model for the Agent Configuration.\n\nPlease specify a model configuration, or disconnect it from the agent."
    #     else:
    #         return f"This Agent Configuration Model: **{ self.agent.config.prompt_driver.model }** may run into issues using tools.\n\nPlease consider using a different configuration, a different model, or removing tools from the agent and use the **Griptape Run: Tool Task** node for specific tool use."

    def run(
        self,
        STRING,
        config=None,
        tools=[],
        rulesets=[],
        agent=None,
        input_string=None,
    ):
        create_dict = {}

        # Configuration
        if config:
            create_dict["config"] = config
        elif agent:
            create_dict["config"] = agent.config

        # Tools
        # make sure to add TaskMemoryClient if it's not present, and one of the tools has off_prompt set to True
        if len(tools) > 0:
            # Check and see if any of the tools have been set to off_prompt
            off_prompt = False
            for tool in tools:
                if tool.off_prompt:
                    off_prompt = True
                    break
            if off_prompt:
                taskMemoryClient = False
                # check and see if TaskMemoryClient is in tools
                for tool in tools:
                    if isinstance(tool, TaskMemoryClient):
                        taskMemoryClient = True
                        break
                if not taskMemoryClient:
                    tools.append(TaskMemoryClient(off_prompt=False))
                create_dict["tools"] = tools
            create_dict["tools"] = tools
        elif agent:
            create_dict["tools"] = agent.tools

        # Rulesets
        if len(rulesets) > 0:
            create_dict["rulesets"] = rulesets
        elif agent:
            create_dict["rulesets"] = agent.rulesets

        # Memory
        if agent:
            create_dict["conversation_memory"] = agent.conversation_memory
            create_dict["meta_memory"] = agent.meta_memory
            create_dict["task_memory"] = agent.task_memory

        # Now create the agent
        self.agent = gtComfyAgent(**create_dict)

        # if not agent:
        #     self.agent = gtComfyAgent()
        # else:
        #     self.agent = agent

        # if config:
        #     # self.agent.config = config
        #     self.agent = self.agent.update_config(config)

        # Replace bits of the agent based off the inputs
        # if len(tools) > 0:
        #     self.agent.tools = tools
        # if len(rulesets) > 0:
        #     self.agent.rulesets = rulesets
        #     print(self.agent.rulesets)

        # Warn for models
        model, simple_model = self.agent.model_check()
        if simple_model:
            return (self.agent.model_response(model), self.agent)

        # Check for inputs. If none, then just create the agent
        if not input_string and STRING == "":
            output_string = "Agent created."
        else:
            # Get the prompt text
            if not input_string:
                prompt_text = STRING
            else:
                prompt_text = STRING + "\n\n" + input_string

            # # Start to think about sending update messages
            # PromptServer.instance.send_sync(
            #     "comfy.gtUI.textmessage",
            #     {"message": f"Created agent with prompt: {prompt_text}"},
            # )

            result = self.agent.run(prompt_text)
            output_string = result.output_task.output.value
        return (
            output_string,
            self.agent,
        )
