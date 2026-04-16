"""Pipeline pattern for journey search workflow.

This module implements a flexible pipeline architecture that allows
easy modification and extension of the search workflow.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.journeys.schemas import JourneySearchRequest, JourneySearchResponse
from app.journeys.utils import _build_journey_result
from app.models import Segment, Timetable
from app.planner.exceptions import NoRoutesFoundError, NoTimetableDataError
from app.planner.index import build_station_index
from app.planner.query import CompiledQuery, compile_query
from app.planner.ranking import (
    apply_display_limit,
    exclude_direct_train_codes_in_transfer_routes,
    filter_routes_by_display_train_types,
    group_and_rank,
)
from app.planner.search import search_journeys
from app.railway.repository import TimetableRepository

logger = logging.getLogger(__name__)


@dataclass
class SearchContext:
    """Context object passed through the pipeline.

    Contains all data needed for the search workflow, including
    intermediate results from each pipeline step.
    """

    request: JourneySearchRequest
    compiled_query: CompiledQuery | None = None
    timetable: Timetable | None = None
    station_index: dict | None = None
    routes: list[list[Segment]] = field(default_factory=list)
    ranked_routes: list[list[Segment]] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Step name for logging."""

    @abstractmethod
    async def execute(self, context: SearchContext) -> SearchContext:
        """Execute the step and return updated context."""

    async def run(self, context: SearchContext) -> SearchContext:
        """Run the step with timing and logging."""
        start = time.time()
        logger.info(f"[Pipeline] Starting step: {self.name}")

        try:
            context = await self.execute(context)
            duration = time.time() - start
            context.metrics[self.name] = duration
            logger.info(f"[Pipeline] Completed step: {self.name} ({duration:.3f}s)")
            return context
        except Exception as e:
            logger.error(f"[Pipeline] Failed step: {self.name} - {e}")
            raise


class CompileQueryStep(PipelineStep):
    @property
    def name(self) -> str:
        return "compile_query"

    async def execute(self, context: SearchContext) -> SearchContext:
        context.compiled_query = compile_query(context.request)
        logger.debug(
            f"Query compiled: {context.compiled_query.from_station} → "
            f"{context.compiled_query.to_station}, "
            f"transfers={context.compiled_query.transfer_values}"
        )
        return context


class LoadTimetableStep(PipelineStep):
    def __init__(self, timetable_repo: TimetableRepository) -> None:
        self._timetable_repo = timetable_repo

    @property
    def name(self) -> str:
        return "load_timetable"

    async def execute(self, context: SearchContext) -> SearchContext:
        if context.compiled_query is None:
            raise ValueError("CompiledQuery not found in context")

        context.timetable = await self._timetable_repo.load_timetable(
            run_date=context.compiled_query.run_date,
            filter_running_only=context.compiled_query.filter_running_only,
        )

        if not context.timetable:
            raise NoTimetableDataError(context.compiled_query.run_date)

        context.station_index = build_station_index(context.timetable)
        logger.debug(f"Loaded {len(context.timetable)} trains")
        return context


class SearchRoutesStep(PipelineStep):
    @property
    def name(self) -> str:
        return "search_routes"

    async def execute(self, context: SearchContext) -> SearchContext:
        if context.compiled_query is None or context.timetable is None:
            raise ValueError("Required data not found in context")

        compiled = context.compiled_query
        context.routes = search_journeys(
            from_stations={compiled.from_station},
            to_stations={compiled.to_station},
            transfer_values=compiled.transfer_values,
            min_transfer_minutes=compiled.min_transfer_minutes,
            max_transfer_minutes=compiled.max_transfer_minutes,
            arrival_deadline_abs_min=compiled.arrival_deadline_abs_min,
            departure_time_start_min=compiled.departure_time_start_min,
            departure_time_end_min=compiled.departure_time_end_min,
            departure_time_cross_day=compiled.departure_time_cross_day,
            excluded_transfer_stations=compiled.excluded_transfer_stations,
            allowed_transfer_stations=compiled.allowed_transfer_stations,
            allowed_train_type_prefixes=compiled.allowed_train_type_prefixes,
            excluded_train_type_prefixes=compiled.excluded_train_type_prefixes,
            excluded_train_tokens=compiled.excluded_train_tokens,
            allowed_train_tokens=compiled.allowed_train_tokens,
            timetable=context.timetable,
            station_index=context.station_index,
        )

        logger.debug(f"Found {len(context.routes)} raw routes")
        return context


class FilterRoutesStep(PipelineStep):
    @property
    def name(self) -> str:
        return "filter_routes"

    async def execute(self, context: SearchContext) -> SearchContext:
        if context.compiled_query is None:
            raise ValueError("CompiledQuery not found in context")

        compiled = context.compiled_query
        context.routes = exclude_direct_train_codes_in_transfer_routes(
            context.routes,
            compiled.exclude_direct_train_codes_in_transfer_routes,
        )
        context.routes = filter_routes_by_display_train_types(
            context.routes,
            compiled.display_train_types,
        )

        logger.debug(f"After filtering: {len(context.routes)} routes")
        return context


class RankRoutesStep(PipelineStep):
    @property
    def name(self) -> str:
        return "rank_routes"

    async def execute(self, context: SearchContext) -> SearchContext:
        if context.compiled_query is None:
            raise ValueError("CompiledQuery not found in context")

        compiled = context.compiled_query
        context.ranked_routes = group_and_rank(
            context.routes,
            sort_by=compiled.sort_by,
            top_n_per_sequence=compiled.train_sequence_top_n,
        )

        logger.debug(f"After ranking: {len(context.ranked_routes)} routes")
        return context


class LimitResultsStep(PipelineStep):
    @property
    def name(self) -> str:
        return "limit_results"

    async def execute(self, context: SearchContext) -> SearchContext:
        if context.compiled_query is None:
            raise ValueError("CompiledQuery not found in context")

        context.ranked_routes = apply_display_limit(
            context.ranked_routes,
            context.compiled_query.display_limit,
        )

        logger.debug(f"Final results: {len(context.ranked_routes)} routes")
        return context


class SearchPipeline:
    """Main pipeline orchestrator for journey search."""

    def __init__(self, timetable_repo: TimetableRepository) -> None:
        self.steps: list[PipelineStep] = [
            CompileQueryStep(),
            LoadTimetableStep(timetable_repo),
            SearchRoutesStep(),
            FilterRoutesStep(),
            RankRoutesStep(),
            LimitResultsStep(),
        ]

    async def execute(self, request: JourneySearchRequest) -> JourneySearchResponse:
        start_time = time.time()
        context = SearchContext(request=request)

        for step in self.steps:
            context = await step.run(context)

        if not context.ranked_routes:
            raise NoRoutesFoundError(
                context.compiled_query.from_station,
                context.compiled_query.to_station,
            )

        journeys = [_build_journey_result(route) for route in context.ranked_routes]

        total_duration = time.time() - start_time
        logger.info(
            f"[Pipeline] Search completed in {total_duration:.3f}s, "
            f"found {len(journeys)} journeys"
        )

        return JourneySearchResponse(
            journeys=journeys,
            total=len(journeys),
            date=context.compiled_query.run_date,
        )
