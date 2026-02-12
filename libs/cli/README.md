# 🧠🤖 Deep Agents CLI

[![PyPI - Version](https://img.shields.io/pypi/v/deepagents-cli?label=%20)](https://pypi.org/project/deepagents-cli/#history)
[![PyPI - License](https://img.shields.io/pypi/l/deepagents-cli)](https://opensource.org/licenses/MIT)
[![PyPI - Downloads](https://img.shields.io/pepy/dt/deepagents-cli)](https://pypistats.org/packages/deepagents-cli)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/langchain.svg?style=social&label=Follow%20%40LangChain)](https://x.com/langchain)

Looking for the JS/TS version? Check out [Deep Agents CLI.js](https://github.com/langchain-ai/deepagentsjs).

To help you ship LangChain apps to production faster, check out [LangSmith](https://smith.langchain.com).
LangSmith is a unified developer platform for building, testing, and monitoring LLM applications.

<p align="center">
  <img src="https://raw.githubusercontent.com/langchain-ai/deepagents/main/libs/cli/images/cli.png" alt="Deep Agents CLI" width="600"/>
</p>

## Quick Install

```bash
uv tool install deepagents-cli
deepagents-custom
```

## Model providers

The CLI supports selecting a model with `--model`. You can either let the CLI auto-detect the provider from the model name (e.g., `gpt-*`, `claude-*`, `gemini-*`), or specify it explicitly as `provider:model`.

In the interactive UI, run `/model` to see which providers are configured from your environment.

### Ollama (local)

Uses Ollama's OpenAI-compatible server.

```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"
export OLLAMA_MODEL="llama3"

deepagents-custom --model ollama:llama3
```

### LM Studio (local)

Uses LM Studio's OpenAI-compatible server.

```bash
export LMSTUDIO_BASE_URL="http://localhost:1234/v1"
export LMSTUDIO_MODEL="your-model"

deepagents-custom --model lmstudio:your-model
```

### Azure OpenAI (custom domain supported)

Provide a full endpoint URL (including custom domains) and your deployment name.

```bash
export AZURE_OPENAI_ENDPOINT="https://ai.mycorp.com/"
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_API_VERSION="2024-10-21"
export AZURE_OPENAI_DEPLOYMENT="my-deployment"

deepagents-custom --model azure:my-deployment
```

## 🤔 What is this?

Using an LLM to call tools in a loop is the simplest form of an agent. This architecture, however, can yield agents that are "shallow" and fail to plan and act over longer, more complex tasks.

Applications like "Deep Research", "Manus", and "Claude Code" have gotten around this limitation by implementing a combination of four things: a **planning tool**, **sub agents**, access to a **file system**, and a **detailed prompt**.

`deepagents` is a Python package that implements these in a general purpose way so that you can easily create a Deep Agent for your application. For a full overview and quickstart of Deep Agents, the best resource is our [docs](https://docs.langchain.com/oss/python/deepagents/overview).

**Acknowledgements: This project was primarily inspired by Claude Code, and initially was largely an attempt to see what made Claude Code general purpose, and make it even more so.**

## 📖 Resources

- **[Documentation](https://docs.langchain.com/oss/python/deepagents/cli)** — Full documentation
- **[Deep Agents](https://github.com/langchain-ai/deepagents)** — The underlying agent harness
- **[Chat LangChain](https://chat.langchain.com)** - Chat interactively with the docs

## 📕 Releases & Versioning

See our [Releases](https://docs.langchain.com/oss/python/release-policy) and [Versioning](https://docs.langchain.com/oss/python/versioning) policies.

## 💁 Contributing

As an open-source project in a rapidly developing field, we are extremely open to contributions, whether it be in the form of a new feature, improved infrastructure, or better documentation.

For detailed information on how to contribute, see the [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview).
