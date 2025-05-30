<img src="https://framerusercontent.com/images/xDisAjh26hdfRjOto5SnUUWvsEQ.svg?scale-down-to=64" width="50" style="position: relative; top: 10px"> Toolhouse Examples

## Intro

Toolhouse is a platform that helps developers integrate AI in their projects, to build powerful AI features and agents.
You can start this journey with only 3 lines of code.

In this repo we'll explore some examples of different ways you can leverage our pre-built tools and create agents that can perform many useful tasks.

We organized this repo in two folders:

- Agents: Agentic projects/demos
- Web: Web-oriented projects/demos

## Examples

Agents:

- Customer Support Agent
- Job Search Agent
- Code assistant

Web:

- arXiv wizard learning: learn with AI audio generated snippets

## ℹ️ Getting started

To follow along these examples we've separated them in sub-folders within this repository. For ease of use, you only have to install the dependencies once.
Each folder uses a different set of Tools hosted and maintained by Toolhouse.

## 🛠️ Installation

Ensure that you have exported into your environment both Toolhouse and Anthropic API Keys.

```
export ANTHROPIC_KEY="your_anthropic_api_key"
export TOOLHOUSE_BEARER_TOKEN="your_toolhouse_bearer_token"
```

Then, to install (from within the folder where this README file lives):

First clone the repo:

```bash
git clone https://github.com/toolhouseai/toolhouse-examples.git
cd toolhouse-examples
```

### Install the required dependencies

Each subproject can optionally have its own set of dependencies. Make sure you installed those too.

#### With virtual environment (Preferred)

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

#### Without virtual env

```bash
pip install -r requirements.txt
```

Finally move to the folder which contains the agent of your choice:

```bash
cd agents/customer-support
```

Start the agent:

```bash
python agent.py
```

## Why build AI Agents

There is a growing interest in creating AI agents - powered by LLMs and tools. The main goal of an AI agent is to complete a task a user gives it. This task might require the agent to perform multiple steps autonomously or with little user intervention. To complete these steps, the LLM powering the agent will require to use function calls (a.k.a tool usage) to interact with other software, for example by calling REST APIs.
Different agents will require different tools to perform their tasks successfully.

## How Toolhouse helps

Today's LLM technology doesn't run any code itself. Instead, you can run code externally: Toolhouse runs the code through the tool chosen by the LLM and on behalf the LLM. Once the tool has run it then tells the LLM what the output was.

Writing good tools is a long and time-consuming exercise which requires a lot of efforts. You have to write definitions of inputs and outputs, robust error handling, handle the infrastructure to host the tool and most importantly effective communication with the model. Every model implements function calling slightly differently. This causes challenges in schema design, logic implementation, and interaction management.

✨ Using Toolhouse - you can use tools that have been written and maintained by developers like you. These tools work with any LLM that supports tool use. As most developers use more than one LLM provider in their deployments, Toolhouse is designed to help you manage your functions across each model.

## Get help

Our growing community awaits you: We're looking forward to meet you and while we focus on subjects relevant to Toolhouse, AI or code we're happy to chat about anything.

[Join us on Discord](https://discord.gg/xPvyBxhHtu)
