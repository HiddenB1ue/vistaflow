"""Shared pagination models and utilities."""

from __future__ import annotations

from math import ceil

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Base pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    pageSize: int = Field(default=20, ge=1, le=100, description="Items per page")


class TaskListQuery(PaginationParams):
    """Query parameters for tasks list."""

    keyword: str = Field(default="", description="Search keyword")
    status: str = Field(default="all", description="Filter by status")


class SystemLogsQuery(PaginationParams):
    """Query parameters for system logs."""

    keyword: str = Field(default="", description="Search keyword")
    severity: str = Field(default="all", description="Filter by severity")
    pageSize: int = Field(default=50, ge=1, le=500)


class TaskRunsQuery(PaginationParams):
    """Query parameters for task runs."""

    pass


class TaskRunLogsQuery(PaginationParams):
    """Query parameters for task run logs."""

    pageSize: int = Field(default=100, ge=1, le=1000)


class PaginatedResponse[T](BaseModel):
    """Generic paginated response."""

    items: list[T]
    page: int
    pageSize: int
    total: int
    totalPages: int


def create_paginated_response[T](
    items: list[T], page: int, page_size: int, total: int
) -> PaginatedResponse[T]:
    """Helper function to create a paginated response with calculated totalPages.

    Args:
        items: List of items for the current page
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total: Total number of items across all pages

    Returns:
        PaginatedResponse with all fields populated
    """
    total_pages = ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        page=page,
        pageSize=page_size,
        total=total,
        totalPages=total_pages,
    )
