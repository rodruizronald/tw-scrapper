# Pipeline

## Layer Hierarchy

```
main_pipeline_flow -> stage_N_flow -> stage_N_task -> StageNProcessor
```

- **Flows** (`flows/`): Prefect orchestration, concurrency via `asyncio.Semaphore(3)`, result aggregation using `TaskResult`
- **Tasks** (`tasks/`): Prefect `@task` wrappers, instantiate processor and delegate. Retry config varies by stage
- **Stages** (`stages/`): Stateless processor classes with business logic. Receive config in constructor, services created internally

## Adding a New Stage

1. Create `stages/stage_N.py` with a processor class
2. Create `tasks/stage_N_task.py` with a `@task` wrapper that instantiates the processor
3. Create `flows/stage_N_flow.py` with semaphore-based concurrency pattern
4. Add stage config to `pipeline.yaml`
5. Wire into `flows/main_pipeline_flow.py` `_execute_stages()`

## Concurrency Pattern

All async flows (stages 1-5) use the same semaphore pattern:

```python
semaphore = asyncio.Semaphore(3)

async def process_with_semaphore(company, semaphore) -> TaskResult:
    async with semaphore:
        try:
            result = await process_task(company, config)
            return TaskResult.ok(result, company.name)
        except Exception as e:
            return TaskResult.fail(str(e), company.name)
```

Stage 6 iterates sequentially (metrics recording).

## Exception Handling by Layer

**Stage processors** - the main error handling layer:
```python
try:
    result = await self._execute(company)
    status = StageStatus.SUCCESS
    return result
except ValidationError:
    return []                    # Non-retryable: return empty
except (WebExtractionError, OpenAIProcessingError, DatabaseOperationError):
    raise                        # Retryable: propagate for Prefect
except Exception as e:
    raise CompanyProcessingError(company_name, e, stage_tag)  # Wrap unexpected
finally:
    self.metrics_service.record_stage_metrics(...)  # Always record
```

**Tasks** - minimal, just instantiate processor and call. Let exceptions propagate.

**Flows** - catch exceptions per-company via `TaskResult`, never let one company failure stop others.

**Main pipeline flow** - stages 1-5 failures stop the pipeline (`raise`). Stage 6 failure logs warning and continues.

## Config Flow

`PipelineConfig.load()` reads `pipeline.yaml` -> passed to each flow -> passed to task -> task creates processor with it. Processors access `config.stage_N.*` for prompts, `config.openai` / `config.web_extraction` for service config.

## Return Types

- Flows return `dict[str, list[Job]]` (company name -> jobs)
- Tasks return `list[Job]`
- Processors return `list[Job]`

## Logging

Use `get_run_logger()` from Prefect in tasks and flows. Stage processors also use it. Log once per layer - don't duplicate what services already logged.

## Retry Config

| Component | Retries | Delay |
|-----------|---------|-------|
| Stages 1-4 tasks | 0 | N/A (processor handles classification) |
| Stage 5 task | 2 | 30s |
| Sync tasks | 2 | 10s |
