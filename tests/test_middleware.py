import pytest
from dataclasses import dataclass
from typing import List, Optional
from wd.di.middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
)
from wd.di import ServiceCollection


@dataclass
class RequestContext:
    path: str
    value: Optional[str] = None


class HelperTestMiddleware(IMiddleware):
    def __init__(self):
        self.executed = False
        self.context_path = None

    async def invoke(self, context: RequestContext, next):
        self.executed = True
        self.context_path = context.path
        return await next()


class ModifyingMiddleware(IMiddleware):
    async def invoke(self, context: RequestContext, next):
        context.value = "modified"
        return await next()


class ResultMiddleware(IMiddleware):
    async def invoke(self, context: RequestContext, next):
        await next()
        return "result"


@pytest.mark.asyncio
async def test_middleware_pipeline_execution():
    pipeline = MiddlewarePipeline()
    middleware = HelperTestMiddleware()
    pipeline.use_middleware(HelperTestMiddleware, instance=middleware)

    context = RequestContext(path="/test")
    await pipeline.execute(context)

    assert middleware.executed
    assert middleware.context_path == "/test"


@pytest.mark.asyncio
async def test_middleware_order():
    executed_order: List[str] = []

    class FirstMiddleware(IMiddleware):
        async def invoke(self, context, next):
            executed_order.append("first")
            return await next()

    class SecondMiddleware(IMiddleware):
        async def invoke(self, context, next):
            executed_order.append("second")
            return await next()

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(FirstMiddleware)
    pipeline.use_middleware(SecondMiddleware)

    await pipeline.execute(RequestContext(path="/test"))
    assert executed_order == ["first", "second"]


@pytest.mark.asyncio
async def test_middleware_modification():
    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(ModifyingMiddleware)

    context = RequestContext(path="/test")
    await pipeline.execute(context)

    assert context.value == "modified"


@pytest.mark.asyncio
async def test_middleware_result():
    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(ResultMiddleware)

    result = await pipeline.execute(RequestContext(path="/test"))
    assert result == "result"


@pytest.mark.asyncio
async def test_validation_middleware():
    def validator(context: RequestContext) -> bool:
        return context.path.startswith("/")

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(lambda: ValidationMiddleware(validator))

    # Valid path should work
    await pipeline.execute(RequestContext(path="/test"))

    # Invalid path should raise ValueError
    with pytest.raises(ValueError):
        await pipeline.execute(RequestContext(path="invalid"))


@pytest.mark.asyncio
async def test_caching_middleware():
    executed_count = 0

    class CountingMiddleware(IMiddleware):
        async def invoke(self, context, next):
            nonlocal executed_count
            executed_count += 1
            return "result"

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(CachingMiddleware)
    pipeline.use_middleware(CountingMiddleware)

    context = RequestContext(path="/test")

    # First call should execute the pipeline
    result1 = await pipeline.execute(context)
    assert result1 == "result"
    assert executed_count == 1

    # Second call should use cached result
    result2 = await pipeline.execute(context)
    assert result2 == "result"
    assert executed_count == 1  # Count shouldn't increase


@pytest.mark.asyncio
async def test_logging_middleware():
    logs = []
    logger = lambda msg: logs.append(msg)

    pipeline = MiddlewarePipeline()
    pipeline.use_middleware(lambda: LoggingMiddleware(logger))
    pipeline.use_middleware(ResultMiddleware)

    await pipeline.execute(RequestContext(path="/test"))

    assert len(logs) == 2
    assert "Executing pipeline" in logs[0]
    assert "completed with result" in logs[1]


@pytest.mark.asyncio
async def test_di_integration():
    services = ServiceCollection()

    app = services.create_application_builder()

    app.configure_middleware(
        lambda builder: (
            builder.use_middleware(LoggingMiddleware)
            .use_middleware(HelperTestMiddleware)
            .use_middleware(ResultMiddleware)
        )
    )

    provider = app.build()

    pipeline = provider.get_service(MiddlewarePipeline)

    result = await pipeline.execute(RequestContext(path="/test"))

    assert result == "result"


@pytest.mark.asyncio
async def test_di_middleware_dependencies():
    services = ServiceCollection()

    class DependentMiddleware(IMiddleware):
        def __init__(self, test_middleware: HelperTestMiddleware):
            self.test_middleware = test_middleware

        async def invoke(self, context, next):
            await self.test_middleware.invoke(context, next)
            return "dependent_result"

    app = services.create_application_builder()

    app.configure_middleware(
        lambda builder: (
            builder.use_middleware(HelperTestMiddleware).use_middleware(DependentMiddleware)
        )
    )

    provider = app.build()

    pipeline = provider.get_service(MiddlewarePipeline)

    result = await pipeline.execute(RequestContext(path="/test"))

    assert result == "dependent_result"
