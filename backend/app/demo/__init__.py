"""The playground: the fourth MCP client, and the only one you can watch.

The landing tells a visitor that an agent reaches their domain through the MCP
server. This package lets them see it happen with their own account, from the
browser, without installing anything.

The agent it runs is real: a graph with a node that decides and a node that runs the
tool, and the loop is the one an agent with a model would drive. Here the decisions
are a list, because nothing in this stack calls a model.
"""
