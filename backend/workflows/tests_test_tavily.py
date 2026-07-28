import pytest
from workflows.utils.tools_registery import ToolRegistry, TavilySearchTool


class DummySearch:
    def __init__(self, results, max_results=10):
        self._results = results
        self.max_results = max_results

    def run(self, query):
        # ignore query, return preset list
        return self._results


@pytest.fixture(autouse=True)
def register_tavily(tmp_path, monkeypatch):
    # ensure registry has the correct tool
    ToolRegistry._tools.clear()
    from workflows.utils.tools_registery import register_search_tools
    register_search_tools()
    yield


def test_tavily_tool_respects_max_results(monkeypatch):
    # create tool with dummy search that returns 20 items
    dummy_results = [{'title': f't{i}'} for i in range(20)]
    monkeypatch.setattr(
        'workflows.utils.tools_registery.TavilySearchTool.__init__',
        lambda self, api_key: setattr(self, 'search', DummySearch(dummy_results, max_results=5))
    )
    tool = ToolRegistry.get_tool('tavily_search', {'tavily_search': 'fake'})
    out = tool._run('anything')
    assert isinstance(out, list)
    assert len(out) == 5


def test_tavily_tool_handles_error(monkeypatch):
    class BrokenSearch:
        def run(self, query):
            raise RuntimeError('oops')

    monkeypatch.setattr(
        'workflows.utils.tools_registery.TavilySearchTool.__init__',
        lambda self, api_key: setattr(self, 'search', BrokenSearch())
    )
    tool = ToolRegistry.get_tool('tavily_search', {'tavily_search': 'fake'})
    out = tool._run('x')
    assert isinstance(out, list)
    assert out and 'error' in out[0]
