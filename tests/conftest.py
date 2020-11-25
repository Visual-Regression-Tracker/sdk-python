import nest_asyncio

# resolve "Cannot run the event loop while another loop is running" in async tests
nest_asyncio.apply()